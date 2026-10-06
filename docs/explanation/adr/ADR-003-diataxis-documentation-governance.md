# ADR-003: Diátaxis Taxonomy Governance & Docs-as-Code

* **Status:** Accepted
* **Date:** 2026-09-30
* **Decision Makers:** AOS Core Architecture Team
* **Code Anchor:** [`docs/triage_matrix.md`](https://github.com/MuzikayiseKhuzwayo/gemma4good/blob/main/docs/triage_matrix.md), [`docs/`](https://github.com/MuzikayiseKhuzwayo/gemma4good/blob/main/docs/)

---

## Context & Problem Statement

Initial project documentation was distributed across loosely structured root markdown files created under hackathon sprint deadlines. This created significant operational risks:
1. Documentation drift: Content drifted from executable code reality.
2. Mixed taxonomies: Single documents mixed step-by-step onboarding with deep architectural philosophy and API specifications.
3. Obsolete artifacts: Stale competition templates and sprint plans lingered in the root directory.

---

## Decision

We adopted the **Diátaxis Documentation Framework** governed under the `dubstrata-docs` standard.
All project documentation is strictly compartmentalized into four distinct quadrants:
1. **Tutorials (`docs/tutorials/`)**: Learning-oriented onboarding for newcomers.
2. **How-To Guides (`docs/how-to/`)**: Problem-oriented step-by-step recipes.
3. **Reference (`docs/reference/`)**: Information-oriented exact technical specifications.
4. **Explanation (`docs/explanation/`)**: Understanding-oriented architecture, design rationale, and ADRs.

In addition, historical hackathon competition artifacts were pruned from the root and preserved under `docs/archive/hackathon/`.

---

## Rationale & Consequences

### Positive Consequences
* **Zero Ambiguity:** Developers immediately know where to look and where to contribute.
* **Separation of Intent & Specification:** How-to recipes do not get clogged with architectural theory, and reference specifications remain concise and authoritative.
* **Drift Boundary Protection:** Reference docs are updated immediately when API schemas change; explanations only change during macro-architectural evolutions.
* **Text-Based Mermaid Standard:** System diagrams are diffable and version-controlled alongside code.
