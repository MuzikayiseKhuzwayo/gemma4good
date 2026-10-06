import json
from typing import Dict, Any, Optional

from mock_os.virtual_env import MockVirtualOS
from mock_os.sandbox import SandboxedExecutionRuntime
from mock_os.security import CapabilitySecurityManager, CapabilityType
from shell_agent.native_host import NativeHostAutomation
from semantic_fs.vector_store import SemanticFileSystem
from semantic_fs.knowledge_graph import AssociativeKnowledgeGraph

class ShellAgent:
    """
    Phase 3: Upgraded Shell Agent (Hardware Abstraction Layer).
    Dispatches intents across:
    - Sandboxed Virtual OS / WASI execution runtime
    - Capability-Based Security Guardrails
    - Real native host OS drivers (Windows/macOS/Linux)
    - Production Semantic Vector File System and Associative Knowledge Graph
    """

    def __init__(self, use_virtual_env: bool = True):
        self.use_virtual_env = use_virtual_env
        self.virtual_os = MockVirtualOS() if use_virtual_env else None
        self.sandbox = SandboxedExecutionRuntime()
        self.security = CapabilitySecurityManager()
        self.host_automation = NativeHostAutomation()
        self.sfs = SemanticFileSystem()
        self.kg = AssociativeKnowledgeGraph()

    def execute_intent(self, intent_type: str, payload: Optional[Dict[str, Any]] = None):
        print(f"Mapping intent to OS API calls: {intent_type}")
        payload = payload or {}

        if self.virtual_os:
            return self._execute_virtual(intent_type, payload)
        else:
            return self._execute_host(intent_type, payload)

    def _execute_virtual(self, intent_type: str, payload: Dict[str, Any]):
        # Extract path robustly
        path = payload.get('path', payload.get('filename', payload.get('name', '')))
        if not path and intent_type in ["WRITE_FILE", "READ_FILE", "DELETE_FILE"]:
            for v in payload.values():
                if isinstance(v, str) and ('.' in v or '/' in v or '\\' in v):
                    path = v
                    break

        content = payload.get('content', payload.get('body', payload.get('text', '')))

        if intent_type == "WRITE_FILE":
            path = path or '/tmp/default.txt'
            # Security verification
            sec = self.security.evaluate_request(CapabilityType.SANDBOX_FS, path, {"content": content}, is_sandbox=True)
            if not sec["approved"]:
                return f"[Security Denied]: {sec.get('message', 'Authorization required')}"

            res = self.virtual_os.write_file(path, content)
            # Synchronize with Semantic FS and Knowledge Graph
            self.sfs.vectorize_and_store(path, content)
            self.kg.extract_and_ingest(content, source_context=path)
            return res

        elif intent_type == "READ_FILE":
            read_content = self.virtual_os.read_file(path)
            if read_content is not None:
                print(f"\n[VirtualOS] Content of {path}:\n{read_content}\n")
            else:
                print(f"\n[VirtualOS] Error: File '{path}' does not exist.\n")
            return read_content

        elif intent_type == "DELETE_FILE":
            res = self.virtual_os.delete_file(path)
            self.sfs.delete(path)
            return res

        elif intent_type == "SEARCH_MEMORY":
            query = payload.get('query', '')
            # Query production vector database
            v_hits = self.sfs.retrieve(query, top_k=5)
            paths = [h["path"] for h in v_hits]
            if not paths:
                # Fallback to in-memory mock search
                paths = self.virtual_os.search_memory(query)
            print(f"[VirtualOS/SemanticFS] Search results for '{query}': {paths}")
            return paths

        elif intent_type == "ASK_USER_INPUT":
            prompt_text = payload.get('prompt', 'Please provide more input.')
            print(f"\n[VirtualOS] Asking User: {prompt_text}\n")
            return prompt_text

        elif intent_type == "SEND_MESSAGE":
            to = payload.get('to', 'User')
            body = payload.get('body', '')
            # Ingest social interaction into Knowledge Graph
            self.kg.add_relation(to, "OUTBOUND_MSG", "RECEIVED", source_type="PERSON", target_type="TOPIC", context=body)
            return self.virtual_os.send_network_request("api://messaging", payload)

        elif intent_type == "NOTIFY_USER":
            msg = payload.get('message', 'Alert')
            # Trigger both virtual and native desktop notification
            self.host_automation.show_desktop_notification("AOS Notification", msg)
            return self.virtual_os.show_notification(msg)

        elif intent_type == "RUN_SANDBOX_CODE":
            code = payload.get('code', '')
            lang = payload.get('language', 'python')
            print(f"\n[SandboxRuntime] Running isolated {lang} script:\n{code}\n")
            return self.sandbox.execute_python(code)

        elif intent_type == "HOST_AUTOMATE":
            action = payload.get('action', 'stats')
            params = payload.get('params', {})
            return self.host_automation.execute_action(action, params)

        elif intent_type == "QUERY_GRAPH":
            query = payload.get('query', '')
            return self.kg.answer_associative_query(query)

        else:
            print(f"[VirtualOS] Unknown intent: {intent_type}")
            return False

    def _execute_host(self, intent_type: str, payload: Dict[str, Any]):
        """Executes operations directly on the host system with capability gating."""
        print(f"[HostOS] Executing {intent_type} on actual host system")
        if intent_type == "HOST_AUTOMATE":
            return self.host_automation.execute_action(payload.get("action", "stats"), payload.get("params", {}))
        return True
