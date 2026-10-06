# Tutorial: Edge & Local-First Deployment

This tutorial guides systems engineers on deploying the Agentic Operating System (AOS) on edge hardware in low-connectivity or air-gapped environments.

---

## 1. Architectural Motivation

In remote regions, developing classrooms, field operations, and air-gapped secure facilities, cloud-hosted AI APIs fail due to:
* Zero or intermittent internet connectivity.
* Severe bandwidth latency and satellite data costs.
* Data sovereignty requirements (local data must never leave the device).

AOS is architected to run with open-weights models (specifically the **Gemma 4** family) directly on consumer laptops, embedded edge compute units, or localized server nodes.

```mermaid
graph TB
    subgraph EdgeDevice ["Edge Host (Laptop / Mini-PC / Jetson)"]
        subgraph Hardware ["Hardware Layer"]
            VRAM["Unified Memory / VRAM (16GB - 32GB)"]
            CPU["Host CPU / NPU Acceleration"]
        end
        subgraph AOSStack ["Agentic OS Core Stack"]
            Weights["Gemma-4 Model Weights (Local)"]
            Kernel["GemmaLatentKernel (mode='local')"]
            Daemon["AOSDaemon (Local Event Loop)"]
            Sandbox["Virtual OS / Local Storage"]
        end
        Hardware --- AOSStack
    end
    Cloud["Cloud / External Internet (DISCONNECTED / NOT REQUIRED)"] -.x EdgeDevice
```

---

## 2. Hardware Sizing & Requirements

| Deployment Tier | Model Target | Precision | Minimum VRAM / RAM | Recommended Hardware |
| :--- | :--- | :--- | :--- | :--- |
| **Tier 1: Minimal Edge** | `gemma-2b-it` / `gemma-4-31b-it` (INT4) | 4-bit Quantized | 8 GB - 16 GB Unified Memory | Apple Silicon (M1/M2/M3, 16GB), RTX 3060/4060 |
| **Tier 2: Standard Edge Node** | `gemma-4-31b-it` | 4-bit / 8-bit | 16 GB - 24 GB VRAM | RTX 3090 / 4080 / 4090, Apple M2/M3 Pro |
| **Tier 3: Full Precision Edge** | `gemma-4-31b-it` | FP16 | 64 GB System RAM / VRAM | Dual RTX 3090/4090, Apple M-series Max/Ultra |

---

## 3. Configuring Local Inference Mode

In [`aos_kernel/inference.py`](https://github.com/MuzikayiseKhuzwayo/gemma4good/blob/main/aos_kernel/inference.py#L18-L32), the kernel supports a native `"local"` mode using HuggingFace `transformers` and PyTorch.

### Step 3.1: Install Acceleration Dependencies

Ensure CUDA-enabled PyTorch or Apple Silicon MPS is installed:

```bash
# For CUDA (Linux / Windows NVIDIA):
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install transformers accelerate bitsandbytes
```

### Step 3.2: Enable Local Mode in Code

To switch AOS to run locally from weights rather than API calls, instantiate `GemmaLatentKernel` with `mode="local"`:

In [`server.py`](https://github.com/MuzikayiseKhuzwayo/gemma4good/blob/main/server.py#L151) or [`main.py`](https://github.com/MuzikayiseKhuzwayo/gemma4good/blob/main/main.py#L9):

```python
# Configure for local weight execution
inference_engine = GemmaLatentKernel(
    model_name="google/gemma-4-31b-it", # Or local directory path
    mode="local"
)
```

The kernel will:
1. Load model weights into memory using `device_map="auto"`.
2. Map inference directly to local tensor accelerators without making any external network requests.
3. Fall back gracefully to `mode="mock"` if PyTorch is not available.

---

## 4. Air-Gapped Operation Verification

To verify that your deployment is 100% self-sufficient and air-gapped:
1. Disconnect your machine from Wi-Fi or unplug the Ethernet cable.
2. Launch the headless verification harness:
   ```bash
   python validate.py
   ```
3. If using `mode="local"` or `mode="mock"`, all seven abstract intents will parse and execute without network timeout errors.
4. Launch the local web UI:
   ```bash
   python server.py
   ```
   Open `http://127.0.0.1:8000/index.html` to operate entirely offline.
