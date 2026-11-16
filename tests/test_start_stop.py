def test_compressor_is_stopped_after_power_up(ctrl):
    s = ctrl.status()
    assert s["state"] == "STOPPED"
    assert s["capacity_pct"] == 0


def test_start_goes_through_starting_before_running(ctrl):
    ctrl.command("start")
    assert ctrl.tick(9)["state"] == "STARTING"
    s = ctrl.tick(1)
    assert s["state"] == "RUNNING"
    assert s["capacity_pct"] >= 10


def test_stop_sets_capacity_to_zero(ctrl):
    ctrl.start_and_wait_running()
    ctrl.tick(30)
    assert ctrl.command("stop").status_code == 200
    s = ctrl.status()
    assert s["state"] == "STOPPED"
    assert s["capacity_pct"] == 0


def test_anti_short_cycle_blocks_quick_restart(ctrl):
    ctrl.start_and_wait_running()
    ctrl.command("stop")
    ctrl.tick(299)
    assert ctrl.command("start").status_code == 409
    ctrl.tick(1)
    assert ctrl.command("start").status_code == 200


def test_unknown_command_is_rejected(ctrl):
    assert ctrl.command("turbo").status_code == 400
