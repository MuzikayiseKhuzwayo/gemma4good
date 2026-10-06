import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
import sys
import json
import time
import queue
import urllib.parse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from dotenv import load_dotenv

load_dotenv()

from shell_agent.api_mapper import ShellAgent
from semantic_fs.vector_store import SemanticFileSystem
from semantic_fs.knowledge_graph import AssociativeKnowledgeGraph
from semantic_fs.watchdog import AOSFileSystemWatchdog
from aos_kernel.inference import GemmaLatentKernel
from aos_kernel.context_manager import ContextBudgetManager
from generative_ui.dsl import GenerativeUIDSL
from generative_ui.stream_renderer import GenerativeUIStreamRenderer
from mesh_swarm.p2p_mesh import AOSMeshSwarm

# Global state for the server
sfs = None
kg = None
agent = None
inference_engine = None
context_manager = None
watchdog = None
swarm = None
sse_clients = []
server_start_time = time.time()

HISTORY_FILE = "conversation_history.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []

def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)

def broadcast_sse(event_type: str, data: dict):
    msg = GenerativeUIStreamRenderer.format_sse_event(event_type, data)
    for q in list(sse_clients):
        try:
            q.put_nowait(msg)
        except Exception:
            pass

class AOSHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # Default static directory is generative_ui/web
        web_dir = os.path.join(os.path.dirname(__file__), "generative_ui", "web")
        super().__init__(*args, directory=web_dir, **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query_params = urllib.parse.parse_qs(parsed.query)

        # 1. Health check & version
        if path == '/api/health':
            self._send_json(200, {
                "status": "healthy",
                "version": "2.0.0",
                "system": "Agentic Operating System (AOS)",
                "kernel_mode": getattr(inference_engine, "mode", "mock"),
                "uptime_seconds": round(time.time() - server_start_time, 2)
            })

        # 2. Conversation History
        elif path == '/api/history':
            history = load_history()
            self._send_json(200, {"history": history})

        # 3. Capability Governance
        elif path == '/api/capabilities/pending':
            pending = list(agent.security.pending_approvals.values()) if agent else []
            self._send_json(200, {"pending": pending})

        elif path == '/api/capabilities/audit':
            audit_log = agent.security.audit_log if agent else []
            self._send_json(200, {"audit": audit_log[-50:]})

        # 4. Swarm Mesh
        elif path == '/api/swarm/status':
            peers = swarm.get_active_peers() if swarm else []
            self._send_json(200, {
                "node_id": swarm.node_id if swarm else "offline",
                "peers": peers,
                "peer_count": len(peers),
                "broadcast_port": getattr(swarm, "broadcast_port", 5005)
            })

        # 5. System Stats & Context Budget Paging
        elif path == '/api/system/stats':
            telemetry = agent.host_automation.get_system_telemetry() if agent else {}
            mem_stats = context_manager.get_memory_stats() if context_manager else {}
            self._send_json(200, {
                "telemetry": telemetry,
                "memory_tiers": mem_stats
            })

        # 6. Semantic Memory Search
        elif path == '/api/memory/search':
            q = query_params.get("q", [""])[0]
            top_k = int(query_params.get("k", [5])[0])
            results = sfs.retrieve(q, top_k=top_k) if sfs and q else []
            self._send_json(200, {"query": q, "results": results})

        # 7. Semantic Files Index
        elif path == '/api/memory/files':
            indexed = sfs.list_indexed_files() if sfs else []
            self._send_json(200, {"files": indexed, "count": len(indexed)})

        # 8. Knowledge Graph Snapshot
        elif path == '/api/graph/snapshot':
            limit = int(query_params.get("limit", [50])[0])
            snapshot = kg.get_graph_snapshot(limit=limit) if kg else {"nodes": [], "edges": []}
            self._send_json(200, snapshot)

        # 9. Knowledge Graph Natural Language Query
        elif path == '/api/graph/query':
            q = query_params.get("q", [""])[0]
            answer = kg.answer_associative_query(q) if kg and q else "Provide a query parameter 'q'."
            self._send_json(200, {"query": q, "answer": answer})

        # 10. Server-Sent Events (SSE) live connection
        elif path == '/api/stream':
            self.send_response(200)
            self.send_header('Content-type', 'text/event-stream')
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('Connection', 'keep-alive')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            client_queue = queue.Queue()
            sse_clients.append(client_queue)
            try:
                welcome = GenerativeUIStreamRenderer.format_sse_event(
                    "connected",
                    {"status": "ok", "message": "AOS Dynamic Canvas SSE Connected", "time": time.time()}
                )
                self.wfile.write(welcome.encode('utf-8'))
                self.wfile.flush()

                while True:
                    try:
                        msg = client_queue.get(timeout=20.0)
                        self.wfile.write(msg.encode('utf-8'))
                        self.wfile.flush()
                    except queue.Empty:
                        self.wfile.write(b": ping\n\n")
                        self.wfile.flush()
            except (ConnectionResetError, BrokenPipeError):
                pass
            finally:
                if client_queue in sse_clients:
                    sse_clients.remove(client_queue)

        # 11. Static Docs route
        elif path.startswith('/docs/'):
            docs_base = os.path.join(os.path.dirname(__file__), "docs")
            rel_path = path[len('/docs/'):]
            target = os.path.join(docs_base, rel_path)
            if os.path.exists(target) and os.path.isfile(target):
                self._serve_raw_file(target)
            else:
                self.send_error(404, "Documentation file not found")

        # 12. Default static file server from generative_ui/web
        else:
            super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length) if content_length > 0 else b'{}'
        
        try:
            data = json.loads(post_data.decode('utf-8')) if post_data else {}
        except Exception:
            data = {}

        if path == '/api/intent':
            user_intent = data.get("intent", "").strip()

            print(f"\n[API] Received Intent: {user_intent}")
            context_manager.append_l1(f"User: {user_intent}")
            context_string = "\n".join(context_manager.active_context[-5:])

            broadcast_sse("reasoning", {"intent": user_intent, "status": "Parsing via Latent Kernel..."})

            # 1. Parse intent via Speculative Dual-Kernel
            intents = inference_engine.parse_intent(user_intent, context_history=context_string)

            responses = []
            execution_logs = []
            widgets = []

            if not intents:
                responses.append("[AOS] No executable intent recognized. Try stating an action (e.g., 'Save note to notes.txt' or 'Search memory for quantum').")
            else:
                for intent in intents:
                    context_manager.add_intent(150)
                    thought = intent.get("thought_process", "Direct execution.")
                    intent_type = intent.get("type")
                    payload = intent.get("payload", {})

                    broadcast_sse("execution_start", {"intent": intent_type, "thought": thought})

                    if intent_type == "NOTIFY_USER":
                        msg = payload.get("message", "Notification from system.")
                        responses.append(msg)
                        continue

                    try:
                        result = agent.execute_intent(intent_type, payload)
                        execution_logs.append(f"[{intent_type}] Result: {result}")

                        # Check if capability requires operator approval
                        if isinstance(result, str) and "[Security Denied]" in result:
                            for req_id, rec in agent.security.pending_approvals.items():
                                if rec.get("status") == "PENDING":
                                    card = GenerativeUIDSL.approval_card(
                                        request_id=req_id,
                                        capability=rec.get("capability", "SYSTEM"),
                                        resource=rec.get("resource", "File"),
                                        diff_preview=rec.get("diff", "")
                                    )
                                    widgets.append(card)
                                    broadcast_sse("widget", card)

                        payload_str = json.dumps(payload)
                        responses.append(f"[{intent_type}] -> {payload_str}")
                        context_manager.append_l1(f"Kernel: {thought} | OS: {intent_type} -> {result}")

                        # If search results or memory hits, render as interactive table widget
                        if intent_type == "SEARCH_MEMORY" and isinstance(result, list) and result:
                            table = GenerativeUIDSL.table(
                                title=f"Memory Retrieval for '{payload.get('query', '')}'",
                                columns=["Index", "File Path"],
                                rows=[[idx + 1, p] for idx, p in enumerate(result)]
                            )
                            widgets.append(table)
                            broadcast_sse("widget", table)

                        broadcast_sse("execution_done", {"intent": intent_type, "result": str(result)})

                    except Exception as e:
                        execution_logs.append(f"[{intent_type}] Failed: {str(e)}")
                        responses.append(f"[{intent_type}] ❌ Execution failed: {e}")

                # Formulate natural language response
                has_notify = any(i.get("type") == "NOTIFY_USER" for i in intents)
                if execution_logs and not has_notify:
                    nl_response = inference_engine.generate_response(user_intent, execution_logs)
                    responses.append(f"🤖 Result:\n{nl_response}")

            combined_response = "\n\n".join(responses) if responses else "No response generated."

            history = load_history()
            history.append({"role": "user", "text": user_intent})
            history.append({"role": "system", "text": combined_response})
            save_history(history)

            self._send_json(200, {
                "responses": [combined_response],
                "widgets": widgets
            })

        elif path == '/api/capabilities/approve':
            req_id = data.get("request_id")
            action = data.get("action", "approve") # 'approve' or 'deny'

            if action == "approve":
                ok = agent.security.approve_request(req_id)
            else:
                ok = agent.security.deny_request(req_id)

            self._send_json(200, {"status": "SUCCESS" if ok else "ERROR", "request_id": req_id, "action": action})

        elif path == '/api/sandbox/run':
            code = data.get("code", "")
            context_vars = data.get("context", {})
            out = agent.sandbox.execute_python(code, context_vars) if agent else {"status": "ERROR", "message": "Agent not initialized"}
            self._send_json(200, out)

        elif path == '/api/swarm/broadcast':
            message = data.get("message", {})
            if swarm:
                swarm.broadcast(message)
                self._send_json(200, {"status": "SUCCESS", "message": "Dispatched across mesh swarm."})
            else:
                self._send_json(503, {"status": "ERROR", "message": "Swarm mesh offline."})

        elif path == '/api/new_chat':
            if context_manager:
                context_manager.active_context = []
            if os.path.exists(HISTORY_FILE):
                archive_name = f"archive_{int(time.time())}_{HISTORY_FILE}"
                # Archive inside data/ directory instead of cluttering root
                data_dir = os.path.join(os.path.dirname(__file__), "data", "history_archive")
                os.makedirs(data_dir, exist_ok=True)
                os.rename(HISTORY_FILE, os.path.join(data_dir, archive_name))
            self._send_json(200, {"status": "success"})

        else:
            self.send_error(404, "Not Found")

    def _serve_raw_file(self, filepath: str):
        try:
            with open(filepath, 'rb') as f:
                content = f.read()
            self.send_response(200)
            if filepath.endswith('.html'):
                self.send_header('Content-Type', 'text/html; charset=utf-8')
            elif filepath.endswith('.css'):
                self.send_header('Content-Type', 'text/css')
            elif filepath.endswith('.js'):
                self.send_header('Content-Type', 'application/javascript')
            elif filepath.endswith('.json'):
                self.send_header('Content-Type', 'application/json')
            elif filepath.endswith('.md'):
                self.send_header('Content-Type', 'text/markdown; charset=utf-8')
            else:
                self.send_header('Content-Type', 'application/octet-stream')
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_error(500, f"Error reading file: {e}")

    def _send_json(self, status: int, data: dict):
        response_bytes = json.dumps(data, indent=2).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Content-Length', str(len(response_bytes)))
        self.end_headers()
        self.wfile.write(response_bytes)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header("Access-Control-Allow-Headers", "X-Requested-With, Content-type")
        self.end_headers()

