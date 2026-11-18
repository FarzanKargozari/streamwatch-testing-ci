# StreamWatch — API Testing & CI/CD Automation

[![StreamWatch Automated Tests](https://github.com/FarzanKargozari/streamwatch-testing-ci/actions/workflows/tests.yml/badge.svg)](https://github.com/FarzanKargozari/streamwatch-testing-ci/actions/workflows/tests.yml)

**Live API:** https://streamwatch-testing-ci.onrender.com/docs  
**GitHub Repository:** https://github.com/FarzanKargozari/streamwatch-testing-ci

StreamWatch is a Python-based API monitoring and automated testing project that simulates video-stream network telemetry. It demonstrates REST API development, database validation, fault simulation, concurrency testing, load testing, Docker containerization, and cloud deployment.

## Project Highlights

- 27 passing automated tests in the latest verified local run
- 100% statement and branch coverage for the measured application modules
- Automated CI testing through GitHub Actions
- Jenkins pipeline configuration
- Docker containerization
- Cloud deployment on Render
- Automatic deployment from the GitHub `main` branch
- Five-camera data isolation testing
- Performance testing using Locust

## Technology Stack

| Category | Technologies |
|---|---|
| Language | Python |
| API framework | FastAPI, Uvicorn |
| Testing | pytest, pytest-cov, unittest.mock |
| Database | SQLite |
| Load testing | Locust |
| CI | GitHub Actions, Jenkins pipeline configuration |
| Containerization | Docker |
| Cloud deployment | Render |
| Version control | Git, GitHub |
| Automation | Bash |

## Application Features

- REST endpoints for telemetry submission and stream health retrieval
- API-key authentication using a training-only credential
- Packet-loss and latency input validation
- Automatic alarms when packet loss reaches 2% or higher
- SQLite telemetry storage
- Lock-protected database access
- Network timeout and retry simulations
- Concurrent API request handling
- Multi-camera data isolation

## API Endpoints

### POST `/api/streams/{stream_id}/telemetry`

Submit camera telemetry measurements.

Example request body:

```json
{
  "packet_loss_percent": 3,
  "latency_ms": 25
}
```

Example successful response — HTTP 201:

```json
{
  "stream_id": "camera-01",
  "alarm": true
}
```

### GET `/api/streams/{stream_id}/health`

Retrieve the latest available measurement for a camera.

Example successful response — HTTP 200:

```json
{
  "stream_id": "camera-01",
  "packet_loss_percent": 3,
  "latency_ms": 25,
  "alarm": true
}
```

These endpoints use the `x-api-key` header. The current training credential is `training-key`, which is not suitable for real production authentication.

## Automated Testing

StreamWatch includes 27 passing pytest tests in the latest verified local execution.

Tests cover:

- HTTP response codes
- API authentication
- Input validation
- Packet-loss alarm thresholds
- SQLite storage and stream isolation
- Missing resources
- Network timeouts and automatic retries
- Mocked network responses
- API latency
- Concurrent requests
- Five-camera data isolation

### Run the test suite

```bash
bash run_tests.sh
```

The test script generates JUnit XML and coverage reports.

**Latest measured coverage:** 100% for `streamwatch.py` and `network_client.py`, including the measured branches. This percentage does not represent every file in the repository.

## CI/CD Pipeline

### Continuous Integration — GitHub Actions

The `.github/workflows/tests.yml` workflow runs on pushes and pull requests targeting `main`, and also supports manual execution.

It:

1. Checks out the repository.
2. Sets up Python 3.14 on Ubuntu 24.04.
3. Creates a virtual environment.
4. Installs dependencies.
5. Runs the automated test suite.
6. Uploads JUnit and coverage reports.

The repository also contains a `Jenkinsfile` defining setup, testing, and report-publishing stages.

### Continuous Deployment — Render

StreamWatch is packaged using Docker and deployed as a Render web service.

The deployment process is:

1. Code is committed and pushed to GitHub.
2. GitHub Actions runs the automated testing workflow.
3. Render detects commits on the connected `main` branch.
4. Render builds and deploys the Docker application.
5. The FastAPI service becomes accessible through its public URL.

**Verification:** Commit `d4e0b83` successfully triggered a new Render deployment, which reached Live status. Its GitHub Actions workflow also passed.

**Current deployment policy:** Render uses **On Commit**. Passing GitHub Actions checks is not yet an enforced prerequisite for deployment.

## Docker

Build the Docker image:

```bash
docker build -t streamwatch:1.0 .
```

Run the container:

```bash
docker run --rm -p 8000:8000 streamwatch:1.0
```

Open the API documentation:

http://localhost:8000/docs

## Engineering Case Study — SQLite Concurrency Defect

### Problem

During concurrent HTTP testing, a request produced HTTP 500 Internal Server Error.

The traceback identified:

```text
sqlite3.DatabaseError: cannot start a transaction within a transaction
```

### Root Cause

Multiple request threads accessed a shared SQLite connection without coordinated transaction handling.

### Solution

A `threading.Lock` was introduced to synchronize database operations and protect database reads and writes.

### Validation

- Existing automated tests passed after the fix.
- Repeated five-camera HTTP requests returned successful responses.
- Multi-camera data isolation was verified through additional testing.

This case study demonstrates defect reproduction, root-cause analysis, synchronization, regression testing, and verification.

## Load Testing — Locust

StreamWatch includes a Locust scenario that simulates multiple users submitting camera telemetry.

Run a local load test:

```bash
python -m locust -f locustfile.py \
  --headless \
  --host http://127.0.0.1:8000 \
  --users 5 \
  --spawn-rate 1 \
  --run-time 30s \
  --csv locust_results
```

### Sample Local Performance Results

| Metric | Result |
|---|---:|
| HTTP requests | 92 |
| Failed requests | 0 |
| Average response time | 5.34 ms |
| Median response time | 5 ms |
| P95 response time | 12 ms |
| P99 response time | 22 ms |
| Throughput | 3.23 requests/second |

These results were measured locally with five simulated users and are not production performance guarantees.

## Running Locally

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Start StreamWatch:

```bash
python -m uvicorn streamwatch:create_app \
  --factory \
  --host 127.0.0.1 \
  --port 8000
```

Visit http://localhost:8000/docs.

## Known Limitations

StreamWatch is an educational software-testing project rather than a production video-monitoring platform.

- SQLite currently stores data in memory; measurements are lost when the application process restarts.
- Authentication uses a hardcoded demonstration API key.
- Local performance results do not represent production-scale throughput.
- Deployment is configured to run on commits, rather than being gated on successful CI checks.
- The Render Free instance can spin down after inactivity.

## Future Improvements

- Configure deployment to require successful CI checks
- Add persistent database storage
- Replace demonstration authentication with secure credential management
- Add dedicated readiness and liveness endpoints
- Add automated post-deployment smoke tests
- Expand security and performance testing

## Purpose

This project demonstrates hands-on software testing and engineering practices, including API development, automated testing, debugging, concurrency control, CI workflows, Docker containerization, and deployment verification.
