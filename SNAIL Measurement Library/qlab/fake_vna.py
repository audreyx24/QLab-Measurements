"""Fake instruments for offline testing (no hardware, no PycQED needed).

FakeVNA implements the same method surface of the lab KST_VNA driver that the
measurement code touches, and returns synthetic-but-physical data:

- a notch-type resonator (Lorentzian dip in |S21|) at ``f_r``
- true cable delay applied to the phase, so the ``delay_t`` parameter is
  meaningful (a correct delay flattens the phase, like on the real VNA)
- punch-out: above ``punchout_power`` the resonance jumps to the bare
  cavity frequency (dressed -> bare, like the high-power scan measures)
- two-tone response: if the FakeSgen pump is ON and near the fake qubit
  frequency ``f_q``, the resonance shifts by the dispersive shift ``chi``
- noise that shrinks with averaging, so `averages` does something

This lets the whole library (sweep loops, saving, plotting) run end-to-end
on a laptop and produce plots that *look like* real measurements.
"""

import numpy as np


class FakeSgen:
    """Stands in for the Anritsu MG3692C: frequency(), power(), on()."""

    def __init__(self):
        self._freq = 5e9
        self._power = -20
        self._output = False

    def frequency(self, f=None):
        if f is None:
            return self._freq
        self._freq = float(f)

    def power(self, p=None):
        if p is None:
            return self._power
        self._power = float(p)

    def on(self, state):
        self._output = (str(state).upper() == "ON")


class FakeVNA:
    """Stands in for the lab KST_VNA driver (Keysight PNA N5222B)."""

    def __init__(self, sgen=None,
                 f_r=8.0122e9,        # dressed resonator frequency [Hz]
                 f_bare_shift=-1.5e6,  # bare - dressed frequency [Hz]
                 kappa=400e3,          # resonator linewidth [Hz]
                 f_q=5.6e9,            # fake qubit frequency [Hz]
                 chi=-350e3,           # dispersive shift [Hz]
                 qubit_linewidth=2e6,  # pump-response linewidth [Hz]
                 punchout_power=-5,    # [dBm] probe power where resonance punches out
                 cable_delay=6.5e-8):  # true electrical delay of fake cabling [s]
        self._sgen = sgen
        self.f_r = f_r
        self.f_bare_shift = f_bare_shift
        self.kappa = kappa
        self.f_q = f_q
        self.chi = chi
        self.qubit_linewidth = qubit_linewidth
        self.punchout_power = punchout_power
        self.cable_delay = cable_delay

        self._rng = np.random.default_rng()
        self.reset()

    # ------------- KST_VNA-compatible surface ------------- #
    def reset(self):
        self._start = self.f_r - 10e6
        self._stop = self.f_r + 10e6
        self._npts = 201
        self._power = -30
        self._timeout = 300
        self._if_bandwidth = 1000
        self._averages = 1
        self._average_state = "off"
        self._average_mode = "POIN"
        self._rf = False
        self._delay_t = 0.0

    def timeout(self, t=None):
        if t is None:
            return self._timeout
        self._timeout = t

    def bandwidth(self, bw=None):
        if bw is None:
            return self._if_bandwidth
        self._if_bandwidth = bw

    def avg(self, n=None):
        if n is None:
            return self._averages
        self._averages = int(n)

    def average_state(self, s=None):
        if s is None:
            return self._average_state
        self._average_state = s

    def average_mode(self, m=None):
        if m is None:
            return self._average_mode
        self._average_mode = m

    def rf_on(self):
        self._rf = True

    def rf_off(self):
        self._rf = False

    def start_sweep_all(self):
        pass  # instant on the fake instrument

    def wait_to_continue(self):
        pass

    def autoscale_trace(self):
        pass

    def get_real_imaginary_data(self):
        s21 = self._compute_s21()
        return np.real(s21), np.imag(s21)

    # ------------- fake-only configuration ------------- #
    def set_sweep(self, start, stop, npts, power=None, delay_t=0.0):
        """Configure the frequency axis (the real driver does this via
        KST_VNA_sweep / measure_resonator_spectroscopy_vna)."""
        self._start = float(start)
        self._stop = float(stop)
        self._npts = int(npts)
        if power is not None:
            self._power = float(power)
        self._delay_t = float(delay_t)

    def freq_axis(self):
        return np.linspace(self._start, self._stop, self._npts)

    # ------------- synthetic physics ------------- #
    def _resonance_freq(self):
        f_r = self.f_r
        # punch-out at high probe power: dressed -> bare cavity
        if self._power >= self.punchout_power:
            f_r = f_r + self.f_bare_shift
        # dispersive shift when the pump drives the fake qubit
        if self._sgen is not None and self._sgen._output:
            detuning = (self._sgen._freq - self.f_q) / self.qubit_linewidth
            drive = 10 ** (self._sgen._power / 20) / 10  # crude power scaling
            f_r = f_r + 2 * self.chi * min(drive, 1.0) / (1 + detuning ** 2)
        return f_r

    def _compute_s21(self):
        f = self.freq_axis()
        f_r = self._resonance_freq()
        # notch resonator: dip to ~0 on resonance
        s21 = 1 - (self.kappa / 2) / (1j * (f - f_r) + self.kappa / 2)
        # residual cable delay (true delay minus user's correction)
        residual = self.cable_delay - self._delay_t
        s21 = s21 * np.exp(-2j * np.pi * f * residual)
        # noise: shrinks with averaging and with lower IF bandwidth
        sigma = 0.05 / np.sqrt(max(self._averages, 1)) \
            * np.sqrt(self._if_bandwidth / 1000)
        noise = self._rng.normal(0, sigma, f.size) \
            + 1j * self._rng.normal(0, sigma, f.size)
        return s21 + noise
