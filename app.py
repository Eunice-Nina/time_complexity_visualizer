import io
import os
import json
import time
import base64

import matplotlib
matplotlib.use("Agg")  # non-interactive backend, safe for a server process
import matplotlib.pyplot as plt

from datetime import timedelta

from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity

from algorithms import ALGORITHMS
from models import db, Analysis, User

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
os.makedirs(STATIC_DIR, exist_ok=True)

# Database setup: analyses saved via /save_analysis go into a SQLite
# file (analysis.db) instead of a JSON file, using SQLAlchemy as the
# only place SQL is written.
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(BASE_DIR, 'analysis.db')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

# JWT setup: token must arrive in the Authorization header as
# "Bearer <token>" -- query-string tokens are NOT accepted.
app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "change-me-in-production-use-a-32-byte-key")
app.config["JWT_TOKEN_LOCATION"] = ["headers"]
app.config["JWT_HEADER_NAME"] = "Authorization"
app.config["JWT_HEADER_TYPE"] = "Bearer"
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
jwt = JWTManager(app)


@jwt.unauthorized_loader
def missing_token(reason):
    return jsonify({"error": "I don't know you"}), 401


@jwt.invalid_token_loader
def invalid_token(reason):
    return jsonify({"error": "Bye"}), 401


@jwt.expired_token_loader
def expired_token(jwt_header, jwt_payload):
    return jsonify({"error": "Bye"}), 401

with app.app_context():
    db.create_all()


def time_complexity_visualizer(algo_name, n_min, n_max, n_step):
    """
    Runs `algo_name` across a range of input sizes, times each run,
    plots running time vs input size, saves the plot as a PNG in
    static/, and returns the raw data plus a base64 encoding of the
    image.
    """
    algorithm = ALGORITHMS[algo_name]

    input_sizes = list(range(n_min, n_max + n_step, n_step))
    # n=0 is degenerate for several algorithms (e.g. binary search on an
    # empty list), so nudge the first point up to 1 if it landed on 0.
    if input_sizes and input_sizes[0] == 0:
        input_sizes[0] = 1

    times = []
    for n in input_sizes:
        start = time.time()
        algorithm(n)
        end = time.time()
        times.append(end - start)

    fig, ax = plt.subplots()
    ax.plot(input_sizes, times, "o-")
    ax.set_xlabel("Input Size (n)")
    ax.set_ylabel("Running Time (seconds)")
    ax.set_title(f"Time Complexity: {algo_name}")

    filename = f"{algo_name}_plot.png"
    filepath = os.path.join(STATIC_DIR, filename)
    fig.savefig(filepath)

    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    buf.seek(0)
    encoded_image = base64.b64encode(buf.read()).decode("utf-8")
    plt.close(fig)

    return input_sizes, times, encoded_image, filepath


@app.route("/analyze", methods=["GET"])
def analyze():
    algo = request.args.get("algo")
    step = request.args.get("step", type=int)
    n_max = request.args.get("n_max", type=int)

    if not algo or step is None or n_max is None:
        return jsonify({
            "error": "Missing required query params: algo, step, n_max"
        }), 400

    # tolerate the example URL's stray quotes/brackets, e.g. algo=['linear_search']
    algo = algo.strip("[]'\" ")

    if algo not in ALGORITHMS:
        return jsonify({
            "error": f"Unsupported algorithm: {algo}",
            "supported_algorithms": sorted(ALGORITHMS.keys())
        }), 400

    if step <= 0 or n_max <= 0:
        return jsonify({"error": "step and n_max must be positive integers"}), 400

    input_sizes, times, encoded_image, filepath = time_complexity_visualizer(
        algo, 0, n_max, step
    )

    return jsonify({
        "algorithm": algo,
        "n_min": 0,
        "n_max": n_max,
        "step": step,
        "input_sizes": input_sizes,
        "times_seconds": times,
        "image_path": filepath,
        "image_base64": encoded_image
    })


@app.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return jsonify({"error": "username and password are required"}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({"error": "username already taken"}), 409
    user = User(username=username)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return jsonify({"message": "User registered successfully"}), 201


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    user = User.query.filter_by(username=data.get("username")).first()
    if not user or not user.check_password(data.get("password", "")):
        return jsonify({"error": "Invalid credentials"}), 401
    token = create_access_token(identity=str(user.id))
    return jsonify({"access_token": token}), 200


@app.route("/save_analysis", methods=["POST"])
@jwt_required()
def save_analysis():
    algo = request.args.get("algo")
    step = request.args.get("step", type=int)
    n_max = request.args.get("n_max", type=int)

    if not algo or step is None or n_max is None:
        return jsonify({
            "error": "Missing required query params: algo, step, n_max"
        }), 400

    # tolerate the example URL's stray quotes/brackets, e.g. algo=['linear_search']
    algo = algo.strip("[]'\" ")

    if algo not in ALGORITHMS:
        return jsonify({
            "error": f"Unsupported algorithm: {algo}",
            "supported_algorithms": sorted(ALGORITHMS.keys())
        }), 400

    if step <= 0 or n_max <= 0:
        return jsonify({"error": "step and n_max must be positive integers"}), 400

    input_sizes, times, encoded_image, filepath = time_complexity_visualizer(
        algo, 0, n_max, step
    )

    # Persist the run through SQLAlchemy (no raw SQL, no JSON file) —
    # the lists are stored as JSON-encoded text columns.
    analysis = Analysis(
        algorithm=algo,
        n_min=0,
        n_max=n_max,
        step=step,
        input_sizes=json.dumps(input_sizes),
        times_seconds=json.dumps(times),
        image_path=filepath,
    )
    db.session.add(analysis)
    db.session.commit()

    return jsonify({
        "message": "Analysis saved successfully",
        "analysis": analysis.to_dict()
    }), 201


@app.route("/analyses", methods=["GET"])
def list_analyses():
    """List previously saved analyses (newest first)."""
    analyses = Analysis.query.order_by(Analysis.created_at.desc()).all()
    return jsonify([a.to_dict() for a in analyses])


@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "message": "Time complexity visualizer API",
        "usage": "/analyze?algo=<name>&step=<int>&n_max=<int>",
        "auth_usage": "POST /register and POST /login (JSON: username, password) -> access_token",
        "save_usage": "POST /save_analysis?algo=<name>&step=<int>&n_max=<int> (header: Authorization: Bearer <token>)",
        "list_usage": "/analyses",
        "supported_algorithms": sorted(ALGORITHMS.keys())
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)