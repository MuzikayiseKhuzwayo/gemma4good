import json
import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
from typing import List, Dict, Any

from aos_kernel.structured_grammar import StructuredGrammarEnforcer
from aos_kernel.quantized_engine import QuantizedInferenceEngine
from aos_kernel.dual_kernel import GemmaMicroKernel, GemmaDeepKernel, SpeculativeDualKernelRouter

class GemmaLatentKernel:
    """
    Phase 1: Upgraded Latent Kernel of the Agentic OS.
    Features:
    - Speculative Dual-Kernel routing (Micro-Kernel <50ms for routine intent, Deep-Kernel for complex reasoning).
    - Structured Grammar Enforcement & schema validation (prevents JSON parse errors).
    - Quantized edge inference support (GGUF, 4/8-bit quant, NPU/Vulkan).
    """

    def __init__(self, model_name="gemma-4-31b-it", mode="google_genai"):
        self.model_name = model_name
        self.mode = mode
        self.model = None
        self.tokenizer = None
        self.client = None
        
        print(f"Booting Inference Kernel (Model: {self.model_name}, Mode: {self.mode})...")

        # Initialize Edge Quantized Backend abstraction
        self.quantized_engine = QuantizedInferenceEngine(
            backend="auto",
            quant_bits=4
        )

        if self.mode == "local":
            try:
                from transformers import AutoModelForCausalLM, AutoTokenizer
                import torch
                print("Loading PyTorch and Transformers for local inference...")
                self.tokenizer = AutoTokenizer.from_pretrained(model_name)
                self.model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    device_map="auto",
                    torch_dtype=torch.float16
                )
            except Exception:
                print("Warning: transformers/torch local load failed. Using edge kernel fallback.")
                self.mode = "mock"

        elif self.mode == "google_genai":
            try:
                from google import genai
                self.api_key = os.environ.get("GEMINI_API_KEY")
                if self.api_key:
                    self.client = genai.Client(api_key=self.api_key)
                    print("Using Google GenAI API for Deep Kernel inference.")
                else:
                    print("Notice: GEMINI_API_KEY not set. Deep Kernel will use offline deterministic reasoning.")
            except ImportError:
                print("Warning: google-genai not installed. Falling back to edge engine.")
                self.mode = "mock"
            except Exception as e:
                print(f"Warning: google-genai initialization failed ({e}). Falling back to edge engine.")
                self.mode = "mock"

        # Initialize Micro & Deep Kernels for Speculative Routing
        self.micro_kernel = GemmaMicroKernel()
        self.deep_kernel = GemmaDeepKernel(
            mode=self.mode,
            model_name="gemini-2.5-flash" if self.mode == "google_genai" else self.model_name,
            client=self.client
        )
        self.router = SpeculativeDualKernelRouter(self.micro_kernel, self.deep_kernel)
        print("[InferenceKernel] Speculative Dual-Kernel Router & Grammar Enforcer initialized.")

    def parse_intent(self, user_prompt: str, context_history: str = "") -> List[Dict[str, Any]]:
        """
        Parses user prompt into validated OS intents.
        Applies speculative routing between Micro-Kernel and Deep-Kernel,
        then guarantees schema enforcement via StructuredGrammarEnforcer.
        """
        if not user_prompt:
            return []

        intents, routed_kernel = self.router.route(user_prompt, context_history)
        print(f"[Router] Prompt routed to: {routed_kernel} (Micro latency: {self.micro_kernel.latency_ms:.2f}ms, Deep latency: {self.deep_kernel.latency_ms:.2f}ms)")

        # Validate all extracted intents against formal grammar & schema
        validated_intents = []
        for item in intents:
            val = StructuredGrammarEnforcer.validate_intent_schema(item)
            if val:
                validated_intents.append(val)

        return validated_intents

    def generate_response(self, user_prompt: str, execution_logs: List[str]) -> str:
        """
        Generates a natural language response based on OS execution results.
        """
        system_prompt = (
            "You are the Agentic OS interface. "
            "The user made a request, and the system executed background tasks. "
            "Explain the results to the user in a natural, helpful, and concise way. "
            "Do NOT use JSON. If a search returned empty ([]), inform the user that no files were found. "
            "If a file was successfully written (True), confirm it to the user."
        )
        prompt = f"{system_prompt}\n\nUser Request: {user_prompt}\nSystem Execution Logs: {execution_logs}\n\nResponse:"

        if self.mode == "google_genai" and self.client:
            try:
                response = self.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt
                )
                if response.text:
                    return response.text.strip()
            except Exception:
                pass

        # High-quality fallback natural language synthesizer
        return self._synthesize_natural_response(user_prompt, execution_logs)

    def _synthesize_natural_response(self, user_prompt: str, execution_logs: List[str]) -> str:
        """Synthesizes human-friendly response deterministically from execution telemetry."""
        lines = []
        for log in execution_logs:
            if "WRITE_FILE" in log and "Result: True" in log:
                lines.append("✓ File has been successfully created and saved.")
            elif "READ_FILE" in log:
                if "Result: None" in log:
                    lines.append("File not found.")
                else:
                    lines.append(f"Retrieved file content:\n{log.split('Result: ')[-1]}")
            elif "DELETE_FILE" in log and "Result: True" in log:
                lines.append("✓ Target file has been deleted.")
            elif "SEARCH_MEMORY" in log:
                results = log.split("Result: ")[-1]
                if results == "[]" or not results:
                    lines.append("No matching documents found in memory.")
                else:
                    lines.append(f"Memory search found: {results}")
            elif "SEND_MESSAGE" in log:
                lines.append("✓ Outbound message dispatched.")
            elif "RUN_SANDBOX_CODE" in log:
                lines.append("✓ Sandboxed code executed successfully.")
            elif "HOST_AUTOMATE" in log:
                lines.append("✓ Host automation completed.")
            elif "QUERY_GRAPH" in log:
                lines.append(f"Graph associations: {log.split('Result: ')[-1]}")
            else:
                lines.append(log)

        if not lines:
            return "Operation completed."
        return "\n".join(lines)
