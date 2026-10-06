# Documentation Triage Matrix & Drift Ledger

This document establishes the baseline audit and governance record for the Agentic Operating System (AOS) documentation suite in accordance with the `dubstrata-docs` standard.

## 1. Audit Baseline & Drift Boundary

* **Audit Target:** `gemma4good` (Agentic OS core repository)
* **Framework:** Diátaxis Documentation Framework (Tutorials, How-To Guides, Reference, Explanation)
* **Audited Git Head:** `2799d96`
* **Primary Interfaces Audited:**
  * Gateway Server: [`server.py`](https://github.com/MuzikayiseKhuzwayo/gemma4good/blob/main/server.py)
  * Latent Kernel Inference: [`aos_kernel/inference.py`](https://github.com/MuzikayiseKhuzwayo/gemma4good/blob/main/aos_kernel/inference.py)
  * System Daemon & ReAct Loop: [`aos_kernel/daemon.py`](https://github.com/MuzikayiseKhuzwayo/gemma4good/blob/main/aos_kernel/daemon.py)
  * Memory & Context Manager: [`aos_kernel/context_manager.py`](https://github.com/MuzikayiseKhuzwayo/gemma4good/blob/main/aos_kernel/context_manager.py)
  * Shell Agent & Hardware Abstraction: [`shell_agent/api_mapper.py`](https://github.com/MuzikayiseKhuzwayo/gemma4good/blob/main/shell_agent/api_mapper.py)
  * Virtual OS Sandbox: [`mock_os/virtual_env.py`](https://github.com/MuzikayiseKhuzwayo/gemma4good/blob/main/mock_os/virtual_env.py)
  * Semantic Storage Stub: [`semantic_fs/vector_store.py`](https://github.com/MuzikayiseKhuzwayo/gemma4good/blob/main/semantic_fs/vector_store.py)
  * Test & Validation Harness: [`validate.py`](https://github.com/MuzikayiseKhuzwayo/gemma4good/blob/main/validate.py), [`test_all_intents.py`](https://github.com/MuzikayiseKhuzwayo/gemma4good/blob/main/test_all_intents.py)

---

## 2. Legacy Document Triage & Pruning Actions

Prior to this documentation overhaul, project documentation consisted of disconnected root-level markdown files drafted during the initial hackathon sprint. Per the **Negative Documentation** invariant, obsolete or competition-specific documents must be pruned or archived to prevent misleading operators.

| Document Path | Original Purpose | Drift Status | Remediation Action | Code Anchor / Rationale |
| :--- | :--- | :--- | :--- | :--- |
| `fakefile.txt` | Junk / test artifact | **Obsolete** | **Deleted** | 14-byte test file containing non-code string |
| `description.md` | Hackathon submission writeup | **Historical** | Relocated to `docs/archive/hackathon/description.md` | Contains hackathon-specific track targeting and narrative |
| `plan.md` | 28-day hackathon sprint schedule | **Obsolete** | Relocated to `docs/archive/hackathon/plan.md` | Sprint timelines expired; superseded by `docs/explanation/roadmap.md` |
| `submission_writeup.md` | Submission portal copy-paste template | **Historical** | Relocated to `docs/archive/hackathon/submission_writeup.md` | Competition-specific submission form metadata |
| `video_script.md` | 3-minute video presentation script | **Historical** | Relocated to `docs/archive/hackathon/video_script.md` | Video recording script for competition judges |
| `README.md` | Basic project overview | **Outdated** | **Rewritten** to serve as the unified Diátaxis index | Missing comprehensive API contracts, architectural diagrams, and links |

---

## 3. Diátaxis Master Catalog

All active documentation in `docs/` is classified into one of the four Diátaxis quadrants:

```
                      PRACTICAL / ACTION-ORIENTED
                                 │
           How-To Guides         │         Tutorials
      (Problem-oriented recipes) │  (Learning-oriented onboarding)
                                 │
  ───────────────────────────────┼───────────────────────────────
                                 │
            Reference            │        Explanation
    (Information-oriented specs) │ (Understanding-oriented architecture)
                                 │
                      THEORETICAL / KNOWLEDGE-ORIENTED
```

### Active Documentation Inventory

| File Path | Diátaxis Quadrant | Target Audience | Primary Focus | Code Anchor |
| :--- | :--- | :--- | :--- | :--- |
| [`docs/tutorials/getting-started.md`](https://github.com/MuzikayiseKhuzwayo/gemma4good/blob/main/docs/tutorials/getting-started.md) | **Tutorial** | Newcomer / Integrator | 10-minute end-to-end setup and first intent execution | [`server.py`](https://github.com/MuzikayiseKhuzwayo/gemma4good/blob/main/server.py), [`main.py`](https://github.com/MuzikayiseKhuzwayo/gemma4good/blob/main/main.py) |
| [`docs/tutorials/edge-deployment.md`](https://github.com/MuzikayiseKhuzwayo/gemma4good/blob/main/docs/tutorials/edge-deployment.md) | **Tutorial** | Edge Engineer | Deploying on low-connectivity and constrained hardware | [`aos_kernel/inference.py`](https://github.com/MuzikayiseKhuzwayo/gemma4good/blob/main/aos_kernel/inference.py#L18-L47) |
| [`docs/how-to/add-custom-intent.md`](https://github.com/MuzikayiseKhuzwayo/gemma4good/blob/main/docs/how-to/add-custom-intent.md) | **How-To** | Developer | Step-by-step recipe to declare and route a new intent | [`aos_kernel/inference.py`](https://github.com/MuzikayiseKhuzwayo/gemma4good/blob/main/aos_kernel/inference.py#L53-L78), [`shell_agent/api_mapper.py`](https://github.com/MuzikayiseKhuzwayo/gemma4good/blob/main/shell_agent/api_mapper.py#L15-L53) |
| [`docs/how-to/run-validation-suite.md`](https://github.com/MuzikayiseKhuzwayo/gemma4good/blob/main/docs/how-to/run-validation-suite.md) | **How-To** | QA / CI Operator | Running automated verification suites against Virtual OS | [`validate.py`](https://github.com/MuzikayiseKhuzwayo/gemma4good/blob/main/validate.py), [`test_all_intents.py`](https://github.com/MuzikayiseKhuzwayo/gemma4good/blob/main/test_all_intents.py) |
| [`docs/how-to/configure-inference.md`](https://github.com/MuzikayiseKhuzwayo/gemma4good/blob/main/docs/how-to/configure-inference.md) | **How-To** | Operator / Sysadmin | Configuring local HuggingFace, Google GenAI, and mock modes | [`aos_kernel/inference.py`](https://github.com/MuzikayiseKhuzwayo/gemma4good/blob/main/aos_kernel/inference.py#L9-L47), [`.env`](https://github.com/MuzikayiseKhuzwayo/gemma4good/blob/main/.env) |
| [`docs/reference/intent-schemas.md`](https://github.com/MuzikayiseKhuzwayo/gemma4good/blob/main/docs/reference/intent-schemas.md) | **Reference** | Core Engineers | Exact JSON schemas, parameters, and return types for intents | [`aos_kernel/inference.py`](https://github.com/MuzikayiseKhuzwayo/gemma4good/blob/main/aos_kernel/inference.py#L58-L78) |
| [`docs/reference/rest-api.md`](https://github.com/MuzikayiseKhuzwayo/gemma4good/blob/main/docs/reference/rest-api.md) | **Reference** | UI / Client Developers | HTTP contracts for `/api/intent`, `/api/history`, `/api/new_chat` | [`server.py`](https://github.com/MuzikayiseKhuzwayo/gemma4good/blob/main/server.py#L40-L143) |
| [`docs/reference/configuration.md`](https://github.com/MuzikayiseKhuzwayo/gemma4good/blob/main/docs/reference/configuration.md) | **Reference** | DevOps / SRE | Environment variables, ports, token caps, and default paths | [`aos_kernel/context_manager.py`](https://github.com/MuzikayiseKhuzwayo/gemma4good/blob/main/aos_kernel/context_manager.py#L2), [`.env`](https://github.com/MuzikayiseKhuzwayo/gemma4good/blob/main/.env) |
| [`docs/reference/virtual-os.md`](https://github.com/MuzikayiseKhuzwayo/gemma4good/blob/main/docs/reference/virtual-os.md) | **Reference** | Test Engineers | Method signatures, state dictionaries, and behavior of MockVirtualOS | [`mock_os/virtual_env.py`](https://github.com/MuzikayiseKhuzwayo/gemma4good/blob/main/mock_os/virtual_env.py#L1-L60) |
| [`docs/explanation/architecture.md`](https://github.com/MuzikayiseKhuzwayo/gemma4good/blob/main/docs/explanation/architecture.md) | **Explanation** | System Architects | Latent Kernel paradigm, Functional Virtualization, ReAct loop | [`aos_kernel/daemon.py`](https://github.com/MuzikayiseKhuzwayo/gemma4good/blob/main/aos_kernel/daemon.py#L36-L73) |
| [`docs/explanation/context-budgeting.md`](https://github.com/MuzikayiseKhuzwayo/gemma4good/blob/main/docs/explanation/context-budgeting.md) | **Explanation** | AI / Systems Engineers | Context window management, token budgeting, and swapping | [`aos_kernel/context_manager.py`](https://github.com/MuzikayiseKhuzwayo/gemma4good/blob/main/aos_kernel/context_manager.py#L1-L15) |
| [`docs/explanation/roadmap.md`](https://github.com/MuzikayiseKhuzwayo/gemma4good/blob/main/docs/explanation/roadmap.md) | **Explanation** | Strategic Stakeholders | Multi-phase evolutionary roadmap from PoC to Sovereign Edge OS | Whole repository |
| [`docs/explanation/adr/ADR-001-gemma-latent-kernel.md`](https://github.com/MuzikayiseKhuzwayo/gemma4good/blob/main/docs/explanation/adr/ADR-001-gemma-latent-kernel.md) | **Explanation (ADR)** | Architects | Architectural Decision Record: Gemma 4 as the Latent Kernel | [`aos_kernel/inference.py`](https://github.com/MuzikayiseKhuzwayo/gemma4good/blob/main/aos_kernel/inference.py#L9) |
| [`docs/explanation/adr/ADR-002-memory-safe-virtual-sandbox.md`](https://github.com/MuzikayiseKhuzwayo/gemma4good/blob/main/docs/explanation/adr/ADR-002-memory-safe-virtual-sandbox.md) | **Explanation (ADR)** | Security / Test Leads | Architectural Decision Record: Simulated OS Sandboxing | [`mock_os/virtual_env.py`](https://github.com/MuzikayiseKhuzwayo/gemma4good/blob/main/mock_os/virtual_env.py#L1) |
| [`docs/explanation/adr/ADR-003-diataxis-documentation-governance.md`](https://github.com/MuzikayiseKhuzwayo/gemma4good/blob/main/docs/explanation/adr/ADR-003-diataxis-documentation-governance.md) | **Explanation (ADR)** | Documentation Leads | Architectural Decision Record: Diátaxis framework governance | `docs/` |

---

## 4. Maintenance & Drift Invariants

1. **Anti-Mirage Invariant:** No parameter, configuration key, or API endpoint shall be documented without an explicit source code anchor.
2. **Lean Documentation Invariant:** When code deprecates a feature or removes an intent type, the corresponding documentation must be pruned or archived immediately.
3. **Doc-Coupled Changes:** Any pull request modifying `aos_kernel/`, `shell_agent/`, or `server.py` interfaces must update the corresponding Reference documents and this Triage Matrix.
