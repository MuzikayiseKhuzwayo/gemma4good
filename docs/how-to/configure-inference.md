# How-To: Configure Inference Modes

The Agentic Operating System provides a flexible inference kernel (`GemmaLatentKernel`) supporting three distinct operating modes:

1. **`google_genai`**: Cloud-assisted edge simulation via the official Google GenAI SDK.
2. **`local`**: Full on-device weights execution using HuggingFace PyTorch.
3. **`mock`**: Instant offline testing engine with zero external dependencies.

This guide demonstrates how to configure and toggle between these modes.

---

## Mode Comparison Matrix

| Feature | `google_genai` | `local` | `mock` |
| :--- | :--- | :--- | :--- |
| **Connectivity Required** | Yes (Internet connection) | **No** (100% offline) | **No** (100% offline) |
| **VRAM / Hardware Sizing** | None (Runs on any machine) | 16 GB - 32 GB VRAM | None |
| **Model Weights Download** | None (Zero download) | ~20 GB - 60 GB | None |
| **Reasoning Depth** | High (`ThinkingConfig`) | High (Native Gemma weights) | Low (Regex / keyword rules) |
| **Target Use Case** | Fast prototyping & web testing | Sovereign air-gapped deployment | Unit testing & CI/CD pipelines |

---

## 1. Configuring `google_genai` Mode (Default)

This mode connects directly to Google's API to run `gemma-4-31b-it` or `gemini-2.5-flash` with chain-of-thought thinking enabled.

### Steps:
1. Ensure your `.env` contains:
   ```ini
   GEMINI_API_KEY=AIzaSy...your_key_here
   ```
2. Verify package installation:
   ```bash
   pip install google-genai python-dotenv
   ```
3. Initialize the kernel in Python:
   ```python
   from aos_kernel.inference import GemmaLatentKernel

   kernel = GemmaLatentKernel(
       model_name="gemma-4-31b-it", # or "gemini-2.5-flash"
       mode="google_genai"
   )
   ```

---

## 2. Configuring `local` Mode (Air-Gapped Sovereign Deployment)

This mode runs the model directly on local GPUs or unified memory hardware.

### Steps:
1. Install PyTorch with your platform's accelerator drivers:
   ```bash
   # NVIDIA CUDA 12.1:
   pip install torch --index-url https://download.pytorch.org/whl/cu121
   pip install transformers accelerate
   ```
2. Download or specify local model weights path:
   ```python
   from aos_kernel.inference import GemmaLatentKernel

   kernel = GemmaLatentKernel(
       model_name="/models/gemma-4-31b-it", # Local directory or HuggingFace repo
       mode="local"
   )
   ```
3. When initialized, the kernel will execute:
   ```python
   self.tokenizer = AutoTokenizer.from_pretrained(model_name)
   self.model = AutoModelForCausalLM.from_pretrained(
       model_name,
       device_map="auto",
       torch_dtype=torch.float16
   )
   ```

---

## 3. Configuring `mock` Mode (Offline Testing & CI/CD)

The mock mode operates deterministically without loading heavy model weights or querying remote APIs.

### Steps:
1. Set the mode to `"mock"` in code:
   ```python
   kernel = GemmaLatentKernel(mode="mock")
   ```
2. Any user prompt will immediately be processed by the deterministic rules in [`aos_kernel/inference.py`](https://github.com/MuzikayiseKhuzwayo/gemma4good/blob/main/aos_kernel/inference.py#L85-L95).
