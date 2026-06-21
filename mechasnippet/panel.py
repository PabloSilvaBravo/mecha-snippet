"""Panel flotante de búsqueda e inserción de snippets.

Es un NSPanel "no activante": puede recibir el teclado (para escribir en el
buscador) sin robarle la activación a la app de fondo, de modo que al insertar
el texto vuelve solo a su lugar. Se cierra con Esc o al perder el foco
(click fuera). Navegación con ↑ ↓; Enter inserta.

Características:
  - Fondo Liquid Glass (NSGlassEffectView en macOS 26+, con fallback).
  - Ancho adaptativo al texto del snippet más largo visible.
  - Navegación con flechas mediante un monitor de eventos local.
  - Aparece centrado en la pantalla del mouse y se puede arrastrar.
  - Al pasar el mouse (o seleccionar) un atajo, despliega su texto COMPLETO.
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
    NSTextView,
    NSView,
    NSViewHeightSizable,
    NSViewWidthSizable,
    NSWorkspace,
    NSWindowStyleMaskBorderless,
    NSWindowStyleMaskNonactivatingPanel,
)
from Foundation import NSMakeRect, NSMakeSize, NSObject, NSIndexSet

from . import matcher

SEARCH_HEIGHT = 30.0
ROW_HEIGHT = 30.0
MAX_VISIBLE_ROWS = 8
PREVIEW_HEIGHT = 88.0
PADDING = 10.0
CORNER_RADIUS = 22.0
GLASS_ALPHA = 0.85  # <1.0 = más translúcido (1.0 = opaco normal)
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


class _DragView(NSView):
    """Vista de fondo: permite arrastrar la ventana desde su área vacía."""

    def mouseDown_(self, event):
        window = self.window()
        if window is not None:
            window.performWindowDragWithEvent_(event)

    def mouseDownCanMoveWindow(self):
        return True


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
        self._needs_center = True
        self._preview_visible = False
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
        panel.setAlphaValue_(GLASS_ALPHA)  # un toque más translúcido
        panel.setMovableByWindowBackground_(True)
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

        # Lista de resultados
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
        table.setAction_("singleClick:")
        table.setDoubleAction_("doubleClick:")

        column = NSTableColumn.alloc().initWithIdentifier_("snippet")
        column.setWidth_(MIN_WIDTH - PADDING * 2)
        table.addTableColumn_(column)

        scroll.setDocumentView_(table)
        inner.addSubview_(scroll)
        self._scroll = scroll
        self._table = table
        self._column = column

        # Vista previa (texto COMPLETO del atajo bajo el mouse / seleccionado)
        preview_scroll = NSScrollView.alloc().initWithFrame_(
            NSMakeRect(0, 0, MIN_WIDTH, PREVIEW_HEIGHT)
        )
        preview_scroll.setHasVerticalScroller_(True)
        preview_scroll.setAutohidesScrollers_(True)
        preview_scroll.setDrawsBackground_(False)
        preview_scroll.setBorderType_(0)
        preview_scroll.setHidden_(True)

        preview = NSTextView.alloc().initWithFrame_(
            NSMakeRect(0, 0, MIN_WIDTH, PREVIEW_HEIGHT)
        )
        preview.setEditable_(False)
        preview.setSelectable_(True)
        preview.setDrawsBackground_(False)
        preview.setFont_(NSFont.systemFontOfSize_(12))
        preview.setTextContainerInset_(NSMakeSize(2.0, 2.0))
        preview.setHorizontallyResizable_(False)
        preview.setAutoresizingMask_(NSViewWidthSizable)
        preview.textContainer().setWidthTracksTextView_(True)
        preview_scroll.setDocumentView_(preview)
        inner.addSubview_(preview_scroll)
        self._preview = preview
        self._preview_scroll = preview_scroll

        self._panel = panel
        self._background = background
        self._inner = inner

        # Monitor de teclado: flechas, Enter y Esc apenas el panel está abierto.
        self._monitor = NSEvent.addLocalMonitorForEventsMatchingMask_handler_(
            NSEventMaskKeyDown, self._handle_key_event
        )

    @objc.python_method
    def _make_background(self, rect):
        """Devuelve (vista_de_fondo, contenedor_interno arrastrable)."""
        inner = _DragView.alloc().initWithFrame_(rect)
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
        self._prev_app = NSWorkspace.sharedWorkspace().frontmostApplication()
        self.store.reload()
        self._search.setStringValue_("")
        self._needs_center = True  # cada apertura parte centrado en pantalla
        self._preview_visible = False
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
        # La vista previa solo aparece tras un clic o navegación con flechas,
        # no al filtrar; se oculta de nuevo en cada cambio de búsqueda.
        self._preview_visible = False
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
        self._update_preview()

    @objc.python_method
    def _update_preview(self):
        if 0 <= self._selected < len(self._results):
            self._preview.setString_(self._results[self._selected][1])
        else:
            self._preview.setString_("")

    @objc.python_method
    def _row_text(self, name, content):
        preview = " ".join(content.replace("\t", " ").split())
        if len(preview) > PREVIEW_MAX_CHARS:
            preview = preview[:PREVIEW_MAX_CHARS] + "…"
        if preview:
            return "%s     ·     %s" % (name, preview)
        return name

    @objc.python_method
    def _show_preview_for_selection(self):
        """Muestra (o actualiza) la vista previa del atajo seleccionado."""
        if not self._preview_visible:
            self._preview_visible = True
            self._sync_selection()
            self._layout_and_place()
        else:
            self._sync_selection()

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
        self._show_preview_for_selection()

    # ----------------------------------------------------------- delegado NSTextField
    def controlTextDidChange_(self, notification):
        self._apply_filter(self._search.stringValue())
        self._layout_and_place()

    # ----------------------------------------------------------- delegado NSWindow
    def windowDidResignKey_(self, notification):
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

    def singleClick_(self, sender):
        # Un clic en una fila abre/actualiza la vista previa (no el hover).
        row = self._table.clickedRow()
        if row < 0:
            return
        self._selected = row
        self._show_preview_for_selection()

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

        # No reactivamos el hotkey aquí: lo hace la app DESPUÉS de pegar
        # (AppDelegate._on_insert / _rearm_hotkey), para que el Cmd+V sintético
        # no reactive la detección de '//'.
        if self.on_insert:
            self.on_insert(content)
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
        for name, content in self._results[:300]:
            w = self._measure(self._row_text(name, content), self._row_font)
            if w > widest:
                widest = w

        content_width = widest + PADDING * 2 + 28.0  # inset de celda + scroller
        loc = NSEvent.mouseLocation()
        screen_width = self._screen_containing(loc.x, loc.y).visibleFrame().size.width
        max_width = min(MAX_WIDTH, screen_width * 0.7)
        return max(MIN_WIDTH, min(max_width, content_width))

    @objc.python_method
    def _layout_and_place(self):
        width = self._compute_width()
        has_results = bool(self._results)
        rows = max(1, min(MAX_VISIBLE_ROWS, len(self._results))) if has_results else 0
        list_height = rows * ROW_HEIGHT if has_results else 0.0
        preview_height = PREVIEW_HEIGHT if (has_results and self._preview_visible) else 0.0

        total = SEARCH_HEIGHT + PADDING * 2
        if has_results:
            total += PADDING + list_height
        if preview_height:
            total += PADDING + preview_height

        if self._needs_center:
            loc = NSEvent.mouseLocation()
            visible = self._screen_containing(loc.x, loc.y).visibleFrame()
            x = visible.origin.x + (visible.size.width - width) / 2.0
            top = visible.origin.y + (visible.size.height + total) / 2.0
            self._needs_center = False
        else:
            frame = self._panel.frame()
            x = frame.origin.x
            top = frame.origin.y + frame.size.height

        x, top = self._clamp_to_screen(x, top, width, total)
        self._panel.setFrame_display_(NSMakeRect(x, top - total, width, total), True)

        self._background.setFrame_(NSMakeRect(0, 0, width, total))
        self._inner.setFrame_(NSMakeRect(0, 0, width, total))
        self._search.setFrame_(
            NSMakeRect(PADDING, total - PADDING - SEARCH_HEIGHT, width - PADDING * 2, SEARCH_HEIGHT)
        )

        inner_w = width - PADDING * 2
        y = PADDING
        if preview_height:
            self._preview_scroll.setHidden_(False)
            self._preview_scroll.setFrame_(NSMakeRect(PADDING, y, inner_w, preview_height))
            y += preview_height + PADDING
        else:
            self._preview_scroll.setHidden_(True)

        if has_results:
            self._scroll.setHidden_(False)
            self._scroll.setFrame_(NSMakeRect(PADDING, y, inner_w, list_height))
        else:
            self._scroll.setHidden_(True)

        self._column.setWidth_(inner_w)

    @staticmethod
    def _screen_containing(x, y):
        screens = NSScreen.screens()
        for s in screens:
            f = s.frame()
            if (f.origin.x <= x < f.origin.x + f.size.width and
                    f.origin.y <= y < f.origin.y + f.size.height):
                return s
        return NSScreen.mainScreen() or screens[0]

    @staticmethod
    def _clamp_to_screen(x, top_y, width, height):
        visible = SnippetController._screen_containing(x, top_y).visibleFrame()
        min_x = visible.origin.x
        max_x = visible.origin.x + visible.size.width - width
        min_top = visible.origin.y + height
        max_top = visible.origin.y + visible.size.height

        x = max(min_x, min(max_x, x))
        top_y = max(min_top, min(max_top, top_y))
        return (x, top_y)
