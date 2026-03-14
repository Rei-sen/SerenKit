import json
from typing import Optional

from urllib.request import urlopen, Request
from urllib.error import URLError

import urllib


_DEFAULT_ADDRESS = "http://localhost:42069"
_API_ADDRESS = _DEFAULT_ADDRESS + "/api"


class PenumbraConnection:

    def send_message(self, endpoint: str, data: dict[str, str] = dict()) -> str:
        url = _API_ADDRESS + endpoint

        json_data = json.dumps(data).encode("utf-8")

        msg = Request(
            url,
            data=json_data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(msg, timeout=10) as response:
                r: str = response.read().decode("utf-8")
                return r
        except URLError as e:
            raise ConnectionError(
                f"Failed to connect to Penumbra API at {url}: {e.reason}"
            )

    def redraw(self) -> None:
        # Index 0 is self
        # https://github.com/xivdev/Penumbra/blob/5bbccc8248b78185ee84097533f8ac3175438555/Penumbra/Interop/Services/RedrawService.cs#L362
        # Type 0 is regular redraw
        # https://github.com/Ottermandias/Penumbra.Api/blob/62e98d9cb1d5c1014a671372d0168ad7e60ec9dd/Enums/RedrawType.cs
        self.send_message("/redraw", {"ObjectTableIndex": "0", "Type": "0"})

    def reload(self, *, path: str = "", name: str = "") -> None:
        msg = dict()
        if path:
            msg["Path"] = path
        if name:
            msg["Name"] = name
        self.send_message("/reloadmod", msg)
