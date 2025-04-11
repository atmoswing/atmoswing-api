import os
from fastapi.responses import HTMLResponse
from fastapi import APIRouter, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from jinja2 import Environment, FileSystemLoader

router = APIRouter()

limiter = Limiter(key_func=get_remote_address)


@router.get("/minidocs", summary="Generate API documentation HTML")
@limiter.limit("10/minute")
async def export_api_docs(request: Request):
    app = request.app
    routes_info = []

    for route in app.routes:
        if hasattr(route, "methods"):
            route_info = {
                "path": route.path,
                "methods": list(route.methods),
                "name": route.name,
                "summary": (getattr(route.endpoint, "__doc__", "") or "").strip() if route.endpoint else "",
                "parameters": list(route.param_convertors.keys())
            }
            routes_info.append(route_info)

    # Prepare context
    context = {
        "routes": sorted(routes_info, key=lambda r: r["path"])
    }

    # Render HTML
    template_dir = os.path.join(os.path.dirname(__file__), "../../templates")
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template("api_doc.html")
    html_out = template.render(context)

    # Return the rendered HTML response directly
    return HTMLResponse(content=html_out)
