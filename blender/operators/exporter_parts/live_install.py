from bpy.types import Context, Operator, Event, UILayout

from .base import ExporterProtocol


class LiveInstallExporterPart(ExporterProtocol):

    live_install: BoolProperty(  # type: ignore
        name="Live Install",
        description="Automatically install exported files to the mod directory",
        default=False,
    )

    live_install_target_dir: StringProperty(  # type: ignore
        name="Live Install Target Directory",
        description="Directory where model files will be installed",
        subtype="DIR_PATH",
        default="",
    )

    live_install_auto_reload: BoolProperty(  # type: ignore
        name="Auto Reload",
        description="Automatically trigger a reload in-game after live install",
        default=False,
    )

    live_install_auto_redraw: BoolProperty(  # type: ignore
        name="Auto Redraw",
        description="Automatically trigger a redraw in-game after live install.",
        default=False,
    )

    def draw_auto_live_install_settings(self, layout: UILayout) -> None:
        header, body = layout.panel("Live Install", default_closed=True)
        header.enabled = self.is_mdl_export_enabled()
        header.prop(self, "live_install", text="Enable Live Install")

        if not body:
            return

        body.enabled = self.live_install
        body.prop(self, "live_install_target_dir", text="Target Directory")
        body.prop(
            self, "live_install_auto_reload", text="Auto Reload After Install"
        )
        body.prop(
            self, "live_install_auto_redraw", text="Auto Redraw After Install"
        )
