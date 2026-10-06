# Reference: Configuration & Environment Variables

This document lists all configuration variables, ports, and operational parameters for the Agentic Operating System.

---

## 1. Environment Variables (`.env`)

The project uses `python-dotenv` to load secrets and settings from `.env` in the repository root.

| Variable Name | Required | Default Value | Description |
| :--- | :--- | :--- | :--- |
| `GEMINI_API_KEY` | Optional | `None` | Google Gemini / GenAI API key for remote acceleration mode (`google_genai`). If omitted, kernel falls back to `mock` mode. |

---

## 2. Server & Network Parameters

| Parameter | Default | Configured In | Description |
| :--- | :--- | :--- | :--- |
| **HTTP Port** | `8000` | [`server.py`](https://github.com/MuzikayiseKhuzwayo/gemma4good/blob/main/server.py#L144) | Gateway port serving static assets and REST API. |
| **Listen Address** | `""` (`0.0.0.0`) | [`server.py`](https://github.com/MuzikayiseKhuzwayo/gemma4good/blob/main/server.py#L154) | Binds to all available host network interfaces. |
| **Messaging URI** | `api://messaging` | [`mock_os/virtual_env.py`](https://github.com/MuzikayiseKhuzwayo/gemma4good/blob/main/mock_os/virtual_env.py#L44) | Simulated network routing target for `SEND_MESSAGE`. |

---

## 3. Kernel & Inference Parameters

Configured in [`aos_kernel/inference.py`](https://github.com/MuzikayiseKhuzwayo/gemma4good/blob/main/aos_kernel/inference.py#L9-L11):

| Parameter | Options / Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `model_name` | `string` | `"gemma-4-31b-it"` | Name or path of the LLM weights. |
| `mode` | `"google_genai" \| "local" \| "mock"` | `"google_genai"` | Operating inference mode. |
| `temperature` | `float` | `0.1` | Low sampling temperature for deterministic JSON output. |
| `thinking_level` | `types.ThinkingLevel` | `HIGH` | Enables deep chain-of-thought `<thought_process>` evaluation. |

---

## 4. Context Budget Parameters

Configured in [`aos_kernel/context_manager.py`](https://github.com/MuzikayiseKhuzwayo/gemma4good/blob/main/aos_kernel/context_manager.py#L2):

| Parameter | Default Value | Description |
| :--- | :--- | :--- |
| `max_tokens` | `8192` | Maximum context window budget before triggering memory swapping. |
| `cost_per_intent` | `150` | Estimated token budget deducted per executed intent step. |
| `history_window` | `5` | Number of recent interaction turns passed into prompt context (`active_context[-5:]`). |
