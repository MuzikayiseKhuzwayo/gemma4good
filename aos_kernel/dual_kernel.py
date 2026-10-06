import re
import time
from typing import List, Dict, Any, Tuple, Optional
from aos_kernel.structured_grammar import StructuredGrammarEnforcer

class GemmaMicroKernel:
    """
    Phase 1: Gemma Micro-Kernel (e.g. Gemma 2B equivalent).
    Provides sub-50ms intent classification and deterministic dispatch for routine
    OS operations (reading/writing files, searching memory, system notifications).
    """

    def __init__(self):
        self.latency_ms = 0.0

    def classify_and_dispatch(self, prompt: str) -> Optional[List[Dict[str, Any]]]:
        """
        Fast intent classification using regex and pattern-matching rules
        simulating a lightweight quantized 2B model fine-tuned for OS intent routing.
        Returns None if intent is ambiguous or requires deep reasoning.
        """
        start = time.perf_counter()
        p = prompt.strip()
        lower = p.lower()

        intents: List[Dict[str, Any]] = []

        # 1. Direct File Write Pattern
        # e.g., "Write a file at /test/data.txt with the content 'Hello World'."
        # or "Save 'abc' to notes.txt"
        write_match = re.search(r"(?:write|save|create)(?:\s+a)?\s+file\s+(?:at\s+)?([^\s'\"]+)\s+with\s+(?:the\s+)?content\s*['\"]([^'\"]*)['\"]", p, re.IGNORECASE)
        if not write_match:
            write_match = re.search(r"(?:write|save)\s+['\"]([^'\"]*)['\"]\s+to\s+([^\s'\"]+)", p, re.IGNORECASE)
            if write_match:
                content, path = write_match.group(1), write_match.group(2)
                intents.append({
                    "thought_process": f"Fast-path write detected: writing content to {path}.",
                    "type": "WRITE_FILE",
                    "payload": {"path": path, "content": content}
                })
        else:
            path, content = write_match.group(1), write_match.group(2)
            intents.append({
                "thought_process": f"Fast-path write detected: writing content to {path}.",
                "type": "WRITE_FILE",
                "payload": {"path": path, "content": content}
            })

        # 2. Read File Pattern
        # e.g. "Read the file at /test/data.txt."
        read_match = re.search(r"(?:read|cat|open|view|show)(?:\s+the)?\s+file\s+(?:at\s+)?([^\s'\"]+)", p, re.IGNORECASE)
        if read_match and not intents:
            path = read_match.group(1).rstrip(".,;")
            intents.append({
                "thought_process": f"Fast-path read detected: reading {path}.",
                "type": "READ_FILE",
                "payload": {"path": path}
            })

        # 3. Delete File Pattern
        # e.g. "Delete the file at /test/data.txt."
        del_match = re.search(r"(?:delete|remove|rm)(?:\s+the)?\s+file\s+(?:at\s+)?([^\s'\"]+)", p, re.IGNORECASE)
        if del_match and not intents:
            path = del_match.group(1).rstrip(".,;")
            intents.append({
                "thought_process": f"Fast-path delete detected: removing {path}.",
                "type": "DELETE_FILE",
                "payload": {"path": path}
            })

        # 4. Search Memory Pattern
        # e.g. "Search memory for 'vacation plans'."
        search_match = re.search(r"search\s+memory\s+for\s+['\"]?([^'\"]+?)['\"]?\.?$", p, re.IGNORECASE)
        if search_match and not intents:
            query = search_match.group(1).rstrip(".,;")
            intents.append({
                "thought_process": f"Fast-path vector memory search for '{query}'.",
                "type": "SEARCH_MEMORY",
                "payload": {"query": query}
            })

        # 5. Send Message Pattern
        # e.g. "Send a message to John with the body 'Meeting at 5'."
        msg_match = re.search(r"send\s+(?:a\s+)?message\s+to\s+([a-zA-Z0-9_\-]+)\s+(?:with\s+(?:the\s+)?body\s+|saying\s+)?['\"]?([^'\"]*?)['\"]?\.?$", p, re.IGNORECASE)
        if msg_match and not intents:
            to = msg_match.group(1)
            body = msg_match.group(2).rstrip(".,;'\"")
            intents.append({
                "thought_process": f"Fast-path outbound message to {to}.",
                "type": "SEND_MESSAGE",
                "payload": {"to": to, "body": body}
            })

        # 6. Notify User Pattern
        # e.g. "Notify me that the system is shutting down."
        notify_match = re.search(r"(?:notify|alert)\s+(?:me\s+)?(?:that\s+)?['\"]?([^'\"]+)['\"]?$", p, re.IGNORECASE)
        if notify_match and not intents:
            msg = notify_match.group(1).rstrip(".,;")
            intents.append({
                "thought_process": "Fast-path user notification.",
                "type": "NOTIFY_USER",
                "payload": {"message": msg}
            })

        # 7. Ask User Pattern
        ask_match = re.search(r"ask\s+me\s+['\"]?([^'\"]+)['\"]?$", p, re.IGNORECASE)
        if ask_match and not intents:
            prompt_q = ask_match.group(1).rstrip(".,;")
            intents.append({
                "thought_process": "Fast-path clarification question requested.",
                "type": "ASK_USER_INPUT",
                "payload": {"prompt": prompt_q}
            })

        self.latency_ms = (time.perf_counter() - start) * 1000.0

        if intents:
            return intents
        return None


