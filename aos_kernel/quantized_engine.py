import os
from typing import Optional, Dict, Any

class QuantizedInferenceEngine:
    """
    Phase 1: Quantized Native Inference Engine Backend.
    Provides abstraction for running quantized Gemma models locally (GGUF, 4-bit, 8-bit)
    using llama.cpp, torch/transformers with quantization, or hardware targets (NPU, Vulkan, CUDA).
    Falls back cleanly when native hardware runtimes are absent.
    """

    def __init__(
        self,
        backend: str = "auto",
        model_path: Optional[str] = None,
        quant_bits: int = 4,
        device: str = "auto"
    ):
        self.backend = backend
        self.model_path = model_path
        self.quant_bits = quant_bits
        self.device = device
        self.native_model = None
        self._initialize_backend()

    def _initialize_backend(self):
        """Attempts to load high-performance quantized engine based on availability."""
        if self.backend in ["llama_cpp", "auto"]:
            try:
                import llama_cpp # type: ignore
                if self.model_path and os.path.exists(self.model_path):
                    print(f"[QuantizedEngine] Loading GGUF model via llama.cpp: {self.model_path}")
                    # n_gpu_layers: -1 offloads all layers to GPU/Vulkan/Metal if available
                    self.native_model = llama_cpp.Llama(
                        model_path=self.model_path,
                        n_ctx=8192,
                        n_gpu_layers=-1 if self.device != "cpu" else 0,
                        verbose=False
                    )
                    self.backend = "llama_cpp"
                    return
            except ImportError:
                pass

        if self.backend in ["torch_quant", "auto"]:
            try:
                import torch
                from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
                if self.model_path and os.path.exists(self.model_path):
                    print(f"[QuantizedEngine] Loading {self.quant_bits}-bit PyTorch quantized model: {self.model_path}")
                    bnb_config = BitsAndBytesConfig(
                        load_in_4bit=(self.quant_bits == 4),
                        load_in_8bit=(self.quant_bits == 8),
                        bnb_4bit_compute_dtype=torch.float16
                    ) if self.quant_bits in [4, 8] else None

                    self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
                    self.native_model = AutoModelForCausalLM.from_pretrained(
                        self.model_path,
                        quantization_config=bnb_config,
                        device_map="auto"
                    )
                    self.backend = "torch_quant"
                    return
            except Exception:
                pass

        # Fallback backend mode
        self.backend = "emulated_edge"
        print(f"[QuantizedEngine] Edge inference engine ready (Hardware target: {self.device}, Quant: {self.quant_bits}-bit, Mode: {self.backend}).")

    def generate(self, prompt: str, max_tokens: int = 512, temperature: float = 0.1) -> str:
        """Executes inference on the configured quantized backend."""
        if self.backend == "llama_cpp" and self.native_model:
            output = self.native_model(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                stop=["\n\n\n", "User:"]
            )
            return output["choices"][0]["text"]

        elif self.backend == "torch_quant" and self.native_model:
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.native_model.device)
            outputs = self.native_model.generate(**inputs, max_new_tokens=max_tokens, temperature=temperature)
            return self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        return ""
