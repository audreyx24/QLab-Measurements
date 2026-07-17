"""Central place for addresses, data directories, and default parameters.

Everything that was a magic number scattered across the notebooks lives here.
Edit this file (not the measurement code) when the setup changes.
"""

import os
import time

# ---------------- Instrument addresses ---------------- #
VNA_NAME = 'N5222B3'
VNA_ADDRESS = 'USB0::0x2A8D::0x2A01::MY58421887::0::INSTR'   # Keysight PNA N5222B

SGEN_NAME = 'MG3692C'
SGEN_ADDRESS = 'GPIB0::5::INSTR'                             # Anritsu MG3692C

# QDAC2 currently unused (kept for reference, was commented out in notebooks)
# QDAC_ADDRESS = 'TCPIP0::169.254.0.6::5025::SOCKET'

# ---------------- Data directories ---------------- #
# On the lab PC (Windows):
DATADIR_LAB = 'C:/Data_HH/stub-s3'
# For offline / fake-instrument runs (created automatically):
DATADIR_FAKE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'fake_data')

# ---------------- Common defaults ---------------- #
# Electrical delay of the cabling [s]; flattens the S21 phase.
# Transmission path ~64-67 ns depending on cabling; reflection path ~1 ns.
DEFAULT_DELAY_S21 = 6.5e-8
DEFAULT_DELAY_S11 = 1e-9

DEFAULT_IF_BANDWIDTH = 1000     # [Hz] lower = less noise, slower sweep
DEFAULT_VNA_TIMEOUT = 1000


# ---------------- Output-folder organization ---------------- #
def make_run_dir(datadir, name):
    """Create and return a timestamped folder for one measurement's output,
    mirroring the layout PycQED itself uses for MC.run() datasets:

        datadir/YYYYMMDD/HHMMSS_name/

    Everything a single measurement produces (CSV, PNG, ...) goes inside
    that folder. This is what makes the direct-save paths (fake-mode scans
    and the Gen3 pump_sweep_fast CSV, which bypass PycQED's own saver) land
    in the SAME date-organized tree as the PycQED datasets — so on the lab
    PC a whole day's data sits together under one YYYYMMDD folder regardless
    of which code path wrote it.

    `name` is sanitized for use as a folder name.
    """
    now = time.localtime()
    day = time.strftime('%Y%m%d', now)
    stamp = time.strftime('%H%M%S', now)
    safe = ''.join(c if (c.isalnum() or c in '-_.') else '_' for c in name)
    run_dir = os.path.join(datadir, day, f'{stamp}_{safe}')
    os.makedirs(run_dir, exist_ok=True)
    return run_dir
