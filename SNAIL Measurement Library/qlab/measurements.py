"""Measurement routines, moved verbatim out of the two notebooks.

Every function takes the ``LabStation`` (from ``connect()`` or
``connect_fake()``) as its first argument. On real hardware the call
sequences are byte-for-byte what the notebook cells did; behavior changes
are limited to bug fixes flagged in docstrings.

Cell mapping (see README.md for the full table):

    resonator_scan          QLab_tra cells 10/15/17, HH_qubit cell 11
    resonator_power_sweep   QLab_tra cell 12  (punch-out)
    stability_monitor       QLab_tra cell 14
    two_tone_pump           HH_qubit cell 9   (Gen1 prebuilt)
    two_tone_probe_sweep    HH_qubit cell 10  (Gen1 prebuilt, 2D)
    pump_sweep_gen2         HH_qubit cell 13  (10 s/pt, kept as reference)
    pump_sweep_fast         HH_qubit cells 16-20 and 30 (Gen3, ~2 s/pt)
    pump_observe            HH_qubit cell 28  (5a; `power` bug fixed)
    kerr_shift_sweep        HH_qubit cell 32  (5c)
    pump_power_ramp         HH_qubit cell 33
"""

import os
import time

import numpy as np

from . import config


# ====================================================================== #
#  Resonator spectroscopy (VNA only)                                     #
# ====================================================================== #

def resonator_scan(st, center, span,
                   power=-30,
                   if_bandwidth=config.DEFAULT_IF_BANDWIDTH,
                   npts=2001,
                   averages=100,
                   delay_t=config.DEFAULT_DELAY_S21,
                   measure='S21',
                   analyze=True,
                   close_fig=False,
                   timeout=config.DEFAULT_VNA_TIMEOUT):
    """Single VNA scan of the readout resonator (S21 or S11).

    S11 note: use delay_t ~ 1e-9 (reflection path), see config.DEFAULT_DELAY_S11.
    """
    start_f = center - span / 2
    stop_f = center + span / 2

    if st.fake:
        return _fake_trace_scan(st, start_f, stop_f, npts, power, averages,
                                if_bandwidth, delay_t, measure,
                                name=f'resonator_scan_{measure}', plot=analyze)

    st.vna.reset()
    st.vna.timeout(timeout)
    return st.Q1.measure_resonator_spectroscopy_vna(
        start=start_f, stop=stop_f,
        if_bandwidth=if_bandwidth, npts=npts,
        averages=averages, MC=st.MC, power=power, delay_t=delay_t,
        analyze=analyze, close_fig=close_fig, measure=measure)


def resonator_power_sweep(st, center, span,
                          power_start=-30, power_stop=20, power_step=1,
                          if_bandwidth=1000, npts=1001, averages=300,
                          delay_t=config.DEFAULT_DELAY_S21,
                          measure='S21', analyze=True, close_fig=False):
    """Punch-out: repeat the resonator scan across probe powers.

    Low power -> dressed frequency; high power -> bare cavity.
    Size of the jump ~ dispersive shift.
    """
    results = []
    for p in range(power_start, power_stop, power_step):
        print(p)
        results.append(resonator_scan(
            st, center, span, power=p,
            if_bandwidth=if_bandwidth, npts=npts, averages=averages,
            delay_t=delay_t, measure=measure,
            analyze=analyze, close_fig=close_fig))
    return results


def stability_monitor(st, center, span,
                      interval_s=7200, n_runs=None,
                      power=-30, if_bandwidth=1000, npts=2001, averages=100,
                      delay_t=6.24e-8, measure='S21',
                      analyze=True, close_fig=False):
    """Long-term stability: rescan the resonator every `interval_s` seconds.

    n_runs=None runs forever (original behavior: while True + 2 h sleep).
    """
    runcount = 0
    while n_runs is None or runcount < n_runs:
        runcount += 1
        print(runcount)
        resonator_scan(st, center, span, power=power,
                       if_bandwidth=if_bandwidth, npts=npts,
                       averages=averages, delay_t=delay_t, measure=measure,
                       analyze=analyze, close_fig=close_fig)
        if n_runs is not None and runcount >= n_runs:
            break
        time.sleep(interval_s)


# ====================================================================== #
#  Two-tone spectroscopy (Gen1: lab-local prebuilt methods)              #
# ====================================================================== #

