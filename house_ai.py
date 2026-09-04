# %%
import requests
import json
import pandas as pd


df = pd.read_csv("Guaynabo_houses.csv")

requirements = {}

def extract_requirements(user_message, current_requirements):

    prompt = f"""
You are an AI real estate assistant.

Your job is to extract property requirements
from the user's message.

The available property fields are:

- price
- bedrooms
- bathrooms

Current requirements:

{json.dumps(current_requirements)}

User message:

{user_message}

Return JSON ONLY.

Use this format:

{{
    "bedrooms": null,
    "bathrooms": null,
    "price_operator": null,
    "price": null
}}

Rules:

- If the user mentions bedrooms, extract the number.
- If the user mentions bathrooms, extract the number.
- If the user mentions a city, extract it.
- If the user requires parking, use true.
- If the user gives a maximum price, use "<=".
- If the user gives a minimum price, use ">=".
- If the user does not mention something, keep it null.
- Return JSON only.
"""

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

        return {}

    try:

        answer = data["choices"][0]["message"]["content"]

    except (KeyError, IndexError):

        print("\nCould not find AI answer.")

        return {}

    print(answer)

    try:

        parsed_answer = json.loads(answer)

    except json.JSONDecodeError:

    

        print("Raw answer:")
        print(answer)

        return {}

    print("\n=================================")
    print("PARSED REQUIREMENTS")
    print("=================================")

    print(parsed_answer)

    return parsed_answer


def update_requirements(current, new):
    
    for key, value in new.items():

        if value is not None:

            current[key] = value
            
    return current


def search_properties(df, requirements):

    results = df.copy()

    column_mapping = {

        "bedrooms": "bed",
        "bathrooms": "bath",
        "city": "city",
        "price": "price",
        "parking": "parking"

    }

    for key, value in requirements.items():


        if value is None:

            print("Skipped: value is None")

            continue

        if key == "price_operator":

            print("Skipped: price operator")

            continue

        column = column_mapping.get(key)

        if column is None:

            print("Skipped: no column mapping")

            continue

        if column not in results.columns:

            print("Skipped: column does not exist")

            continue

        print("Filtering column:", column)

        print("Rows before:", len(results))

    
        

        if key == "price":

            operator = requirements.get("price_operator")

            print("Price operator:", operator)

            results[column] = pd.to_numeric(
                results[column],
                errors="coerce"
            )

            if operator == "<=":

                results = results[
                    results[column] <= float(value)
                ]

            elif operator == ">=":

                results = results[
                    results[column] >= float(value)
                ]

            else:

                results = results[
                    results[column] == float(value)
                ]

      
        elif isinstance(value, bool):

            print("Boolean filter")

            results = results[
                results[column] == value
            ]

        else:

            print("Numeric filter")

            results[column] = pd.to_numeric(
                results[column],
                errors="coerce"
            )

            print("Unique values in column:")
            print(results[column].unique())

            print("Looking for:", value)

            results = results[
                results[column] == float(value)
            ]

    return results


while True:

    user = input("\nYou: ")

    if user.lower().strip() == "exit":

        print("bye")
        break


    new_requirements = extract_requirements(
        user,
        requirements
    )

  
    requirements = update_requirements(
        requirements,
        new_requirements
    )

   
    if not requirements:

        print(
            "\nChatbot: "
            "Hi  my name is ai assistant! Tell me what kind of house you are looking for."
        )

        continue

    print(requirements)


    results = search_properties(
        df,
        requirements
    )


    if results.empty:

        print(
            "\nChatbot: "
            "I couldn't find any matching houses."
        )

    else:

        print(
            f"\nChatbot: "
            f"I found {len(results)} matching houses:\n"
        )

        display(results)

# %%



