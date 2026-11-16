import pytest

pytestmark = pytest.mark.control


@pytest.mark.parametrize("load", [20, 50, 80])
def test_suction_pressure_settles_at_setpoint(ctrl, load):
    ctrl.set_load(load)
    ctrl.set_setpoint(3.0)
    ctrl.start_and_wait_running()
    s = ctrl.tick(120)
    assert s["suction_pressure_bar"] == pytest.approx(3.0, abs=0.1)
    assert s["capacity_pct"] == pytest.approx(load, abs=2)


def test_capacity_increases_when_load_steps_up(ctrl):
    ctrl.set_load(30)
    ctrl.start_and_wait_running()
    before = ctrl.tick(120)["capacity_pct"]
    ctrl.set_load(90)
    after = ctrl.tick(120)["capacity_pct"]
    assert after > before


@pytest.mark.parametrize("load", [0, 100])
def test_capacity_stays_within_limits(ctrl, load):
    ctrl.set_load(load)
    ctrl.start_and_wait_running()
    for _ in range(20):
        s = ctrl.tick(10)
        assert 10 <= s["capacity_pct"] <= 100


@pytest.mark.parametrize("bad", [0.5, 6.5])
def test_setpoint_outside_range_is_rejected(ctrl, bad):
    assert ctrl.set_setpoint(bad).status_code == 400
    assert ctrl.status()["setpoint_bar"] == 3.0
