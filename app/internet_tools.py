import openai

class WebSearchTool:
    def __init__(self, api_key: str, base_url: str = "https://openrouter.ai/api/v1"):
        self.client = openai.OpenAI(api_key="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")

    def search(self, query: str):
        response = self.client.responses.create(
            model="gpt-4.1",
            input=query,
            tools=[{"type": "web_search_preview"}]
        )
        print(response.output_text)
        return response.output_text
