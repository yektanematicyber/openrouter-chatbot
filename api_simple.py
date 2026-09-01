import requests
import json

while True:
    user = input(" ")

    if user.lower() == "exit":
        print("bye")
        break

    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": "Bearer ",
            "Content-Type": "application/json",
        },
        data=json.dumps({
            "model": "openrouter/free",
            "messages": [
                {
                    "role": "user",
                    "content": user
                }
            ],
            "reasoning": {"enabled": True}
        })
    )
    data = response.json()


    answer = data["choices"][0]["message"]["content"]

    print("Chatbot:", answer)