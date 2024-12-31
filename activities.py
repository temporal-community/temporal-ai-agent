from temporalio import activity
from ollama import chat, ChatResponse

class OllamaActivities:
    @activity.defn
    def prompt_ollama(self, prompt: str) -> str:
        model_name = 'mistral'
        messages = [
            {
                'role': 'user',
                'content': prompt
            }
        ]

        # Call ollama's chat function
        response: ChatResponse = chat(model=model_name, messages=messages)
        
        # Return the model's text response
        return response.message.content
