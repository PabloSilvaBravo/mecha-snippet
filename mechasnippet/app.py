"""Punto de entrada de la app: ciclo de vida, ícono de barra de menú y cableado.

Conecta el listener global (hotkey) con el panel y el insertador:
  hotkey detecta "//"  ->  se muestra el panel  ->  Enter inserta el snippet.
"""

import subprocess
import sys

import objc
from AppKit import (
    NSApplication,
    NSApplicationActivationPolicyAccessory,
    NSImage,
    NSMenu,
    NSMenuItem,
    NSStatusBar,
    NSVariableStatusItemLength,
    NSWorkspace,
)
from Foundation import NSObject
from PyObjCTools import AppHelper

from . import inserter
from .hotkey import HotkeyListener
from .panel import SnippetController
from .store import SnippetStore

INSERT_DELAY = 0.15  # margen para que el foco vuelva a la app antes de pegar


class AppDelegate(NSObject):
    def applicationDidFinishLaunching_(self, notification):
        self.store = SnippetStore()
        self._prompt_accessibility()

        self.controller = (
            SnippetController.alloc().initWithStore_onInsert_onClose_(
                self.store, self._on_insert, self._on_close
            )
        )

        self.hotkey = HotkeyListener(self._on_trigger)
        self.hotkey.start()

        self._paused = False
        self._build_status_item()

    @objc.python_method
    def _prompt_accessibility(self):
        """Pide Accesibilidad (necesaria para ENVIAR el Cmd+V al pegar).

        Distinta del Monitoreo de entrada (que solo permite ESCUCHAR el "//").
        Mostrar el diálogo agrega el binario a la lista correcta de Accesibilidad.
        """
        try:
            import ApplicationServices as AX

            prompt_key = getattr(AX, "kAXTrustedCheckOptionPrompt", None)
            if prompt_key is not None:
                trusted = AX.AXIsProcessTrustedWithOptions({prompt_key: True})
            else:
                trusted = AX.AXIsProcessTrusted()
            sys.stderr.write("[mecha] Accesibilidad concedida: %s\n" % bool(trusted))
            sys.stderr.flush()
        except Exception:
            import traceback

            traceback.print_exc()

    # ------------------------------------------------------------- barra de menú
    @objc.python_method
    def _build_status_item(self):
        bar = NSStatusBar.systemStatusBar()
        self.status_item = bar.statusItemWithLength_(NSVariableStatusItemLength)
        button = self.status_item.button()

        image = NSImage.imageWithSystemSymbolName_accessibilityDescription_(
            "scissors", "Mecha Snippet"
        )
        if image is not None:
            image.setTemplate_(True)
            button.setImage_(image)
        else:
            button.setTitle_("MS")

        menu = NSMenu.alloc().init()
        menu.addItem_(self._item("Buscar snippet  (//)", "showFromMenu:"))
        menu.addItem_(NSMenuItem.separatorItem())
        menu.addItem_(self._item("Recargar snippets", "reloadSnippets:"))
        menu.addItem_(self._item("Abrir snippets.json", "openSnippetsFile:"))
        self._pause_item = self._item("Pausar detección", "togglePause:")
        menu.addItem_(self._pause_item)
        menu.addItem_(NSMenuItem.separatorItem())
        menu.addItem_(self._item("Salir de Mecha Snippet", "quit:"))
        self.status_item.setMenu_(menu)

    @objc.python_method
    def _item(self, title, action):
        item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(title, action, "")
        item.setTarget_(self)
        return item

    # --------------------------------------------------------------- callbacks panel
    @objc.python_method
    def _on_trigger(self):
        if self._paused:
            return
        self.hotkey.suspended = True
        self.controller.show()

    @objc.python_method
    def _on_close(self):
        self.hotkey.reset()
        self.hotkey.suspended = False

    @objc.python_method
    def _on_insert(self, content):
        # Pega tras un pequeño retardo (para que vuelva el foco) y RECIÉN AHÍ
        # reactiva el listener, para que el Cmd+V sintético no reactive la
        # detección de '//' ni se coma el próximo disparador.
        def do_insert():
            inserter.insert_snippet(content)
            AppHelper.callLater(0.1, self._rearm_hotkey)

        AppHelper.callLater(INSERT_DELAY, do_insert)

    @objc.python_method
    def _rearm_hotkey(self):
        self.hotkey.reset()
        self.hotkey.suspended = False

    # --------------------------------------------------------------- acciones de menú
    def showFromMenu_(self, sender):
        if not self._paused:
            self.hotkey.suspended = True
            self.controller.show()

    def reloadSnippets_(self, sender):
        self.store.reload()

    def openSnippetsFile_(self, sender):
        # Abrir explícitamente con TextEdit. Si usáramos la app por defecto del
        # sistema para .json, en algunos Mac es Xcode (y abre su instalador).
        subprocess.Popen(["/usr/bin/open", "-a", "TextEdit", self.store.path])

    def togglePause_(self, sender):
        self._paused = not self._paused
        self.hotkey.enabled = not self._paused
        self._pause_item.setTitle_(
            "Reanudar detección" if self._paused else "Pausar detección"
        )

    def quit_(self, sender):
        self.hotkey.stop()
        NSApplication.sharedApplication().terminate_(None)


_delegate = None  # referencia global para que el GC no recolecte el delegate


def main():
    global _delegate
    app = NSApplication.sharedApplication()
    app.setActivationPolicy_(NSApplicationActivationPolicyAccessory)
    _delegate = AppDelegate.alloc().init()
    app.setDelegate_(_delegate)
    AppHelper.runEventLoop()


if __name__ == "__main__":
    main()
