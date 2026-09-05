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


# %%
def llm(user_message, input_data):

    prompt = f"""
You are an AI real estate assistant.

Your job is to find the property that best matches
the user's request.

The available property fields are:
- id
- price
- bedrooms
- bathrooms
- house size

Available properties:

{input_data}

User message:

{user_message}

Choose the property that best matches the user's request.

Return JSON only:

{{
    "id": null,
    "aiopinion": null
}}
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
        df.to_json(orient="records")
    )


    if response["id"] is None:

        print(
            "\nChatbot:",
            response.get(
                "aiopinion",
                "I couldn't find a matching house."
            )
        )

        continue


    result = df[df["id"] == response["id"]]


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