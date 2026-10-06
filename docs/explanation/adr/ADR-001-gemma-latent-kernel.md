# ADR-001: Gemma 4 as the Foundational Latent Kernel

* **Status:** Accepted
* **Date:** 2026-09-30
* **Decision Makers:** AOS Core Architecture Team
* **Code Anchor:** [`aos_kernel/inference.py`](https://github.com/MuzikayiseKhuzwayo/gemma4good/blob/main/aos_kernel/inference.py#L9)

---

## Context & Problem Statement

An Agentic Operating System requires a foundation model capable of serving as its core reasoning daemon. The model must:
1. Support local on-device execution on consumer-grade hardware to function in low-connectivity or air-gapped environments.
2. Possess state-of-the-art instruction-following capabilities to reliably emit strict JSON payloads without hallucinatory syntax breaks.
3. Support deep chain-of-thought planning (`<thought_process>`) to navigate autonomous ReAct tool loops.
4. Guarantee digital sovereignty with an open-weights license, ensuring student and citizen data is never exfiltrated to external proprietary APIs.

---

## Decision

We chose **Gemma-4-31b-it** (with fallback to cloud-assisted Google GenAI simulation and offline mock modes) as the primary foundational model for the Latent Kernel.

---

## Rationale & Consequences

### Positive Consequences
* **Parameter Efficiency:** Gemma 4 provides reasoning density comparable to 70B+ parameter models while fitting into consumer-accessible unified memory spaces (16 GB - 24 GB) under 4-bit quantization.
* **Deterministic Structured Output:** Demonstrated superior compliance with JSON schema constraints during benchmarking.
* **Chain-of-Thought Native:** Effectively uses reasoning tokens to evaluate prerequisites before selecting OS intent types.
* **Digital Sovereignty:** Completely open weights enable local compilation and deployment without recurring API costs or privacy violations.

### Negative Consequences / Trade-offs
* Full-precision local execution requires modern GPU hardware or Apple Silicon. Mitigated by providing `mode="google_genai"` for development and `mode="mock"` for unit testing.