def two_tone_pump(st, probe_freq,
                  pump_freq_start, pump_freq_stop, pump_f_npts,
                  pump_power=-10, probe_power=-25,
                  if_bandwidth=1000, averages=500,
                  delay_t=config.DEFAULT_DELAY_S21,
                  measure='S21', analyze=True, close_fig=False):
    """2-tone scan with the prebuilt QLab_Neon method (HH_qubit cell 9).

    Probe fixed at the resonator, pump swept; qubit shows up as a shift.
    """
    if st.fake:
        raise NotImplementedError(
            "two_tone_pump goes through the PycQED QLab_Neon wrapper - "
            "real hardware only. Offline, use pump_sweep_fast() instead.")

    st.vna.reset()
    result = st.Q1.measure_two_tone_pump(
        probe_freq=probe_freq,
        if_bandwidth=if_bandwidth,
        delay_t=delay_t,
        averages=averages,
        probe_power=probe_power,
        pump_freq_start=pump_freq_start,
        pump_freq_stop=pump_freq_stop,
        pump_f_npts=pump_f_npts,
        pump_power=pump_power,
        MC=st.MC, measure=measure,
        analyze=analyze, close_fig=close_fig)
    st.sgen.on("OFF")
    return result


def two_tone_probe_sweep(st,
                         pump_freq_start, pump_freq_stop, pump_f_npts,
                         probe_freq_start, probe_freq_stop, probe_f_npts,
                         pump_power=-30, probe_power=-30,
                         if_bandwidth=500, averages=100,
                         delay_t=config.DEFAULT_DELAY_S21,
                         measure='S21', analyze=True, close_fig=False):
    """2D version: sweep pump frequency AND probe frequency (HH_qubit cell 10)."""
    if st.fake:
        raise NotImplementedError(
            "two_tone_probe_sweep goes through the PycQED QLab_Neon wrapper - "
            "real hardware only.")

    st.vna.reset()
    return st.Q1.measure_two_tone_probe_sweep(
        pump_power=pump_power,
        pump_freq_start=pump_freq_start,
        pump_freq_stop=pump_freq_stop,
        pump_f_npts=pump_f_npts,
        probe_power=probe_power,
        probe_freq_start=probe_freq_start,
        probe_freq_stop=probe_freq_stop,
        probe_f_npts=probe_f_npts,
        delay_t=delay_t,
        if_bandwidth=if_bandwidth,
        averages=averages,
        MC=st.MC, measure=measure,
        analyze=analyze, close_fig=close_fig)


# ====================================================================== #
#  Pump-frequency sweeps (Gen2 reference + Gen3 workhorse)               #
# ====================================================================== #

def pump_sweep_gen2(st, probe_freq,
                    pump_freq_start, pump_freq_stop, pump_freq_step,
                    pump_power=20, vna_power=-25,
                    if_bandwidth=500, averages=1000,
                    delay_t=6.39e-8, measure='S21'):
    """Gen2 (~10 s/pt) pump sweep - HH_qubit cell 13. KEPT AS REFERENCE.

    One full MC.run() (fresh sweep + detector + HDF5 dataset) per pump
    point; that overhead is why it is slow. Use pump_sweep_fast() instead.
    """
    if st.fake:
        raise NotImplementedError("Gen2 uses PycQED MC - real hardware only. "
                                  "Use pump_sweep_fast() instead.")

    swf, det = st._swf, st._det
    st.sgen.power(pump_power)
    st.sgen.on("ON")

    st.vna.bandwidth(if_bandwidth)
    st.vna.timeout(300)
    st.vna.avg(averages)
    st.vna.average_state("on")
    st.vna.average_mode("POIN")

    for pump_freq in range(int(pump_freq_start),
                           int(pump_freq_stop) + int(pump_freq_step),
                           int(pump_freq_step)):
        print("Pump freq:", pump_freq / 1e9, "GHz")
        st.sgen.frequency(pump_freq)
        st.MC.set_sweep_function(swf.KST_VNA_sweep(
            st.vna, start_freq=probe_freq, stop_freq=probe_freq, npts=1,
            if_bandwidth=if_bandwidth, power=vna_power, delay_t=delay_t,
            measure=measure, force_reset=False))
        st.MC.set_detector_function(det.KST_VNA_detector(st.vna))
        st.MC.run(name='resonator_vna_scan_frquency_{}_at_qubit_{}_power_{}_'
                  .format(probe_freq, pump_freq, vna_power))

    st.sgen.on("OFF")


