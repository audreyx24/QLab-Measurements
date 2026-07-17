"""Offline smoke test: exercises the library end-to-end with fake instruments.

Run from this folder:  python3 smoke_test.py
No hardware, no PycQED needed. Checks that every offline-capable code path
runs, produces data of the right shape, and that the fake physics behaves
(resonance found, punch-out jump, two-tone dip at the fake qubit).
"""

import matplotlib
matplotlib.use('Agg')   # no GUI needed

import numpy as np
import qlab

st = qlab.connect_fake()

# ---- 1. resonator scan finds the fake resonance ---- #
res = qlab.resonator_scan(st, center=8.0122e9, span=20e6, power=-30,
                          npts=1001, averages=200, delay_t=6.5e-8)
assert res['freq_Hz'].shape == (1001,)
assert abs(res['f_min_Hz'] - st.vna.f_r) < 200e3, \
    f"resonance found at {res['f_min_Hz']}, expected ~{st.vna.f_r}"
print("PASS resonator_scan: resonance found within 200 kHz")

# ---- 2. punch-out: high power shifts the dip ---- #
res_hi = qlab.resonator_scan(st, center=8.0122e9, span=20e6, power=10,
                             npts=1001, averages=200)
jump = res_hi['f_min_Hz'] - res['f_min_Hz']
assert abs(jump - st.vna.f_bare_shift) < 300e3, f"punch-out jump {jump}"
print(f"PASS punch-out: dip jumped {jump/1e6:.2f} MHz at high power")

# ---- 3. power sweep loop runs ---- #
out = qlab.resonator_power_sweep(st, center=8.0122e9, span=20e6,
                                 power_start=-30, power_stop=0, power_step=10,
                                 npts=201, averages=50, analyze=False)
assert len(out) == 3
print("PASS resonator_power_sweep: 3 scans")

# ---- 4. stability monitor (2 quick runs) ---- #
qlab.stability_monitor(st, center=8.0122e9, span=10e6, interval_s=0.1,
                       n_runs=2, npts=201, averages=50, analyze=False)
print("PASS stability_monitor: 2 runs")

# ---- 5. Gen3 fast pump sweep sees the fake qubit ---- #
df = qlab.pump_sweep_fast(st, probe_freq=st.vna.f_r,
                          pump_freq_start=5.5e9, pump_freq_stop=5.7e9,
                          pump_freq_step=5e6,
                          pump_power=5, vna_power=-20, averages=300)
assert len(df) == 41
amps = np.array([float(np.atleast_1d(a)[0]) for a in df["amplitude_dB"]])
qubit_idx = np.argmax(amps)   # probe sits in the dip; shift raises |S21|
found = df["pump_freq_Hz"].iloc[qubit_idx]
assert abs(found - st.vna.f_q) < 20e6, f"fake qubit found at {found}"
print(f"PASS pump_sweep_fast: fake qubit response peaks at {found/1e9:.3f} GHz")

# ---- 6. Kerr sweep runs offline ---- #
kerr = qlab.kerr_shift_sweep(st, probe_freq=8.0122e9, span=10e6,
                             delta_freq=200e6,
                             pump_power_start=-20, pump_power_stop=-15,
                             npts=201, averages=50)
assert len(kerr) == 6
print("PASS kerr_shift_sweep: 6 traces")

# ---- 7. real-hardware-only functions refuse politely ---- #
for fn, kw in [(qlab.two_tone_pump, dict(probe_freq=8e9, pump_freq_start=5e9,
                                         pump_freq_stop=6e9, pump_f_npts=10)),
               (qlab.two_tone_probe_sweep, dict(pump_freq_start=5e9,
                                                pump_freq_stop=6e9, pump_f_npts=10,
                                                probe_freq_start=8e9,
                                                probe_freq_stop=8.1e9,
                                                probe_f_npts=10)),
               (qlab.pump_sweep_gen2, dict(probe_freq=8e9, pump_freq_start=5e9,
                                           pump_freq_stop=5.1e9,
                                           pump_freq_step=50e6))]:
    try:
        fn(st, **kw)
        raise AssertionError(f"{fn.__name__} should refuse in fake mode")
    except NotImplementedError:
        pass
print("PASS hardware-only functions raise NotImplementedError in fake mode")

qlab.all_off(st)
print("\nALL SMOKE TESTS PASSED - data + plots in", st.datadir)
