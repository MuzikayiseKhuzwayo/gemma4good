# Reference: Intent Schemas & Payloads

This document defines the formal schema and behavior contracts for all abstract intent types recognized by the `GemmaLatentKernel` and executed by the `ShellAgent`.

---

## 1. Intent Object Structure

Every intent emitted by the Latent Kernel is an element within a top-level JSON array. Each object adheres to the following interface:

```typescript
interface IntentObject {
  /** Step-by-step chain-of-thought explaining why this intent was selected */
  thought_process: string;
  
  /** The abstract OS intent type */
  type: IntentType;
  
  /** Typed payload matching the specific intent type */
  payload: IntentPayload;
}

type IntentType = 
  | "WRITE_FILE"
  | "READ_FILE"
  | "DELETE_FILE"
  | "SEARCH_MEMORY"
  | "SEND_MESSAGE"
  | "NOTIFY_USER"
  | "ASK_USER_INPUT";
```

---

## 2. Intent Specifications

### 2.1. `WRITE_FILE`
* **Purpose:** Create or overwrite a file in the filesystem.
* **Payload Schema:**
  ```json
  {
    "path": "/path/to/target.txt",
    "content": "UTF-8 string content"
  }
  ```
* **Fallback Resolution:** If `"path"` is omitted, the Shell Agent inspects alternative keys (`"filename"`, `"name"`) or detects paths embedded in payload values. If unresolved, it defaults to `/tmp/default.txt`.
* **Execution Return:** `boolean` (`True` if written successfully).

---

### 2.2. `READ_FILE`
* **Purpose:** Read and return the text contents of a target file.
* **Payload Schema:**
  ```json
  {
    "path": "/path/to/target.txt"
  }
  ```
* **Execution Return:** `string | null` (File content string if found; `null` if the file does not exist).
* **Feedback Loop:** In ReAct mode, the returned string is fed back into the Latent Kernel via `[System Callback]`.

---

### 2.3. `DELETE_FILE`
* **Purpose:** Remove a specified file from the filesystem.
* **Payload Schema:**
  ```json
  {
    "path": "/path/to/target.txt"
  }
  ```
* **Execution Return:** `boolean` (`True` if deleted; `False` if not found).

---

### 2.4. `SEARCH_MEMORY`
* **Purpose:** Query the semantic/vector memory layer for indexed concepts, notes, or files.
* **Payload Schema:**
  ```json
  {
    "query": "search query terms"
  }
  ```
* **Execution Return:** `string[]` (Array of matching file paths or memory node identifiers).
* **Feedback Loop:** The results array is injected into the ReAct auto-callback to trigger subsequent analysis or reading.

---

### 2.5. `SEND_MESSAGE`
* **Purpose:** Route an outbound communication payload to a network messaging service.
* **Payload Schema:**
  ```json
  {
    "to": "recipient_identifier",
    "body": "message text"
  }
  ```
* **Target Endpoint:** In sandbox mode, routed to `api://messaging`.
* **Execution Return:** Object:
  ```json
  {
    "url": "api://messaging",
    "payload": { "to": "...", "body": "..." },
    "status": "200 OK"
  }
  ```

---

### 2.6. `NOTIFY_USER`
* **Purpose:** Display a high-priority system notification or terminal message to the operator.
* **Payload Schema:**
  ```json
  {
    "message": "Notification text string"
  }
  ```
* **Terminal Status:** `NOTIFY_USER` is a terminal intent; it stops the autonomous ReAct callback loop.
* **Execution Return:** `boolean` (`True`).

---

### 2.7. `ASK_USER_INPUT`
* **Purpose:** Pause autonomous execution to solicit required missing context or operator confirmation.
* **Payload Schema:**
  ```json
  {
    "prompt": "Clarifying question for the operator"
  }
  ```
* **Terminal Status:** `ASK_USER_INPUT` halts the autonomous loop and yields control back to the operator.
* **Execution Return:** `string` (The clarifying question string).

---

## 3. Kernel Output Envelope Example

```json
[
  {
    "thought_process": "The user asked to save notes about the physics exam. I need to write the file to /notes/physics.txt.",
    "type": "WRITE_FILE",
    "payload": {
      "path": "/notes/physics.txt",
      "content": "Physics Exam Review: Newton's Laws and Energy Conservation."
    }
  },
  {
    "thought_process": "File written. I will notify the user that their notes are secured.",
    "type": "NOTIFY_USER",
    "payload": {
      "message": "Physics notes successfully saved to /notes/physics.txt."
    }
  }
]
```
