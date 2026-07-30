"""Minimal Supabase Storage support for workspace folder persistence.

The editor, compiler and builder continue to use ``workspaces/<slug>``.  This
module only mirrors those folders to an optional Supabase Storage bucket so
Render's local disk can be treated as a cache.
"""

from __future__ import annotations

import hashlib
import json
import logging
import mimetypes
import os
import shutil
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from workspace.manager import WORKSPACES_ROOT


logger = logging.getLogger(__name__)

_MANIFEST_NAME = ".degreebaba-workspace-manifest.json"
_IGNORED_PARTS = {".DS_Store", "__pycache__"}


class SupabaseWorkspaceStorage:
    """A deliberately small Storage REST client; no database is required."""

    def __init__(self) -> None:
        self.url = os.getenv("SUPABASE_URL", "").rstrip("/")
        self.key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
        self.bucket = os.getenv("SUPABASE_WORKSPACE_BUCKET", "degreebaba-workspaces")

    @property
    def enabled(self) -> bool:
        return bool(self.url and self.key and self.bucket)

    def _object_url(self, object_path: str) -> str:
        return f"{self.url}/storage/v1/object/{quote(self.bucket, safe='')}/{quote(object_path, safe='/')}"

    def _headers(self, **extra: str) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.key}",
            "apikey": self.key,
            **extra,
        }

    def _request(self, request: Request, *, timeout: int = 60) -> bytes:
        try:
            with urlopen(request, timeout=timeout) as response:
                return response.read()
        except HTTPError:
            raise
        except URLError as exc:
            raise RuntimeError(f"Supabase Storage is unavailable: {exc.reason}") from exc

    def get_bytes(self, object_path: str) -> bytes | None:
        if not self.enabled:
            return None
        try:
            return self._request(Request(self._object_url(object_path), headers=self._headers()))
        except HTTPError as exc:
            if exc.code == 404:
                return None
            raise RuntimeError(f"Supabase download failed ({exc.code}) for {object_path}") from exc

    def put_bytes(self, object_path: str, data: bytes, content_type: str | None = None) -> None:
        if not self.enabled:
            return
        headers = self._headers(
            **{
                "x-upsert": "true",
                "Content-Type": content_type or "application/octet-stream",
            }
        )
        request = Request(self._object_url(object_path), data=data, headers=headers, method="POST")
        try:
            self._request(request, timeout=180)
        except HTTPError as exc:
            raise RuntimeError(f"Supabase upload failed ({exc.code}) for {object_path}") from exc

    def delete_objects(self, object_paths: list[str]) -> None:
        if not self.enabled or not object_paths:
            return
        body = json.dumps({"prefixes": object_paths}).encode("utf-8")
        request = Request(
            f"{self.url}/storage/v1/object/{quote(self.bucket, safe='')}",
            data=body,
            headers=self._headers(**{"Content-Type": "application/json"}),
            method="DELETE",
        )
        try:
            self._request(request)
        except HTTPError as exc:
            raise RuntimeError(f"Supabase deletion failed ({exc.code})") from exc

    def list_prefix(self, prefix: str) -> list[dict[str, Any]]:
        if not self.enabled:
            return []
        payload = json.dumps({
            "prefix": prefix,
            "limit": 1000,
            "offset": 0,
            "sortBy": {"column": "name", "order": "asc"},
        }).encode("utf-8")
        request = Request(
            f"{self.url}/storage/v1/object/list/{quote(self.bucket, safe='')}",
            data=payload,
            headers=self._headers(**{"Content-Type": "application/json"}),
            method="POST",
        )
        try:
            raw = self._request(request)
            data = json.loads(raw.decode("utf-8"))
            return data if isinstance(data, list) else []
        except HTTPError as exc:
            raise RuntimeError(f"Supabase list failed ({exc.code}) for {prefix}") from exc


def _safe_relative(path: Path) -> str:
    relative = path.as_posix().lstrip("/")
    if not relative or relative.startswith("../") or "/../" in relative:
        raise ValueError("Unsafe workspace path")
    return relative


def _file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _workspace_files(workspace_dir: Path) -> dict[str, dict[str, Any]]:
    files: dict[str, dict[str, Any]] = {}
    for path in workspace_dir.rglob("*"):
        if not path.is_file() or any(part in _IGNORED_PARTS for part in path.parts):
            continue
        relative = _safe_relative(path.relative_to(workspace_dir))
        if relative == _MANIFEST_NAME:
            continue
        files[relative] = {"sha256": _file_hash(path), "size": path.stat().st_size}
    return files


def _manifest_path(slug: str) -> str:
    return f"workspaces/{slug}/{_MANIFEST_NAME}"


def _load_remote_manifest(storage: SupabaseWorkspaceStorage, slug: str) -> dict[str, Any] | None:
    raw = storage.get_bytes(_manifest_path(slug))
    if not raw:
        return None
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return None
    return value if isinstance(value, dict) else None


