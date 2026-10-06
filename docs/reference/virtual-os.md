# Reference: MockVirtualOS Sandbox Specification

This document specifies the behavior, methods, and state contracts of the `MockVirtualOS` sandbox defined in [`mock_os/virtual_env.py`](https://github.com/MuzikayiseKhuzwayo/gemma4good/blob/main/mock_os/virtual_env.py).

---

## 1. Overview & Isolation Guarantees

The `MockVirtualOS` simulates core operating system primitives (file system, network layer, notification daemon, and in-memory search) entirely within process memory.

* **Host Safety:** Zero mutations are made to the host machine's physical file system or network stack.
* **Deterministic Inspection:** Exposes complete operational logs for automated validation and assertions.

---

## 2. State Representation

```python
class MockVirtualOS:
    file_system: dict[str, str]    # Map of virtual file paths to string contents
    network_logs: list[dict]        # Log entries for outbound network requests
    active_services: list           # Active virtual background daemons
    notifications: list[str]        # Log of displayed notification messages
```

---

## 3. Public Method Contracts

### `write_file(path: str, content: str) -> bool`
Stores `content` at key `path` in `self.file_system`.
* **Returns:** `True`.

### `read_file(path: str) -> str | None`
Retrieves content stored at `path`.
* **Fuzzy Resolution:** If `path` is not an exact match, searches for keys ending with `path` or keys that `path` ends with (e.g. `/notes/todo.txt` matches `notes/todo.txt`).
* **Returns:** File content string if resolved, `None` if missing.

### `delete_file(path: str) -> bool`
Removes `path` from `self.file_system`.
* **Returns:** `True` if deleted, `False` if not found.

### `search_memory(query: str) -> list[str]`
Performs case-insensitive substring search across all file paths and stored content strings.
* **Returns:** Array of matching virtual file paths.

### `send_network_request(url: str, payload: dict) -> dict`
Simulates dispatching an HTTP/API call to an external service.
* **Appends to:** `self.network_logs`.
* **Returns:** `{"url": url, "payload": payload, "status": "200 OK"}`.

### `show_notification(message: str) -> bool`
Records a system notification in `self.notifications`.
* **Returns:** `True`.

### `get_state_summary() -> dict`
Returns a structural snapshot of sandbox state:
```python
{
    "files_in_system": list(self.file_system.keys()),
    "total_network_requests": len(self.network_logs),
    "total_notifications": len(self.notifications)
}
```
