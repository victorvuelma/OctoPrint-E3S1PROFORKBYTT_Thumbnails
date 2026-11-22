# coding=utf-8
"""File selection and transfer lifecycle event handler."""

import posixpath

from ..events.types import Event, EventType
from .base import EventHandler


class FileSelectionEventHandler(EventHandler):
    """Handle selected-file helper generation and cleanup lifecycle."""

    event_types = [
        EventType.FILE_SELECTED,
        EventType.TRANSFER_DONE,
    ]

    def __init__(self, plugin):
        self._plugin = plugin
        super().__init__()

    def _is_helper_transfer(self, payload):
        """Return whether a TransferDone payload belongs to the helper file.

        OctoPrint 1.x reports the name passed to ``add_sd_file`` as ``local``.
        OctoPrint 2.x reports the remote path (which may carry a leading
        ``/`` and be lower case) as both ``local`` and ``remote``, and plans to
        drop ``local`` in 3.0.0. Compare base names so all of these match.
        """
        helper = self._plugin._helper_basename.upper()
        for key in ("local", "remote"):
            name = payload.get(key) or ""
            if posixpath.basename(name).upper() == helper:
                return True
        return False

    def handle(self, event: Event):
        payload = event.payload

        if event.type == EventType.TRANSFER_DONE:
            if self._is_helper_transfer(payload):
                self._plugin._logger.debug(
                    f"Dispatching TransferDone for helper local={payload.get('local')}"
                )
                self._plugin._workflow.handle_helper_transfer_done(payload)
            else:
                self._plugin._logger.debug(
                    f"Ignoring TransferDone for non-helper local={payload.get('local')}"
                )
            return

        storage = payload.get("storage")
        if storage not in (None, "local") or not payload.get("name"):
            self._plugin._logger.debug(
                f"Ignoring FileSelected due to payload: storage={storage!r} "
                f"name={payload.get('name')!r} path={payload.get('path')!r}"
            )
            return
        if payload.get("name", "").upper() == self._plugin._helper_basename:
            self._plugin._logger.debug(
                f"Ignoring FileSelected for helper {payload.get('name')}"
            )
            return
        self._plugin._logger.debug(
            f"Dispatching FileSelected to workflow for {payload.get('name')} "
            f"(path={payload.get('path')})"
        )
        self._plugin._workflow.handle_file_selected(payload)
