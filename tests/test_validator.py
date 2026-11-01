import unittest

from citygml_audit.validator import audit_text

HEADER = '<core:CityModel xmlns:core="http://www.opengis.net/citygml/2.0" xmlns:bldg="http://www.opengis.net/citygml/building/2.0" xmlns:gml="http://www.opengis.net/gml">'
FOOTER = "</core:CityModel>"


def model(coords, ring_attributes=""):
    return HEADER + '<bldg:Building gml:id="b1"><gml:Polygon gml:id="p1"><gml:exterior><gml:LinearRing ' + ring_attributes + '><gml:posList>' + coords + '</gml:posList></gml:LinearRing></gml:exterior></gml:Polygon></bldg:Building>' + FOOTER


class ValidatorTests(unittest.TestCase):
    def test_valid_ring(self):
        result = audit_text(model("0 0 0 1 0 0 1 1 0 0 0 0"))
        self.assertEqual(result["buildings"], 1)
        self.assertEqual(result["rings"], 1)
        self.assertEqual(result["findings"], [])

    def test_unclosed_ring(self):
        codes = [f["code"] for f in audit_text(model("0 0 0 1 0 0 1 1 0 0 1 0"))["findings"]]
        self.assertIn("UNCLOSED_RING", codes)

    def test_malformed_xml(self):
        self.assertEqual(audit_text("<broken")["findings"][0]["code"], "INVALID_XML")

    def test_degenerate(self):
        codes = [f["code"] for f in audit_text(model("0 0 0 0 0 0 0 0 0 0 0 0"))["findings"]]
        self.assertIn("DEGENERATE_RING", codes)

    def test_dimension_2(self):
        result = audit_text(model("0 0 1 0 1 1 0 0", 'srsDimension="2"'), dimension=3)
        self.assertEqual(result["findings"], [])

    def test_nonplanar(self):
        codes = [f["code"] for f in audit_text(model("0 0 0 1 0 0 1 1 1 0 1 0 0 0 0"))["findings"]]
        self.assertIn("NON_PLANAR_RING", codes)

    def test_duplicates(self):
        xml = HEADER + '<bldg:Building gml:id="same"/><bldg:Building gml:id="same"/>' + FOOTER
        self.assertIn("DUPLICATE_ID", [f["code"] for f in audit_text(xml)["findings"]])

    def test_invalid_dimension(self):
        with self.assertRaises(ValueError):
            audit_text(HEADER + FOOTER, dimension=4)


if __name__ == "__main__":
    unittest.main()
