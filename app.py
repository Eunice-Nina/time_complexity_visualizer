import io
import os
import time
import base64

import matplotlib
matplotlib.use("Agg")  # non-interactive backend, safe for a server process
import matplotlib.pyplot as plt

from flask import Flask, request, jsonify

from algorithms import ALGORITHMS

app = Flask(__name__)

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
os.makedirs(STATIC_DIR, exist_ok=True)


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


@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "message": "Time complexity visualizer API",
        "usage": "/analyze?algo=<name>&step=<int>&n_max=<int>",
        "supported_algorithms": sorted(ALGORITHMS.keys())
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)