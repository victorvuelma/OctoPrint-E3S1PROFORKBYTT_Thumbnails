# coding=utf-8
"""Small G-code helpers that do not depend on OctoPrint internals.

OctoPrint 2.0.0 moved the old comm layer (``octoprint.util.comm``) into the
bundled ``serial_connector`` plugin. ``octoprint.util.comm`` only survives as a
deprecated re-export shim that the core no longer imports, so accessing it as
``octoprint.util.comm`` after ``import octoprint.util`` raises
``AttributeError``. The plugin only needed it to find the first extrusion move,
so that logic lives here instead.
"""

import re

# Equivalent to ``octoprint...serial_comm.gcode_command_for_cmd(line) == "G1"``:
# matches "G1" and "G1.<subcode>", but not "G10", "G11" or "G01". Like
# OctoPrint, this is case sensitive.
_G1_COMMAND_REGEX = re.compile(r"^\s*G1(?!\d)")

# Same pattern as OctoPrint's ``regexes_parameters["floatE"]``. Like the
# original check, it is applied to the whole line, comments included.
_FLOAT_E_REGEX = re.compile(r"(^|[^A-Za-z])[Ee](?P<value>[-+]?[0-9]*\.?[0-9]+)")


def is_extrusion_move(line):
    """Return whether ``line`` is a ``G1`` command carrying an ``E`` parameter.

    This mirrors the check the plugin used to do with
    ``octoprint.util.comm`` and is used to stop scanning a G-code header at
    the first extrusion.
    """
    return bool(_G1_COMMAND_REGEX.search(line) and _FLOAT_E_REGEX.search(line))
