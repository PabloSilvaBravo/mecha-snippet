"""Listener de teclado global. Detecta el disparador "//".

Usa pynput (que por debajo monta un CGEventTap de macOS), por lo que requiere
permiso de Accesibilidad / Monitoreo de entrada. El listener corre en su propio
hilo; cuando detecta el disparador despacha la acción al hilo principal de
AppKit con AppHelper.callAfter (la UI solo se toca desde el main thread).
"""

from pynput import keyboard
from PyObjCTools import AppHelper

TRIGGER = "/"
TRIGGER_COUNT = 2
# No disparar tras estos caracteres, para no activarse dentro de URLs ("http://")
# ni de comentarios "///".
BLOCK_BEFORE = (":", "/")


class HotkeyListener:
    def __init__(self, on_trigger):
        self.on_trigger = on_trigger
        self.enabled = True       # interruptor global (menú Pausar)
        self.suspended = False    # True mientras el panel está visible
        self._recent = []         # últimos caracteres tecleados
        self._listener = None

    def start(self):
        self._listener = keyboard.Listener(on_press=self._on_press)
        self._listener.daemon = True
        self._listener.start()

    def stop(self):
        if self._listener is not None:
            self._listener.stop()
            self._listener = None

    def reset(self):
        self._recent.clear()

    @staticmethod
    def _char_of(key):
        try:
            return key.char
        except AttributeError:
            return None

    def _on_press(self, key):
        if not self.enabled or self.suspended:
            return

        char = self._char_of(key)
        if char is None:
            # Tecla especial (flechas, modificadores, etc.): corta la secuencia.
            self._recent.clear()
            return

        self._recent.append(char)
        if len(self._recent) > 3:
            self._recent.pop(0)

        if (
            len(self._recent) >= TRIGGER_COUNT
            and self._recent[-1] == TRIGGER
            and self._recent[-2] == TRIGGER
        ):
            preceding = self._recent[-3] if len(self._recent) >= 3 else ""
            if preceding in BLOCK_BEFORE:
                return
            self._recent.clear()
            # Saltar al hilo principal para mostrar el panel.
            AppHelper.callAfter(self.on_trigger)
