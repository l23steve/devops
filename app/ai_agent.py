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

class AIAgent:
    def __init__(self, docker_manager, api_key: str, base_url: str = "https://openrouter.ai/api/v1"):
        self.docker_manager = docker_manager
        self.client = openai.OpenAI(api_key=api_key, base_url=base_url)
        self.messages: List[Dict[str, str]] = [
            {
                "role": "system",
                "content": "You are a devops AI. Use `run_command` to execute commands in the container. Run as many commands as needed to complete the task."
            }
        ]

    def chat(self, user_message: str, stream_callback=None):
        self.messages.append({"role": "user", "content": user_message})
        while True:
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=self.messages,
                    tools=[RUN_COMMAND_TOOL]
                )
            except openai.OpenAIError as exc:
                return f"Error communicating with language model: {exc}"
            message = response.choices[0].message
            if message.tool_calls:
                for call in message.tool_calls:
                    if call.function.name == "run_command":
                        args = json.loads(call.function.arguments)
                        output = self.docker_manager.run_command(
                            args["command"], stream_callback=stream_callback
                        )
                        self.messages.append({"role": "assistant", "tool_calls": message.tool_calls})
                        self.messages.append({
                            "role": "tool",
                            "tool_call_id": call.id,
                            "name": "run_command",
                            "content": output
                        })
            else:
                self.messages.append({"role": "assistant", "content": message.content})
                return message.content
