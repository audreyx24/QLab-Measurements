"""The real pyvisa transport. Lab PC only — pyvisa is not installed offline.

Kept in its own tiny module so that scpi_vna.py never imports pyvisa at module
level, which is what lets the driver be tested on a laptop.

The transport is deliberately dumb: it moves strings and bytes, and knows
nothing about VNAs. All SCPI lives in scpi_vna.py.
"""


class VisaTransport:
    def __init__(self, address, timeout_ms=30000):
        import pyvisa
        self._rm = pyvisa.ResourceManager()
        self.inst = self._rm.open_resource(address)
        self.inst.timeout = timeout_ms
        self.address = address

    @property
    def timeout_ms(self):
        return self.inst.timeout

    @timeout_ms.setter
    def timeout_ms(self, value):
        self.inst.timeout = value

    def write(self, command):
        self.inst.write(command)

    def query(self, command):
        return self.inst.query(command)

    def query_raw(self, command):
        """Send a query and return the raw bytes, header and all.

        We do the IEEE 488.2 block parsing ourselves (parse_binary_block) so
        that the same code path is exercised offline against FakeSCPIInstrument.
        """
        self.inst.write(command)
        return self.inst.read_raw()

    def close(self):
        self.inst.close()
        self._rm.close()
