from __future__ import annotations

import cgi
import http.server
import json
import socketserver
from http import HTTPStatus
from pathlib import Path
from urllib.parse import urlparse

from custom_artwork import MAX_UPLOAD_BYTES, save_custom_artwork
from display_controller import (
    cancel_override,
    create_schedule,
    delete_schedule,
    list_schedules,
    remove_artwork_references,
    resolve_display,
    set_temporary_override,
)
from gallery_library import build_library, delete_artwork, update_artwork_metadata
from presentation_manager import apply_presentation
from display_settings import load_display_settings, save_display_settings
from reliability import create_backup, create_diagnostics, health_report

PORT = 8000
OUTPUT_FOLDER = Path("output")


class ReusableTCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(OUTPUT_FOLDER), **kwargs)

    def do_GET(self) -> None:
        route = urlparse(self.path).path
        if route == "/api/display":
            self.send_json(resolve_display())
            return
        if route == "/api/schedules":
            self.send_json({"schedules": list_schedules()})
            return
        if route == "/api/library":
            self.send_json(build_library())
            return
        if route == "/api/display/settings":
            self.send_json(load_display_settings())
            return
        if route == "/api/health":
            self.send_json(health_report(resolve_display()))
            return
        if route.startswith("/downloads/"):
            filename = route.removeprefix("/downloads/")
            path = Path("backups") / filename
            if not path.exists() or not path.is_file():
                self.send_error(404)
                return
            body = path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "application/zip")
            self.send_header("Content-Disposition", f'attachment; filename="{path.name}"')
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        super().do_GET()

    def do_POST(self) -> None:
        route = urlparse(self.path).path
        try:
            if route == "/api/backup":
                path = create_backup()
                self.send_json({"ok": True, "download_url": f"/downloads/{path.name}"})
                return
            if route == "/api/diagnostics":
                path = create_diagnostics(resolve_display())
                self.send_json({"ok": True, "download_url": f"/downloads/{path.name}"})
                return
            if route == "/api/display/settings":
                payload = self.read_json_body()
                self.send_json({"ok": True, "settings": save_display_settings(payload)})
                return
            if route == "/api/override":
                payload = self.read_json_body()
                self.send_json(set_temporary_override(str(payload.get("artwork_id", "")), int(payload.get("duration_minutes", 0))))
                return
            if route == "/api/override/cancel":
                self.send_json(cancel_override())
                return
            if route == "/api/upload":
                self.handle_upload()
                return
            if route == "/api/schedules":
                payload = self.read_json_body()
                schedule = create_schedule(str(payload.get("artwork_id", "")), str(payload.get("starts_at", "")), str(payload.get("ends_at", "")))
                self.send_json({"ok": True, "schedule": schedule}, HTTPStatus.CREATED)
                return
            if route == "/api/schedules/delete":
                payload = self.read_json_body()
                delete_schedule(str(payload.get("schedule_id", "")))
                self.send_json({"ok": True})
                return
            if route in {"/api/artwork/update", "/api/custom/update"}:
                payload = self.read_json_body()
                manifest = update_artwork_metadata(
                    str(payload.get("artwork_id", "")),
                    title=payload.get("title") if "title" in payload else None,
                    favourite=payload.get("favourite") if "favourite" in payload else None,
                    hidden=payload.get("hidden") if "hidden" in payload else None,
                    notes=payload.get("notes") if "notes" in payload else None,
                )
                self.send_json({"ok": True, "artwork": manifest})
                return
            if route == "/api/artwork/presentation":
                payload = self.read_json_body()
                result = apply_presentation(
                    str(payload.get("artwork_id", "")),
                    str(payload.get("mode", "auto")),
                )
                self.send_json({"ok": True, **result})
                return
            if route in {"/api/artwork/delete", "/api/custom/delete"}:
                payload = self.read_json_body()
                artwork_id = str(payload.get("artwork_id", "")).strip()
                if not artwork_id:
                    raise ValueError("Artwork ID is required.")

                active_display = resolve_display()
                active_artwork = active_display.get("artwork")
                active_id = (
                    str(active_artwork.get("id", "")).strip()
                    if isinstance(active_artwork, dict)
                    else ""
                )
                if active_id == artwork_id:
                    raise ValueError(
                        "This artwork is currently being displayed. "
                        "Display another artwork before deleting it."
                    )

                remove_artwork_references(artwork_id)
                deleted = delete_artwork(artwork_id)
                self.send_json({
                    "ok": True,
                    "deleted": {
                        "id": deleted["id"],
                        "title": deleted["title"],
                    },
                    "library": deleted["library"],
                })
                return
        except (ValueError, TypeError, OSError) as error:
            self.send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
            return

        self.send_json({"error": "Not found"}, HTTPStatus.NOT_FOUND)

    def handle_upload(self) -> None:
        content_length = int(self.headers.get("Content-Length", "0"))
        if content_length <= 0:
            raise ValueError("No upload was received.")
        if content_length > MAX_UPLOAD_BYTES + 1024 * 1024:
            self.send_json({"error": "The upload is larger than the 20 MB limit."}, HTTPStatus.REQUEST_ENTITY_TOO_LARGE)
            return
        content_type = self.headers.get("Content-Type", "")
        if not content_type.startswith("multipart/form-data"):
            raise ValueError("Upload must use multipart form data.")

        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={"REQUEST_METHOD": "POST", "CONTENT_TYPE": content_type, "CONTENT_LENGTH": str(content_length)},
        )
        image_field = form["image"] if "image" in form else None
        if image_field is None or not getattr(image_field, "file", None):
            raise ValueError("Choose an image to upload.")

        manifest = save_custom_artwork(
            file_stream=image_field.file,
            filename=image_field.filename or "upload",
            content_type=image_field.type or "",
            title=form.getfirst("title", "Custom artwork"),
        )
        display = None
        if form.getfirst("show_now", "false").lower() == "true":
            display = set_temporary_override(manifest["id"], int(form.getfirst("duration_minutes", "0")))
        self.send_json({"ok": True, "artwork": manifest, "display": display}, HTTPStatus.CREATED)

    def read_json_body(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        try:
            value = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError as error:
            raise ValueError("Invalid JSON request.") from error
        if not isinstance(value, dict):
            raise ValueError("Request must be a JSON object.")
        return value

    def send_json(self, value: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(value).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)


def start_server() -> None:
    try:
        with ReusableTCPServer(("", PORT), Handler) as httpd:
            print("\nGalleryOS is running.")
            print(f"Display: http://localhost:{PORT}")
            print(f"Phone control: http://localhost:{PORT}/control/")
            print(f"Library: http://localhost:{PORT}/gallery/\n")
            print("Press Ctrl+C to stop.")
            httpd.serve_forever()
    except OSError as error:
        if error.errno == 98:
            print(f"\nGalleryOS server already appears to be running on port {PORT}.\n")
        else:
            raise


if __name__ == "__main__":
    start_server()
