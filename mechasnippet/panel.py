"""Panel flotante de búsqueda e inserción de snippets.

Es un NSPanel "no activante": puede recibir el teclado (para escribir en el
buscador) sin robarle la activación a la app de fondo, de modo que al insertar
el texto vuelve solo a su lugar. Se cierra con Esc o al perder el foco
(click fuera). Navegación con ↑ ↓; Enter inserta.
"""

import objc
from AppKit import (
    NSBackingStoreBuffered,
    NSColor,
    NSFont,
    NSFloatingWindowLevel,
    NSPanel,
    NSScrollView,
    NSTableColumn,
    NSTableView,
    NSTableViewSelectionHighlightStyleRegular,
    NSTextField,
    NSView,
    NSWorkspace,
    NSApplicationActivateIgnoringOtherApps,
    NSWindowStyleMaskBorderless,
    NSWindowStyleMaskNonactivatingPanel,
)
from Foundation import NSMakeRect, NSObject, NSIndexSet

from . import matcher

WIDTH = 460.0
SEARCH_HEIGHT = 30.0
ROW_HEIGHT = 28.0
MAX_VISIBLE_ROWS = 8
PADDING = 10.0
CORNER_RADIUS = 12.0


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
        self._build_panel()
        return self

    # ----------------------------------------------------------------- construcción
    @objc.python_method
    def _build_panel(self):
        style = NSWindowStyleMaskBorderless | NSWindowStyleMaskNonactivatingPanel
        rect = NSMakeRect(0, 0, WIDTH, SEARCH_HEIGHT + PADDING * 2)
        panel = _KeyablePanel.alloc().initWithContentRect_styleMask_backing_defer_(
            rect, style, NSBackingStoreBuffered, False
        )
        panel.setLevel_(NSFloatingWindowLevel)
        panel.setFloatingPanel_(True)
        panel.setOpaque_(False)
        panel.setBackgroundColor_(NSColor.clearColor())
        panel.setHasShadow_(True)
        panel.setDelegate_(self)

        container = self._make_background(rect)
        panel.setContentView_(container)

        # Campo de búsqueda
        search = NSTextField.alloc().initWithFrame_(
            NSMakeRect(PADDING, PADDING, WIDTH - PADDING * 2, SEARCH_HEIGHT)
        )
        search.setFont_(NSFont.systemFontOfSize_(15))
        search.setBezeled_(False)
        search.setDrawsBackground_(False)
        search.setFocusRingType_(1)  # NSFocusRingTypeNone
        search.setPlaceholderString_("Buscar snippet…")
        search.setDelegate_(self)
        container.addSubview_(search)
        self._search = search

        # Lista de resultados (NSTableView dentro de un NSScrollView)
        scroll = NSScrollView.alloc().initWithFrame_(NSMakeRect(0, 0, WIDTH, 0))
        scroll.setHasVerticalScroller_(True)
        scroll.setAutohidesScrollers_(True)
        scroll.setDrawsBackground_(False)
        scroll.setBorderType_(0)  # NSNoBorder

        table = NSTableView.alloc().initWithFrame_(NSMakeRect(0, 0, WIDTH, 0))
        table.setRowHeight_(ROW_HEIGHT)
        table.setHeaderView_(None)
        table.setBackgroundColor_(NSColor.clearColor())
        table.setSelectionHighlightStyle_(NSTableViewSelectionHighlightStyleRegular)
        table.setAllowsEmptySelection_(True)
        table.setAllowsMultipleSelection_(False)
        table.setDataSource_(self)
        table.setDelegate_(self)
        table.setTarget_(self)
        table.setDoubleAction_("doubleClick:")

        column = NSTableColumn.alloc().initWithIdentifier_("snippet")
        column.setWidth_(WIDTH)
        table.addTableColumn_(column)

        scroll.setDocumentView_(table)
        container.addSubview_(scroll)
        self._scroll = scroll
        self._table = table

        self._panel = panel
        self._container = container

    @objc.python_method
    def _make_background(self, rect):
        """Fondo translúcido con esquinas redondeadas (NSVisualEffectView si existe)."""
        try:
            from AppKit import (
                NSVisualEffectView,
                NSVisualEffectBlendingModeBehindWindow,
                NSVisualEffectStateActive,
            )

            view = NSVisualEffectView.alloc().initWithFrame_(rect)
            material = getattr(__import__("AppKit"), "NSVisualEffectMaterialMenu", None)
            if material is not None:
                view.setMaterial_(material)
            view.setBlendingMode_(NSVisualEffectBlendingModeBehindWindow)
            view.setState_(NSVisualEffectStateActive)
        except Exception:
            view = NSView.alloc().initWithFrame_(rect)
            view.setWantsLayer_(True)
            view.layer().setBackgroundColor_(
                NSColor.windowBackgroundColor().CGColor()
            )

        view.setWantsLayer_(True)
        view.layer().setCornerRadius_(CORNER_RADIUS)
        view.layer().setMasksToBounds_(True)
        return view

    # ------------------------------------------------------------------- mostrar/ocultar
    @objc.python_method
    def show(self):
        self._prev_app = NSWorkspace.sharedWorkspace().frontmostApplication()
        self.store.reload()
        self._search.setStringValue_("")
        self._apply_filter("")
        self._layout_and_place()
        self._open = True
        self._closing = False
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

    # ----------------------------------------------------------- delegado NSTextField
    def controlTextDidChange_(self, notification):
        self._apply_filter(self._search.stringValue())
        self._layout_and_place()

    def control_textView_doCommandBySelector_(self, control, textView, selector):
        name = str(selector)
        if name in ("moveUp:",):
            self._move(-1)
            return True
        if name in ("moveDown:",):
            self._move(1)
            return True
        if name in ("insertNewline:", "insertLineBreak:"):
            self._insert_selected()
            return True
        if name in ("cancelOperation:", "cancel:", "complete:"):
            self.hide()
            return True
        return False

    @objc.python_method
    def _move(self, delta):
        if not self._results:
            return
        self._selected = max(0, min(len(self._results) - 1, self._selected + delta))
        self._sync_selection()

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
                NSMakeRect(0, 0, WIDTH, ROW_HEIGHT)
            )
            field.setIdentifier_(identifier)
            field.setBezeled_(False)
            field.setDrawsBackground_(False)
            field.setEditable_(False)
            field.setSelectable_(False)
            field.setFont_(NSFont.systemFontOfSize_(13))
            field.setLineBreakMode_(5)  # NSLineBreakByTruncatingTail

        name, content = self._results[row]
        preview = content.replace("\n", " ").strip()
        if len(preview) > 64:
            preview = preview[:64] + "…"
        field.setStringValue_("%s     ·     %s" % (name, preview))
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
    def _layout_and_place(self):
        rows = max(1, min(MAX_VISIBLE_ROWS, len(self._results)))
        list_height = rows * ROW_HEIGHT if self._results else 0.0
        total = SEARCH_HEIGHT + PADDING * 2 + list_height
        if self._results:
            total += PADDING  # respiro entre buscador y lista

        # Reposicionar las subvistas (origen abajo a la izquierda).
        self._container.setFrame_(NSMakeRect(0, 0, WIDTH, total))
        self._search.setFrame_(
            NSMakeRect(PADDING, total - PADDING - SEARCH_HEIGHT, WIDTH - PADDING * 2, SEARCH_HEIGHT)
        )
        self._scroll.setFrame_(NSMakeRect(0, 0, WIDTH, list_height))

        from .caret import panel_top_left

        x, y = panel_top_left()
        x, y = self._clamp_to_screen(x, y, WIDTH, total)

        frame = NSMakeRect(x, y - total, WIDTH, total)
        self._panel.setFrame_display_(frame, True)

    @staticmethod
    def _clamp_to_screen(x, top_y, width, height):
        from AppKit import NSScreen

        visible = NSScreen.screens()[0].visibleFrame()
        min_x = visible.origin.x
        max_x = visible.origin.x + visible.size.width - width
        min_top = visible.origin.y + height
        max_top = visible.origin.y + visible.size.height

        x = max(min_x, min(max_x, x))
        top_y = max(min_top, min(max_top, top_y))
        return (x, top_y)
