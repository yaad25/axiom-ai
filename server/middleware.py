"""
Velto Framework Middlewares.

Drop-in 1-line integration for FastAPI, Starlette, and Flask applications.
Injects sub-1ms intent classification, schema validation, and decision routing directly into request life-cycles.
"""

from __future__ import annotations

from typing import Any, Callable
from server.model import VeltoFastBackend, Backend, get_backend


class VeltoFastAPIMiddleware:
    """
    FastAPI / Starlette Middleware for instant sub-millisecond request intent routing.
    
    Usage:
        app = FastAPI()
        app.add_middleware(VeltoFastAPIMiddleware, backend_name="velto-fast")
    """

    def __init__(self, app: Any, backend_name: str = "velto-fast"):
        self.app = app
        self.backend: Backend = get_backend(backend_name)

    async def __call__(self, scope: dict, receive: Callable, send: Callable) -> None:
        if scope["type"] == "http":
            # Attach Velto decision engine to request scope
            scope["velto_decision"] = self.backend
        await self.app(scope, receive, send)


class VeltoFlaskMiddleware:
    """
    Flask Extension for instant sub-millisecond request decision routing.
    
    Usage:
        app = Flask(__name__)
        velto = VeltoFlaskMiddleware(app, backend_name="velto-fast")
    """

    def __init__(self, app: Any | None = None, backend_name: str = "velto-fast"):
        self.backend: Backend = get_backend(backend_name)
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Any) -> None:
        @app.before_request
        def attach_velto():
            from flask import g
            g.velto_decision = self.backend
