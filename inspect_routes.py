import asyncio
from starlette.applications import Starlette
from starlette.routing import Mount, Route
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.testclient import TestClient

class AsgiApp:
    async def __call__(self, scope, receive, send):
        request = Request(scope, receive)
        response = JSONResponse({"method": request.method})
        await response(scope, receive, send)

asgi_app = AsgiApp()

app = Starlette(routes=[Route('/', endpoint=asgi_app, methods=["GET", "POST"])])
client = TestClient(app)
try:
    print("Route POST:", client.post("/").status_code)
except Exception as e:
    print("ERROR:", e)

app2 = Starlette(routes=[Mount('/', app=asgi_app)])
client2 = TestClient(app2)
print("Mount POST:", client2.post("/").status_code)

