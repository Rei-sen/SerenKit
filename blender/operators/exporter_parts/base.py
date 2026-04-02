from typing import Optional, Protocol

from ..._shared.profile import Profile


class ExporterProtocol(Protocol):

    def current_profile_name(self) -> str: ...

    def current_profile(self) -> Optional[Profile]: ...

    def is_mdl_export_enabled(self) -> bool: ...
