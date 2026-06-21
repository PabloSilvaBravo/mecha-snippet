"""Inserción del snippet en la app activa.

Antes de tocar nada verifica el permiso de Accesibilidad: si falta, NO borra el
disparador (para no comerse texto del usuario) ni pega. Preserva TODO el
portapapeles del usuario (no solo texto: imágenes, archivos, RTF, etc.), marca
el snippet como efímero para que los gestores de historial no lo capturen, y
restaura en el hilo principal solo si nadie más tocó el portapapeles entremedio.
"""

import sys
import traceback

import Quartz
from AppKit import NSPasteboard, NSPasteboardItem, NSPasteboardTypeString
from ApplicationServices import AXIsProcessTrusted
from PyObjCTools import AppHelper

KEY_DELETE = 51  # tecla Borrar (backspace)
KEY_V = 9        # tecla "v"
RESTORE_DELAY = 0.5  # segundos antes de devolver el portapapeles original

# Tipos que avisan a los gestores de portapapeles (Raycast, Maccy, Paste) que
# este contenido es sensible/transitorio y NO deben guardarlo en su historial.
CONCEALED_TYPE = "org.nspasteboard.ConcealedType"
TRANSIENT_TYPE = "org.nspasteboard.TransientType"


def _post_key(keycode, flags=0):
    source = Quartz.CGEventSourceCreate(Quartz.kCGEventSourceStateHIDSystemState)
    down = Quartz.CGEventCreateKeyboardEvent(source, keycode, True)
    up = Quartz.CGEventCreateKeyboardEvent(source, keycode, False)
    if flags:
        Quartz.CGEventSetFlags(down, flags)
        Quartz.CGEventSetFlags(up, flags)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, down)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, up)


def _snapshot(pasteboard):
    """Copia TODOS los tipos de TODOS los items del portapapeles."""
    snapshot = []
    for item in (pasteboard.pasteboardItems() or []):
        data = {}
        for t in item.types():
            payload = item.dataForType_(t)
            if payload is not None:
                data[t] = payload
        if data:
            snapshot.append(data)
    return snapshot


def _restore(pasteboard, snapshot, expected_change):
    # Si alguien más modificó el portapapeles desde que pegamos, no lo pisamos.
    if pasteboard.changeCount() != expected_change:
        return
    pasteboard.clearContents()
    items = []
    for data in snapshot:
        item = NSPasteboardItem.alloc().init()
        for t, payload in data.items():
            item.setData_forType_(payload, t)
        items.append(item)
    if items:
        pasteboard.writeObjects_(items)


def insert_snippet(content, backspaces=2):
    """Borra el disparador y pega `content` en la app que tenga el foco."""
    try:
        if not AXIsProcessTrusted():
            # Sin Accesibilidad, CGEventPost no tiene efecto. No borramos el
            # disparador ni tocamos el portapapeles, para no dejar texto comido.
            sys.stderr.write(
                "[mecha] Sin permiso de Accesibilidad: no se pega ni se borra el disparador.\n"
            )
            sys.stderr.flush()
            return

        sys.stderr.write(
            "[mecha] insert_snippet: borrando %d, pegando %d chars\n"
            % (backspaces, len(content))
        )
        sys.stderr.flush()

        pasteboard = NSPasteboard.generalPasteboard()
        saved = _snapshot(pasteboard)

        for _ in range(backspaces):
            _post_key(KEY_DELETE)

        # Escribir el snippet marcado como efímero/oculto.
        pasteboard.clearContents()
        item = NSPasteboardItem.alloc().init()
        item.setString_forType_(content, NSPasteboardTypeString)
        item.setString_forType_("", CONCEALED_TYPE)
        item.setString_forType_("", TRANSIENT_TYPE)
        pasteboard.writeObjects_([item])
        our_change = pasteboard.changeCount()

        _post_key(KEY_V, Quartz.kCGEventFlagMaskCommand)

        # Restaurar en el hilo principal y solo si nadie más tocó el portapapeles.
        AppHelper.callLater(RESTORE_DELAY, _restore, pasteboard, saved, our_change)
    except Exception:
        sys.stderr.write("[mecha] ERROR en insert_snippet:\n")
        traceback.print_exc()
        sys.stderr.flush()