def pump_sweep_fast(st, probe_freq,
                    pump_freq_start, pump_freq_stop, pump_freq_step,
                    pump_power=5, vna_power=-20,
                    if_bandwidth=500, averages=300,
                    delay_t=6.62e-8, measure='S21',
                    settle_s=0.0, csv_path=None):
    """Gen3 (~2 s/pt) pump sweep - HH_qubit cells 16-20 / 30.

    VNA configured ONCE as a single-point trace at probe_freq with point
    averaging; then the loop only moves the pump and triggers/reads the VNA
    directly (no per-point MC overhead). Returns a DataFrame; also saved
    to CSV.

    settle_s: wait after setting the pump frequency before triggering the
    VNA. Original code had no wait (flagged in the notebook as a plausible
    cause of SNR drift); default 0.0 keeps the original behavior.
    """
    import pandas as pd

    all_data = []

    st.sgen.power(pump_power)
    st.sgen.on("ON")

    st.vna.reset()
    st.vna.bandwidth(if_bandwidth)
    st.vna.timeout(300)
    st.vna.avg(averages)
    st.vna.average_state("on")
    st.vna.average_mode("POIN")   # average each pt before moving on

    # single-point trace at the probe frequency
    if st.fake:
        st.vna.set_sweep(probe_freq, probe_freq, 1,
                         power=vna_power, delay_t=delay_t)
    else:
        swf, det = st._swf, st._det
        st.MC.set_sweep_function(swf.KST_VNA_sweep(
            st.vna, start_freq=probe_freq, stop_freq=probe_freq, npts=1,
            if_bandwidth=if_bandwidth, power=vna_power, delay_t=delay_t,
            measure=measure, force_reset=False))
        st.MC.set_detector_function(det.KST_VNA_detector(st.vna))
        st.MC.run(name='resonator_vna_scan_frquency_{}_at_qubit_{}_power_{}_'
                  .format(probe_freq, pump_freq_start, vna_power))

    # fast pump-frequency loop: trigger + read the VNA directly
    st.vna.rf_on()
    for pump_freq in range(int(pump_freq_start),
                           int(pump_freq_stop) + int(pump_freq_step),
                           int(pump_freq_step)):
        print("Pump freq:", pump_freq / 1e9, "GHz")
        st.sgen.frequency(pump_freq)
        if settle_s:
            time.sleep(settle_s)
        st.vna.start_sweep_all()
        st.vna.wait_to_continue()
        st.vna.autoscale_trace()   # VNA screen only, no effect on data

        real_data, imag_data = st.vna.get_real_imaginary_data()
        complex_data = np.add(real_data, 1j * imag_data)
        ampl_dB = 20 * np.log10(np.abs(complex_data))
        phase_deg = np.arctan2(imag_data, real_data) * 180 / np.pi

        all_data.append({
            "pump_freq_Hz": pump_freq,
            "vna_freq_Hz": probe_freq,
            "real": real_data,
            "imag": imag_data,
            "amplitude_dB": ampl_dB,
            "phase_deg": phase_deg,
        })

    st.vna.rf_off()
    st.sgen.on("OFF")

    df = pd.DataFrame(all_data)
    if csv_path is None:
        name = 'pumpsweep_{:.4f}GHz_to_{:.4f}GHz_pump{}dBm'.format(
            pump_freq_start / 1e9, pump_freq_stop / 1e9, pump_power)
        run_dir = config.make_run_dir(st.datadir, name)
        csv_path = os.path.join(run_dir, name + '.csv')
    df.to_csv(csv_path, index=False)
    print("Saved:", csv_path)
    return df


def pump_observe(st, resonance_freq, pump_power,
                 fmin=0.995, fmax=1.005, pump_freq_step=10e6,
                 dwell_s=25):
    """5a: step the pump around 2x the resonance and just watch the VNA
    screen (HH_qubit cell 28). No data is taken.

    BUG FIX vs the notebook: `power` there was undefined and silently
    reused whatever a previous cell left in the namespace; here it is the
    explicit, required `pump_power` argument.
    """
    pump_freq_start = int(resonance_freq * 2 * fmin)
    pump_freq_stop = int(resonance_freq * 2 * fmax)
    print(pump_freq_start)
    print(pump_freq_stop)

    st.sgen.power(pump_power)
    st.sgen.on("ON")

    for pump_freq in range(pump_freq_start,
                           pump_freq_stop + int(pump_freq_step),
                           int(pump_freq_step)):
        print("Pump freq:", pump_freq / 1e9, "GHz")
        st.sgen.frequency(pump_freq)
        time.sleep(dwell_s)

    st.vna.rf_off()
    st.sgen.on("OFF")


# ====================================================================== #
#  SNAIL tests                                                           #
# ====================================================================== #

