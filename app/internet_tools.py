import os
import openai

class WebSearchTool:
    def __init__(self, api_key: str, base_url: str = "https://openrouter.ai/api/v1"):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_KEY"))

    def search(self, query: str):
        response = self.client.responses.create(
            model="gpt-4.1",
            input=query,
            tools=[{"type": "web_search_preview"}]
        )
        print(response.output_text)
        return response.output_text
