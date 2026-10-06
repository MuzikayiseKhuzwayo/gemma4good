import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
import time
import json
import unittest
import tempfile
import shutil

# Phase 1 imports
from aos_kernel.structured_grammar import StructuredGrammarEnforcer
from aos_kernel.dual_kernel import GemmaMicroKernel, GemmaDeepKernel, SpeculativeDualKernelRouter
from aos_kernel.quantized_engine import QuantizedInferenceEngine
from aos_kernel.inference import GemmaLatentKernel

# Phase 2 imports
from semantic_fs.vector_store import SemanticFileSystem, LocalTextVectorizer
from semantic_fs.knowledge_graph import AssociativeKnowledgeGraph
from semantic_fs.watchdog import AOSFileSystemWatchdog
from aos_kernel.context_manager import ContextBudgetManager

# Phase 3 imports
from mock_os.sandbox import SandboxedExecutionRuntime
from mock_os.security import CapabilitySecurityManager, CapabilityType
from shell_agent.native_host import NativeHostAutomation
from shell_agent.api_mapper import ShellAgent

# Phase 4 imports
from generative_ui.dsl import GenerativeUIDSL
from generative_ui.stream_renderer import GenerativeUIStreamRenderer
from mesh_swarm.p2p_mesh import AOSMeshSwarm


class TestPhase1EdgeInference(unittest.TestCase):
    def test_structured_grammar_repair(self):
        malformed_json = """
        Here is the JSON you requested:
        ```json
        [
            {
                "thought_process": "Writing notes",
                "type": "WRITE_FILE",
                "payload": {"path": "/notes/test.txt", "content": "Hello"}
            },
        ]
        ```
        Hope this helps!
        """
        intents = StructuredGrammarEnforcer.parse_and_validate(malformed_json)
        self.assertEqual(len(intents), 1)
        self.assertEqual(intents[0]["type"], "WRITE_FILE")
        self.assertEqual(intents[0]["payload"]["path"], "/notes/test.txt")

    def test_micro_kernel_latency_and_dispatch(self):
        micro = GemmaMicroKernel()
        prompt = "Write a file at /notes/todo.txt with the content 'Buy milk'."
        intents = micro.classify_and_dispatch(prompt)
        self.assertIsNotNone(intents)
        self.assertEqual(len(intents), 1)
        self.assertEqual(intents[0]["type"], "WRITE_FILE")
        # Micro kernel latency must be sub-50ms (typically <2ms)
        self.assertLess(micro.latency_ms, 50.0)

    def test_speculative_routing(self):
        micro = GemmaMicroKernel()
        deep = GemmaDeepKernel(mode="mock")
        router = SpeculativeDualKernelRouter(micro, deep)

        # Simple prompt -> micro_kernel
        simple_res, routed = router.route("Read the file at /test.txt.")
        self.assertEqual(routed, "micro_kernel")

        # Complex reasoning prompt -> deep_kernel
        complex_res, routed = router.route("Analyze and summarize why Alice was late and compare with Bob.")
        self.assertEqual(routed, "deep_kernel")


