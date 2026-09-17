"""Zero-dependency HTTP server for the Redundancy Linter Web Demo.

Provides static file serving, byte-range video streaming (for smooth seeking),
and REST APIs for pre-computed samples, live file uploads, and URL analysis.
"""

from __future__ import annotations

import cgi
import json
import os
import re
import sys
import tempfile
import urllib.parse
from http import HTTPStatus
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data.input_manager import resolve_input
from src.results.pipeline_runner import analyze_video

APP_DIR = PROJECT_ROOT / "app"
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = DATA_DIR / "results"
VIDEOS_DIR = DATA_DIR / "videos"

# Pre-indexed friendly names for demo samples
SAMPLE_METADATA = {
    "01 [01]": "MIT 18.06 Linear Algebra - Lecture 1 (Gilbert Strang)",
    "18200-lecture-1-version-2_360p_16_9": "MIT 18.200 Discrete Applied Math - Lecture 1",
    "18200-lecture-2-version-2_360p_16_9": "MIT 18.200 Discrete Applied Math - Lecture 2",
    "Lecture_5": "MIT 6.006 Algorithms - Lecture 5 (Linear Sorting)",
    "Lecture_6": "MIT 6.006 Algorithms - Lecture 6 (Binary Trees I)",
    "Lecture_7": "MIT 6.006 Algorithms - Lecture 7 (Binary Trees II: AVL)",
}


