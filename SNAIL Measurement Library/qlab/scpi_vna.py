"""Direct SCPI driver for the Keysight PNA N5222B — no PycQED, no KST_VNA.

This is the "cut out the middleman" layer. Instead of
    our code -> PycQED detector -> KST_VNA driver -> QCoDeS VisaInstrument -> VNA
we go
    our code -> pyvisa -> VNA

It exposes the SAME method names as FakeVNA and the parts of KST_VNA that
measurements.py touches, so it is a drop-in replacement for either.

Two speed decisions, both measured against the 2026-07-20 format capture
(see VNA_GETTING_STARTED.md):

1. BINARY TRANSFER. The instrument was found sending 'ASC,0' — ASCII text,
   ~15-20 bytes per number, which then has to be parsed from strings. We set
   REAL,64 instead: 8 raw bytes per number, no parsing. For 2001 points that
   is ~80 kB of text down to 32 kB of bytes.

2. ONE ROUND TRIP PER SWEEP. The frequency axis is computed locally with
   linspace instead of asking the instrument (CALC:X?), because it is fully
   determined by start/stop/points, which we set ourselves.

TRANSPORT SPLIT
---------------
Nothing here imports pyvisa at module level. The class takes a `transport`
object with .write() / .query() / .query_raw(), so the exact same SCPI and
parsing code can run against a fake instrument on a laptop. Use
``SCPIVNA.open(address)`` on the lab PC to build a real pyvisa transport.
"""

import numpy as np

from . import config

# Map SCPI format name -> numpy dtype. The byte-order prefix is filled in from
# FORM:BORD (NORM = big-endian '>', SWAP = little-endian '<').
_FORMATS = {
    ('REAL', 64): 'f8',
    ('REAL', 32): 'f4',
}


def parse_binary_block(raw):
    """Parse an IEEE 488.2 definite-length block into its payload bytes.

    Layout:  #  <n>  <n digits of byte count>  <payload>  [trailing newline]

    e.g. b'#432000<32000 bytes>' -> n=4, count=2000, payload is 32000 bytes.

    This is the parsing step that silently produces wrong numbers if you get
    it wrong, so it is a standalone function with its own tests rather than
    being buried inline in a read method.
    """
    if not raw:
        raise ValueError('empty response from instrument (no data at all)')
    if raw[0:1] != b'#':
        raise ValueError(
            f'expected IEEE 488.2 block starting with #, got {raw[:20]!r}. '
            'The instrument is probably still in ASCII mode (FORM:DATA ASC).')

    ndigits = int(raw[1:2])
    if ndigits == 0:
        # '#0' means indefinite length: payload runs to the final newline.
        return raw[2:].rstrip(b'\n')

    header_len = 2 + ndigits
    nbytes = int(raw[2:header_len])
    payload = raw[header_len:header_len + nbytes]
    if len(payload) != nbytes:
        raise ValueError(
            f'block header promised {nbytes} bytes but only {len(payload)} '
            'arrived — the read was truncated (raise the VISA timeout).')
    return payload


