"""Instrument connection / station setup.

Two entry points:

- ``connect()``       -> real hardware, on the lab PC (needs PycQED etc.)
- ``connect_fake()``  -> fake instruments, runs anywhere (laptop smoke tests)

Both return a ``LabStation`` object holding everything the measurement
functions need. All PycQED / QCoDeS imports happen *inside* ``connect()`` so
this package imports cleanly on machines without the lab environment.

Original source: setup cells of QLab_tra_HH.ipynb (cells 2-8) and
HH_qubit.ipynb (cells 2-7). The call sequence is preserved verbatim.
"""

import os

from . import config


class LabStation:
    """Bag of handles: vna, sgen, MC, Q1, station, IM, datadir, fake flag."""

    def __init__(self):
        self.vna = None
        self.sgen = None
        self.MC = None
        self.Q1 = None
        self.station = None
        self.IM = None
        self.datadir = None
        self.fake = False
        # PycQED modules stashed here at connect() time so measurement code
        # never imports pycqed at module level
        self._swf = None
        self._det = None


def connect(datadir=config.DATADIR_LAB, live_plot=True, with_monitor=True):
    """Connect to the real instruments and build the PycQED measurement stack.

    Mirrors the setup cells of both notebooks exactly:
    imports -> instruments -> Station -> MeasurementControl -> datadir ->
    add components -> InstrumentMonitor -> QLab_Neon wrapper.
    """
    # ---------------- Imports (deferred: lab PC only) ---------------- #
    from pycqed.instrument_drivers.physical_instruments.KST_VNA import KST_VNA
    from pycqed.measurement import detector_functions as det
    from pycqed.measurement import sweep_functions as swf
    from pycqed.measurement import measurement_control
    from pycqed.instrument_drivers.meta_instrument.qubit_objects import QLab_Neon as eNeQ
    from qcodes.instrument_drivers.Anritsu import MG369xC
    import pycqed.analysis.analysis_toolbox as a_tools
    from qcodes import Station

    st = LabStation()
    st._swf = swf
    st._det = det

    # ---------------- Instruments ---------------- #
    st.vna = KST_VNA(name=config.VNA_NAME, address=config.VNA_ADDRESS)
    st.sgen = MG369xC.ANRITSU_MG369xC(name=config.SGEN_NAME,
                                      address=config.SGEN_ADDRESS)
    # qdac = QDAC2.QDac2(name='qdac5', address='TCPIP0::169.254.0.6::5025::SOCKET')

    # ---------------- MeasurementControl + data directory ---------------- #
    st.station = Station()
    st.MC = measurement_control.MeasurementControl(
        'MC', live_plot_enabled=live_plot, verbose=True)
    st.MC.station = st.station
    st.station.add_component(st.MC)
    st.MC.live_plot_enabled(live_plot)

    a_tools.datadir = datadir
    st.MC.datadir(a_tools.datadir)
    st.datadir = datadir

    # ---------------- Register instruments ---------------- #
    st.station.add_component(st.vna)
    st.station.add_component(st.sgen)

    if with_monitor:
        from pycqed.instrument_drivers.virtual_instruments import instrument_monitor as im
        st.IM = im.InstrumentMonitor('IM', st.station)
        st.station.add_component(st.IM)
        st.MC.instrument_monitor('IM')
        st.IM.update()

    # ---------------- Lab-local qubit wrapper ---------------- #
    st.Q1 = eNeQ.QLab_Neon('Q1', st.MC, st.vna, sgen_instr=st.sgen)

    st.vna.reset()
    return st


def connect_fake(datadir=config.DATADIR_FAKE):
    """Build a station backed by FakeVNA/FakeSgen. Runs on any machine."""
    from .fake_vna import FakeVNA, FakeSgen

    st = LabStation()
    st.fake = True
    st.sgen = FakeSgen()
    st.vna = FakeVNA(sgen=st.sgen)
    os.makedirs(datadir, exist_ok=True)
    st.datadir = datadir
    print(f"[qlab] FAKE station: synthetic resonator at "
          f"{st.vna.f_r/1e9:.4f} GHz, fake qubit at {st.vna.f_q/1e9:.4f} GHz. "
          f"Data -> {datadir}")
    return st


def all_off(st):
    """Pump off, VNA RF off. Call at the end of a session."""
    st.sgen.on("OFF")
    st.vna.rf_off()
