
import time


# Simulated processing stage
def process_data(sample_input):
    time.sleep(0.05)  # Simulate 50 ms of work
    return [item.upper() for item in sample_input]


def test_stage_latency_and_output():
    sample_input = ["camera_frame_01"]

    start = time.perf_counter()

    result = process_data(sample_input)

    elapsed = time.perf_counter() - start

    print(f"Processing time: {elapsed:.3f} seconds")

    assert isinstance(result, list)
    assert len(result) > 0
    assert elapsed < 0.2
