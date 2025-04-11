from fastapi import APIRouter, Request
from fastapi.responses import FileResponse
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
import os
from typing import Any

router = APIRouter()


@router.get("/docs/export", summary="Generate API documentation PDF")
async def export_api_docs(request: Request):
    app = request.app
    routes_info = []

    for route in app.routes:
        if hasattr(route, "methods"):
            route_info = {
                "path": route.path,
                "methods": list(route.methods),
                "name": route.name,
                "summary": getattr(route.endpoint, "__doc__", "").strip()
            }
            routes_info.append(route_info)

    # Prepare context
    context = {
        "routes": sorted(routes_info, key=lambda r: r["path"])
    }

    # Render HTML
    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template("api_doc.html")
    html_out = template.render(context)

    # Convert to PDF
    pdf_path = "/tmp/api_doc.pdf"
    HTML(string=html_out).write_pdf(pdf_path)

    return FileResponse(pdf_path, media_type="application/pdf", filename="api_doc.pdf")
