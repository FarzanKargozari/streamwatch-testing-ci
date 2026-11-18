
# StreamWatch — API Testing & CI/CD Automation

[![StreamWatch Automated Tests](https://github.com/FarzanKargozari/streamwatch-testing-ci/actions/workflows/tests.yml/badge.svg)](https://github.com/FarzanKargozari/streamwatch-testing-ci/actions/workflows/tests.yml)


A Python-based software testing project simulating video-stream telemetry monitoring, featuring REST API testing, database validation, network failure simulation, concurrent requests, and Jenkins CI/CD automation.

## Technologies

- Python
- Pytest and pytest-cov
- FastAPI and Uvicorn
- SQLite
- unittest.mock
- Bash and Git
- Jenkins CI/CD

## Features

- REST endpoints for camera telemetry and health monitoring
- API-key authentication (dummy training credential)
- Input validation and error handling
- Packet-loss alarm detection
- SQLite telemetry storage
- Thread-safe database access for the shared connection
- Network timeout and retry simulation
- Concurrent request testing

## Automated Testing

The project currently includes 26 passing Pytest tests covering:

- API functionality and HTTP status codes
- Authentication and invalid input
- Packet-loss alarm thresholds
- Database storage and stream isolation
- Network timeout and retry behavior
- API response-time measurements
- Concurrent telemetry requests

Run all tests:

```bash
python -m pytest -v
```

## Running the Application

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
python -m pip install uvicorn
```

Start the API:

```bash
python -m uvicorn streamwatch:create_app --factory --host 127.0.0.1 --port 8000
```

## CI/CD Automation

The Jenkins pipeline:

1. Creates a Python virtual environment.
2. Installs dependencies.
3. Executes automated Pytest tests.
4. Generates JUnit XML test reports.
5. Collects code coverage results.
6. Reports pipeline success or failure.

The repository includes a reusable Bash script,
`git_push.sh`, for testing and reviewing changes
before committing and pushing them.

## Engineering Case Study: SQLite Concurrency Bug

### Problem

During concurrent HTTP testing, one camera request returned:

`HTTP 500 Internal Server Error`

The server traceback identified:

`sqlite3.DatabaseError: cannot start a transaction within a transaction`

### Root Cause

Multiple FastAPI request threads accessed the same
SQLite connection without coordinated transaction handling.

### Solution

Introduced a `threading.Lock` to synchronize database
operations, keeping SQL writes and commits in one
critical section and protecting database reads.

### Validation

- Existing automated tests passed after the change.
- A repeated five-camera HTTP test returned HTTP 201
  for all five cameras.

This demonstrates a practical workflow of reproducing,
investigating, fixing, and retesting a concurrency defect.


## Load Testing with Locust

StreamWatch includes a Locust scenario that simulates
concurrent HTTP users submitting camera telemetry.

Run the API locally, then execute:

```bash
python -m locust -f locustfile.py \
  --headless \
  --host http://127.0.0.1:8000 \
  --users 5 \
  --spawn-rate 1 \
  --run-time 30s \
  --csv locust_results
```

### Sample Local Results

| Metric | Result |
|---|---|
| HTTP requests | 92 |
| Failed requests | 0 |
| Average response time | 5.34 ms |
| Median response time | 5 ms |
| P95 response time | 12 ms |
| P99 response time | 22 ms |
| Throughput | 3.23 requests/second |

Test environment: local StreamWatch API running on
127.0.0.1:8000, with 5 simulated users.

Results describe this specific local workload and
are not production performance guarantees.

## Project Scope

StreamWatch is an educational testing project, not a
production video-monitoring system. The application uses
an in-memory SQLite database and a dummy API key.
Performance tests provide local measurements rather than
production load-testing guarantees.
Auto-deployment test: GitHub to Render
