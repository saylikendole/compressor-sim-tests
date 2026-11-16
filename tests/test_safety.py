import pytest

pytestmark = pytest.mark.safety


def test_high_discharge_temperature_trips_compressor(ctrl):
    ctrl.start_and_wait_running()
    ctrl.inject_fault(80)
    s = ctrl.tick(1)
    assert s["state"] == "TRIPPED"
    assert s["capacity_pct"] == 0
    assert "HIGH_DISCHARGE_TEMP" in s["alarms"]


def test_start_is_rejected_while_tripped(ctrl):
    ctrl.start_and_wait_running()
    ctrl.inject_fault(80)
    ctrl.tick(1)
    assert ctrl.command("start").status_code == 409


def test_alarm_reset_rejected_while_still_hot(ctrl):
    ctrl.start_and_wait_running()
    ctrl.inject_fault(80)
    ctrl.tick(1)
    assert ctrl.command("reset_alarm").status_code == 409
    assert ctrl.status()["state"] == "TRIPPED"


def test_recovery_after_fault_is_cleared(ctrl):
    ctrl.start_and_wait_running()
    ctrl.inject_fault(80)
    ctrl.tick(1)
    ctrl.inject_fault(0)
    assert ctrl.command("reset_alarm").status_code == 200
    assert ctrl.status()["alarms"] == []
    ctrl.tick(300)  # anti-short-cycle still applies after a trip
    assert ctrl.command("start").status_code == 200


def test_normal_operation_never_trips(ctrl):
    ctrl.set_load(100)
    ctrl.start_and_wait_running()
    for _ in range(60):
        assert ctrl.tick(10)["state"] == "RUNNING"