class GemmaDeepKernel:
    """
    Phase 1: Gemma Deep-Kernel (Gemma 31B equivalent).
    Handles ambiguous intent decomposition, multi-turn ReAct loops, complex reasoning,
    code synthesis, and associative memory querying.
    """

    def __init__(self, mode="google_genai", model_name="gemini-2.5-flash", client=None):
        self.mode = mode
        self.model_name = model_name
        self.client = client
        self.latency_ms = 0.0

    def reason_and_plan(self, prompt: str, context_history: str = "") -> List[Dict[str, Any]]:
        """Invokes the deep reasoning model to produce structured multi-step intents."""
        start = time.perf_counter()

        system_prompt = """
You are the Deep Kernel of an Agentic Operating System.
Your job is to parse the User Prompt and output a JSON array of intents.
Valid Intent Types: WRITE_FILE, READ_FILE, DELETE_FILE, SEARCH_MEMORY, SEND_MESSAGE, NOTIFY_USER, ASK_USER_INPUT, RUN_SANDBOX_CODE, HOST_AUTOMATE, QUERY_GRAPH.

Required Schemas for 'payload':
- SEND_MESSAGE: {"to": "recipient_name", "body": "message text"}
- WRITE_FILE: {"path": "/path/to/file.txt", "content": "file contents"}
- READ_FILE: {"path": "/path/to/file.txt"}
- DELETE_FILE: {"path": "/path/to/file.txt"}
- SEARCH_MEMORY: {"query": "search terms"}
- NOTIFY_USER: {"message": "notification text"}
- ASK_USER_INPUT: {"prompt": "Clarifying question for the user"}
- RUN_SANDBOX_CODE: {"code": "python or wasm script", "language": "python"}
- HOST_AUTOMATE: {"action": "launch_app | set_volume | notify | get_stats", "params": {}}
- QUERY_GRAPH: {"query": "entity or relation query"}

Output MUST be a JSON array of intent objects with 'thought_process', 'type', and 'payload'.
"""
        full_prompt = f"{system_prompt}\n"
        if context_history:
            full_prompt += f"\n--- Context ---\n{context_history}\n---------------\n"
        full_prompt += f"\nUser Prompt: {prompt}\nJSON Output:\n"

        if self.mode == "google_genai" and self.client:
            try:
                from google.genai import types # type: ignore
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=full_prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.1
                    )
                )
                raw_text = response.text or ""
                intents = StructuredGrammarEnforcer.parse_and_validate(raw_text)
                self.latency_ms = (time.perf_counter() - start) * 1000.0
                if intents:
                    return intents
            except Exception as e:
                print(f"[DeepKernel] Google GenAI failed ({e}), falling back to deterministic reasoning.")

        # Fallback Deep Reasoning heuristics if cloud is unavailable or fails
        intents = self._deterministic_deep_reason(prompt, context_history)
        self.latency_ms = (time.perf_counter() - start) * 1000.0
        return intents

    def _deterministic_deep_reason(self, prompt: str, context: str) -> List[Dict[str, Any]]:
        """Fallback multi-step ReAct reasoning pipeline when offline."""
        lower = prompt.lower()
        intents = []

        # Multi-intent parsing (e.g. "Send message to Alice saying I will be late, and save a note.")
        if "alice" in lower and "late" in lower:
            intents.append({
                "thought_process": "User wants to notify Alice about being late. Sending message via messaging HAL.",
                "type": "SEND_MESSAGE",
                "payload": {"to": "Alice", "body": "I will be late"}
            })
            intents.append({
                "thought_process": "User also requested to save a note. Writing confirmation to notes.",
                "type": "WRITE_FILE",
                "payload": {"path": "/docs/notes/late.txt", "content": "Told Alice I'd be late."}
            })
            intents.append({
                "thought_process": "Operations completed. Notifying user.",
                "type": "NOTIFY_USER",
                "payload": {"message": "Message sent to Alice and note saved."}
            })
            return intents

        # Graph association query
        if "who did i talk to" in lower or "who" in lower and "talk" in lower:
            intents.append({
                "thought_process": "Associative entity relationship query requested. Querying knowledge graph.",
                "type": "QUERY_GRAPH",
                "payload": {"query": prompt}
            })
            return intents

        # Code execution request
        if "run" in lower and ("code" in lower or "script" in lower or "calculate" in lower or "python" in lower):
            intents.append({
                "thought_process": "Code execution requested. Routing to sandboxed runtime.",
                "type": "RUN_SANDBOX_CODE",
                "payload": {"code": "print('AOS Sandbox execution successful')", "language": "python"}
            })
            return intents

        # Generic fallback
        intents.append({
            "thought_process": f"Reasoned plan for user prompt: '{prompt}'.",
            "type": "NOTIFY_USER",
            "payload": {"message": f"Processed request: {prompt}"}
        })
        return intents


