"""Local workspace-cache lifecycle backed by optional Supabase Storage."""

from __future__ import annotations

import logging
import shutil
import threading
import time
from collections import defaultdict
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from workspace.manager import WORKSPACES_ROOT, list_workspaces, workspace_lock
from workspace.supabase_storage import SupabaseWorkspaceStorage, restore_workspace_from_supabase, sync_workspace_to_supabase


logger = logging.getLogger(__name__)
DEFAULT_IDLE_SECONDS = 10 * 60

_state_lock = threading.RLock()
_workspace_state: dict[str, dict[str, float | bool | int]] = defaultdict(
    lambda: {"last_activity": time.monotonic(), "dirty": False, "in_use": 0}
)


def storage_enabled() -> bool:
    return SupabaseWorkspaceStorage().enabled


def ensure_workspace_local(slug: str) -> bool:
    """Restore a missing workspace; returns whether it is now available."""
    slug = slug.lower().strip()
    path = WORKSPACES_ROOT / slug
    if path.is_dir():
        mark_workspace_activity(slug)
        return True
    restored = restore_workspace_from_supabase(slug)
    if restored:
        from workspace.compiler import invalidate_workspace_index
        invalidate_workspace_index(slug)
        mark_workspace_activity(slug)
    return restored


def mark_workspace_activity(slug: str) -> None:
    with _state_lock:
        _workspace_state[slug.lower().strip()]["last_activity"] = time.monotonic()


def mark_workspace_dirty(slug: str) -> None:
    with _state_lock:
        state = _workspace_state[slug.lower().strip()]
        state["dirty"] = True
        state["last_activity"] = time.monotonic()


def register_local_workspaces() -> None:
    """Treat workspaces present at process start as cache entries too."""
    for slug in list_workspaces():
        mark_workspace_activity(slug)


@contextmanager
def workspace_in_use(slug: str) -> Iterator[None]:
    slug = slug.lower().strip()
    with _state_lock:
        state = _workspace_state[slug]
        state["in_use"] = int(state["in_use"]) + 1
        state["last_activity"] = time.monotonic()
    try:
        yield
    finally:
        with _state_lock:
            state = _workspace_state[slug]
            state["in_use"] = max(0, int(state["in_use"]) - 1)
            state["last_activity"] = time.monotonic()


def sync_workspace(slug: str) -> dict:
    """Synchronize a dirty workspace. Failed uploads leave it untouched."""
    slug = slug.lower().strip()
    if not storage_enabled():
        return {"enabled": False, "uploaded": 0, "deleted": 0}
    result = sync_workspace_to_supabase(slug)
    with _state_lock:
        _workspace_state[slug]["dirty"] = False
        _workspace_state[slug]["last_activity"] = time.monotonic()
    return result


def cleanup_inactive_workspaces(idle_seconds: int = DEFAULT_IDLE_SECONDS) -> list[str]:
    """Safely sync and evict inactive local workspaces when storage is enabled."""
    if not storage_enabled():
        return []
    now = time.monotonic()
    evicted: list[str] = []
    with _state_lock:
        candidates = [
            slug for slug, state in _workspace_state.items()
            if int(state["in_use"]) == 0 and now - float(state["last_activity"]) >= idle_seconds
        ]
    for slug in candidates:
        path = WORKSPACES_ROOT / slug
        if not path.is_dir():
            continue
        try:
            # Sync even if state was not marked dirty: this covers a process
            # restart or a file changed by a maintenance command.
            # The workspace lock prevents cleanup from swapping/deleting files
            # while this process is compiling or exporting the same workspace.
            with workspace_lock(slug):
                result = sync_workspace(slug)
                shutil.rmtree(path)
                from workspace.compiler import invalidate_workspace_index
                invalidate_workspace_index(slug)
                evicted.append(slug)
                logger.info("workspace_cleanup slug=%s uploaded=%s deleted=%s", slug, result.get("uploaded"), result.get("deleted"))
        except Exception:
            logger.exception("workspace_cleanup_failed slug=%s; local files retained", slug)
    return evicted


def flush_cached_workspaces() -> list[str]:
    """Best-effort shutdown sync; failures deliberately keep local files."""
    if not storage_enabled():
        return []
    with _state_lock:
        slugs = [slug for slug, state in _workspace_state.items() if bool(state["dirty"])]
    synced: list[str] = []
    for slug in slugs:
        try:
            sync_workspace(slug)
            synced.append(slug)
        except Exception:
            logger.exception("workspace_shutdown_sync_failed slug=%s", slug)
    return synced
