"""`python -m algo_coach.api`: the API, and the built pages where
ALGO_COACH_PAGES names them. Locally Vite serves the pages instead, on the same
origin: `README.md` gives why."""

import argparse
import json
import os
from pathlib import Path

import uvicorn
from dotenv import find_dotenv, load_dotenv
from fastapi import FastAPI

from algo_coach.api.app import create_app
from algo_coach.api.signin import SignIn
from algo_coach.storage import Database

# the port `web/vite.config.ts` proxies `/api` to
PORT = 8000


def app() -> FastAPI:
    root = Database(url=os.environ.get("DATABASE_URL"))
    return create_app(
        root,
        sign_in=SignIn.from_environ(os.environ),
        dev_login=os.environ.get("ALGO_COACH_DEV_LOGIN") or None,
        pages=Path(pages) if (pages := os.environ.get("ALGO_COACH_PAGES")) else None,
    )


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m algo_coach.api")
    parser.add_argument("--reload", action="store_true", help="restart when the source changes")
    parser.add_argument(
        "--openapi", action="store_true", help="print the OpenAPI schema the page is typed from"
    )
    args = parser.parse_args()
    if args.openapi:
        print(json.dumps(app().openapi(), indent=2))
        return
    load_dotenv(find_dotenv(usecwd=True))
    # by import path: a reload re-imports the factory rather than reusing an app
    uvicorn.run(
        "algo_coach.api.__main__:app",
        factory=True,
        host="127.0.0.1",
        port=PORT,
        reload=args.reload,
        reload_dirs=["src"] if args.reload else None,
    )


if __name__ == "__main__":
    main()
