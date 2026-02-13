

from typing import Callable, Any, Optional, cast

import bpy
from bpy.types import UILayout

# A tiny transient state dictionary keyed by strings.
_TRANSIENT_STATE: dict[str, dict[str, bool]] = {}


def _ensure_state(state_key: str, default_is_expanded: bool = True) -> dict[str, bool]:
    s = _TRANSIENT_STATE.get(state_key)
    if s is None:
        s = {'is_expanded': bool(default_is_expanded)}
        _TRANSIENT_STATE[state_key] = s
    return s


def toggle_transient_state(state_key: str) -> bool:
    """Toggle and return the expanded state for `state_key`."""
    s = _ensure_state(state_key)
    s['is_expanded'] = not bool(s.get('is_expanded', True))
    return s['is_expanded']


def get_transient_state(
    state_key: str,
    default_is_expanded: bool = True,
) -> dict[str, bool]:
    """Return or create transient state dict for `state_key`."""
    return _ensure_state(state_key, default_is_expanded)


def draw_collapsible_section(
    layout: UILayout,
    title: str,
    state_key: Optional[str] = None,
    extra: Optional[Callable[[UILayout], None]] = None,
    icon: str = 'FILE_FOLDER',
) -> bool:
    """Draw a collapsible header controlled by `state_key` (optional)."""
    row = layout.row(align=True)

    if state_key is not None:
        st = get_transient_state(state_key)
        expanded = bool(st.get('is_expanded', True))
    else:
        expanded = True

    tri_icon: str = 'DOWNARROW_HLT' if expanded else 'RIGHTARROW'

    if state_key is not None:
        try:
            op = row.operator('modkit.toggle_transient',
                              text='', icon=tri_icon, emboss=False)
            op.state_key = state_key
        except Exception:
            row.label(text='', icon=tri_icon)
    else:

        row.label(text='', icon=cast(Any, tri_icon))

    row.label(text=title, icon=cast(Any, icon))

    if extra:
        try:
            extra(row)
        except Exception:
            pass

    return expanded


def draw_info_box(layout: UILayout, title: str, icon: str = 'INFO') -> UILayout:
    box = layout.box()
    row = box.row()
    row.alignment = 'CENTER'
    row.label(text=title, icon=icon)
    box.separator(type='LINE')
    return box


def draw_grid_flow(layout: UILayout, items: list[tuple[str, Any]],
                   draw_func: Callable[[UILayout, str, Any], None],
                   title: Optional[str] = None) -> None:
    box = layout.box()
    if title:
        row = box.row()
        row.alignment = 'CENTER'
        row.label(text=title)
        box.separator(type='LINE')

    flow = box.grid_flow(row_major=True, columns=0,
                         even_columns=False, even_rows=False, align=True)
    flow.scale_x = 0.6
    for label, value in items:
        draw_func(flow, label, value)


def draw_toggle_with_field(
    layout: UILayout,
    owner: Any,
    toggle_attr: str,
    field_attr: str,
    label: Optional[str] = None,
) -> None:
    """Draw a checkbox that toggles an adjacent field."""

    layout.prop(owner, toggle_attr)  # Pre-draw to avoid layout issues
    if owner.get(toggle_attr, False):
        box = layout.box()
        box.prop(owner, field_attr, text=label)


def call_operator_in_3d_viewport(op_func: Callable[[str], Any], context: str) -> Any:
    """Invoke an operator in a 3D Viewport area and return its result."""
    assert bpy.context.window_manager

    for window in bpy.context.window_manager.windows:
        screen = window.screen
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                with bpy.context.temp_override(window=window, area=area):
                    return op_func(context)
    raise RuntimeError("No 3D Viewport found to call operator in")
