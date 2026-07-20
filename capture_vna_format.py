"""Capture the RAW SCPI responses of the Keysight PNA N5222B.

RUN THIS ON THE LAB PC. It is READ-ONLY: every SCPI string it sends ends in
'?', i.e. it is a *query* (ask the instrument something) and never a *command*
(tell the instrument to do something). It does not start a sweep, does not
change any setting, and does not touch the signal generator. Whatever the VNA
is currently showing is what gets read.

Why this exists
---------------
We want to talk to the VNA directly over SCPI instead of going through the
PycQED KST_VNA driver. To do that we have to know EXACTLY what bytes the
instrument sends back: ASCII or binary, 32- or 64-bit floats, byte order, and
how the real/imaginary pairs are laid out. Guessing gets you silently wrong
numbers. This script writes the ground truth to a file we can then match.

Usage
-----
    python capture_vna_format.py

Optional: if the data queries come back empty because no trace is selected on
this VISA session, re-run with

    python capture_vna_format.py --allow-select

which permits ONE state-changing command (CALC:PAR:SEL, selecting an existing
trace). That does not alter the measurement, but it is a write, so it is
off by default and clearly logged.

Output: vna_format_capture.txt in this folder. Send me that file.
"""

import argparse
import datetime
import sys

# Note: the address lives in qlab/config.py so there is one source of truth.
try:
    from qlab import config
    DEFAULT_ADDRESS = config.VNA_ADDRESS
except Exception:
    DEFAULT_ADDRESS = 'USB0::0x2A8D::0x2A01::MY58421887::0::INSTR'

OUTFILE = 'vna_format_capture.txt'

# Every entry: (label, scpi_query, why_we_care)
QUERIES = [
    # --- identity / sanity ---
    ('IDN', '*IDN?',
     'Confirms we are talking to the right box and gives the firmware rev.'),

    # --- how numbers come back over the wire (THE important part) ---
    ('DATA_FORMAT', 'FORM:DATA?',
     'ASC,0 = ASCII text. REAL,32 / REAL,64 = binary floats. Decides how we parse.'),
    ('BYTE_ORDER', 'FORM:BORD?',
     'NORM = big-endian, SWAP = little-endian. Wrong choice = garbage numbers.'),

    # --- what traces exist ---
    ('MEAS_CATALOG', 'CALC:PAR:CAT:EXT?',
     'Lists the measurement names and their S-parameters, e.g. "CH1_S21_1,S21".'),
    ('ACTIVE_CHANNELS', 'SYST:CHAN:CAT?',
     'Which channels are defined.'),

    # --- the frequency axis ---
    ('SWEEP_START', 'SENS:FREQ:STAR?', 'Start frequency in Hz.'),
    ('SWEEP_STOP', 'SENS:FREQ:STOP?', 'Stop frequency in Hz.'),
    ('SWEEP_POINTS', 'SENS:SWE:POIN?',
     'Number of points. Must equal len(data)/2 for SDATA. Key consistency check.'),
    ('SWEEP_TYPE', 'SENS:SWE:TYPE?', 'LIN / LOG / SEGM - affects axis construction.'),
    ('SWEEP_TIME', 'SENS:SWE:TIME?',
     'Seconds per sweep. This is the number our speed work has to beat.'),

    # --- settings our code sets, so we learn the exact spelling ---
    ('IF_BANDWIDTH', 'SENS:BWID?', 'IF bandwidth in Hz.'),
    ('POWER', 'SOUR:POW?', 'Probe power in dBm.'),
    ('AVG_STATE', 'SENS:AVER:STAT?', 'Averaging on (1) or off (0).'),
    ('AVG_COUNT', 'SENS:AVER:COUN?', 'Number of averages.'),
    ('AVG_MODE', 'SENS:AVER:MODE?', 'POIN or SWE - matches average_mode() in our code.'),
    ('ELEC_DELAY', 'CALC:CORR:EDEL:TIME?', 'Electrical delay in seconds.'),
    ('RF_OUTPUT', 'OUTP?', 'RF source on (1) or off (0).'),
    ('TRIGGER_SOURCE', 'TRIG:SOUR?', 'IMM / MAN / EXT - matters for sweep timing.'),

    # --- CALIBRATION: if a cal is applied, our rewrite must not break it ---
    ('CAL_STATE', 'SENS:CORR:STAT?',
     '1 = calibration applied. If 1, changing npts/span can invalidate it. CRITICAL.'),
    ('CAL_INTERPOLATE', 'SENS:CORR:INT?',
     '1 = VNA silently interpolates the cal when the sweep changes. Quality risk.'),
    ('CAL_SET_NAME', 'SENS:CORR:CSET:ACT? NAME',
     'Which cal set is active, so we can re-apply the same one.'),
    ('CAL_TYPE', 'SENS:CORR:TYPE:CAT?',
     'What kind of cal (SOLT, response, etc.).'),

    # --- how sweeps are armed / how we know one finished ---
    ('CONTINUOUS', 'INIT:CONT?',
     '1 = free-running. If 1, reading data returns a STALE trace, not a fresh one.'),
    ('SWEEP_MODE', 'SENS:SWE:MODE?',
     'HOLD / CONT / SING / GRO - how a sweep gets triggered.'),
    ('SWEEP_GROUP_COUNT', 'SENS:SWE:GRO:COUN?',
     'Sweeps per group in GRO mode; relevant to how averaging is driven.'),

    # --- source levelling, affects absolute power accuracy ---
    ('POWER_ATTEN', 'SOUR:POW:ATT?', 'Port attenuator setting in dB.'),
    ('POWER_COUPLED', 'SOUR:POW:COUP?', 'Are port powers coupled together.'),
]


