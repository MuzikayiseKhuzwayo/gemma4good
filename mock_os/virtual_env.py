class MockVirtualOS:
    """
    A simulated environment to validate the AOS interactions without
    touching the host operating system. Used for sandboxing and CI/CD.
    """
    def __init__(self):
        self.file_system = {}
        self.network_logs = []
        self.active_services = []
        self.notifications = []
        
    def write_file(self, path, content):
        self.file_system[path] = content
        print(f"[VirtualOS] File written: {path}")
        return True
        
    def read_file(self, path):
        if path in self.file_system:
            return self.file_system[path]
        # Fallback for minor path discrepancies (e.g., cake.txt vs /cake.txt)
        for stored_path, content in self.file_system.items():
            if stored_path.endswith(path) or path.endswith(stored_path):
                return content
        return None
        
    def delete_file(self, path):
        if path in self.file_system:
            del self.file_system[path]
            print(f"[VirtualOS] File deleted: {path}")
            return True
        print(f"[VirtualOS] Delete failed. File not found: {path}")
        return False
        
    def search_memory(self, query):
        # Basic mock text search to represent Vector DB semantic search
        results = []
        for path, content in self.file_system.items():
            if query.lower() in content.lower() or query.lower() in path.lower():
                results.append(path)
        print(f"[VirtualOS] Search results for '{query}': {results}")
        return results
        
    def send_network_request(self, url, payload):
        log = {"url": url, "payload": payload, "status": "200 OK"}
        self.network_logs.append(log)
        print(f"[VirtualOS] Network request sent to {url}")
        return log
        
    def show_notification(self, message):
        self.notifications.append(message)
        print(f"[VirtualOS] Notification displayed: {message}")
        return True
        
    def get_state_summary(self):
        return {
            "files_in_system": list(self.file_system.keys()),
            "total_network_requests": len(self.network_logs),
            "total_notifications": len(self.notifications)
        }
