"""Inserción del snippet en la app activa.

Estrategia:
  1. Guardar el contenido actual del portapapeles.
  2. Borrar el disparador "//" con backspaces sintéticos.
  3. Poner el snippet en el portapapeles y pegar con Cmd+V (confiable para texto
     multilínea, a diferencia de teclear carácter por carácter).
  4. Restaurar el portapapeles del usuario tras un breve retardo.

Enviar eventos de teclado requiere permiso de Accesibilidad (el mismo del
listener global).
"""

import sys
import threading
import traceback

import Quartz
from AppKit import NSPasteboard, NSPasteboardTypeString

KEY_DELETE = 51  # tecla Borrar (backspace)
KEY_V = 9        # tecla "v"
RESTORE_DELAY = 0.4  # segundos antes de devolver el portapapeles original


def _post_key(keycode, flags=0):
    source = Quartz.CGEventSourceCreate(Quartz.kCGEventSourceStateHIDSystemState)
    down = Quartz.CGEventCreateKeyboardEvent(source, keycode, True)
    up = Quartz.CGEventCreateKeyboardEvent(source, keycode, False)
    if flags:
        Quartz.CGEventSetFlags(down, flags)
        Quartz.CGEventSetFlags(up, flags)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, down)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, up)


def insert_snippet(content, backspaces=2):
    """Borra el disparador y pega `content` en la app que tenga el foco."""
    try:
        sys.stderr.write(
            "[mecha] insert_snippet: borrando %d, pegando %d chars\n"
            % (backspaces, len(content))
        )
        sys.stderr.flush()

        pasteboard = NSPasteboard.generalPasteboard()
        previous = pasteboard.stringForType_(NSPasteboardTypeString)

        for _ in range(backspaces):
            _post_key(KEY_DELETE)

        pasteboard.clearContents()
        pasteboard.setString_forType_(content, NSPasteboardTypeString)

        _post_key(KEY_V, Quartz.kCGEventFlagMaskCommand)

        _schedule_restore(previous)
    except Exception:
        sys.stderr.write("[mecha] ERROR en insert_snippet:\n")
        traceback.print_exc()
        sys.stderr.flush()


def _schedule_restore(previous):
    def restore():
        board = NSPasteboard.generalPasteboard()
        board.clearContents()
        if previous is not None:
            board.setString_forType_(previous, NSPasteboardTypeString)

    timer = threading.Timer(RESTORE_DELAY, restore)
    timer.daemon = True
    timer.start()
