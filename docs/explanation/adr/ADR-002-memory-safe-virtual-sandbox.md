# ADR-002: Memory-Safe Virtual OS Sandboxing for Validation

* **Status:** Accepted
* **Date:** 2026-09-30
* **Decision Makers:** AOS Core Architecture Team
* **Code Anchor:** [`mock_os/virtual_env.py`](https://github.com/MuzikayiseKhuzwayo/gemma4good/blob/main/mock_os/virtual_env.py#L1), [`shell_agent/api_mapper.py`](https://github.com/MuzikayiseKhuzwayo/gemma4good/blob/main/shell_agent/api_mapper.py#L5)

---

## Context & Problem Statement

Prototyping an autonomous agent with operating system capabilities (file writing, deletion, network dispatch) on a developer's host machine creates severe safety risks:
* An unconstrained ReAct loop could delete critical host files or overwrite configuration data.
* Host file I/O introduces non-deterministic test states across different platforms (Windows vs. macOS vs. Linux).
* Running automated continuous integration (CI) tests on raw host environments creates side effects and security vectors.

---

## Decision

We implemented a pure in-memory simulated environment, `MockVirtualOS`, wrapped by the `ShellAgent` hardware abstraction layer (`use_virtual_env=True`).

---

## Rationale & Consequences

### Positive Consequences
* **Zero Host Blast Radius:** The agent can write, read, or delete files without any possibility of corrupting host data.
* **Deterministic Automated Verification:** Test suites ([`validate.py`](https://github.com/MuzikayiseKhuzwayo/gemma4good/blob/main/validate.py), [`test_all_intents.py`](https://github.com/MuzikayiseKhuzwayo/gemma4good/blob/main/test_all_intents.py)) can assert exact state changes using `get_state_summary()`.
* **Platform Independence:** Tests pass identically on Windows, Linux, and macOS.

### Negative Consequences / Trade-offs
* Does not interact with real host applications or physical files yet.
* Evolution plan: In Phase 3, this simulated environment will transition into a genuine WASM/WASI micro-sandbox with capability-based security.
