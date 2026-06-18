"""Panel flotante de búsqueda e inserción de snippets.

Es un NSPanel "no activante": puede recibir el teclado (para escribir en el
buscador) sin robarle la activación a la app de fondo, de modo que al insertar
el texto vuelve solo a su lugar. Se cierra con Esc o al perder el foco
(click fuera). Navegación con ↑ ↓; Enter inserta.

Características:
  - Fondo Liquid Glass (NSGlassEffectView en macOS 26+, con fallback).
  - Ancho adaptativo al texto del snippet más largo visible.
  - Navegación con flechas mediante un monitor de eventos local, que funciona
    apenas el panel se abre (sin depender del campo de texto).
"""

import objc
from AppKit import (
    NSApplicationActivateIgnoringOtherApps,
    NSAttributedString,
    NSBackingStoreBuffered,
    NSColor,
    NSEvent,
    NSEventMaskKeyDown,
    NSFont,
    NSFontAttributeName,
    NSFloatingWindowLevel,
    NSPanel,
    NSScreen,
    NSScrollView,
    NSTableColumn,
    NSTableView,
    NSTableViewSelectionHighlightStyleRegular,
    NSTextField,
    NSView,
    NSViewHeightSizable,
    NSViewWidthSizable,
    NSWorkspace,
    NSWindowStyleMaskBorderless,
    NSWindowStyleMaskNonactivatingPanel,
)
from Foundation import NSMakeRect, NSObject, NSIndexSet

from . import matcher

SEARCH_HEIGHT = 30.0
ROW_HEIGHT = 30.0
MAX_VISIBLE_ROWS = 8
PADDING = 10.0
CORNER_RADIUS = 14.0
MIN_WIDTH = 300.0
MAX_WIDTH = 760.0
PREVIEW_MAX_CHARS = 140

# keycodes de macOS
KEY_DOWN = 125
KEY_UP = 126
KEY_RETURN = 36
KEY_ENTER = 76
KEY_ESC = 53


class _KeyablePanel(NSPanel):
    """NSPanel que sí puede convertirse en ventana clave estando sin borde."""

    def canBecomeKeyWindow(self):
        return True

    def canBecomeMainWindow(self):
        return False


