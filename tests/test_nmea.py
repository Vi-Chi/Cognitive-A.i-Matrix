import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from mebus import (
    MMessage, Mode, MembraneBus, AdapterRegistry, NMEAAdapter,
    nmea_checksum, MessageValidationError,
)

GGA = "$GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47"
RMC = "$GPRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*6A"


class TestNMEAAdapter(unittest.TestCase):
    def test_checksum_helper(self):
        self.assertEqual(nmea_checksum(GGA), "47")
        self.assertEqual(nmea_checksum(RMC), "6A")

    def test_gga_parses_position(self):
        m = NMEAAdapter().ingest(GGA)
        m.validate()
        self.assertEqual(m.sigma, "m.state")
        self.assertEqual(m.context["domain"], "maritime.nav")
        v = m.payload["value"]
        self.assertAlmostEqual(v["latitude"], 48.1173, places=3)
        self.assertAlmostEqual(v["longitude"], 11.5167, places=3)
        self.assertEqual(v["fix_quality"], 1)

    def test_rmc_parses_sog_cog(self):
        m = NMEAAdapter().ingest(RMC)
        v = m.payload["value"]
        self.assertAlmostEqual(v["sog_knots"], 22.4, places=1)
        self.assertAlmostEqual(v["cog_deg"], 84.4, places=1)

    def test_southern_western_hemisphere_signs(self):
        s = "$GPGGA,123519,4807.038,S,01131.000,W,1,08,0.9,545.4,M,46.9,M,,"
        v = NMEAAdapter().ingest(s).payload["value"]
        self.assertLess(v["latitude"], 0)
        self.assertLess(v["longitude"], 0)

    def test_bad_checksum_raises(self):
        with self.assertRaises(MessageValidationError):
            NMEAAdapter().ingest(GGA[:-2] + "00")

    def test_unknown_sentence_carried_as_ext(self):
        m = NMEAAdapter().ingest("$GPVTG,054.7,T,034.4,M,005.5,N,010.2,K")
        self.assertEqual(m.sigma, "ext.nmea")
        self.assertEqual(m.sigma_class, "ext")

    def test_registry_and_emit_roundtrip(self):
        r = AdapterRegistry()
        r.register(NMEAAdapter())
        m = r.ingest("nmea", RMC)
        self.assertEqual(r.emit("nmea", m), RMC)

    def test_ext_nmea_passes_in_dream(self):
        bus = MembraneBus()
        got = []
        bus.subscribe("ext.nmea", lambda m: got.append(m))
        m = NMEAAdapter().ingest("$GPVTG,054.7,T,034.4,M,005.5,N,010.2,K", mode=Mode.DREAM)
        self.assertTrue(bus.publish(m))


if __name__ == "__main__":
    unittest.main()
