"""qlab: SNAIL / resonator measurement library for Xu Han's group setup.

Usage on the lab PC:
    import qlab
    st = qlab.connect()
    qlab.resonator_scan(st, center=8.01225e9, span=20e6, power=-30)

Offline (any machine, no hardware / no PycQED):
    st = qlab.connect_fake()
    qlab.resonator_scan(st, center=8.0122e9, span=20e6, power=-30)
"""

from .instruments import connect, connect_fake, all_off, LabStation
from .measurements import (
    resonator_scan,
    resonator_power_sweep,
    stability_monitor,
    two_tone_pump,
    two_tone_probe_sweep,
    pump_sweep_gen2,
    pump_sweep_fast,
    pump_observe,
    kerr_shift_sweep,
    pump_power_ramp,
)
from . import config

__all__ = [
    'connect', 'connect_fake', 'all_off', 'LabStation', 'config',
    'resonator_scan', 'resonator_power_sweep', 'stability_monitor',
    'two_tone_pump', 'two_tone_probe_sweep',
    'pump_sweep_gen2', 'pump_sweep_fast', 'pump_observe',
    'kerr_shift_sweep', 'pump_power_ramp',
]