class SnippetController(NSObject):
    """Dueño del panel. Maneja búsqueda, navegación, selección e inserción."""

    def initWithStore_onInsert_onClose_(self, store, on_insert, on_close):
        self = objc.super(SnippetController, self).init()
        if self is None:
            return None
        self.store = store
        self.on_insert = on_insert
        self.on_close = on_close
        self._results = []
        self._selected = 0
        self._open = False
        self._closing = False
        self._prev_app = None
        self._anchor = (0.0, 0.0)
        self._row_font = NSFont.systemFontOfSize_(13)
        self._search_font = NSFont.systemFontOfSize_(15)
        self._build_panel()
        return self

    # ----------------------------------------------------------------- construcción
    @objc.python_method
    def _build_panel(self):
        style = NSWindowStyleMaskBorderless | NSWindowStyleMaskNonactivatingPanel
        rect = NSMakeRect(0, 0, MIN_WIDTH, SEARCH_HEIGHT + PADDING * 2)
        panel = _KeyablePanel.alloc().initWithContentRect_styleMask_backing_defer_(
            rect, style, NSBackingStoreBuffered, False
        )
        panel.setLevel_(NSFloatingWindowLevel)
        panel.setFloatingPanel_(True)
        panel.setOpaque_(False)
        panel.setBackgroundColor_(NSColor.clearColor())
        panel.setHasShadow_(True)
        panel.setDelegate_(self)

        background, inner = self._make_background(rect)
        panel.setContentView_(background)

        # Campo de búsqueda
        search = NSTextField.alloc().initWithFrame_(
            NSMakeRect(PADDING, PADDING, MIN_WIDTH - PADDING * 2, SEARCH_HEIGHT)
        )
        search.setFont_(self._search_font)
        search.setBezeled_(False)
        search.setDrawsBackground_(False)
        search.setFocusRingType_(1)  # NSFocusRingTypeNone
        search.setPlaceholderString_("Buscar snippet…")
        search.setDelegate_(self)
        inner.addSubview_(search)
        self._search = search

        # Lista de resultados (NSTableView dentro de un NSScrollView)
        scroll = NSScrollView.alloc().initWithFrame_(NSMakeRect(0, 0, MIN_WIDTH, 0))
        scroll.setHasVerticalScroller_(True)
        scroll.setAutohidesScrollers_(True)
        scroll.setDrawsBackground_(False)
        scroll.setBorderType_(0)  # NSNoBorder

        table = NSTableView.alloc().initWithFrame_(NSMakeRect(0, 0, MIN_WIDTH, 0))
        table.setRowHeight_(ROW_HEIGHT)
        table.setHeaderView_(None)
        table.setBackgroundColor_(NSColor.clearColor())
        table.setSelectionHighlightStyle_(NSTableViewSelectionHighlightStyleRegular)
        table.setAllowsEmptySelection_(True)
        table.setAllowsMultipleSelection_(False)
        table.setIntercellSpacing_((0.0, 2.0))
        table.setDataSource_(self)
        table.setDelegate_(self)
        table.setTarget_(self)
        table.setDoubleAction_("doubleClick:")

        column = NSTableColumn.alloc().initWithIdentifier_("snippet")
        column.setWidth_(MIN_WIDTH - PADDING * 2)
        table.addTableColumn_(column)

        scroll.setDocumentView_(table)
        inner.addSubview_(scroll)
        self._scroll = scroll
        self._table = table
        self._column = column

        self._panel = panel
        self._background = background
        self._inner = inner

        # Monitor de teclado: maneja flechas, Enter y Esc apenas el panel está
        # abierto, sin depender de que el campo de texto los reenvíe.
        self._monitor = NSEvent.addLocalMonitorForEventsMatchingMask_handler_(
            NSEventMaskKeyDown, self._handle_key_event
        )

    @objc.python_method
    def _make_background(self, rect):
        """Devuelve (vista_de_fondo, contenedor_interno).

        Usa Liquid Glass (NSGlassEffectView) si está disponible; si no, cae a
        NSVisualEffectView y, en último caso, a una vista con color sólido.
        """
        inner = NSView.alloc().initWithFrame_(rect)
        inner.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)

        appkit = __import__("AppKit")

        glass_cls = getattr(appkit, "NSGlassEffectView", None)
        if glass_cls is not None:
            try:
                glass = glass_cls.alloc().initWithFrame_(rect)
                glass.setCornerRadius_(CORNER_RADIUS)
                glass.setContentView_(inner)
                return glass, inner
            except Exception:
                pass

        try:
            from AppKit import (
                NSVisualEffectView,
                NSVisualEffectBlendingModeBehindWindow,
                NSVisualEffectStateActive,
            )

            effect = NSVisualEffectView.alloc().initWithFrame_(rect)
            material = (
                getattr(appkit, "NSVisualEffectMaterialPopover", None)
                or getattr(appkit, "NSVisualEffectMaterialMenu", None)
            )
            if material is not None:
                effect.setMaterial_(material)
            effect.setBlendingMode_(NSVisualEffectBlendingModeBehindWindow)
            effect.setState_(NSVisualEffectStateActive)
            effect.setWantsLayer_(True)
            effect.layer().setCornerRadius_(CORNER_RADIUS)
            effect.layer().setMasksToBounds_(True)
            inner.setFrame_(rect)
            effect.addSubview_(inner)
            return effect, inner
        except Exception:
            pass

        plain = NSView.alloc().initWithFrame_(rect)
        plain.setWantsLayer_(True)
        plain.layer().setBackgroundColor_(NSColor.windowBackgroundColor().CGColor())
        plain.layer().setCornerRadius_(CORNER_RADIUS)
        plain.layer().setMasksToBounds_(True)
        inner.setFrame_(rect)
        plain.addSubview_(inner)
        return plain, inner

    # ------------------------------------------------------------------- mostrar/ocultar
    @objc.python_method
    def show(self):
        from .caret import panel_top_left

        self._prev_app = NSWorkspace.sharedWorkspace().frontmostApplication()
        self.store.reload()
        self._search.setStringValue_("")
        self._anchor = panel_top_left()
        self._open = True
        self._closing = False
        self._apply_filter("")
        self._layout_and_place()
        self._panel.makeKeyAndOrderFront_(None)
        self._panel.makeFirstResponder_(self._search)

    @objc.python_method
    def hide(self):
        if not self._open:
            return
        self._open = False
        self._panel.orderOut_(None)
        if self.on_close:
            self.on_close()

    # --------------------------------------------------------------------- filtro/datos
    @objc.python_method
    def _apply_filter(self, query):
        self._results = matcher.filter_snippets(self.store.items, query)
        self._selected = 0 if self._results else -1
        self._table.reloadData()
        self._sync_selection()

    @objc.python_method
    def _sync_selection(self):
        if 0 <= self._selected < len(self._results):
            index = NSIndexSet.indexSetWithIndex_(self._selected)
            self._table.selectRowIndexes_byExtendingSelection_(index, False)
            self._table.scrollRowToVisible_(self._selected)
        else:
            self._table.deselectAll_(None)

    @objc.python_method
    def _row_text(self, name, content):
        preview = " ".join(content.replace("\t", " ").split())
        if len(preview) > PREVIEW_MAX_CHARS:
            preview = preview[:PREVIEW_MAX_CHARS] + "…"
        if preview:
            return "%s     ·     %s" % (name, preview)
        return name

    # ----------------------------------------------------------- monitor de teclado
    @objc.python_method
    def _handle_key_event(self, event):
        if not self._open:
            return event
        code = event.keyCode()
        if code == KEY_DOWN:
            self._move(1)
            return None
        if code == KEY_UP:
            self._move(-1)
            return None
        if code in (KEY_RETURN, KEY_ENTER):
            self._insert_selected()
            return None
        if code == KEY_ESC:
            self.hide()
            return None
        return event

    @objc.python_method
    def _move(self, delta):
        if not self._results:
            return
        self._selected = max(0, min(len(self._results) - 1, self._selected + delta))
        self._sync_selection()

    # ----------------------------------------------------------- delegado NSTextField
    def controlTextDidChange_(self, notification):
        self._apply_filter(self._search.stringValue())
        self._layout_and_place()

    # ----------------------------------------------------------- delegado NSWindow
    def windowDidResignKey_(self, notification):
        # Click fuera del panel: cerrar (salvo que ya estemos insertando).
        if self._open and not self._closing:
            self.hide()

    # --------------------------------------------------------- data source NSTableView
    def numberOfRowsInTableView_(self, tableView):
        return len(self._results)

    def tableView_viewForTableColumn_row_(self, tableView, column, row):
        identifier = "cell"
        field = tableView.makeViewWithIdentifier_owner_(identifier, self)
        if field is None:
            field = NSTextField.alloc().initWithFrame_(
                NSMakeRect(0, 0, MIN_WIDTH, ROW_HEIGHT)
            )
            field.setIdentifier_(identifier)
            field.setBezeled_(False)
            field.setDrawsBackground_(False)
            field.setEditable_(False)
            field.setSelectable_(False)
            field.setFont_(self._row_font)
            field.setLineBreakMode_(5)  # NSLineBreakByTruncatingTail

        name, content = self._results[row]
        field.setStringValue_(self._row_text(name, content))
        return field

    def tableViewSelectionDidChange_(self, notification):
        selected = self._table.selectedRow()
        if selected >= 0:
            self._selected = selected

    def doubleClick_(self, sender):
        clicked = self._table.clickedRow()
        if clicked >= 0:
            self._selected = clicked
        self._insert_selected()

    # ----------------------------------------------------------------- inserción
    @objc.python_method
    def _insert_selected(self):
        if not (0 <= self._selected < len(self._results)):
            self.hide()
            return
        _name, content = self._results[self._selected]

        self._closing = True
        self._open = False
        self._panel.orderOut_(None)
        if self._prev_app is not None:
            self._prev_app.activateWithOptions_(NSApplicationActivateIgnoringOtherApps)

        if self.on_insert:
            self.on_insert(content)
        if self.on_close:
            self.on_close()
        self._closing = False

    # ------------------------------------------------------------------- layout
    @objc.python_method
    def _measure(self, text, font):
        if not text:
            text = " "
        attributed = NSAttributedString.alloc().initWithString_attributes_(
            text, {NSFontAttributeName: font}
        )
        return float(attributed.size().width)

    @objc.python_method
    def _compute_width(self):
        widest = self._measure(
            self._search.stringValue() or "Buscar snippet…", self._search_font
        )
        # Medimos hasta 300 filas para no penalizar catálogos enormes.
        for name, content in self._results[:300]:
            w = self._measure(self._row_text(name, content), self._row_font)
            if w > widest:
                widest = w

        content_width = widest + PADDING * 2 + 28.0  # inset de celda + scroller
        screen_width = NSScreen.screens()[0].visibleFrame().size.width
        max_width = min(MAX_WIDTH, screen_width * 0.7)
        return max(MIN_WIDTH, min(max_width, content_width))

    @objc.python_method
    def _layout_and_place(self):
        width = self._compute_width()
        rows = max(1, min(MAX_VISIBLE_ROWS, len(self._results)))
        list_height = rows * ROW_HEIGHT if self._results else 0.0
        total = SEARCH_HEIGHT + PADDING * 2 + list_height
        if self._results:
            total += PADDING  # respiro entre buscador y lista

        x, top = self._clamp_to_screen(self._anchor[0], self._anchor[1], width, total)
        self._panel.setFrame_display_(NSMakeRect(x, top - total, width, total), True)

        self._background.setFrame_(NSMakeRect(0, 0, width, total))
        self._inner.setFrame_(NSMakeRect(0, 0, width, total))
        self._search.setFrame_(
            NSMakeRect(PADDING, total - PADDING - SEARCH_HEIGHT, width - PADDING * 2, SEARCH_HEIGHT)
        )
        self._scroll.setFrame_(
            NSMakeRect(PADDING, PADDING if self._results else 0, width - PADDING * 2, list_height)
        )
        self._column.setWidth_(width - PADDING * 2)

    @staticmethod
    def _clamp_to_screen(x, top_y, width, height):
        visible = NSScreen.screens()[0].visibleFrame()
        min_x = visible.origin.x
        max_x = visible.origin.x + visible.size.width - width
        min_top = visible.origin.y + height
        max_top = visible.origin.y + visible.size.height

        x = max(min_x, min(max_x, x))
        top_y = max(min_top, min(max_top, top_y))
        return (x, top_y)
