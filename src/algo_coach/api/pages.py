"""The built pages, served on the API's origin: `README.md` gives why the two
share one."""

from pathlib import Path

from starlette.exceptions import HTTPException
from starlette.responses import Response
from starlette.staticfiles import StaticFiles
from starlette.types import Scope


class Pages(StaticFiles):
    """The pages' files, with a path naming no file answered by `index.html`."""

    def __init__(self, directory: Path, api_prefix: str) -> None:
        super().__init__(directory=directory, html=True)
        self.api_prefix = api_prefix.strip("/")

    async def get_response(self, path: str, scope: Scope) -> Response:
        try:
            return await super().get_response(path, scope)
        except HTTPException as missing:
            # a path under the API's prefix names a route, so a miss there stays
            # a 404 rather than a page
            if missing.status_code != 404 or path.split("/")[0] == self.api_prefix:
                raise
            return await super().get_response("index.html", scope)
