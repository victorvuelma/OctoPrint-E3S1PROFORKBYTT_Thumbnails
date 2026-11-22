import os
import tempfile
import unittest
import warnings
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock

try:
    from octoprint_e3s1proforkbyttthumbnails.events.types import Event, EventType
    from octoprint_e3s1proforkbyttthumbnails.handlers.file_selection_event_handler import (
        FileSelectionEventHandler,
    )
    from octoprint_e3s1proforkbyttthumbnails.services.printer_sync_service import (
        PrinterSyncService,
    )

    IMPORT_ERROR = None
except Exception as exc:  # pragma: no cover - environment dependent
    IMPORT_ERROR = exc

HELPER = "OCTODGUS.GCO"
TAGS = {"source:plugin"}


class _FileManager:
    """Minimal stand-in that maps between disk paths and local storage paths."""

    def __init__(self, basefolder):
        self.basefolder = basefolder

    def path_in_storage(self, location, path):
        assert location == "local"
        return os.path.relpath(path, self.basefolder).replace(os.sep, "/")

    def path_on_disk(self, location, path):
        assert location == "local"
        return os.path.join(self.basefolder, *path.split("/"))


@unittest.skipIf(IMPORT_ERROR is not None, f"plugin import failed: {IMPORT_ERROR}")
class StartHelperTransferTests(unittest.TestCase):
    def setUp(self):
        self.basefolder = tempfile.mkdtemp()
        self.sidecar = os.path.join(self.basefolder, "sub", "benchy.gcode.thumb")
        self.file_manager = _FileManager(self.basefolder)

    def test_octoprint_1_argument_order(self):
        printer = Mock(spec=["add_sd_file"])  # no is_storage_mounted -> 1.x
        service = PrinterSyncService(Mock(), printer, self.file_manager)

        service._start_helper_transfer(self.sidecar, HELPER, TAGS)

        printer.add_sd_file.assert_called_once_with(HELPER, self.sidecar, tags=TAGS)

    def test_octoprint_2_argument_order(self):
        printer = Mock(spec=["add_sd_file", "is_storage_mounted"])
        service = PrinterSyncService(Mock(), printer, self.file_manager)

        service._start_helper_transfer(self.sidecar, HELPER, TAGS)

        printer.add_sd_file.assert_called_once_with(
            "sub/benchy.gcode.thumb", HELPER, tags=TAGS
        )

    def test_octoprint_2_real_add_sd_file_streams_sidecar_as_helper(self):
        """Run OctoPrint 2.x's own Printer.add_sd_file and check what it streams."""
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", DeprecationWarning)
                import octoprint.filemanager  # noqa: F401  (avoids a circular import)
                from octoprint.printer.standard import Printer
        except Exception:
            self.skipTest("OctoPrint is not installed")
        if not hasattr(Printer, "is_storage_mounted"):
            self.skipTest("installed OctoPrint is older than 2.0")

        printer = MagicMock()
        printer.is_storage_mounted.return_value = True
        printer._connection.is_ready.return_value = True
        printer._connection.current_storage_capabilities.write_file = True
        printer.sd_card_upload_hooks = {}
        printer._file_manager = self.file_manager
        printer.add_sd_file = lambda *args, **kwargs: Printer.add_sd_file(
            printer, *args, **kwargs
        )

        service = PrinterSyncService(Mock(), printer, self.file_manager)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            service._start_helper_transfer(self.sidecar, HELPER, TAGS)

        source, target = printer._connection.upload_printer_file.call_args.args
        self.assertEqual(source, self.sidecar)
        self.assertEqual(target, HELPER)


@unittest.skipIf(IMPORT_ERROR is not None, f"plugin import failed: {IMPORT_ERROR}")
class HelperTransferDoneDetectionTests(unittest.TestCase):
    def _handler(self):
        plugin = SimpleNamespace(
            _helper_basename=HELPER, _logger=Mock(), _workflow=Mock()
        )
        return FileSelectionEventHandler(plugin), plugin

    def _dispatch(self, payload):
        handler, plugin = self._handler()
        handler.handle(Event(EventType.TRANSFER_DONE, payload))
        return plugin._workflow.handle_helper_transfer_done.called

    def test_octoprint_1_payload(self):
        self.assertTrue(self._dispatch({"local": HELPER, "remote": "/octodgus.gco"}))

    def test_octoprint_2_payload(self):
        self.assertTrue(
            self._dispatch({"local": "/octodgus.gco", "remote": "/octodgus.gco"})
        )

    def test_payload_without_local(self):
        self.assertTrue(self._dispatch({"remote": "OCTODGUS.GCO"}))

    def test_other_file_is_ignored(self):
        self.assertFalse(
            self._dispatch({"local": "benchy.gco", "remote": "/benchy.gco"})
        )


if __name__ == "__main__":
    unittest.main()
