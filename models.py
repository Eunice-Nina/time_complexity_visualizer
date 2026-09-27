"""
SQLAlchemy model used by the /save_analysis endpoint to persist
visualizer runs to a database instead of a JSON file.
"""
import json
from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Analysis(db.Model):
    """A single saved run of the time complexity visualizer."""

    id = db.Column(db.Integer, primary_key=True)
    algorithm = db.Column(db.String(50), nullable=False)
    n_min = db.Column(db.Integer, nullable=False)
    n_max = db.Column(db.Integer, nullable=False)
    step = db.Column(db.Integer, nullable=False)
    input_sizes = db.Column(db.Text, nullable=False)      # stored as a JSON string
    times_seconds = db.Column(db.Text, nullable=False)     # stored as a JSON string
    image_path = db.Column(db.String(255), nullable=False)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    def to_dict(self):
        return {
            "id": self.id,
            "algorithm": self.algorithm,
            "n_min": self.n_min,
            "n_max": self.n_max,
            "step": self.step,
            "input_sizes": json.loads(self.input_sizes),
            "times_seconds": json.loads(self.times_seconds),
            "image_path": self.image_path,
            "created_at": self.created_at.isoformat(),
        }