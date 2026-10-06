# How-To: Run the Automated Validation Suite

This guide explains how to execute and interpret the automated verification suites for the Agentic Operating System.

---

## 1. Available Test Suites

AOS includes two primary automated validation scripts:

1. **`validate.py` (Smoke & Lifecycle Test):**
   * Validates multi-step execution: network dispatch, file writing, token budget tracking, and Virtual OS state summary.
   * Execution time: ~2 seconds.
2. **`test_all_intents.py` (Comprehensive Intent Coverage Test):**
   * Validates all seven primary intent types (`WRITE_FILE`, `READ_FILE`, `DELETE_FILE`, `SEARCH_MEMORY`, `SEND_MESSAGE`, `NOTIFY_USER`, `ASK_USER_INPUT`).
   * Tests context gathering and interactive pause loops.
   * Execution time: ~15-20 seconds (includes rate limit mitigation pauses).

---

## 2. Running `validate.py`

Execute from the repository root:

```bash
python validate.py
```

### Expected Output
```text
Starting Virtual OS Validation Run...

Initializing Semantic File System (Vector DB Layer)
Booting Inference Kernel (Model: gemma-4-31b-it, Mode: google_genai)...
Using Google GenAI API for inference (No local download required).

--- User Intent Detected: 'Send a message to Alice saying I will be late, and save a note.' ---
--- Simulating AI Intent Generation via Gemma ---

--- Routing Intents through Shell Agent to Virtual OS ---
Mapping intent to OS API calls: SEND_MESSAGE
[VirtualOS] Network request sent to api://messaging
Mapping intent to OS API calls: WRITE_FILE
[VirtualOS] File written: /notes/alice_late.txt

--- Virtual OS Final State ---
files_in_system: ['/notes/alice_late.txt']
total_network_requests: 1
total_notifications: 0

Validation Complete. System state accurately reflects AI intentions without host side-effects.
```

---

## 3. Running `test_all_intents.py`

Execute:

```bash
python test_all_intents.py
```

### Verification Checklist

Review the output to ensure each intent passes:

- [x] **`WRITE_FILE`**: Confirmed with `[VirtualOS] File written: /test/data.txt`
- [x] **`READ_FILE`**: Confirmed with `[VirtualOS] Content of /test/data.txt: Hello World`
- [x] **`DELETE_FILE`**: Confirmed with `[VirtualOS] File deleted: /test/data.txt`
- [x] **`SEARCH_MEMORY`**: Confirmed with `[VirtualOS] Search results for 'vacation plans': [...]`
- [x] **`SEND_MESSAGE`**: Confirmed with `[VirtualOS] Network request sent to api://messaging`
- [x] **`NOTIFY_USER`**: Confirmed with `[VirtualOS] Notification displayed: ...`
- [x] **`ASK_USER_INPUT`**: Confirmed with `[VirtualOS] Asking User: What is your favorite color?`

---

## 4. Running Offline Without API Keys

If you do not have an active `GEMINI_API_KEY`, modify the test file temporarily or configure the mode in code:

```python
inference_engine = GemmaLatentKernel(mode="mock")
```

The mock engine returns deterministic keyword-matched intents for immediate testing.
