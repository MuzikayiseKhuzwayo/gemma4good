import os
import time
import threading
from typing import List, Optional, Callable
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent, FileDeletedEvent

from semantic_fs.vector_store import SemanticFileSystem
from semantic_fs.knowledge_graph import AssociativeKnowledgeGraph

SUPPORTED_EXTENSIONS = {
    ".txt", ".md", ".py", ".json", ".csv", ".log",
    ".js", ".ts", ".html", ".css", ".rst", ".yaml", ".yml"
}

class AOSFileEventHandler(FileSystemEventHandler):
    """
    Handles live filesystem events and dispatches incremental indexing.
    """

    def __init__(
        self,
        sfs: SemanticFileSystem,
        kg: Optional[AssociativeKnowledgeGraph] = None,
        debounce_seconds: float = 1.0
    ):
        super().__init__()
        self.sfs = sfs
        self.kg = kg
        self.debounce_seconds = debounce_seconds
        self._pending_updates = {}
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._worker_thread = threading.Thread(target=self._debounce_worker, daemon=True)
        self._worker_thread.start()

    def _is_supported(self, path: str) -> bool:
        if os.path.basename(path).startswith("."):
            return False
        if "__pycache__" in path or ".git" in path or "node_modules" in path:
            return False
        ext = os.path.splitext(path)[1].lower()
        return ext in SUPPORTED_EXTENSIONS

    def on_created(self, event):
        if not event.is_directory and self._is_supported(event.src_path):
            self._queue_file(event.src_path, "upsert")

    def on_modified(self, event):
        if not event.is_directory and self._is_supported(event.src_path):
            self._queue_file(event.src_path, "upsert")

    def on_deleted(self, event):
        if not event.is_directory and self._is_supported(event.src_path):
            self._queue_file(event.src_path, "delete")

    def _queue_file(self, path: str, action: str):
        with self._lock:
            self._pending_updates[path] = (action, time.time() + self.debounce_seconds)

    def _debounce_worker(self):
        while not self._stop_event.is_set():
            time.sleep(0.5)
            now = time.time()
            to_process = []

            with self._lock:
                for path, (action, due_time) in list(self._pending_updates.items()):
                    if now >= due_time:
                        to_process.append((path, action))
                        del self._pending_updates[path]

            for path, action in to_process:
                try:
                    if action == "upsert" and os.path.exists(path):
                        self._index_file(path)
                    elif action == "delete":
                        self.sfs.delete(path)
                        print(f"[Watchdog] Removed deleted file from index: {path}")
                except Exception as e:
                    print(f"[Watchdog] Error indexing {path}: {e}")

    def _index_file(self, path: str):
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            if not content.strip():
                return

            mtime = os.path.getmtime(path)
            self.sfs.vectorize_and_store(path, content, metadata={"mtime": mtime})

            if self.kg:
                self.kg.extract_and_ingest(content, source_context=os.path.basename(path))

            print(f"[Watchdog] Continuous ingestion completed: {path}")
        except Exception as e:
            print(f"[Watchdog] Failed to read file {path}: {e}")

    def stop(self):
        self._stop_event.set()


class AOSFileSystemWatchdog:
    """
    Phase 2: Live Filesystem Watchdog & Continuous Ingestion.
    Monitors host user directories and automatically synchronizes
    text/markdown/code into the Semantic File System and Knowledge Graph.
    """

    def __init__(
        self,
        sfs: SemanticFileSystem,
        kg: Optional[AssociativeKnowledgeGraph] = None,
        watch_paths: Optional[List[str]] = None
    ):
        self.sfs = sfs
        self.kg = kg
        self.watch_paths = watch_paths or []
        self.observer = Observer()
        self.handler = AOSFileEventHandler(sfs=self.sfs, kg=self.kg)
        self.is_running = False

    def add_watch_path(self, path: str):
        """Adds a path to be monitored if it exists."""
        abs_path = os.path.abspath(path)
        if os.path.exists(abs_path) and abs_path not in self.watch_paths:
            self.watch_paths.append(abs_path)
            if self.is_running:
                self.observer.schedule(self.handler, abs_path, recursive=True)
                print(f"[Watchdog] Monitoring attached to: {abs_path}")

    def start(self):
        """Starts background file monitoring across all configured paths."""
        if self.is_running:
            return

        for path in self.watch_paths:
            if os.path.exists(path):
                self.observer.schedule(self.handler, path, recursive=True)
                print(f"[Watchdog] Live monitor active on: {path}")

        self.observer.start()
        self.is_running = True

    def stop(self):
        """Stops the watchdog observer gracefully."""
        if not self.is_running:
            return
        self.handler.stop()
        self.observer.stop()
        self.observer.join()
        self.is_running = False
        print("[Watchdog] Live filesystem monitor stopped.")
