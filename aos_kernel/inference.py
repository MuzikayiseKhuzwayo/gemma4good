import json
import os

class GemmaLatentKernel:
    """
    The core reasoning engine of the AOS, mapping natural language
    intent into latent space structure and outputting OS execution JSON.
    """
    def __init__(self, model_name="gemma-4-31b-it", mode="google_genai"):
        self.model_name = model_name
        self.mode = mode
        self.model = None
        self.tokenizer = None
        self.client = None
        
        print(f"Booting Inference Kernel (Model: {self.model_name}, Mode: {self.mode})...")
        
        if self.mode == "local":
            try:
                from transformers import AutoModelForCausalLM, AutoTokenizer
                import torch
                print("Loading PyTorch and Transformers for actual local inference...")
                self.tokenizer = AutoTokenizer.from_pretrained(model_name)
                self.model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    device_map="auto",
                    torch_dtype=torch.float16
                )
            except ImportError:
                print("Warning: transformers/torch not installed. Falling back to mock engine.")
                self.mode = "mock"
                
        elif self.mode == "google_genai":
            try:
                from google import genai
                self.api_key = os.environ.get("GEMINI_API_KEY")
                if not self.api_key:
                    print("Warning: GEMINI_API_KEY environment variable not set. Please set it to use google_genai mode.")
                self.client = genai.Client(api_key=self.api_key)
                print("Using Google GenAI API for inference (No local download required).")
            except ImportError:
                print("Warning: google-genai not installed. Falling back to mock engine.")
                self.mode = "mock"
            
        if self.mode == "mock":
            print("Using Mock Inference Engine for fast validation.")

    def parse_intent(self, user_prompt, context_history=""):
        """
        Parses a natural language prompt into a structured list of intents
        that the ShellAgent can execute.
        """
        system_prompt = """
        You are the Latent Kernel of an Agentic Operating System.
        Your job is to parse the User Prompt and output a JSON array of intents.
        Valid Intent Types: WRITE_FILE, READ_FILE, DELETE_FILE, SEARCH_MEMORY, SEND_MESSAGE, NOTIFY_USER, ASK_USER_INPUT.
        
        Required Schemas for 'payload':
        - SEND_MESSAGE: {"to": "recipient_name", "body": "message text"}
        - WRITE_FILE: {"path": "/path/to/file.txt", "content": "file contents"}
        - READ_FILE: {"path": "/path/to/file.txt"}
        - DELETE_FILE: {"path": "/path/to/file.txt"}
        - SEARCH_MEMORY: {"query": "search terms"}
        - NOTIFY_USER: {"message": "notification text"}
        - ASK_USER_INPUT: {"prompt": "Clarifying question for the user"}
        
        Required Output Structure:
        You must output a JSON array of intent objects. Each object MUST include a "thought_process" field where you explain your step-by-step reasoning BEFORE selecting the intent type.
        
        Example Output:
        [
          {
            "thought_process": "The user wants to know 1+2*4/2. By order of operations, 2*4=8, 8/2=4, 1+4=5. I will notify the user.",
            "type": "NOTIFY_USER", 
            "payload": {"message": "5"}
          }
        ]
        """
        
        if context_history:
            prompt = f"{system_prompt}\n\n--- Recent Interaction Context ---\n{context_history}\n--------------------------------\n\nUser Prompt: {user_prompt}\nJSON Output:\n["
        else:
            prompt = f"{system_prompt}\n\nUser Prompt: {user_prompt}\nJSON Output:\n["
        
        if self.mode == "mock":
            # Simple keyword-based mock for demonstration
            intents = []
            lower_prompt = user_prompt.lower()
            if "late" in lower_prompt and "alice" in lower_prompt:
                intents.append({"type": "SEND_MESSAGE", "payload": {"to": "Alice", "body": "I will be late"}})
                intents.append({"type": "WRITE_FILE", "payload": {"path": "/docs/notes/late.txt", "content": "Told Alice I'd be late."}})
                intents.append({"type": "NOTIFY_USER", "payload": {"message": "Message sent to Alice and noted."}})
            else:
                intents.append({"type": "NOTIFY_USER", "payload": {"message": "Intent not understood by mock parser."}})
            return intents
            
        elif self.mode == "google_genai":
            from google.genai import types
            
            try:
                # We format the prompt and pass it to the Google GenAI SDK
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        # We use the thinking config as shown in your snippet
                        thinking_config=types.ThinkingConfig(
                            thinking_level=types.ThinkingLevel.HIGH
                        ),
                        temperature=0.1 # low temp for JSON parsing
                    )
                )
                
                result = response.text
                json_str = "[" + result
                start = json_str.find('[')
                end = json_str.rfind(']') + 1
                json_str = json_str[start:end]
                return json.loads(json_str)
            except Exception as e:
                print(f"Google GenAI API Error: {e}")
                return []
                
        elif self.mode == "local":
            # Actual Gemma local inference
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
            outputs = self.model.generate(**inputs, max_new_tokens=200)
            result = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            try:
                start = result.find('[')
                end = result.rfind(']') + 1
                json_str = result[start:end]
                return json.loads(json_str)
            except Exception as e:
                print(f"Failed to parse model output: {e}")
                return []

    def generate_response(self, user_prompt, execution_logs):
        """
        Generates a natural language response based on the results of the OS execution.
        """
        system_prompt = (
            "You are the Agentic OS interface. "
            "The user made a request, and the system executed background tasks. "
            "Explain the results to the user in a natural, helpful, and concise way. "
            "Do NOT use JSON. If a search returned empty ([]), inform the user that no files were found. "
            "If a file was successfully written (True), confirm it to the user."
        )
        prompt = f"{system_prompt}\n\nUser Request: {user_prompt}\nSystem Execution Logs: {execution_logs}\n\nResponse:"
        
        if self.mode == "mock":
            return f"System operations completed based on your request. Logs: {execution_logs}"
            
        elif self.mode == "google_genai":
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt
                )
                return response.text.strip()
            except Exception as e:
                return f"Execution completed: {execution_logs}"
                
        elif self.mode == "local":
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
            outputs = self.model.generate(**inputs, max_new_tokens=150)
            return self.tokenizer.decode(outputs[0], skip_special_tokens=True).split("Response:")[-1].strip()

