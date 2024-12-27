from openai import OpenAI
import os
from typing import override
from openai import AssistantEventHandler
import json

class Assistant:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        self.thread = self.client.beta.threads.create()
        self.functions = [
            # {"type": "code_interpreter"},
            {
                "type": "function",
                "function": {
                    "name": "get_current_weather",
                    "description": "Retrieve the current weather for a specified location.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "The city and country, e.g., 'Toronto, Canada'."
                            }
                        },
                        "required": ["location"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "calculate_sum",
                    "description": "Calculate the sum of two numbers.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "a": {
                                "type": "number",
                                "description": "The first number."
                            },
                            "b": {
                                "type": "number",
                                "description": "The second number."
                            }
                        },
                        "required": ["a", "b"]
                    }
                }
            }
        ]
        self.assistant = self.client.beta.assistants.create(
            name="Marketing Assistant",
            instructions="You are a marketing assistant. You are tasked with creating a marketing plan for a product as mentioned and desired by the user.",
            tools=self.functions,
            model="gpt-4",
        )
        

    def add_message(self, message):
        messages = self.client.beta.threads.messages.create(
            thread_id=self.thread.id,
            role="user",
            content=message,
        )

    def run_assistant(self):
        print(f"DEBUG: Creating run with thread ID: {self.thread.id} and assistant ID: {self.assistant.id}")
        # First create the run
        with self.client.beta.threads.runs.stream(
            thread_id=self.thread.id,
            assistant_id=self.assistant.id,
            instructions="Please address the user as Jane Doe. The user has a premium account.",
            event_handler=EventHandler(),
        ) as stream:
            stream.until_done()
            final_run = stream.get_final_run()
            if final_run.last_error:
                print(f"DEBUG: Stream completed with status: {final_run.last_error}")
            elif final_run.status == 'completed':
                print(f"DEBUG: Stream completed with status: {final_run.status}")
            elif final_run.status == 'cancelled':
                print(f"DEBUG: Stream cancelled with status: {final_run.status}")
            elif final_run.status == 'failed':
                print(f"DEBUG: Stream failed with status: {final_run.status}")
            elif final_run.status == 'requires_action':
                print(f"DEBUG: Stream requires action with status: {final_run.status}")
                self.handle_requires_action(self, final_run, final_run.id)
            return final_run

    def handle_requires_action(self, data, run_id):
        tool_outputs = []
        
        for tool in data.required_action.submit_tool_outputs.tool_calls:
            if tool.function.name == "get_current_temperature":
                tool_outputs.append({"tool_call_id": tool.id, "output": "57"})
            elif tool.function.name == "get_rain_probability":
                tool_outputs.append({"tool_call_id": tool.id, "output": "0.06"})
            
            # Submit all tool_outputs at the same time
            self.submit_tool_outputs(self, tool_outputs, run_id)

    def submit_tool_outputs(self, tool_outputs, run_id):
        # Use the submit_tool_outputs_stream helper
        
        with self.client.beta.threads.runs.submit_tool_outputs_stream(
        thread_id=self.current_run.thread_id,
        run_id=run_id,
        tool_outputs=tool_outputs,
        event_handler=EventHandler(),
        ) as stream:
            for text in stream.text_deltas:
                print(text, end="", flush=True)
            print()

    def get_messages(self, run):
        messages = self.client.beta.threads.messages.list(thread_id=self.thread.id)
        if run.status == 'completed':
            return messages 
        else:
            return run.status

    def get_thread(self):
        return self.client.beta.threads.retrieve(thread_id=self.thread.id)
    
    def get_current_weather(self, location):
        return f"The current weather in {location} is 72 degrees."
    
    def calculate_sum(self, a, b):
        return a + b

class EventHandler(AssistantEventHandler):
    @override
    def on_event(self, event):
        # Retrieve events that are denoted with 'requires_action'
        # since these will have our tool_calls
        if event.event == 'thread.run.requires_action':
            run_id = event.data.id  # Retrieve the run ID from the event data
            print(f"DEBUG: Run ID >", run_id)
            self.handle_requires_action(event.data, run_id)


    @override
    def on_text_created(self, text) -> None:
        print(f"assistant > ", end="", flush=True)
        
    @override
    def on_text_delta(self, delta, snapshot):
        print(delta.value, end="", flush=True)
        
    @override
    def on_run_started(self, run) -> None:
        print(f"\nDEBUG: Run started with ID: {run.id}")
        
    @override
    def on_tool_call_created(self, tool_call):
        pass

    @override
    def on_tool_call_delta(self, delta, snapshot):
        if delta.type == 'code_interpreter':
            if hasattr(delta.code_interpreter, 'input') and delta.code_interpreter.input:
                print(delta.code_interpreter.input, end="", flush=True)
            if hasattr(delta.code_interpreter, 'outputs') and delta.code_interpreter.outputs:
                print(f"\n\noutput >", flush=True)
                for output in delta.code_interpreter.outputs:
                    print(f"\n\noutput logs >", output)
                    if output.type == "logs":
                        print(f"\n{output.logs}", flush=True)
        elif delta.type == 'function':
            try:
                function_name = delta.function.name
                print(f"DEBUG: Function name >", delta)
                
                # Check if arguments exist and are not empty
                if hasattr(delta.function, 'arguments') and delta.function.arguments:
                    try:
                        # Parse JSON string to dict
                        arguments = json.loads(delta.function.arguments)
                        print(f"DEBUG: Parsed arguments >", arguments)
                        
                        # Call the appropriate function based on name
                        if function_name == 'get_current_weather':
                            result = self.get_current_weather(arguments.get('location'))
                            print(f"DEBUG: Weather result >", result)
                        elif function_name == 'calculate_sum':
                            result = self.calculate_sum(arguments.get('a'), arguments.get('b'))
                            print(f"DEBUG: Sum result >", result)
                    except json.JSONDecodeError as e:
                        print(f"DEBUG: JSON parsing error >", str(e))
                else:
                    print(f"DEBUG: No arguments provided for function {function_name}")
            except Exception as e:
                print(f"DEBUG: Error occurred >", str(e))

    def get_current_weather(self, location):
            return f"The current weather in {location} is 72 degrees."