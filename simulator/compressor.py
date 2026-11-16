"""Simulated refrigeration compressor controller.

Time is simulated: nothing happens until tick() is called, so tests are
fast and deterministic instead of waiting on real clocks.
"""

STOPPED, STARTING, RUNNING, TRIPPED = "STOPPED", "STARTING", "RUNNING", "TRIPPED"

START_DELAY_S = 10          # time from start command to RUNNING
ANTI_SHORT_CYCLE_S = 300    # minimum time between stop and next start
MIN_CAPACITY = 10.0         # % when running
MAX_CAPACITY = 100.0
TRIP_TEMP_C = 110.0         # discharge temperature that trips the compressor
RESET_TEMP_C = 100.0        # alarm can only be reset below this
KP, KI = 12.0, 1.0          # PI gains for suction pressure control
PLANT_GAIN = 0.02           # bar per (% load - % capacity) per second


class CommandRejected(Exception):
    pass


class Compressor:
    def __init__(self):
        self.state = STOPPED
        self.capacity = 0.0
        self.suction_pressure = 3.0
        self.setpoint = 3.0
        self.load = 50.0
        self.fault_offset = 0.0
        self.time_s = 0
        self._state_since = 0
        self._last_stop = -ANTI_SHORT_CYCLE_S
        self._integral = 0.0
        self.alarms = []

    @property
    def discharge_temp(self):
        return round(40.0 + 0.5 * self.capacity + self.fault_offset, 1)

    def status(self):
        return {
            "state": self.state,
            "capacity_pct": round(self.capacity, 1),
            "suction_pressure_bar": round(self.suction_pressure, 2),
            "setpoint_bar": self.setpoint,
            "load_pct": self.load,
            "discharge_temp_c": self.discharge_temp,
            "time_s": self.time_s,
            "alarms": list(self.alarms),
        }

    # --- commands ---
    def start(self):
        if self.state == TRIPPED:
            raise CommandRejected("compressor is tripped; reset the alarm first")
        if self.state in (STARTING, RUNNING):
            return
        if self.time_s - self._last_stop < ANTI_SHORT_CYCLE_S:
            raise CommandRejected("anti-short-cycle timer active")
        self._set_state(STARTING)

    def stop(self):
        if self.state in (STARTING, RUNNING):
            self._last_stop = self.time_s
        if self.state != TRIPPED:
            self._set_state(STOPPED)
        self.capacity = 0.0
        self._integral = 0.0

    def reset_alarm(self):
        if self.state != TRIPPED:
            return
        if self.discharge_temp >= RESET_TEMP_C:
            raise CommandRejected("discharge temperature still too high to reset")
        self.alarms.clear()
        self._set_state(STOPPED)

    def set_setpoint(self, bar):
        if not 1.0 <= bar <= 6.0:
            raise ValueError("setpoint must be between 1.0 and 6.0 bar")
        self.setpoint = bar

    def set_load(self, pct):
        if not 0 <= pct <= 100:
            raise ValueError("load must be between 0 and 100 %")
        self.load = pct

    def inject_fault(self, discharge_temp_offset):
        self.fault_offset = discharge_temp_offset

    # --- simulation ---
    def tick(self, seconds):
        for _ in range(int(seconds)):
            self._step()

    def _step(self):
        self.time_s += 1
        if self.state == STARTING and self.time_s - self._state_since >= START_DELAY_S:
            self._set_state(RUNNING)
            self.capacity = MIN_CAPACITY
        if self.state == RUNNING:
            error = self.suction_pressure - self.setpoint
            self._integral = max(-100.0, min(100.0, self._integral + error))
            target = KP * error + KI * self._integral
            self.capacity = max(MIN_CAPACITY, min(MAX_CAPACITY, target))
        self.suction_pressure += PLANT_GAIN * (self.load - self.capacity)
        self.suction_pressure = max(0.5, min(8.0, self.suction_pressure))
        if self.state != TRIPPED and self.discharge_temp > TRIP_TEMP_C:
            self._trip("HIGH_DISCHARGE_TEMP")

    def _trip(self, alarm):
        if self.state in (STARTING, RUNNING):
            self._last_stop = self.time_s
        self._set_state(TRIPPED)
        self.capacity = 0.0
        self._integral = 0.0
        self.alarms.append(alarm)

    def _set_state(self, state):
        self.state = state
        self._state_since = self.time_s
