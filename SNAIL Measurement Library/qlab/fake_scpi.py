"""A fake N5222B that speaks SCPI at the byte level. Runs anywhere, no pyvisa.

WHY THIS EXISTS, AND HOW IT DIFFERS FROM fake_vna.FakeVNA
--------------------------------------------------------
FakeVNA fakes the *driver*: it hands back numpy arrays, so it tests the
measurement logic (sweep loops, saving, plotting) but never exercises a single
byte of SCPI.

FakeSCPIInstrument fakes the *instrument*: it accepts SCPI strings and returns
bytes, including real IEEE 488.2 definite-length binary blocks encoded at the
requested float width and byte order. So SCPIVNA's actual parsing code runs
against it unchanged — the header parse, the dtype choice, the real/imag
de-interleave. That is precisely the code we could not verify from the
2026-07-20 capture, and precisely the code that fails silently when wrong.

It deliberately reproduces the failure we hit on the real instrument: querying
CALC:DATA? without first selecting a measurement returns nothing and pushes
'+103,"CALC measurement selection set to none"' onto the error queue.

The physics comes from FakeVNA, so the fake resonator is the same one the rest
of the offline test suite uses.
"""

import numpy as np

from .fake_vna import FakeVNA, FakeSgen


class ScpiTimeout(Exception):
    """Raised where the real instrument would time out (no reply came back)."""


