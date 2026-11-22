import importlib.util
import os
import unittest
import warnings

# Load the module straight from its file so this test does not need OctoPrint
# (the package's __init__ imports the plugin, which imports OctoPrint).
_MODULE_PATH = os.path.join(
    os.path.dirname(__file__),
    os.pardir,
    "octoprint_e3s1proforkbyttthumbnails",
    "services",
    "gcode_utils.py",
)
_spec = importlib.util.spec_from_file_location("gcode_utils", _MODULE_PATH)
gcode_utils = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gcode_utils)

is_extrusion_move = gcode_utils.is_extrusion_move

EXPECTED = {
    "G1 X10 E1.5": True,
    "G1 F1800 E-2": True,
    "  G1 X1 E.5": True,
    "G1 X5 Y5 E0.4 F1200": True,
    "G1X10E1": True,
    "G1.1 X1 E2": True,
    "G1 X1 e2": True,
    "G1 X1 ; E3": True,  # inherited quirk: E inside a comment also counts
    "G1 X1 Y2": False,
    "G1 Z0.2 F600": False,
    "G1 X1 E": False,
    "G1 X1 NE1": False,
    "g1 X1 E1": False,
    "G0 E5": False,
    "G10 E1": False,
    "G11 E1": False,
    "G01 X1 E1": False,
    "G28": False,
    "G92 E0": False,
    "M104 S200": False,
    "; G1 E5": False,
    "T0": False,
    "": False,
}


def _octoprint_reference():
    """Return OctoPrint's original check, or None if it is not available."""
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            from octoprint.util.comm import gcode_command_for_cmd, regexes_parameters
    except Exception:
        return None

    def reference(line):
        return gcode_command_for_cmd(line) == "G1" and bool(
            regexes_parameters["floatE"].search(line)
        )

    return reference


class IsExtrusionMoveTests(unittest.TestCase):
    def test_expected_values(self):
        for line, expected in EXPECTED.items():
            with self.subTest(line=line):
                self.assertIs(is_extrusion_move(line), expected)

    def test_matches_octoprint_reference_implementation(self):
        reference = _octoprint_reference()
        if reference is None:
            self.skipTest("OctoPrint is not installed")
        for line in EXPECTED:
            with self.subTest(line=line):
                self.assertEqual(is_extrusion_move(line), reference(line))


if __name__ == "__main__":
    unittest.main()