def sync_workspace_to_supabase(slug: str) -> dict[str, int | bool]:
    """Upload only changed workspace files and publish a manifest last."""
    storage = SupabaseWorkspaceStorage()
    if not storage.enabled:
        return {"enabled": False, "uploaded": 0, "deleted": 0}

    workspace_dir = WORKSPACES_ROOT / slug
    if not workspace_dir.is_dir():
        raise FileNotFoundError(f"Workspace '{slug}' is not available locally")

    started = time.monotonic()
    local_files = _workspace_files(workspace_dir)
    remote_manifest = _load_remote_manifest(storage, slug) or {}
    remote_files = remote_manifest.get("files") if isinstance(remote_manifest.get("files"), dict) else {}
    uploaded = 0

    for relative, info in local_files.items():
        remote_info = remote_files.get(relative)
        if isinstance(remote_info, dict) and remote_info.get("sha256") == info["sha256"]:
            continue
        path = workspace_dir / relative
        content_type = mimetypes.guess_type(path.name)[0]
        storage.put_bytes(f"workspaces/{slug}/{relative}", path.read_bytes(), content_type)
        uploaded += 1

    removed = [relative for relative in remote_files if relative not in local_files]
    if removed:
        storage.delete_objects([f"workspaces/{slug}/{relative}" for relative in removed])

    summary = _workspace_summary(workspace_dir, local_files)
    manifest = {
        "version": 1,
        "workspace_slug": slug,
        "updated_at": time.time(),
        "files": local_files,
        "summary": summary,
    }
    storage.put_bytes(_manifest_path(slug), json.dumps(manifest, separators=(",", ":")).encode("utf-8"), "application/json")
    logger.info("workspace_sync slug=%s uploaded=%s deleted=%s duration_ms=%s", slug, uploaded, len(removed), round((time.monotonic() - started) * 1000))
    return {"enabled": True, "uploaded": uploaded, "deleted": len(removed)}


def restore_workspace_from_supabase(slug: str) -> bool:
    """Restore a complete workspace atomically. Returns False when absent."""
    storage = SupabaseWorkspaceStorage()
    if not storage.enabled:
        return False
    manifest = _load_remote_manifest(storage, slug)
    if not manifest:
        return False
    files = manifest.get("files")
    if not isinstance(files, dict):
        raise RuntimeError(f"Remote workspace '{slug}' has an invalid manifest")

    started = time.monotonic()
    target = WORKSPACES_ROOT / slug
    staging = Path(tempfile.mkdtemp(prefix=f".restore-{slug}-", dir=WORKSPACES_ROOT))
    try:
        for relative in files:
            safe_relative = _safe_relative(Path(relative))
            content = storage.get_bytes(f"workspaces/{slug}/{safe_relative}")
            if content is None:
                raise RuntimeError(f"Remote workspace '{slug}' is missing {safe_relative}")
            destination = staging / safe_relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(content)
        if target.exists():
            return True
        staging.replace(target)
        logger.info("workspace_restore slug=%s files=%s duration_ms=%s", slug, len(files), round((time.monotonic() - started) * 1000))
        return True
    finally:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)


def remote_workspace_summaries() -> dict[str, dict[str, Any]]:
    """Fetch lightweight remote summaries without restoring page trees."""
    storage = SupabaseWorkspaceStorage()
    if not storage.enabled:
        return {}
    summaries: dict[str, dict[str, Any]] = {}
    for entry in storage.list_prefix("workspaces/"):
        slug = str(entry.get("name") or "").strip("/")
        if not slug or "/" in slug:
            continue
        manifest = _load_remote_manifest(storage, slug)
        if isinstance(manifest, dict):
            summary = manifest.get("summary")
            if isinstance(summary, dict):
                summaries[slug] = summary
    return summaries


def delete_workspace_from_supabase(slug: str) -> None:
    """Delete a remotely persisted workspace after a confirmed local delete."""
    storage = SupabaseWorkspaceStorage()
    if not storage.enabled:
        return
    manifest = _load_remote_manifest(storage, slug) or {}
    files = manifest.get("files") if isinstance(manifest.get("files"), dict) else {}
    paths = [f"workspaces/{slug}/{relative}" for relative in files]
    paths.append(_manifest_path(slug))
    storage.delete_objects(paths)


def _workspace_summary(workspace_dir: Path, files: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
    """Build the small dashboard payload stored in the workspace manifest."""
    try:
        metadata = json.loads((workspace_dir / "metadata.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        metadata = {}
    counts = {"university": 0, "courses": 0, "specializations": 0, "blogs": 0}
    for relative in (files or _workspace_files(workspace_dir)):
        if relative == "University/source.json":
            counts["university"] = 1
        elif relative.startswith("Courses/") and relative.endswith("/source.json"):
            counts["courses"] += 1
        elif relative.startswith("Specializations/") and relative.endswith("/source.json"):
            counts["specializations"] += 1
        elif relative.startswith("Blogs/") and relative.endswith("/source.json"):
            counts["blogs"] += 1
    return {
        "slug": workspace_dir.name,
        "name": metadata.get("university_name") or workspace_dir.name.replace("-", " ").title(),
        "last_compiled_at": metadata.get("last_compiled_at"),
        "created_at": metadata.get("created_at"),
        "branding": metadata.get("branding") or {"logo": "", "favicon": ""},
        "site": metadata.get("site") or {"primary_domain": "", "default_og_image": ""},
        "counts": counts,
        "status": "built" if metadata.get("last_compiled_at") else "draft",
    }
