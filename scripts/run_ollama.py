from ollama import chat, ChatResponse


def main():
    model_name = "mistral"

    # The messages to pass to the model
    messages = [
        {
            "role": "user",
            "content": "Why is the sky blue?",
        }
    ]

    # Call ollama's chat function
    response: ChatResponse = chat(model=model_name, messages=messages)

    # Print the full message content
    print(response.message.content)


if __name__ == "__main__":
    main()
