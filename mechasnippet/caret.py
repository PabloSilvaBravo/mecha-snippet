"""Posición donde mostrar el panel flotante.

Intenta ubicar el cursor de texto (caret) vía la API de Accesibilidad. Si la
app activa no expone esa información (muchas no lo hacen), cae al puntero del
mouse, que siempre está disponible.

Todas las coordenadas que devuelve están en el sistema de AppKit (origen abajo
a la izquierda) y representan la esquina SUPERIOR IZQUIERDA donde debe quedar el
panel.
"""

from AppKit import NSEvent, NSScreen


def panel_top_left():
    """(x, y) en coordenadas AppKit para la esquina superior izquierda del panel."""
    point = _caret_via_accessibility()
    if point is not None:
        return point
    return _mouse_point()


def _mouse_point():
    loc = NSEvent.mouseLocation()  # ya viene en coords AppKit (abajo-izquierda)
    return (float(loc.x), float(loc.y))


def _caret_via_accessibility():
    """Devuelve la esquina inferior del caret, o None si no se puede obtener.

    Todo el bloque está protegido: si cualquier símbolo de Accessibility falta o
    la app no responde, devolvemos None y el llamador usa el mouse.
    """
    try:
        from ApplicationServices import (
            AXUIElementCreateSystemWide,
            AXUIElementCopyAttributeValue,
            AXUIElementCopyParameterizedAttributeValue,
            AXValueGetValue,
            kAXFocusedUIElementAttribute,
            kAXSelectedTextRangeAttribute,
            kAXBoundsForRangeParameterizedAttribute,
        )
    except Exception:
        return None

    try:
        import Quartz

        rect_type = (
            getattr(Quartz, "kAXValueTypeCGRect", None)
            or getattr(Quartz, "kAXValueCGRectType", None)
            or 3  # valor histórico de kAXValueCGRectType
        )

        system = AXUIElementCreateSystemWide()

        err, focused = AXUIElementCopyAttributeValue(
            system, kAXFocusedUIElementAttribute, None
        )
        if err != 0 or focused is None:
            return None

        err, text_range = AXUIElementCopyAttributeValue(
            focused, kAXSelectedTextRangeAttribute, None
        )
        if err != 0 or text_range is None:
            return None

        err, bounds_value = AXUIElementCopyParameterizedAttributeValue(
            focused, kAXBoundsForRangeParameterizedAttribute, text_range, None
        )
        if err != 0 or bounds_value is None:
            return None

        ok, rect = AXValueGetValue(bounds_value, rect_type, None)
        if not ok or rect is None:
            return None

        # AX entrega coords con origen arriba a la izquierda; convertimos a AppKit.
        screen_height = NSScreen.screens()[0].frame().size.height
        x = float(rect.origin.x)
        y_top = float(rect.origin.y)
        height = float(rect.size.height)
        appkit_y = screen_height - (y_top + height) - 4.0
        return (x, appkit_y)
    except Exception:
        return None
