
import logging
import sqlite3

from threading import Lock
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field


# Validate incoming network measurements
class Telemetry(BaseModel):
    packet_loss_percent: float = Field(ge=0, le=100)
    latency_ms: float = Field(ge=0)


def create_app():
    app = FastAPI()

    # Create an in-memory database
    db = sqlite3.connect(
        ":memory:",
        check_same_thread=False
    )

    db.execute("""
        CREATE TABLE readings (
            id INTEGER PRIMARY KEY,
            stream_id TEXT NOT NULL,
            packet_loss REAL NOT NULL,
            latency_ms REAL NOT NULL
        )
    """)

    # Protect the shared SQLite connection
    db_lock = Lock()

    app.state.db = db
    app.state.alerts = []

    # Simple authentication for training
    def check_auth(api_key):
        if api_key != "training-key":
            raise HTTPException(
                status_code=401,
                detail="Invalid API key"
            )

    # POST: Submit a new network measurement
    @app.post(
        "/api/streams/{stream_id}/telemetry",
        status_code=201
    )
    def add_telemetry(
        stream_id: str,
        reading: Telemetry,
        x_api_key: str | None = Header(default=None)
    ):
        check_auth(x_api_key)

        # Store telemetry safely in SQL
        with db_lock:
            db.execute(
                "INSERT INTO readings "
                "(stream_id, packet_loss, latency_ms) "
                "VALUES (?, ?, ?)",
                (
                    stream_id,
                    reading.packet_loss_percent,
                    reading.latency_ms
                )
            )
            db.commit()

        # Detect excessive packet loss
        alarm = reading.packet_loss_percent >= 2

        if alarm:
            app.state.alerts.append(stream_id)
            logging.warning(
                "Alarm for stream %s",
                stream_id
            )

        return {
            "stream_id": stream_id,
            "alarm": alarm
        }

    # GET: Retrieve latest stream health
    @app.get("/api/streams/{stream_id}/health")
    def get_health(
        stream_id: str,
        x_api_key: str | None = Header(default=None)
    ):
        check_auth(x_api_key)

        # Safely read the latest measurement
        with db_lock:
            row = db.execute(
                "SELECT packet_loss, latency_ms "
                "FROM readings "
                "WHERE stream_id = ? "
                "ORDER BY id DESC LIMIT 1",
                (stream_id,)
            ).fetchone()

        if row is None:
            raise HTTPException(
                status_code=404,
                detail="Stream not found"
            )

        loss, latency = row

        return {
            "stream_id": stream_id,
            "packet_loss_percent": loss,
            "latency_ms": latency,
            "alarm": loss >= 2
        }

    return app


# Create the application
app = create_app()
