from dataclasses import dataclass
from temporalio import activity
from ollama import chat, ChatResponse

@dataclass
class OllamaPromptInput:
    prompt: str
    context_instructions: str

class OllamaActivities:
    @activity.defn
    def prompt_ollama(self, input: OllamaPromptInput) -> str:
        model_name = 'mistral'
        messages = [
            {
                'role': 'system',
                'content': input.context_instructions,
            },
            {
                'role': 'user',
                'content': input.prompt,
            }
        ]

        response: ChatResponse = chat(model=model_name, messages=messages)
        return response.message.content
