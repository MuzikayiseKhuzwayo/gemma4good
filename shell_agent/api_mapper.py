from mock_os.virtual_env import MockVirtualOS

class ShellAgent:
    def __init__(self, use_virtual_env=False):
        self.virtual_os = MockVirtualOS() if use_virtual_env else None
        
    def execute_intent(self, intent_type, payload=None):
        print(f"Mapping intent to OS API calls: {intent_type}")
        
        if self.virtual_os:
            return self._execute_virtual(intent_type, payload)
        else:
            return self._execute_host(intent_type, payload)
            
    def _execute_virtual(self, intent_type, payload):
        payload = payload or {}
        
        # Robust path extraction
        path = payload.get('path', payload.get('filename', payload.get('name', '')))
        if not path and intent_type in ["WRITE_FILE", "READ_FILE", "DELETE_FILE"]:
            for v in payload.values():
                if isinstance(v, str) and ('.' in v or '/' in v):
                    path = v
                    break
                    
        content = payload.get('content', payload.get('body', payload.get('text', '')))
        
        if intent_type == "WRITE_FILE":
            path = path or '/tmp/default.txt'
            return self.virtual_os.write_file(path, content)
        elif intent_type == "READ_FILE":
            read_content = self.virtual_os.read_file(path)
            if read_content is not None:
                print(f"\n[VirtualOS] Content of {path}:\n{read_content}\n")
            else:
                print(f"\n[VirtualOS] Error: File '{path}' does not exist.\n")
            return read_content
        elif intent_type == "DELETE_FILE":
            return self.virtual_os.delete_file(path)
        elif intent_type == "SEARCH_MEMORY":
            return self.virtual_os.search_memory(payload.get('query', ''))
        elif intent_type == "ASK_USER_INPUT":
            prompt_text = payload.get('prompt', 'Please provide more input.')
            print(f"\n[VirtualOS] Asking User: {prompt_text}\n")
            return prompt_text
        elif intent_type == "SEND_MESSAGE":
            return self.virtual_os.send_network_request("api://messaging", payload)
        elif intent_type == "NOTIFY_USER":
            return self.virtual_os.show_notification(payload.get('message', 'Alert'))
        else:
            print(f"[VirtualOS] Unknown intent: {intent_type}")
            return False

    def _execute_host(self, intent_type, payload):
        # Stub for actual host OS execution (e.g. real Windows/Linux calls)
        print(f"[HostOS] Executing {intent_type} on actual host system (STUB)")
        return True
