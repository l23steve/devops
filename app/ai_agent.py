import json
import openai
from typing import List, Dict
import uuid

def make_id(prefix):
    return f"{prefix}_{uuid.uuid4().hex}"

def append_function_call(messages, call):
    call_id = make_id("fc")
    messages.append({
        "type": "function_call",
        "call_id": call_id,
        "name": call.name,
        "arguments": call.arguments
    })
    reasoning_id = make_id("rs")
    messages.append({
        "type": "reasoning",
        "id": reasoning_id,
        "summary": f"Explains why {call.name} is being called"  # Only here!
    })
    return call_id

def append_function_call_output(messages, call_id, call, output):
    output_id = make_id("fco")
    messages.append({
        "type": "function_call_output",
        "id": output_id,
        "call_id": call_id,
        "name": call.name,
        "output": output,
    })
    reasoning_id = make_id("rs")
    messages.append({
        "type": "reasoning",
        "id": reasoning_id,
        "input_message_id": output_id,
        "summary": f"Explains output for {call.name}"  # Only here!
    })
    return output_id



RUN_COMMAND_TOOL = {
    "type": "function",
    "name": "run_command",
    "function": {
        "description": "Run a shell command inside the docker container.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Command to run"}
            },
            "required": ["command"]
        }
    }
}
RUN_INTERNET_TOOL = {
    "type": "function",
    "name": "search_internet",
    "function": {
        "description": "Search the internet for information.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"}
            },
            "required": ["query"]
        }
    }
}



class AIAgent:
    def __init__(self, docker_manager, internet_tools, api_key: str, base_url: str = "https://openrouter.ai/api/v1"):
        self.docker_manager = docker_manager
        self.internet_tools = internet_tools
        self.client = openai.OpenAI(api_key=api_key)
        self.messages: List[Dict[str, str]] = [
            {
                "type": "message",
                "role": "system",
                "content": """
                You are a devops AI. You are an expert at working with people to solve their sysops problems.
                Use `run_command` to execute commands in the container that has full internet access.
                The `run_command` tool runs on Ubuntu and has the AWS CLI installed and full configured for the user's account.
                You have the SSH key necessary to access any EC2 resources.
                To access any RDS or Opensearch resources, you will need to SSH into the EC2 instance and run commands there.
                You are free to install any tools that will help you solve the problem.
                Use `search_internet` to search the internet for information.
                Run as many commands as needed to complete the task.
                Be proactive. Run all read-only commands you think will help you understand the user's problem.
                """
            }
        ]

    def handle_tool_call(self, call):
        # Validate arguments
        if not call.arguments:
            error_msg = f"The '{call.name}' tool was called but no arguments were provided. Please specify the required arguments."
            self.messages.append({"type": "message", "role": "assistant", "content": error_msg})
            return False

        try:
            args = json.loads(call.arguments)
        except Exception as e:
            error_msg = f"The '{call.name}' tool was called, but the arguments were not valid JSON: {e}. Please correct and try again."
            self.messages.append({"type": "message", "role": "assistant", "content": error_msg})
            return False

        # Check required fields for run_command
        if call.name == "run_command":
            if not isinstance(args, dict) or "command" not in args or not args["command"]:
                error_msg = f"The 'run_command' tool requires a 'command' argument, but it was missing or empty. Please provide the shell command to run."
                self.messages.append({"type": "message", "role": "user", "content": error_msg})
                return False

        return True

    
    def chat(self, user_message: str, stream_callback=None):
        self.messages.append({"type": "message", "role": "user", "content": user_message})
        while True:
            try:
                response = self.client.responses.create(
                    model="o4-mini",
                    input=self.messages,
                    reasoning={"effort": "medium"},
                    tools=[RUN_COMMAND_TOOL, RUN_INTERNET_TOOL],
                    store=False
                )
            except openai.OpenAIError as exc:
                return f"Error communicating with language model: {exc}"

            print(response)
            if getattr(response, "output", None):
                message = response.output
                for call in message:
                    if call.type != "function_call":
                        continue

                    if not self.handle_tool_call(call):
                        continue
                    # Use fixed helper to append with all required fields
                    call_id = append_function_call(self.messages, call)
                    call.id = call_id  # For later use

                    args = json.loads(call.arguments)
                    print(f"Tool call: {call.name} with args: {args}")

                    if call.name == "run_command":
                        output = self.docker_manager.run_command(args["command"])
                        if stream_callback:
                            prompt = f"ai@container:~$ {args['command']}\n"
                            stream_callback(prompt + output)

                        append_function_call_output(self.messages, call_id, call, output)

                    if call.name == "search_internet":
                        output = self.internet_tools.search(args["query"])
                        append_function_call_output(self.messages, call_id, call, output)
            else:
                self.messages.append({"type": "message", "role": "assistant", "content": message.content})
                return message.content