class LinterServerHandler(SimpleHTTPRequestHandler):
    """Custom request handler with streaming video and analysis endpoints."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(APP_DIR), **kwargs)

    def do_HEAD(self) -> None:
        self.do_GET()

    def do_GET(self) -> None:
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query = urllib.parse.parse_qs(parsed_url.query)

        if path == "/api/samples":
            self.handle_get_samples()
        elif path == "/api/results":
            self.handle_get_results(query)
        elif path == "/media/video":
            self.handle_stream_video(query)
        else:
            # Serve static assets from app/ directory
            super().do_GET()

    def do_POST(self) -> None:
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        if path == "/api/analyze-url":
            self.handle_analyze_url()
        elif path == "/api/upload":
            self.handle_analyze_upload()
        else:
            self.send_error(HTTPStatus.NOT_FOUND, "Endpoint not found")

    def handle_get_samples(self) -> None:
        """Return list of available pre-analyzed videos."""
        samples = []
        if RESULTS_DIR.is_dir():
            for json_file in sorted(RESULTS_DIR.glob("*.json")):
                stem = json_file.stem
                try:
                    data = json.loads(json_file.read_text(encoding="utf-8"))
                    violations_count = len(data.get("violations", []))
                except Exception:
                    violations_count = 0

                # Check if matching video file exists
                video_match = self._find_video_file(stem)
                samples.append(
                    {
                        "stem": stem,
                        "title": SAMPLE_METADATA.get(stem, stem),
                        "has_video": video_match is not None,
                        "violations_count": violations_count,
                    }
                )

        self._send_json({"samples": samples})

    def handle_get_results(self, query: dict[str, list[str]]) -> None:
        """Fetch pre-computed results JSON for a given video stem."""
        video_stem = query.get("video", [""])[0]
        if not video_stem:
            self.send_error(HTTPStatus.BAD_REQUEST, "Missing 'video' query parameter")
            return

        result_path = RESULTS_DIR / f"{video_stem}.json"
        if not result_path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND, f"Results not found for {video_stem}")
            return

        try:
            data = json.loads(result_path.read_text(encoding="utf-8"))
            self._send_json(data)
        except Exception as error:
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(error))

    def handle_analyze_url(self) -> None:
        """Download URL to temp and execute pipeline analysis."""
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length)

        try:
            payload = json.loads(post_data.decode("utf-8"))
            url = payload.get("url", "").strip()
            duration = float(payload.get("duration", 60.0))
            if not url:
                self.send_error(HTTPStatus.BAD_REQUEST, "Missing 'url' field")
                return

            temp_dir = Path(tempfile.mkdtemp(prefix="web_url_analysis_"))
            video_path = resolve_input(url, temp_dir=temp_dir)
            result = analyze_video(video_path, start=0.0, duration=duration)
            result["temp_media_path"] = str(video_path)
            self._send_json(result)
        except Exception as error:
            self._send_json({"error": str(error)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def handle_analyze_upload(self) -> None:
        """Handle multipart uploaded video file and run analysis."""
        try:
            content_type = self.headers.get("Content-Type", "")
            if not content_type.startswith("multipart/form-data"):
                self.send_error(HTTPStatus.BAD_REQUEST, "Content-Type must be multipart/form-data")
                return

            environ = {
                "REQUEST_METHOD": "POST",
                "CONTENT_TYPE": content_type,
                "CONTENT_LENGTH": self.headers.get("Content-Length", 0),
            }
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ=environ,
                keep_blank_values=True,
            )

            if "file" not in form:
                self.send_error(HTTPStatus.BAD_REQUEST, "Missing 'file' field in form")
                return

            file_item = form["file"]
            duration = float(form.getvalue("duration", 60.0))

            temp_dir = Path(tempfile.mkdtemp(prefix="web_upload_analysis_"))
            filename = file_item.filename or "uploaded_video.mp4"
            dest_path = temp_dir / filename

            with open(dest_path, "wb") as f_out:
                f_out.write(file_item.file.read())

            result = analyze_video(dest_path, start=0.0, duration=duration)
            result["temp_media_path"] = str(dest_path)
            self._send_json(result)
        except Exception as error:
            self._send_json({"error": str(error)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def handle_stream_video(self, query: dict[str, list[str]]) -> None:
        """Stream video files supporting HTTP 206 Range requests for instant seeking."""
        video_stem = query.get("stem", [""])[0]
        custom_path = query.get("path", [""])[0]

        video_path = None
        if custom_path:
            cand = Path(custom_path)
            if cand.is_file():
                video_path = cand
        elif video_stem:
            video_path = self._find_video_file(video_stem)

        if not video_path or not video_path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND, "Video file not found")
            return

        file_size = video_path.stat().st_size
        range_header = self.headers.get("Range")

        content_type = "video/mp4"
        if video_path.suffix.lower() == ".webm":
            content_type = "video/webm"
        elif video_path.suffix.lower() == ".mov":
            content_type = "video/quicktime"

        if range_header:
            match = re.search(r"bytes=(\d+)-(\d*)", range_header)
            if match:
                start = int(match.group(1))
                end = int(match.group(2)) if match.group(2) else file_size - 1
                if start >= file_size or end >= file_size or start > end:
                    self.send_error(HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE)
                    return

                length = end - start + 1
                self.send_response(HTTPStatus.PARTIAL_CONTENT)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
                self.send_header("Content-Length", str(length))
                self.send_header("Accept-Ranges", "bytes")
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()

                with open(video_path, "rb") as video_file:
                    video_file.seek(start)
                    bytes_remaining = length
                    while bytes_remaining > 0:
                        chunk_size = min(64 * 1024, bytes_remaining)
                        chunk = video_file.read(chunk_size)
                        if not chunk:
                            break
                        try:
                            self.wfile.write(chunk)
                        except (ConnectionResetError, BrokenPipeError):
                            break
                        bytes_remaining -= len(chunk)
                return

        # No Range header: full video response
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(file_size))
        self.send_header("Accept-Ranges", "bytes")
        self.end_headers()

        with open(video_path, "rb") as video_file:
            while True:
                chunk = video_file.read(64 * 1024)
                if not chunk:
                    break
                try:
                    self.wfile.write(chunk)
                except (ConnectionResetError, BrokenPipeError):
                    break

    def _find_video_file(self, stem: str) -> Path | None:
        """Locate video matching stem in data/videos/."""
        if not VIDEOS_DIR.is_dir():
            return None
        for ext in [".mp4", ".mov", ".webm", ".mkv"]:
            cand = VIDEOS_DIR / f"{stem}{ext}"
            if cand.is_file():
                return cand
        # Also check for brackets / fuzzy matches
        for f in VIDEOS_DIR.glob(f"*{stem}*"):
            if f.is_file() and f.suffix.lower() in {".mp4", ".mov", ".webm", ".mkv"}:
                return f
        return None

    def _send_json(self, data: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)


def run_server(port: int = 8000) -> None:
    server_address = ("", port)
    httpd = HTTPServer(server_address, LinterServerHandler)
    print(f"Redundancy Linter Web UI running at http://localhost:{port}")
    print("Press Ctrl+C to stop.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        httpd.server_close()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    run_server(port)
