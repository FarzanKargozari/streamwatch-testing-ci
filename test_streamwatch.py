
import time
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

from streamwatch import create_app


# Training-only API key
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


# Helper function to submit camera telemetry
def send_reading(client, loss, latency=20):
    return client.post(
        "/api/streams/camera-01/telemetry",
        headers=AUTH,
        json={
            "packet_loss_percent": loss,
            "latency_ms": latency
        }
    )


# TEST: Database isolation between cameras
def test_sql_stream_isolation(client):
    # First camera reports 3% packet loss
    response = send_reading(client, 3)
    assert response.status_code == 201

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

    # Verify Camera 02
    row = client.app.state.db.execute(
        "SELECT packet_loss FROM readings "
        "WHERE stream_id = ?",
        ("camera-02",)
    ).fetchone()

    assert row is not None
    assert row[0] == 0.5

    # Verify Camera 01 is unchanged
    camera_01 = client.app.state.db.execute(
        "SELECT packet_loss FROM readings "
        "WHERE stream_id = ?",
        ("camera-01",)
    ).fetchone()

    assert camera_01 is not None
    assert camera_01[0] == 3


# TEST: Packet-loss alarm boundaries
@pytest.mark.parametrize(
    "loss, expected_alarm",
    [
        (0, False),
        (1.5, False),
        (2, True),
        (3, True)
    ]
)
def test_alarm_threshold(client, loss, expected_alarm):
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


# TEST: Request a stream that does not exist
def test_missing_stream(client):
    response = client.get(
        "/api/streams/unknown/health",
        headers=AUTH
    )

    assert response.status_code == 404


# TEST: Reject unauthorized requests
def test_unauthorized_request(client):
    response = client.get(
        "/api/streams/camera-01/health"
    )

    assert response.status_code == 401


# TEST: Reject invalid packet-loss measurements
@pytest.mark.parametrize("loss", [-1, 101])
def test_invalid_packet_loss(client, loss):
    response = send_reading(client, loss)

    assert response.status_code == 422


# TEST: Return the latest measurement
def test_latest_measurement(client):
    response_1 = send_reading(client, 1)
    response_2 = send_reading(client, 3)

    assert response_1.status_code == 201
    assert response_2.status_code == 201

    response = client.get(
        "/api/streams/camera-01/health",
        headers=AUTH
    )

    assert response.status_code == 200

    data = response.json()

    assert data["packet_loss_percent"] == 3
    assert data["alarm"] is True


# TEST: Verify telemetry is stored in SQLite
def test_database_storage(client):
    response = send_reading(client, 3)

    assert response.status_code == 201

    row = client.app.state.db.execute(
        "SELECT packet_loss "
        "FROM readings WHERE stream_id = ?",
        ("camera-01",)
    ).fetchone()

    assert row is not None
    assert row[0] == 3


# TEST: Verify packet-loss alarm notification
def test_alarm_notification(client):
    response = send_reading(client, 3)

    assert response.status_code == 201
    assert "camera-01" in client.app.state.alerts


# TEST: Reject negative latency
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


# TEST: Store high-latency readings correctly
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


# TEST: Measure one API response time
def test_api_response_time(client):
    start = time.perf_counter()

    response = client.post(
        "/api/streams/camera-01/telemetry",
        headers=AUTH,
        json={
            "packet_loss_percent": 2,
            "latency_ms": 10
        }
    )

    duration = time.perf_counter() - start

    print(
        f"API response time: "
        f"{duration * 1000:.2f} ms"
    )

    assert response.status_code == 201
    assert duration < 0.5


# TEST: Measure average API response time
def test_average_api_response_time(client):
    durations = []

    for _ in range(100):
        start = time.perf_counter()

        response = send_reading(
            client,
            loss=1
        )

        duration = time.perf_counter() - start
        durations.append(duration * 1000)

        assert response.status_code == 201

    average = sum(durations) / len(durations)
    slowest = max(durations)

    print(
        f"Average response time: "
        f"{average:.2f} ms"
    )

    print(
        f"Slowest response: "
        f"{slowest:.2f} ms"
    )

    assert average < 500


# TEST: Concurrent requests with separate applications
def test_concurrent_api_requests():
    def send_request(camera_id):
        app = create_app()

        try:
            with TestClient(app) as test_client:
                response = test_client.post(
                    f"/api/streams/{camera_id}/telemetry",
                    headers=AUTH,
                    json={
                        "packet_loss_percent": 1,
                        "latency_ms": 10
                    }
                )

                return response.status_code

        finally:
            app.state.db.close()

    camera_ids = [
        f"camera-{i}"
        for i in range(5)
    ]

    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(
            executor.map(send_request, camera_ids)
        )

    print(
        f"Separate application responses: {results}"
    )

    assert all(code == 201 for code in results)


# TEST: SQLite concurrency regression and data integrity
def test_concurrent_shared_api(client):
    def send_request(camera_id):
        response = client.post(
            f"/api/streams/{camera_id}/telemetry",
            headers=AUTH,
            json={
                "packet_loss_percent": 1,
                "latency_ms": 10
            }
        )

        return response.status_code

    camera_ids = [
        f"camera-{i}"
        for i in range(5)
    ]

    # 10 batches of 5 concurrent requests = 50 requests
    for batch in range(10):
        with ThreadPoolExecutor(max_workers=5) as executor:
            results = list(
                executor.map(send_request, camera_ids)
            )

        print(
            f"Batch {batch + 1}: {results}"
        )

        assert all(code == 201 for code in results)

    # Verify exactly 10 stored measurements per camera
    for camera_id in camera_ids:
        rows = client.app.state.db.execute(
            "SELECT packet_loss FROM readings "
            "WHERE stream_id = ?",
            (camera_id,)
        ).fetchall()

        assert len(rows) == 10
        assert all(row[0] == 1 for row in rows)

    print(
        "Concurrency regression test passed: "
        "50 readings verified."
    )