def main(argv=None):
    # argv=None -> read the command line (normal `python capture_vna_format.py`).
    # Pass a list instead to call this from a notebook, e.g. main([]) or
    # main(['--allow-select']), which avoids parsing Jupyter's own arguments.
    ap = argparse.ArgumentParser()
    ap.add_argument('--address', default=DEFAULT_ADDRESS)
    ap.add_argument('--allow-select', action='store_true',
                    help='Permit ONE write (CALC:PAR:SEL) to select an existing trace.')
    args = ap.parse_args(argv)

    try:
        import pyvisa
    except ImportError:
        sys.exit('pyvisa not installed in this environment. '
                 'Activate the lab conda env and retry.')

    lines = []

    def log(s=''):
        print(s)
        lines.append(s)

    log('=' * 70)
    log('N5222B SCPI FORMAT CAPTURE  (read-only)')
    log(f'timestamp : {datetime.datetime.now().isoformat(timespec="seconds")}')
    log(f'address   : {args.address}')
    log('=' * 70)

    rm = pyvisa.ResourceManager()
    log('\n--- VISA resources visible on this PC ---')
    for r in rm.list_resources():
        log(f'  {r}')

    inst = rm.open_resource(args.address)
    inst.timeout = 10000  # ms

    # ------------------------------------------------------------------ #
    # Pass 1: plain text queries
    # ------------------------------------------------------------------ #
    log('\n--- SETTINGS / IDENTITY ---')
    for label, scpi, why in QUERIES:
        assert '?' in scpi, f'refusing non-query: {scpi}'
        try:
            resp = inst.query(scpi).strip()
            log(f'{label:16s} | {scpi:26s} -> {resp!r}')
        except Exception as e:
            log(f'{label:16s} | {scpi:26s} -> ERROR: {type(e).__name__}: {e}')
        log(f'{"":16s} | ^ {why}')

    # ------------------------------------------------------------------ #
    # Pass 2: the actual trace data, in every representation we might use
    # ------------------------------------------------------------------ #
    log('\n--- TRACE DATA ---')

    if args.allow_select:
        try:
            cat = inst.query('CALC:PAR:CAT:EXT?').strip().strip('"')
            first = cat.split(',')[0]
            log(f'[WRITE] CALC:PAR:SEL "{first}"   <-- the one allowed write')
            inst.write(f'CALC:PAR:SEL "{first}"')
        except Exception as e:
            log(f'[WRITE] select failed: {e}')
    else:
        log('(no trace selected; using whatever this session already has. '
            'If the reads below fail, re-run with --allow-select)')

    data_queries = [
        ('SDATA', 'CALC:DATA? SDATA',
         'Complex corrected data: real,imag,real,imag,... THIS is what our code needs.'),
        ('FDATA', 'CALC:DATA? FDATA',
         'Formatted data - what the screen shows (e.g. log-mag). One value per point.'),
        ('XAXIS', 'CALC:X?',
         'The frequency axis as the VNA computes it. Compare to our linspace.'),
    ]

    for label, scpi, why in data_queries:
        log(f'\n>>> {label}: {scpi}')
        log(f'    ({why})')

        # (a) raw bytes, exactly as they arrive
        try:
            inst.write(scpi)
            raw_bytes = inst.read_raw()
            log(f'    total bytes returned : {len(raw_bytes)}')
            log(f'    first 80 bytes (repr): {raw_bytes[:80]!r}')
            log(f'    last  20 bytes (repr): {raw_bytes[-20:]!r}')
            # A leading b'#' means IEEE binary block; anything else means ASCII.
            if raw_bytes[:1] == b'#':
                ndigits = int(raw_bytes[1:2])
                nbytes = int(raw_bytes[2:2 + ndigits])
                log(f'    -> IEEE 488.2 binary block: header #{ndigits}{nbytes}, '
                    f'{nbytes} payload bytes')
            else:
                ncommas = raw_bytes.count(b',')
                log(f'    -> ASCII, {ncommas + 1} comma-separated values')
        except Exception as e:
            log(f'    RAW READ ERROR: {type(e).__name__}: {e}')

        # (b) parsed via pyvisa's own ASCII reader, as a cross-check
        try:
            vals = inst.query_ascii_values(scpi)
            log(f'    parsed as ASCII      : {len(vals)} values')
            log(f'    first 6              : {vals[:6]}')
        except Exception as e:
            log(f'    ASCII PARSE          : {type(e).__name__}: {e}')

    # ------------------------------------------------------------------ #
    # Pass 3: did the instrument log any complaints?
    # ------------------------------------------------------------------ #
    log('\n--- ERROR QUEUE (drained) ---')
    for _ in range(20):
        try:
            err = inst.query('SYST:ERR?').strip()
        except Exception as e:
            log(f'  could not read error queue: {e}')
            break
        log(f'  {err}')
        if err.startswith('+0') or 'No error' in err:
            break

    inst.close()

    with open(OUTFILE, 'w') as f:
        f.write('\n'.join(lines) + '\n')
    log(f'\nWrote {OUTFILE}')


if __name__ == '__main__':
    main()
