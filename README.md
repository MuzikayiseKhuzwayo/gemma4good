# Agentic Operating System (AOS)

This project instantiates the initial architecture for the Agentic OS (AOS), shifting the software stack paradigm from a traditional "Kernel-Application-User" hierarchy to an "Inference Kernel-Tool Interface-Agentic Intent" model.

*Recent updates have successfully integrated a Generative Web Interface, allowing users to interact directly with the Latent Kernel via a visually driven, responsive local server.*

## Directory Structure

*   **`aos_kernel/`**: Contains the core inference engine/daemon that manages user intent and context token budgeting.
*   **`shell_agent/`**: Development of a "Shell Agent" that wraps existing OS calls. Maps intents to system APIs (File I/O, Network Sockets).
*   **`semantic_fs/`**: The Semantic File System which replaces traditional folder paths with a Vector Database layer, indexing content for RAG based retrieval.
*   **`generative_ui/`**: A Generative Stream web interface replacing static layouts, serving a modern front-end that communicates with the AOS daemon.

## Execution

### 1. Launch the Web Interface (Recommended)
To run the full Agentic OS with the new web-based generative UI:
```bash
python server.py
```
*Navigate to `http://127.0.0.1:8000` in your browser to access the system.*

### 2. Run Headless CLI Mode
To run the core daemon in the terminal without the web interface:
```bash
python main.py
```