def kerr_shift_sweep(st, probe_freq, span, delta_freq,
                     pump_power_start=-20, pump_power_stop=0, pump_power_step=1,
                     vna_power=0,
                     if_bandwidth=1000, npts=1001, averages=200,
                     delay_t=6.9e-8, measure='S21'):
    """5c: Kerr-shift test - full resonator trace per pump power, pump
    detuned by delta_freq below the probe (HH_qubit cell 32)."""
    start_f = probe_freq - span / 2
    stop_f = probe_freq + span / 2

    if st.fake:
        results = []
        st.sgen.frequency(probe_freq - delta_freq)
        st.sgen.on("ON")
        for pump_power in range(int(pump_power_start),
                                int(pump_power_stop) + int(pump_power_step),
                                int(pump_power_step)):
            st.sgen.power(pump_power)
            results.append(_fake_trace_scan(
                st, start_f, stop_f, npts, vna_power, averages,
                if_bandwidth, delay_t, measure,
                name=f'kerr_pump{pump_power}dBm', plot=False))
        st.sgen.on("OFF")
        return results

    swf, det = st._swf, st._det
    st.vna.reset()

    st.sgen.power(pump_power_start)
    st.sgen.on("ON")
    st.sgen.frequency(probe_freq - delta_freq)

    st.vna.bandwidth(if_bandwidth)
    st.vna.timeout(300)
    st.vna.avg(averages)
    st.vna.average_state("on")
    st.vna.average_mode("POIN")

    for pump_power in range(int(pump_power_start),
                            int(pump_power_stop) + int(pump_power_step),
                            int(pump_power_step)):
        st.sgen.power(pump_power)
        st.MC.set_sweep_function(swf.KST_VNA_sweep(
            st.vna, start_freq=start_f, stop_freq=stop_f, npts=npts,
            if_bandwidth=if_bandwidth, power=vna_power, delay_t=delay_t,
            measure=measure, force_reset=False))
        st.MC.set_detector_function(det.KST_VNA_detector(st.vna))
        st.MC.run(name='Kerr_from_{}_to_{}_at_deturn_{}_power_{}_with_VNApower_{}'
                  .format(start_f, stop_f, delta_freq, pump_power, vna_power))

    st.sgen.on("OFF")


def pump_power_ramp(st, pump_freq,
                    pump_power_start=-20, pump_power_stop=25,
                    pump_power_step=1, dwell_s=10):
    """Step the pump power at fixed frequency, observation only
    (HH_qubit cell 33)."""
    st.sgen.frequency(pump_freq)
    st.sgen.power(pump_power_start)
    st.sgen.on("ON")

    for pump_power in range(int(pump_power_start),
                            int(pump_power_stop) + int(pump_power_step),
                            int(pump_power_step)):
        st.sgen.power(pump_power)
        time.sleep(dwell_s)

    st.sgen.on("OFF")


# ====================================================================== #
#  Fake-mode helper                                                      #
# ====================================================================== #

def _fake_trace_scan(st, start_f, stop_f, npts, power, averages,
                     if_bandwidth, delay_t, measure, name, plot=True):
    """Offline stand-in for a Q1.measure_resonator_spectroscopy_vna call:
    configure the FakeVNA axis, read a trace, plot, save CSV."""
    import pandas as pd

    st.vna.avg(averages)
    st.vna.bandwidth(if_bandwidth)
    st.vna.set_sweep(start_f, stop_f, npts, power=power, delay_t=delay_t)
    real_data, imag_data = st.vna.get_real_imaginary_data()

    freqs = st.vna.freq_axis()
    complex_data = real_data + 1j * imag_data
    ampl_dB = 20 * np.log10(np.abs(complex_data))
    phase_deg = np.unwrap(np.angle(complex_data)) * 180 / np.pi

    run_dir = config.make_run_dir(st.datadir, name)
    csv_path = os.path.join(run_dir, f'{name}.csv')
    pd.DataFrame({'freq_Hz': freqs, 'real': real_data, 'imag': imag_data,
                  'amplitude_dB': ampl_dB, 'phase_deg': phase_deg}
                 ).to_csv(csv_path, index=False)

    f0 = freqs[np.argmin(ampl_dB)]
    print(f'[fake] {name}: min |{measure}| at {f0/1e9:.6f} GHz  ->  {csv_path}')

    if plot:
        import matplotlib.pyplot as plt
        fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True, figsize=(7, 5))
        ax1.plot(freqs / 1e9, ampl_dB)
        ax1.set_ylabel(f'|{measure}| [dB]')
        ax1.set_title(f'{name} (FAKE data)  power={power} dBm')
        ax2.plot(freqs / 1e9, phase_deg)
        ax2.set_ylabel('phase [deg]')
        ax2.set_xlabel('frequency [GHz]')
        fig.tight_layout()
        fig.savefig(csv_path.replace('.csv', '.png'), dpi=110)

    return {'freq_Hz': freqs, 's': complex_data,
            'amplitude_dB': ampl_dB, 'phase_deg': phase_deg,
            'f_min_Hz': f0, 'csv_path': csv_path}
