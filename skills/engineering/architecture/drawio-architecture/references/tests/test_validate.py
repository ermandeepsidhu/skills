import os
import unittest

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from validate import validate_drawio  # noqa: E402

FIX = os.path.join(os.path.dirname(__file__), "fixtures")


class TestValidateDrawio(unittest.TestCase):
    def test_good_file_has_no_problems(self):
        self.assertEqual(validate_drawio(os.path.join(FIX, "good.drawio")), [])

    def test_overlap_is_detected(self):
        problems = validate_drawio(os.path.join(FIX, "bad_overlap.drawio"))
        self.assertTrue(any("overlap" in p for p in problems), problems)

    def test_dangling_edge_is_detected(self):
        problems = validate_drawio(os.path.join(FIX, "bad_dangling.drawio"))
        self.assertTrue(any("does not resolve" in p for p in problems), problems)

    def test_malformed_xml_is_reported(self):
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".drawio", delete=False) as f:
            f.write("<mxfile><diagram>")  # unclosed
            path = f.name
        problems = validate_drawio(path)
        os.unlink(path)
        self.assertTrue(any("well-formed" in p for p in problems), problems)

    def test_vertex_without_id_is_reported(self):
        import tempfile
        xml = (
            '<mxfile><diagram name="noid"><mxGraphModel><root>'
            '<mxCell id="0"/><mxCell id="1" parent="0"/>'
            '<mxCell value="A" vertex="1" parent="1">'
            '<mxGeometry x="40" y="40" width="160" height="80" as="geometry"/></mxCell>'
            '<mxCell value="B" vertex="1" parent="1">'
            '<mxGeometry x="100" y="60" width="160" height="80" as="geometry"/></mxCell>'
            '</root></mxGraphModel></diagram></mxfile>'
        )
        with tempfile.NamedTemporaryFile("w", suffix=".drawio", delete=False) as f:
            f.write(xml)
            path = f.name
        problems = validate_drawio(path)
        os.unlink(path)
        self.assertTrue(any("missing its required id" in p for p in problems), problems)


if __name__ == "__main__":
    unittest.main()
