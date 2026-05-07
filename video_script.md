# Video Script & Storyboard: Agentic OS (AOS)
**Target Length:** 3:00 Minutes
**Track Focus:** Cactus Prize (Local-First / Task Routing)
**Core Rule:** "Show, Don't Tell"

---

## 🎬 Part 1: The Problem (0:00 - 0:30)
**Goal:** Show the friction of application-centric computing, especially offline.

*   **[Visual 0:00 - 0:15]:** Screen recording of a cluttered traditional desktop. A user is trying to find information offline. They open a browser and hit the offline "Dinosaur" error. They open a messy directory of disorganized files, click into a Word document, switch to a spreadsheet, and look frustrated. 
*   **[Voiceover]:** "Today’s computing relies heavily on cloud applications and rigid, menu-driven interfaces. For users in low-connectivity environments—like rural classrooms or remote edge deployments—this model is broken. If the internet drops, or if you don't know exactly which app to navigate, you are locked out of your own workflow."
*   **[Visual 0:15 - 0:30]:** Big red 'X' over the desktop. Fade to black. The words **"The Luggage Problem"** appear on screen, followed by **"What if the AI was the Operating System?"**

## 🎬 Part 2: The Agentic Solution (0:30 - 2:00)
**Goal:** Show the interface solving complex problems locally, without apps, through a genuine multi-step interaction.

*   **[Visual 0:30 - 0:40]:** A clean, dark-mode generative web UI appears. The text types out: `Booting Agentic OS... Initializing Latent Kernel... Model: Gemma-4-31b-it (Local Edge)`.
*   **[Voiceover]:** "Meet the Agentic OS. We’ve deprecated the traditional application layer. Instead of launching apps, we’ve embedded Gemma 4 directly as the system's core kernel. Let's look at a genuine interaction."

**Command 1: RAG & File I/O**
*   **[Visual 0:40 - 0:55]:** User Prompt: *"Search my memory for the Solar System lesson plan and save a summary to /docs/summary.txt."* 
    *   `[Kernel] Mapping intent: SEARCH_MEMORY -> "Solar System"`
    *   `[Kernel] Mapping intent: WRITE_FILE -> /docs/summary.txt`
*   **[Voiceover]:** "The user simply states their intent. The Latent Kernel parses this and performs Semantic Retrieval, bypassing folders entirely, then maps a `WRITE_FILE` intent directly to the virtual file system. No word processors needed."

**Command 2: Interactive Context Gathering**
*   **[Visual 0:55 - 1:15]:** User Prompt: *"Send this summary to the Principal."*
    *   `[Kernel] Mapping intent: ASK_USER_INPUT -> "I lack the Principal's local network ID. Please provide it."`
    *   *(User provides ID: 192.168.1.5)*
    *   `[Kernel] Mapping intent: SEND_MESSAGE -> 192.168.1.5`
*   **[Voiceover]:** "Here we see the ReAct loop in action. The Kernel detects missing context and issues an `ASK_USER_INPUT` intent, proving the OS is interactive, not just a static script. Once provided, it routes the message."

**Command 3: File System Manipulation**
*   **[Visual 1:15 - 1:35]:** User Prompt: *"Read the old curriculum draft, and since it's outdated, delete it from the system."*
    *   `[Kernel] Mapping intent: READ_FILE -> /docs/old_draft.txt`
    *   `[Kernel] Mapping intent: DELETE_FILE -> /docs/old_draft.txt`
*   **[Voiceover]:** "The system executes a `READ_FILE` intent, loading data into its token budget. It reasons over the content, then safely invokes `DELETE_FILE` using its strict JSON API schema—without user micro-management."

**Command 4: System State & Notifications**
*   **[Visual 1:35 - 2:00]:** User Prompt: *"Distribute the new lesson plan to the offline student mesh and notify me when done."*
    *   `[Kernel] Mapping intent: SEND_MESSAGE -> [student_mesh_group]`
    *   `[Kernel] Mapping intent: NOTIFY_USER -> "Distribution complete."`
*   **[Voiceover]:** "Finally, it orchestrates network distribution via `SEND_MESSAGE` and updates the generative UI state with a `NOTIFY_USER` callback. Gemma 4 breaks the prompts down, generates deterministic JSON execution plans, and handles OS operations completely autonomously."

## 🎬 Part 3: Technical Validation (2:00 - 3:00)
**Goal:** Prove the code works and highlight why Gemma 4 was used.

*   **[Visual 2:00 - 2:30]:** Split screen. Left side: The live terminal running `python test_all_intents.py`, successfully blazing through the 7 different intent paths and exiting with `Exit code: 0`. Right side: A quick glance at `aos_kernel/inference.py` highlighting the intent parser.
*   **[Voiceover]:** "To validate this, we built a memory-safe Virtual OS Sandbox. As you can see in the live terminal, the system effortlessly executes a 7-path ReAct loop. It correctly extracts and executes system intents without hallucinatory syntax errors, proving the viability of our contextual budgeting."
*   **[Visual 2:30 - 2:50]:** Text on screen: **"Why Gemma 4?"** followed by bullet points: *Parameter Efficient for Edge*, *Strict JSON Adherence*, *Open Weights for Sovereignty*.
*   **[Voiceover]:** "We chose Gemma-4-31b-it because its parameter efficiency allows it to run on consumer hardware, while its instruction-tuning ensures strict adherence to system API schemas. Most importantly, its open weights guarantee digital sovereignty for the user."
*   **[Visual 2:50 - 3:00]:** Final Title Card: **Agentic OS. Sovereign Computing for the Edge.** (Include Cactus Prize & Main Track logos if applicable).
*   **[Voiceover]:** "By embedding Gemma directly into the kernel, we deliver a local-first computing interface driven entirely by intent. Thank you."
