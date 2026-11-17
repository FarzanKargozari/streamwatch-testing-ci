
import pytest

from fastapi.testclient import TestClient
from streamwatch import create_app


def test_sql_stream_isolation(client):
    # First camera reports 3% packet loss
    send_reading(client, 3)

    # Second camera reports 0.5% packet loss
    response = client.post(
        "/api/streams/camera-02/telemetry",
        headers=AUTH,
        json={
            "packet_loss_percent": 0.5,
            "latency_ms": 10
        }
    )
    assert response.status_code == 201

    # Query the SQL database for camera-02
    row = client.app.state.db.execute(
        "SELECT packet_loss FROM readings "
        "WHERE stream_id = ?",
        ("camera-02",)
    ).fetchone()

    assert row is not None
    assert row[0] == 0.5
    # Verify Camera 01 still has its own measurement
    camera_01 = client.app.state.db.execute(
        "SELECT packet_loss FROM readings "
        "WHERE stream_id = ?",
        ("camera-01",)
    ).fetchone()

    assert camera_01 is not None
    assert camera_01[0] == 3




AUTH = {"x-api-key": "training-key"}


# Create a fresh application for each test
@pytest.fixture
def client():
    app = create_app()

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.state.db.close()


# Helper function to submit telemetry
def send_reading(client, loss, latency=20):
    return client.post(
        "/api/streams/camera-01/telemetry",
        headers=AUTH,
        json={
            "packet_loss_percent": loss,
            "latency_ms": latency
        }
    )


# TEST 1-4: Alarm threshold boundaries
@pytest.mark.parametrize(
    "loss, expected_alarm",
    [
        (0, False),
        (1.5, False),
        (2, True),
        (3, True)
    ]
)
def test_alarm_threshold(
    client, loss, expected_alarm
):
    response = send_reading(client, loss)

    assert response.status_code == 201

    response = client.get(
        "/api/streams/camera-01/health",
        headers=AUTH
    )

    assert response.status_code == 200


    data = response.json()

    assert data["stream_id"] == "camera-01"
    assert data["packet_loss_percent"] == loss
    assert data["alarm"] is expected_alarm


# TEST 5: Missing stream
def test_missing_stream(client):
    response = client.get(
        "/api/streams/unknown/health",
        headers=AUTH
    )

    assert response.status_code == 404


# TEST 6: Unauthorized access
def test_unauthorized_request(client):
    response = client.get(
        "/api/streams/camera-01/health"
    )

    assert response.status_code == 401


# TEST 7-8: Invalid packet loss
@pytest.mark.parametrize("loss", [-1, 101])
def test_invalid_packet_loss(client, loss):
    response = send_reading(client, loss)

    assert response.status_code == 422


# TEST 9: Latest measurement
def test_latest_measurement(client):
    send_reading(client, 1)
    send_reading(client, 3)

    response = client.get(
        "/api/streams/camera-01/health",
        headers=AUTH
    )

    data = response.json()

    assert response.status_code == 200
    assert data["packet_loss_percent"] == 3
    assert data["alarm"] is True


# TEST 10: SQL database storage
def test_database_storage(client):
    send_reading(client, 3)

    row = client.app.state.db.execute(
        "SELECT packet_loss "
        "FROM readings WHERE stream_id = ?",
        ("camera-01",)
    ).fetchone()

    assert row is not None
    assert row[0] == 3


# TEST 11: Alarm notification
def test_alarm_notification(client):
    send_reading(client, 3)

    assert "camera-01" in client.app.state.alerts


def test_negative_latency(client):
    response = client.post(
        "/api/streams/camera-01/telemetry",
        headers=AUTH,
        json={
            "packet_loss_percent": 2,
            "latency_ms": -10
        }
    )

    assert response.status_code == 422
    errors = response.json()["detail"]
    assert errors[0]["loc"][-1] == "latency_ms"

    #Add a high-latency test

def test_high_latency_storage(client):
    response = send_reading(
        client,
        loss=1,
        latency=500
    )

    assert response.status_code == 201

    row = client.app.state.db.execute(
        "SELECT latency_ms FROM readings "
        "WHERE stream_id = ?",
        ("camera-01",)
    ).fetchone()

    assert row is not None
    assert row[0] == 500