class SCPIVNA:
    """Keysight PNA N5222B over raw SCPI."""

    def __init__(self, transport, measurement=None, binary=True,
                 float_bits=64, byte_order='SWAP'):
        self.t = transport
        self.binary = binary
        self.float_bits = float_bits
        self.byte_order = byte_order
        self._dtype = None
        self._measurement = measurement

        # Local mirror of the sweep settings, so freq_axis() needs no I/O.
        self._start = None
        self._stop = None
        self._npts = None

        self._configure_format()
        if measurement is None:
            self._measurement = self.first_measurement()
        self.select_measurement(self._measurement)

    # ---------------- construction ---------------- #
    @classmethod
    def open(cls, address=config.VNA_ADDRESS, timeout_ms=30000, **kw):
        """Build a real pyvisa transport and connect. Lab PC only."""
        from .visa_transport import VisaTransport
        return cls(VisaTransport(address, timeout_ms=timeout_ms), **kw)

    # ---------------- format / selection ---------------- #
    def _configure_format(self):
        """Put the instrument into binary mode and remember how to decode it."""
        if not self.binary:
            self._dtype = None
            self.t.write('FORM:DATA ASC,0')
            return
        self.t.write(f'FORM:DATA REAL,{self.float_bits}')
        self.t.write(f'FORM:BORD {self.byte_order}')
        prefix = '<' if self.byte_order.upper().startswith('SWAP') else '>'
        self._dtype = np.dtype(prefix + _FORMATS[('REAL', self.float_bits)])

    def catalog(self):
        """List (name, s_parameter) for every measurement defined on the VNA."""
        raw = self.t.query('CALC:PAR:CAT:EXT?').strip().strip('"')
        if not raw or raw.upper() == 'NO CATALOG':
            return []
        fields = raw.split(',')
        return list(zip(fields[0::2], fields[1::2]))

    def first_measurement(self):
        cat = self.catalog()
        if not cat:
            raise RuntimeError(
                'No measurements defined on the VNA. Set up a trace on the '
                'front panel first, or call create_measurement().')
        return cat[0][0]

    def select_measurement(self, name):
        """Point this VISA session's CALC: commands at measurement `name`.

        Required before any CALC:DATA? read. Without it the instrument answers
        nothing and the read times out with '+103,"CALC measurement selection
        set to none"' in the error queue — exactly what the 2026-07-20 capture
        hit. Per-session, so it does not disturb anyone else's connection.
        """
        self.t.write(f"CALC:PAR:SEL '{name}'")
        self._measurement = name

    # ---------------- sweep configuration ---------------- #
    def set_sweep(self, start, stop, npts, power=None, delay_t=None,
                  if_bandwidth=None):
        """Configure the frequency axis. Same signature as FakeVNA.set_sweep."""
        self.t.write(f'SENS:FREQ:STAR {float(start)}')
        self.t.write(f'SENS:FREQ:STOP {float(stop)}')
        self.t.write(f'SENS:SWE:POIN {int(npts)}')
        if power is not None:
            self.t.write(f'SOUR:POW {float(power)}')
        if delay_t is not None:
            self.t.write(f'CALC:CORR:EDEL:TIME {float(delay_t)}')
        if if_bandwidth is not None:
            self.t.write(f'SENS:BWID {float(if_bandwidth)}')
        self._start, self._stop, self._npts = float(start), float(stop), int(npts)

    def freq_axis(self):
        """The frequency axis, computed locally (no instrument round trip).

        Equivalent to CALC:X? for a LIN sweep, which is what we always use.
        verify_against_instrument() checks this claim on real hardware.
        """
        if self._npts is None:
            self._sync_sweep_from_instrument()
        return np.linspace(self._start, self._stop, self._npts)

    def _sync_sweep_from_instrument(self):
        """Read start/stop/points back, for when we did not set them ourselves."""
        self._start = float(self.t.query('SENS:FREQ:STAR?'))
        self._stop = float(self.t.query('SENS:FREQ:STOP?'))
        self._npts = int(float(self.t.query('SENS:SWE:POIN?')))

    # ---------------- KST_VNA-compatible surface ---------------- #
    def timeout(self, t=None):
        if t is None:
            return self.t.timeout_ms / 1000
        self.t.timeout_ms = float(t) * 1000

    def bandwidth(self, bw=None):
        if bw is None:
            return float(self.t.query('SENS:BWID?'))
        self.t.write(f'SENS:BWID {float(bw)}')

    def avg(self, n=None):
        if n is None:
            return int(float(self.t.query('SENS:AVER:COUN?')))
        self.t.write(f'SENS:AVER:COUN {int(n)}')

    def average_state(self, s=None):
        if s is None:
            return 'on' if self.t.query('SENS:AVER:STAT?').strip() in ('1', 'ON') else 'off'
        self.t.write(f"SENS:AVER:STAT {'ON' if str(s).lower() in ('on', '1', 'true') else 'OFF'}")

    def average_mode(self, m=None):
        if m is None:
            return self.t.query('SENS:AVER:MODE?').strip()
        self.t.write(f'SENS:AVER:MODE {m}')

    def average_clear(self):
        self.t.write('SENS:AVER:CLE')

    def rf_on(self):
        self.t.write('OUTP ON')

    def rf_off(self):
        self.t.write('OUTP OFF')

    def autoscale_trace(self):
        self.t.write('DISP:WIND:TRAC:Y:AUTO')

    def reset(self):
        self.t.write('SYST:PRES')

    # ---------------- acquisition ---------------- #
    def start_sweep_all(self):
        """Trigger a fresh sweep and block until it is finished.

        Why not just read the trace: with INIT:CONT ON the instrument is free
        running, and CALC:DATA? then returns whatever sweep happened to be in
        the buffer — usually a stale one taken under the *previous* settings.
        Every wrong-looking pump sweep starts here.

        SENS:SWE:MODE SING arms exactly one sweep (or one full averaging group
        if averaging is on); *OPC? then blocks until it completes.
        """
        if self.average_state() == 'on':
            n = self.avg()
            self.average_clear()
            self.t.write(f'SENS:SWE:GRO:COUN {n}')
            self.t.write('SENS:SWE:MODE GRO')
        else:
            self.t.write('SENS:SWE:MODE SING')
        self.t.query('*OPC?')

    def wait_to_continue(self):
        self.t.query('*OPC?')

    def get_real_imaginary_data(self):
        """Return (real, imag) arrays of the corrected complex trace.

        CALC:DATA? SDATA gives real,imag,real,imag,... interleaved, one pair
        per frequency point.
        """
        values = self._read_data('CALC:DATA? SDATA')
        npts = self._npts if self._npts is not None else len(values) // 2
        if len(values) != 2 * npts:
            raise ValueError(
                f'expected {2 * npts} numbers for {npts} points, got '
                f'{len(values)}. Format or point count is out of sync.')
        return values[0::2], values[1::2]

    def get_complex_data(self):
        re, im = self.get_real_imaginary_data()
        return re + 1j * im

    def get_formatted_data(self):
        """CALC:DATA? FDATA — what the screen shows, one value per point.

        Used by verify_against_instrument() as an independent check on our
        SDATA parse.
        """
        return self._read_data('CALC:DATA? FDATA')

    def get_x_axis(self):
        """CALC:X? — the instrument's own frequency axis. Slow; for checking."""
        return self._read_data('CALC:X?')

    def _read_data(self, command):
        if not self.binary:
            return np.array(
                [float(x) for x in self.t.query(command).strip().split(',')])
        payload = parse_binary_block(self.t.query_raw(command))
        return np.frombuffer(payload, dtype=self._dtype)

    # ---------------- diagnostics ---------------- #
    def errors(self):
        """Drain and return the SCPI error queue."""
        out = []
        for _ in range(50):
            e = self.t.query('SYST:ERR?').strip()
            out.append(e)
            if e.startswith('+0') or e.startswith('0,'):
                break
        return out

    def sweep_time(self):
        return float(self.t.query('SENS:SWE:TIME?'))

    def verify_against_instrument(self, rtol=1e-3):
        """Prove the binary parse is correct, using the VNA as its own oracle.

        Three independent checks, all run against a single fresh sweep:

        1. length   — SDATA must contain exactly 2 numbers per point.
        2. magnitude— our |S| from SDATA must match the instrument's own FDATA
                      (when the trace format is log-mag). This catches wrong
                      float width, wrong byte order, and swapped real/imag all
                      at once, because any of them changes the magnitude.
        3. axis     — our local linspace must match CALC:X?.

        Run this once on real hardware before trusting the driver with data.
        Returns a dict of results; raises nothing, so you can inspect it.
        """
        self.start_sweep_all()
        re, im = self.get_real_imaginary_data()
        result = {'npts': len(re), 'length_ok': len(re) == self._npts}

        ours = 20 * np.log10(np.abs(re + 1j * im))
        theirs = self.get_formatted_data()
        if len(theirs) == len(ours):
            result['max_mag_diff_dB'] = float(np.max(np.abs(ours - theirs)))
            result['magnitude_ok'] = bool(
                np.allclose(ours, theirs, rtol=rtol, atol=1e-3))
        else:
            result['magnitude_ok'] = None  # trace not in log-mag format
            result['note'] = (f'FDATA has {len(theirs)} values vs {len(ours)} '
                              'points; set the trace to log-mag to compare.')

        theirs_x = self.get_x_axis()
        ours_x = self.freq_axis()
        if len(theirs_x) == len(ours_x):
            result['max_freq_diff_Hz'] = float(np.max(np.abs(ours_x - theirs_x)))
            result['axis_ok'] = bool(np.allclose(ours_x, theirs_x, rtol=0, atol=1.0))
        else:
            result['axis_ok'] = False

        result['errors'] = self.errors()
        return result
