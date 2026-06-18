"""Punto de entrada de la app: ciclo de vida, ícono de barra de menú y cableado.

Conecta el listener global (hotkey) con el panel y el insertador:
  hotkey detecta "//"  ->  se muestra el panel  ->  Enter inserta el snippet.
"""

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
from Foundation import NSObject, NSURL
from PyObjCTools import AppHelper

from . import inserter
from .hotkey import HotkeyListener
from .panel import SnippetController
from .store import SnippetStore

INSERT_DELAY = 0.08  # margen para que el foco vuelva a la app antes de pegar


class AppDelegate(NSObject):
    def applicationDidFinishLaunching_(self, notification):
        self.store = SnippetStore()

        self.controller = (
            SnippetController.alloc().initWithStore_onInsert_onClose_(
                self.store, self._on_insert, self._on_close
            )
        )

        self.hotkey = HotkeyListener(self._on_trigger)
        self.hotkey.start()

        self._paused = False
        self._build_status_item()

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
        # Pequeño retardo para que el foco regrese a la app destino antes de pegar.
        AppHelper.callLater(INSERT_DELAY, inserter.insert_snippet, content)

    # --------------------------------------------------------------- acciones de menú
    def showFromMenu_(self, sender):
        if not self._paused:
            self.hotkey.suspended = True
            self.controller.show()

    def reloadSnippets_(self, sender):
        self.store.reload()

    def openSnippetsFile_(self, sender):
        url = NSURL.fileURLWithPath_(self.store.path)
        NSWorkspace.sharedWorkspace().openURL_(url)

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