def run_server(port=8000, host='0.0.0.0'):
    global sfs, kg, agent, inference_engine, context_manager, watchdog, swarm
    print("=" * 60)
    print("Booting Agentic OS (AOS) Master Gateway...")
    print("=" * 60)

    # Initialize Core Kernel & HAL
    sfs = SemanticFileSystem()
    kg = AssociativeKnowledgeGraph()
    agent = ShellAgent(use_virtual_env=True)
    inference_engine = GemmaLatentKernel(mode="google_genai")
    context_manager = ContextBudgetManager(sfs=sfs)

    # Initialize Live Filesystem Watchdog
    watchdog = AOSFileSystemWatchdog(sfs=sfs, kg=kg)
    notes_dir = os.path.join(os.path.dirname(__file__), "docs")
    watchdog.add_watch_path(notes_dir)
    watchdog.start()

    # Initialize Sovereign P2P Mesh Swarm
    swarm = AOSMeshSwarm()
    swarm.start()

    server_address = (host, port)
    # Using ThreadingHTTPServer for concurrent SSE streaming and REST dispatch
    httpd = ThreadingHTTPServer(server_address, AOSHandler)
    display_host = "127.0.0.1" if host == "0.0.0.0" else host
    print(f"\n[AOS Gateway Online]")
    print(f" • Studio Cockpit:  http://{display_host}:{port}/")
    print(f" • REST API Docs:   http://{display_host}:{port}/docs/reference/rest-api.md")
    print(f" • Telemetry:       http://{display_host}:{port}/api/system/stats")
    print(f" • Health Check:    http://{display_host}:{port}/api/health\n")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        print("\nShutting down AOS Gateway...")
        if watchdog:
            watchdog.stop()
        if swarm:
            swarm.stop()
        httpd.server_close()
        print("AOS Gateway stopped cleanly.")

if __name__ == '__main__':
    port = 8000
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        port = int(sys.argv[1])
    run_server(port=port)
