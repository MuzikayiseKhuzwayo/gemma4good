# Agentic Operating System (AOS)

This project instantiates the initial architecture for the Agentic OS (AOS), shifting the software stack paradigm from a traditional "Kernel-Application-User" hierarchy to an "Inference Kernel-Tool Interface-Agentic Intent" model.

## Directory Structure

*   **`aos_kernel/`**: Contains the core inference engine/daemon that manages user intent and context token budgeting.
*   **`shell_agent/`**: Development of a "Shell Agent" that wraps existing OS calls. Maps intents to system APIs (File I/O, Network Sockets).
*   **`semantic_fs/`**: The Semantic File System which replaces traditional folder paths with a Vector Database layer, indexing content for RAG based retrieval.
*   **`generative_ui/`**: A Generative Stream interface to replace static layouts, outputting UI-definition tokens instead of traditional UI elements.

## Execution

Run the main application:
```bash
python main.py
```
