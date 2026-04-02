from __future__ import annotations
from typing import Iterable, Optional

from bpy.types import Collection, Context, UILayout
from bpy.props import StringProperty

from ..._shared.profile import get_profile_items


from .base import ExporterProtocol


class ProfileExporterPart(ExporterProtocol):

    def _get_profile_items(
        self, context: Optional[Context] = None
    ) -> Iterable[tuple[str, str, str]]:
        return get_profile_items()

    profile: EnumProperty(  # type: ignore
        name="Export Profile",
        description="Profile to use by this collection",
        items=_get_profile_items,
    )

    def draw_profile_info(self, layout: UILayout, profile: Profile) -> None:
        info = profile.profile_info
        if not info:
            return

        has_info = bool(info.summary or info.instructions or info.links)
        if not has_info:
            return

        header, body = layout.panel("ProfileInfo", default_closed=True)
        header.label(text="Profile Info", icon="INFO")
        if not body:
            return

        if info.summary:
            for line in textwrap.wrap(info.summary, width=100):
                body.label(text=line)

        if info.instructions:
            body.separator(type="LINE")
            body.label(text="Instructions", icon="INFO")
            for instruction in info.instructions:
                for line in textwrap.wrap(instruction, width=100):
                    body.label(text=f"- {line}")

        if info.links:
            body.separator(type="LINE")
            body.label(text="Links", icon="WORLD")
            for label, url in info.links:
                op = body.operator("wm.url_open", text=label, icon="WORLD")
                op.url = url