class FakeSCPIInstrument:
    """Transport-shaped fake: .write() / .query() / .query_raw()."""

    IDN = 'Keysight Technologies,N5222B,MY58421887,A.13.50.09'

    def __init__(self, sgen=None, strict_selection=True, seed=0):
        self.vna = FakeVNA(sgen=sgen if sgen is not None else FakeSgen())
        # Deterministic noise: two instruments built with the same seed produce
        # byte-identical traces, which is what lets the test compare REAL,32
        # against REAL,64 and see only the encoding difference.
        self.vna._rng = np.random.default_rng(seed)
        self.timeout_ms = 30000
        self.strict_selection = strict_selection
        # The acquired trace. A real VNA samples once per sweep and then serves
        # every CALC:DATA? query from that one buffer — SDATA and FDATA are two
        # views of the SAME acquisition, not two fresh measurements. The first
        # version of this fake recomputed (with new noise) per query, which made
        # the SDATA-vs-FDATA oracle check fail against itself.
        self._trace = None

        self.data_format = 'ASC'      # matches the instrument as we found it
        self.float_bits = 0
        self.byte_order = 'NORM'
        self.selected = None
        self.measurements = [('CH1_S11_1', 'S21')]   # the real catalog, mismatched name and all
        self.errors = []
        self.log = []                 # every command, for assertions in tests
        self._swept = False
        self._sweep_mode = 'HOLD'

    # ---------------- transport surface ---------------- #
    def write(self, command):
        self.log.append(command)
        self._dispatch_write(command.strip())

    def query(self, command):
        self.log.append(command)
        out = self._dispatch_query(command.strip())
        if out is None:
            raise ScpiTimeout(f'no response to {command!r} (VI_ERROR_TMO)')
        return out

    def query_raw(self, command):
        self.log.append(command)
        out = self._dispatch_query_raw(command.strip())
        if out is None:
            raise ScpiTimeout(f'no response to {command!r} (VI_ERROR_TMO)')
        return out

    def close(self):
        pass

    # ---------------- command handling ---------------- #
    def _dispatch_write(self, c):
        u = c.upper()
        if u.startswith('FORM:DATA'):
            arg = c.split(None, 1)[1]
            if arg.upper().startswith('REAL'):
                self.data_format = 'REAL'
                self.float_bits = int(arg.split(',')[1])
            else:
                self.data_format, self.float_bits = 'ASC', 0
        elif u.startswith('FORM:BORD'):
            self.byte_order = c.split(None, 1)[1].upper()
        elif u.startswith('CALC:PAR:SEL'):
            name = c.split(None, 1)[1].strip().strip("'\"")
            if name in [m[0] for m in self.measurements]:
                self.selected = name
            else:
                self.errors.append(f'-113,"Undefined header; no measurement {name}"')
        elif u.startswith('SENS:FREQ:STAR'):
            self.vna._start = float(c.split()[-1])
        elif u.startswith('SENS:FREQ:STOP'):
            self.vna._stop = float(c.split()[-1])
        elif u.startswith('SENS:SWE:POIN'):
            self.vna._npts = int(float(c.split()[-1]))
        elif u.startswith('SOUR:POW'):
            self.vna._power = float(c.split()[-1])
        elif u.startswith('SENS:BWID'):
            self.vna._if_bandwidth = float(c.split()[-1])
        elif u.startswith('CALC:CORR:EDEL:TIME'):
            self.vna._delay_t = float(c.split()[-1])
        elif u.startswith('SENS:AVER:COUN'):
            self.vna._averages = int(float(c.split()[-1]))
        elif u.startswith('SENS:AVER:STAT'):
            self.vna._average_state = 'on' if c.split()[-1].upper() in ('ON', '1') else 'off'
        elif u.startswith('SENS:AVER:MODE'):
            self.vna._average_mode = c.split()[-1]
        elif u.startswith('SENS:AVER:CLE'):
            pass
        elif u.startswith('SENS:SWE:MODE'):
            self._sweep_mode = c.split()[-1].upper()
            self._acquire()             # arming a sweep latches a new trace
        elif u.startswith('OUTP'):
            self.vna._rf = c.split()[-1].upper() in ('ON', '1')
        elif u.startswith(('DISP:', 'SENS:SWE:GRO:COUN', 'SYST:PRES')):
            pass
        else:
            self.errors.append(f'-113,"Undefined header; {c}"')

    def _dispatch_query(self, c):
        u = c.upper()
        if u == '*IDN?':
            return self.IDN
        if u == '*OPC?':
            return '+1'
        if u == 'SYST:ERR?':
            return self.errors.pop(0) if self.errors else '+0,"No error"'
        if u == 'CALC:PAR:CAT:EXT?':
            flat = ','.join(f'{n},{s}' for n, s in self.measurements)
            return f'"{flat}"'
        if u == 'SENS:FREQ:STAR?':
            return f'{self.vna._start:+.11E}'
        if u == 'SENS:FREQ:STOP?':
            return f'{self.vna._stop:+.11E}'
        if u == 'SENS:SWE:POIN?':
            return f'{self.vna._npts:+d}'
        if u == 'SENS:BWID?':
            return f'{self.vna._if_bandwidth:+.11E}'
        if u == 'SOUR:POW?':
            return f'{self.vna._power:+.11E}'
        if u == 'SENS:AVER:COUN?':
            return f'{self.vna._averages:+d}'
        if u == 'SENS:AVER:STAT?':
            return '1' if self.vna._average_state == 'on' else '0'
        if u == 'SENS:AVER:MODE?':
            return self.vna._average_mode
        if u == 'SENS:SWE:TIME?':
            return f'{self.vna._npts / max(self.vna._if_bandwidth, 1):+.11E}'
        if u == 'FORM:DATA?':
            return 'ASC,0' if self.data_format == 'ASC' else f'REAL,{self.float_bits}'
        if u == 'FORM:BORD?':
            return self.byte_order
        if u.startswith('CALC:'):
            # data queries in ASCII mode land here
            values = self._data_for(u)
            if values is None:
                return None
            return ','.join(f'{v:+.11E}' for v in values)
        return None

    def _dispatch_query_raw(self, c):
        u = c.upper()
        if not u.startswith('CALC:'):
            text = self._dispatch_query(c)
            return None if text is None else (text + '\n').encode()

        values = self._data_for(u)
        if values is None:
            return None

        if self.data_format == 'ASC':
            return (','.join(f'{v:+.11E}' for v in values) + '\n').encode()

        prefix = '<' if self.byte_order.startswith('SWAP') else '>'
        dtype = np.dtype(f'{prefix}f{self.float_bits // 8}')
        payload = values.astype(dtype).tobytes()
        return self._ieee_block(payload)

    @staticmethod
    def _ieee_block(payload):
        """Wrap bytes in an IEEE 488.2 definite-length header: #<n><count>."""
        count = str(len(payload)).encode()
        return b'#' + str(len(count)).encode() + count + payload + b'\n'

    def _acquire(self):
        """Run one sweep and latch the result, as the hardware does."""
        self._trace = self.vna._compute_s21()

    def _data_for(self, u):
        """Produce the numbers behind a CALC: data query, or None to time out."""
        if self.strict_selection and self.selected is None:
            # Exactly what the real instrument did on 2026-07-20.
            self.errors.append('+103,"CALC measurement selection set to none"')
            self.errors.append('-420,"Query UNTERMINATED"')
            return None

        if self._trace is None:
            # Never swept since power-on: the real instrument would hand back
            # whatever stale buffer it holds. Give it something rather than
            # nothing, so the stale-data guard is what catches this, not a crash.
            self._acquire()
        s21 = self._trace
        if 'SDATA' in u:
            out = np.empty(2 * s21.size)
            out[0::2] = np.real(s21)     # real first — the convention under test
            out[1::2] = np.imag(s21)
            return out
        if 'FDATA' in u:
            return 20 * np.log10(np.abs(s21))     # log-mag, as on screen
        if u.startswith('CALC:X'):
            return self.vna.freq_axis()
        return None
