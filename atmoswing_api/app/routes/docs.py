from pathlib import Path
from fastapi.responses import HTMLResponse
from fastapi import APIRouter, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from jinja2 import Environment, FileSystemLoader, select_autoescape

router = APIRouter()

limiter = Limiter(key_func=get_remote_address)

_template = Environment(
    loader=FileSystemLoader(Path(__file__).parents[2] / "templates"),
    autoescape=select_autoescape(["html"]),
).get_template("api_doc.html")


@router.get("/minidocs", summary="Generate API documentation HTML")
@limiter.limit("10/minute")
async def export_api_docs(request: Request):
    # The OpenAPI schema is used rather than app.routes, whose structure depends on
    # the FastAPI version (recent versions wrap the routes of included routers).
    routes_info = []
    for path, operations in request.app.openapi().get("paths", {}).items():
        for method, operation in operations.items():
            routes_info.append({
                "path": path,
                "methods": [method.upper()],
                "summary": operation.get("summary", ""),
                "description": (operation.get("description") or "").strip(),
                "parameters": [
                    param["name"] if param.get("in") == "path"
                    else f"{param['name']} ({param.get('in')})"
                    for param in operation.get("parameters", [])],
            })

    html_out = _template.render(routes=sorted(routes_info, key=lambda r: r["path"]))

    return HTMLResponse(content=html_out)
