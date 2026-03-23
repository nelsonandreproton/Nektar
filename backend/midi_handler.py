"""MIDI input handler using mido + python-rtmidi."""
import logging
import mido
import threading
import time
from typing import Callable, List, Optional

log = logging.getLogger(__name__)


class MidiHandler:
    def __init__(self):
        self._thread: Optional[threading.Thread] = None
        self._running: bool = False
        self._callback: Optional[Callable] = None
        self._disconnect_cb: Optional[Callable] = None
        self._connected_device: Optional[str] = None

    def get_input_devices(self) -> List[str]:
        try:
            return mido.get_input_names()
        except Exception:
            return []

    def connect(self, device_name: str, callback: Callable,
                disconnect_cb: Optional[Callable] = None) -> bool:
        """Connect to a MIDI input device. Returns True on success.

        disconnect_cb, if provided, is called (with no arguments) when the
        device disconnects unexpectedly.
        """
        self.disconnect()
        try:
            self._callback = callback
            self._disconnect_cb = disconnect_cb
            self._running = True
            self._connected_device = device_name
            self._thread = threading.Thread(
                target=self._listen_loop,
                args=(device_name,),
                daemon=True,
            )
            self._thread.start()
            return True
        except Exception:
            self._running = False
            self._connected_device = None
            return False

    def disconnect(self):
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        self._thread = None
        self._connected_device = None

    def _listen_loop(self, device_name: str):
        try:
            with mido.open_input(device_name) as port:
                while self._running:
                    for msg in port.iter_pending():
                        if self._callback and not msg.is_meta:
                            self._callback(msg)
                    time.sleep(0.001)
        except Exception as exc:
            log.warning("MIDI device '%s' disconnected: %s", device_name, exc)
            self._running = False
            self._connected_device = None
            if self._disconnect_cb:
                try:
                    self._disconnect_cb()
                except Exception:
                    pass

    @property
    def connected_device(self) -> Optional[str]:
        return self._connected_device

    @property
    def is_connected(self) -> bool:
        return self._running and self._thread is not None and self._thread.is_alive()
