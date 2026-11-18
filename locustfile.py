
from locust import HttpUser, task, between


class StreamWatchUser(HttpUser):
    # Each simulated user waits 1–2 seconds
    # between tasks.
    wait_time = between(1, 2)

    @task
    def send_telemetry(self):
        self.client.post(
            "/api/streams/camera-01/telemetry",
            headers={
                "x-api-key": "training-key"
            },
            json={
                "packet_loss_percent": 1,
                "latency_ms": 10
            },
            name="/api/streams/[id]/telemetry"
        )