class TestPhase2SemanticFSAndMemory(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_sfs.db")
        self.kg_path = os.path.join(self.temp_dir, "test_kg.db")
        self.sfs = SemanticFileSystem(db_path=self.db_path)
        self.kg = AssociativeKnowledgeGraph(db_path=self.kg_path)

    def tearDown(self):
        import gc
        gc.collect()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_vector_store_indexing_and_retrieval(self):
        self.sfs.vectorize_and_store("/notes/quantum.txt", "Quantum entanglement and photon spin dynamics in physics.")
        self.sfs.vectorize_and_store("/notes/recipe.txt", "Delicious chocolate cake recipe with flour and sugar.")

        results = self.sfs.retrieve("quantum physics dynamics")
        self.assertTrue(len(results) > 0)
        self.assertEqual(results[0]["path"], "/notes/quantum.txt")

    def test_associative_knowledge_graph(self):
        text = "Had a meeting with Alice regarding Physics Exam yesterday."
        triplets = self.kg.extract_and_ingest(text)
        self.assertTrue(len(triplets) > 0)

        answer = self.kg.answer_associative_query("Who did I talk to about Physics Exam?")
        self.assertIn("Alice", answer)

    def test_hierarchical_context_paging(self):
        cm = ContextBudgetManager(max_tokens=80, sfs=self.sfs)
        # Fill L1 context to trigger swap
        for i in range(10):
            cm.append_l1(f"Turn {i}: System executed task number {i} regarding biology research.")

        # L1 should have evicted older items to L2
        self.assertGreater(len(cm.l2_episodic_memory), 0)
        self.assertGreater(cm.stats["context_swaps"], 0)

        # Trigger Page Fault to restore paged memory into L1
        paged = cm.page_fault("biology research")
        self.assertGreater(len(paged), 0)
        self.assertIn("biology research", cm.active_context[0].lower())


class TestPhase3SandboxedExecutionAndSecurity(unittest.TestCase):
    def setUp(self):
        self.sandbox = SandboxedExecutionRuntime()
        self.security = CapabilitySecurityManager()

    def test_sandboxed_python_execution(self):
        code = "result = sum([x * 2 for x in range(10)])\nprint(f'Computed: {result}')"
        out = self.sandbox.execute_python(code)
        self.assertEqual(out["status"], "SUCCESS")
        self.assertEqual(out["result"], 90)
        self.assertIn("Computed: 90", out["stdout"])

    def test_capability_security_policy(self):
        # 1. Sandbox FS operation is auto-approved
        sandbox_req = self.security.evaluate_request(CapabilityType.SANDBOX_FS, "/tmp/sandbox.txt", is_sandbox=True)
        self.assertTrue(sandbox_req["approved"])
        self.assertFalse(sandbox_req["requires_prompt"])

        # 2. Host FS Write requires diff preview & operator approval
        host_req = self.security.evaluate_request(
            CapabilityType.HOST_FS_WRITE,
            "C:/important_system_file.cfg",
            {"content": "new_config_data = 1"},
            is_sandbox=False
        )
        self.assertFalse(host_req["approved"])
        self.assertTrue(host_req["requires_prompt"])
        self.assertIn("diff_preview", host_req)

        # Approve the pending token
        req_id = host_req["request_id"]
        approved = self.security.approve_request(req_id)
        self.assertTrue(approved)

    def test_shell_agent_extended_intents(self):
        agent = ShellAgent(use_virtual_env=True)
        # Execute sandboxed code intent
        res = agent.execute_intent("RUN_SANDBOX_CODE", {"code": "result = 42"})
        self.assertEqual(res["result"], 42)

        # Execute host telemetry query
        stats = agent.execute_intent("HOST_AUTOMATE", {"action": "stats"})
        self.assertEqual(stats["status"], "SUCCESS")


class TestPhase4GenerativeUIAndMesh(unittest.TestCase):
    def test_generative_ui_dsl(self):
        table = GenerativeUIDSL.table("Files", ["Name", "Size"], [["a.txt", "1KB"], ["b.txt", "2KB"]])
        self.assertEqual(table["widget"], "TABLE")
        self.assertEqual(len(table["rows"]), 2)

        approval = GenerativeUIDSL.approval_card("req-123", "HOST_WRITE", "/config.sys", "+ new line")
        self.assertEqual(approval["widget"], "APPROVAL_CARD")
        self.assertEqual(approval["request_id"], "req-123")

    def test_sse_stream_renderer(self):
        sse = GenerativeUIStreamRenderer.format_sse_event("widget", {"type": "CARD"})
        self.assertTrue(sse.startswith("data: "))
        self.assertTrue(sse.endswith("\n\n"))
        parsed = json.loads(sse.replace("data: ", "").strip())
        self.assertEqual(parsed["event"], "widget")

    def test_p2p_mesh_swarm_lifecycle(self):
        node = AOSMeshSwarm(node_id="test-node-1", broadcast_port=52345)
        node.start()
        time.sleep(0.5)
        self.assertTrue(node.is_running)
        node.stop()
        self.assertFalse(node.is_running)

    def test_knowledge_graph_snapshot(self):
        kg = AssociativeKnowledgeGraph()
        kg.add_relation("Alice", "Physics Exam", "STUDIES", "PERSON", "TOPIC")
        snapshot = kg.get_graph_snapshot(limit=10)
        self.assertIn("nodes", snapshot)
        self.assertIn("edges", snapshot)
        self.assertTrue(any(e["source"] == "Alice" for e in snapshot["edges"]))

    def test_unified_gateway_components(self):
        import server
        self.assertIsNotNone(server.AOSHandler)
        self.assertIsNotNone(server.run_server)


if __name__ == "__main__":
    unittest.main(verbosity=2)
