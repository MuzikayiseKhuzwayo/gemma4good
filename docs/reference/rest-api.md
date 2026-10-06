# Reference: HTTP Master Gateway REST & SSE API

This specification documents the HTTP interface exposed by [`server.py`](https://github.com/MuzikayiseKhuzwayo/gemma4good/blob/main/server.py). The server runs on port `8000` by default and connects the client UI Cockpit, CLI, and external services to the Latent Kernel, Security HAL, and Semantic Storage.

---

## 1. Global Server Properties

* **Base URL:** `http://127.0.0.1:8000`
* **Default Port:** `8000`
* **Concurrency:** `ThreadingHTTPServer` (Multi-threaded asynchronous request & SSE dispatch)
* **CORS Support:** Permissive headers enabled (`Access-Control-Allow-Origin: *`, `Access-Control-Allow-Methods: GET, POST, OPTIONS`).
* **Static File Serving:** 
  * `/` and `/index.html` -> Serves the AOS Studio Cockpit (`generative_ui/web/`)
  * `/docs/...` -> Directly serves markdown documentation files from `docs/`
  * `/style.css`, `/script.js` -> Cockpit styling and interactive scripts

---

## 2. API Endpoints

### 2.1. System Health & Diagnostics

#### `GET /api/health`
Returns live daemon health, uptime, and kernel execution mode.
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "system": "Agentic Operating System (AOS)",
  "kernel_mode": "google_genai",
  "uptime_seconds": 42.15
}
```

#### `GET /api/system/stats`
Returns host OS telemetry and 3-tier hierarchical context memory pager stats.
```json
{
  "telemetry": {
    "os": "Windows",
    "cpu_count": 16,
    "ram_total_gb": 31.85,
    "ram_used_gb": 18.22,
    "ram_percent": 57.2
  },
  "memory_tiers": {
    "l1_active_turns": 4,
    "l1_token_usage": 450,
    "l1_max_budget": 8192,
    "l2_episodic_entries": 1,
    "total_page_faults": 2,
    "total_swaps": 1
  }
}
```

---

### 2.2. Intent & ReAct Execution

#### `POST /api/intent`
Submits a user prompt to the Speculative Dual-Kernel router, validates schemas with `StructuredGrammarEnforcer`, dispatches through the Shell Agent HAL, and broadcasts live telemetry to connected SSE clients.

* **Request Body:**
  ```json
  {
    "intent": "Send a message to Alice saying I will be late, and save a note."
  }
  ```
* **Response Body:**
  ```json
  {
    "responses": [
      "[SEND_MESSAGE] -> {\"to\": \"Alice\", \"body\": \"I will be late\"}",
      "[WRITE_FILE] -> {\"path\": \"/docs/notes/late.txt\", \"content\": \"Told Alice I'd be late.\"}",
      "🤖 Result:\n✓ Outbound message dispatched.\n✓ File has been successfully created and saved."
    ],
    "widgets": []
  }
  ```

#### `GET /api/history`
Returns persistent conversation history.
```json
{
  "history": [
    {"role": "user", "text": "Save note to /test.txt"},
    {"role": "system", "text": "✓ File has been successfully created and saved."}
  ]
}
```

#### `POST /api/new_chat`
Clears L1 active context memory and safely archives session history into `data/history_archive/`.
```json
{
  "status": "success"
}
```

---

### 2.3. Capability-Based Security Governance

#### `GET /api/capabilities/pending`
Lists all actions requiring operator authorization (e.g. host filesystem write, outbound network, host automation).
```json
{
  "pending": [
    {
      "request_id": "8f3b12a0",
      "capability": "HOST_FS_WRITE",
      "resource": "C:/system.cfg",
      "diff": "--- a/system.cfg\n+++ b/system.cfg\n@@ -1 +1 @@\n-debug=0\n+debug=1",
      "status": "PENDING"
    }
  ]
}
```

#### `POST /api/capabilities/approve`
Approves or denies a pending capability authorization token.
* **Request Body:**
  ```json
  {
    "request_id": "8f3b12a0",
    "action": "approve"
  }
  ```
* **Response Body:**
  ```json
  {
    "status": "SUCCESS",
    "request_id": "8f3b12a0",
    "action": "approve"
  }
  ```

#### `GET /api/capabilities/audit`
Retrieves recent security authorization audit events.
```json
{
  "audit": [
    {
      "request_id": "8f3b12a0",
      "capability": "HOST_FS_WRITE",
      "resource": "C:/system.cfg",
      "action": "GRANTED",
      "reason": "Token cap_tok_8f3b12a0_1791286000",
      "timestamp": 1791286000.12
    }
  ]
}
```

---

### 2.4. Semantic Vector Store & Knowledge Graph

#### `GET /api/memory/search?q={query}&k={top_k}`
Queries 128-dimensional normalized dense vectors in SQLite.
```json
{
  "query": "quantum entanglement",
  "results": [
    {
      "id": 1,
      "path": "/notes/quantum.txt",
      "chunk_index": 0,
      "content": "Quantum entanglement and photon spin dynamics in physics.",
      "similarity": 0.8412
    }
  ]
}
```

#### `GET /api/memory/files`
Lists all documents currently indexed in the Semantic File System.
```json
{
  "files": ["/notes/quantum.txt", "/notes/recipe.txt"],
  "count": 2
}
```

#### `GET /api/graph/snapshot?limit={limit}`
Returns nodes and relational directed edges for interactive knowledge graph visualization.
```json
{
  "nodes": [
    {"id": 1, "name": "Alice", "type": "PERSON"},
    {"id": 2, "name": "Physics Exam", "type": "TOPIC"}
  ],
  "edges": [
    {"id": 1, "source": "Alice", "target": "Physics Exam", "relation": "DISCUSSED", "context": "Meeting with Alice regarding Physics Exam"}
  ]
}
```

#### `GET /api/graph/query?q={natural_language_query}`
Executes relational graph traversal to answer questions like *"Who did I talk to about Physics Exam?"*.
```json
{
  "query": "Who did I talk to about Physics Exam?",
  "answer": "Knowledge Graph Associations:\n• Alice [PERSON] --(DISCUSSED)--> Physics Exam [TOPIC]"
}
```

---

### 2.5. Isolated Code Sandbox Runtime

#### `POST /api/sandbox/run`
Executes Python scripts in an isolated execution sandbox with stdout/stderr capture and timeout limits.

* **Request Body:**
  ```json
  {
    "code": "result = sum([x * 2 for x in range(10)])\nprint(f'Computed: {result}')"
  }
  ```
* **Response Body:**
  ```json
  {
    "status": "SUCCESS",
    "stdout": "Computed: 90\n",
    "stderr": "",
    "result": 90,
    "duration_ms": 1.25
  }
  ```

---

### 2.6. Sovereign P2P Mesh Swarm

#### `GET /api/swarm/status`
Returns local mesh node identity, UDP broadcast port, and active peers.
```json
{
  "node_id": "aos-node-9a2f",
  "broadcast_port": 5005,
  "peer_count": 0,
  "peers": []
}
```

#### `POST /api/swarm/broadcast`
Broadcasts a decentralized JSON gossip message across the local network mesh.
* **Request Body:**
  ```json
  {
    "message": {
      "type": "GOSSIP",
      "payload": "Peer sync request"
    }
  }
  ```
* **Response Body:**
  ```json
  {
    "status": "SUCCESS",
    "message": "Dispatched across mesh swarm."
  }
  ```

---

### 2.7. Server-Sent Events (SSE) Stream

#### `GET /api/stream`
Establishes an active SSE connection (`Content-Type: text/event-stream`). Emits real-time reasoning events, hardware execution logs, and dynamic UI widgets formatted via `GenerativeUIStreamRenderer`.

* **Events Emitted:**
  * `connected` — Initial handshake.
  * `reasoning` — Real-time intent classification status.
  * `execution_start` — Dispatched intent type and kernel thought monologue.
  * `execution_done` — OS HAL execution verdict.
  * `widget` — Dynamic DSL widget payloads (`TABLE`, `APPROVAL_CARD`, `AUDIO_PLAYER`).