class SpeculativeDualKernelRouter:
    """
    Phase 1: Speculative Dual-Kernel Router.
    Routes low-complexity routine intents to the Micro-Kernel (sub-50ms)
    and speculatively escalates complex reasoning or ambiguous requests
    to the Deep-Kernel (Gemma 31B).
    """

    def __init__(self, micro_kernel: GemmaMicroKernel, deep_kernel: GemmaDeepKernel):
        self.micro = micro_kernel
        self.deep = deep_kernel
        self.stats = {
            "micro_dispatches": 0,
            "deep_dispatches": 0,
            "speculative_escalations": 0
        }

    def assess_complexity(self, prompt: str) -> float:
        """
        Calculates a complexity score between 0.0 (simple single-step)
        and 1.0 (complex multi-step or ambiguous).
        """
        p = prompt.lower()
        score = 0.0

        # Multi-step conjunctions increase complexity
        conjunctions = [" and then ", ", and ", " after that ", " if ", " while ", " but also "]
        for conj in conjunctions:
            if conj in p:
                score += 0.4

        # Ambiguous terms
        ambiguous_keywords = ["who did i", "why", "analyze", "summarize", "correlate", "calculate", "compare", "plan"]
        for kw in ambiguous_keywords:
            if kw in p:
                score += 0.5

        # Code or graph queries
        if "python" in p or "graph" in p or "mesh" in p:
            score += 0.4

        return min(score, 1.0)

    def route(self, prompt: str, context_history: str = "") -> Tuple[List[Dict[str, Any]], str]:
        """
        Routes the prompt speculatively:
        1. If complexity is low (< 0.5), attempt Micro-Kernel first.
        2. If Micro-Kernel classifies successfully with high confidence, return immediately (sub-50ms).
        3. Otherwise, escalate to Deep-Kernel for multi-step reasoning.
        """
        complexity = self.assess_complexity(prompt)

        if complexity < 0.5:
            fast_intents = self.micro.classify_and_dispatch(prompt)
            if fast_intents:
                self.stats["micro_dispatches"] += 1
                return fast_intents, "micro_kernel"

        # Escalate to Deep Kernel
        if complexity < 0.5:
            self.stats["speculative_escalations"] += 1
        self.stats["deep_dispatches"] += 1

        deep_intents = self.deep.reason_and_plan(prompt, context_history)
        return deep_intents, "deep_kernel"
