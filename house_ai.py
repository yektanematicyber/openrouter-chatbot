# %%
import requests
import json
import pandas as pd
import os
from dotenv import load_dotenv


load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")


df = pd.read_csv("Guaynabo_houses.csv")


renaming = {
    "bed": "bedrooms",
    "bath": "bathrooms",
    "house_size": "house size"
}

df = df.rename(columns=renaming)

memory = []


# %%
def llm(user_message, input_data, memory):


    prompt = f"""
You are an AI real estate assistant.

Find all properties that match the user's request.

Available fields:
- id
- price
- bedrooms
- bathrooms
- house size

Properties:
{input_data}

Conversation memory:
{memory}

User message:
{user_message}

Return JSON only:

{{
    "ids": [],
    "confidence": 0,
    "aiopinion": ""
}}

Rules:
- Return all matching property IDs in "ids".
- "confidence" is a number from 0 to 100.
- If there are no matches, return an empty "ids" list.
- Use the conversation memory to understand previous requirements.
"""


    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",

        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        },

        data=json.dumps({
            "model": "openrouter/free",

            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],

            "reasoning": {
                "enabled": True
            }
        })
    )


    data = response.json()

    if response.status_code != 200:

        print("\nAPI ERROR!")
        print(response.text)

        return {}


    try:

        answer = data["choices"][0]["message"]["content"]

    except (KeyError, IndexError):

        print("\nCould not find AI answer.")

        return {}



    start = answer.find("{")
    end = answer.rfind("}") + 1

    if start == -1 or end == 0:

        print("\nCould not find JSON in AI answer.")

        return {}


    answer = answer[start:end]


    try:

        parsed_answer = json.loads(answer)

    except json.JSONDecodeError:

        print("\nThe AI did not return valid JSON.")
        print(answer)

        return {}


    return parsed_answer


# %%
while True:

    user = input("\nYou: ")


    # Exit
    if user.lower().strip() == "exit":

        print("Bye!")
        break



    response = llm(
        user,
        df.to_json(orient="records"),
        memory
    )

    memory.append({
        "user": user,
        "assistant": response
    })


    ids = response.get("ids", [])

    if not ids:
        print(
            "\nChatbot:",
            response.get(
                "aiopinion",
                "I couldn't find any matching houses."
        )
    )
    continue

    result = df[df["id"].isin(ids)]


    if result.empty:

        print("\nChatbot: I couldn't find this house.")

        continue


    print("\nChatbot:")

    print(
        response.get(
            "aiopinion",
            ""
        )
    )


    print("\nHouse:")

    print(result)