# Compressor controller – simulated test bench

![Controller tests](https://github.com/saylikendole/compressor-sim-tests/actions/workflows/ci.yml/badge.svg)

Automated integration tests for a simulated refrigeration compressor controller. The simulator and the pytest suite run in separate Docker containers and talk over HTTP, the same way tests would talk to a real controller on a hardware-in-the-loop bench. GitHub Actions runs everything on every push and writes the results to the job summary.

## What is tested

| Area | Examples |
|---|---|
| Start/stop sequence | STOPPED → STARTING → RUNNING after the start delay; stop sets capacity to 0 |
| Anti-short-cycle | A restart within 300 s of a stop is rejected |
| Capacity control | Suction pressure settles at the setpoint for low, medium and high load; capacity stays between 10 and 100 % |
| Safety | High discharge temperature trips the compressor; start and alarm reset are blocked until it is safe |
| Input validation | Out-of-range setpoints and unknown commands are rejected |

## Design choices

- **Simulated time.** The simulator only moves forward when a test calls `/tick`. A test that checks a 300-second timer runs in milliseconds and gives the same result every time. The whole suite runs in under a second.
- **One fresh controller per test.** A fixture resets the simulator before each test, so no test depends on another one.
- **Same tests, different target.** The tests only know `SIM_URL`. Pointing it at a real controller or a bench adapter would reuse the suite without changes.
- **Results where developers look.** CI posts a pass/fail summary to the GitHub job page and keeps the JUnit report as an artifact.
- **Tests checked against injected bugs.** I broke the controller on purpose (removed the trip limit, the anti-short-cycle timer, the start delay, the minimum capacity, the alarm-reset interlock, and each part of the PI controller). At least one test failed for every one of those bugs.

## Run it

With Docker:

```bash
docker compose up --build --abort-on-container-exit --exit-code-from tests
```

Without Docker:

```bash
python simulator/server.py            # terminal 1
pip install -r tests/requirements.txt # terminal 2
cd tests && pytest -v
```

Run only the safety tests: `pytest -m safety`

## Structure

```
simulator/   compressor model (compressor.py) and HTTP API (server.py)
tests/       pytest suite and API client fixture (conftest.py)
docker-compose.yml          runs simulator + tests together
.github/workflows/ci.yml    CI: build, test, summary, report artifact
```

## Next steps

- Robot Framework version of the safety tests, reusing the same API
- Fault injection for sensor failures (frozen or out-of-range pressure readings)
