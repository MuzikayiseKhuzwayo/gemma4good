import os
import json
from http.server import SimpleHTTPRequestHandler, HTTPServer
from dotenv import load_dotenv

load_dotenv()

from shell_agent.api_mapper import ShellAgent
from semantic_fs.vector_store import SemanticFileSystem
from aos_kernel.inference import GemmaLatentKernel
from aos_kernel.context_manager import ContextBudgetManager

# Global state for the server
sfs = None
agent = None
inference_engine = None
context_manager = None

HISTORY_FILE = "conversation_history.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return []

def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f)

class AOSHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # Serve static files directly from generative_ui/web
        web_dir = os.path.join(os.path.dirname(__file__), "generative_ui", "web")
        super().__init__(*args, directory=web_dir, **kwargs)

    def do_GET(self):
        if self.path == '/api/history':
            history = load_history()
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"history": history}).encode('utf-8'))
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == '/api/intent':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)
            user_intent = data.get("intent", "")
            
            print(f"\n[API] Received Intent: {user_intent}")
            
            context_manager.active_context.append(f"User: {user_intent}")
            context_string = "\n".join(context_manager.active_context[-5:])
            
            # 1. Parse intent
            print("--- Parsing Intent via Latent Kernel ---")
            intents = inference_engine.parse_intent(user_intent, context_history=context_string)
            
            responses = []
            execution_logs = []
            if not intents:
                responses.append("[AOS Error] No executable intent recognized.")
            else:
                # 2. Execute mapped OS API calls
                for intent in intents:
                    context_manager.add_intent(150)
                    thought = intent.get("thought_process", "Direct execution.")
                    print(f"[Latent Kernel Thought]: {thought}")
                    
                    intent_type = intent.get("type")
                    payload = intent.get("payload", {})
                    
                    if intent_type == "NOTIFY_USER":
                        responses.append(payload.get("message", "Notification from system."))
                        continue
                        
                    try:
                        result = agent.execute_intent(intent_type, payload)
                        execution_logs.append(f"[{intent_type}] Result: {result}")
                        responses.append(f"[{intent_type}] Executed successfully.\nResult: {result}")
                        context_manager.active_context.append(f"Kernel Reasoned: {thought} | OS Executed: {intent_type} with result: {result}")
                    except Exception as e:
                        execution_logs.append(f"[{intent_type}] Failed: {str(e)}")
                        responses.append(f"[{intent_type}] Execution failed: {str(e)}")
                
                # 3. Formulate natural language response if OS actions were taken
                has_notify = any(i.get("type") == "NOTIFY_USER" for i in intents)
                if execution_logs and not has_notify:
                    print("--- Formulating Natural Language Response ---")
                    nl_response = inference_engine.generate_response(user_intent, execution_logs)
                    responses.append(f"🤖 {nl_response}")
                    
            # Combine all responses into a single bubble
            if responses:
                combined_response = "\n\n".join(responses)
                responses = [combined_response]
            
            history = load_history()
            history.append({"role": "user", "text": user_intent})
            for res_text in responses:
                history.append({"role": "system", "text": res_text})
            save_history(history)
            
            response_data = json.dumps({"responses": responses})
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(response_data.encode('utf-8'))
        elif self.path == '/api/new_chat':
            import time
            context_manager.active_context = []
            if os.path.exists(HISTORY_FILE):
                os.rename(HISTORY_FILE, f"archive_{int(time.time())}_{HISTORY_FILE}")
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "success"}).encode('utf-8'))
        else:
            self.send_error(404, "Not Found")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header("Access-Control-Allow-Headers", "X-Requested-With, Content-type")
        self.end_headers()

def run_server(port=8000):
    global sfs, agent, inference_engine, context_manager
    print("Booting Agentic OS Web Server...")
    
    # Initialize Core Kernel
    sfs = SemanticFileSystem()
    agent = ShellAgent(use_virtual_env=True)
    inference_engine = GemmaLatentKernel(mode="google_genai")
    context_manager = ContextBudgetManager()
    
    server_address = ('', port)
    httpd = HTTPServer(server_address, AOSHandler)
    print(f"\nServer running at http://127.0.0.1:{port}")
    print(f"Open http://127.0.0.1:{port}/index.html in your browser to view the interface.\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print("\nServer stopped.")

if __name__ == '__main__':
    run_server()
