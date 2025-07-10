import json
import openai
from typing import List, Dict

RUN_COMMAND_TOOL = {
    "type": "function",
    "function": {
        "name": "run_command",
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
    "function": {
        "name": "search_internet",
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
        self.client = openai.OpenAI(api_key=api_key, base_url=base_url)
        self.messages: List[Dict[str, str]] = [
            {
                "role": "system",
                "content": """
                You are a devops AI. You are an expert at working with people to solve their sysops problems.
                Use `run_command` to execute commands in the container that has full internet access. It runs Ubuntu and has the AWS CLI installed.
                You are free to install any tools that will help you solve the problem.
                Use `search_internet` to search the internet for information.
                Run as many commands as needed to complete the task.
                """
            }
        ]

    def chat(self, user_message: str, stream_callback=None):
        self.messages.append({"role": "user", "content": user_message})
        while True:
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=self.messages,
                    tools=[RUN_COMMAND_TOOL, RUN_INTERNET_TOOL]
                )
            except openai.OpenAIError as exc:
                return f"Error communicating with language model: {exc}"
            message = response.choices[0].message
            if message.tool_calls:
                self.messages.append({"role": "assistant", "tool_calls": message.tool_calls})
                for call in message.tool_calls:
                    args = json.loads(call.function.arguments)
                    print(f"Tool call: {call.function.name} with args: {args}")
                    if call.function.name == "run_command":
                        output = self.docker_manager.run_command(args["command"])
                        if stream_callback:
                            prompt = f"ai@container:~$ {args['command']}\n"
                            stream_callback(prompt + output)
                        self.messages.append({
                            "role": "tool",
                            "tool_call_id": call.id,
                            "name": "run_command",
                            "content": output if len(output) < 50000 else f"Command completed successfully, output too large ({len(output)} bytes)"
                        })
                    if call.function.name == "search_internet":
                        output = self.internet_tools.search(args["query"])
                        self.messages.append({
                            "role": "tool",
                            "tool_call_id": call.id,
                            "name": "run_command",
                            "content": output
                        })
                        

            else:
                self.messages.append({"role": "assistant", "content": message.content})
                return message.content
