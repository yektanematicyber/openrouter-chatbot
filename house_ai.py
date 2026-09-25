# %%
import requests
import json
import pandas as pd
import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import faiss
import time
import numpy as np

load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")


df = pd.read_csv("Guaynabo_houses.csv")


renaming = {
    "bed": "bedrooms",
    "bath": "bathrooms",
    "house_size": "house size"
}

df = df.rename(columns=renaming)
df["text"] = df.apply(
    lambda row: f"""
    House ID: {row['id']}
    Price: {row['price']}
    Bedrooms: {row['bedrooms']}
    Bathrooms: {row['bathrooms']}
    House size: {row['house size']}
    """,
    axis=1
)
embedding_model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)

# 5. Create embeddings
embeddings = embedding_model.encode(
    df["text"].tolist()
)

print("Embeddings created:", len(embeddings))



embeddings = np.array(embeddings).astype("float32")

index = faiss.IndexFlatL2(
    embeddings.shape[1]
)

index.add(embeddings)

memory = []



def create_query_embedding(query):

    query_embedding = embedding_model.encode(
        [query]
    ).astype("float32")

    return query_embedding

def search_faiss(query_embedding, k):

    distances, indices = index.search(
        query_embedding,
        k
    )

    return distances, indices

def get_houses(indices, distances):

    results = df.iloc[indices[0]].copy()

    results["distance"] = distances[0]

    return results

def retrieve(query, k=20):

    query_embedding = create_query_embedding(query)

    distances, indices = search_faiss(
        query_embedding,
        k
    )

    results = get_houses(
        indices,
        distances
    )

    return results
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



    retrieved_houses = retrieve(user, k=30)
    print("\nRetrieved houses:")
    print(
        retrieved_houses[
            ["id", "bedrooms", "bathrooms", "price", "distance"]
        ]
    )

    start_time = time.time()

    response = llm(
    user,
    retrieved_houses.to_json(orient="records"),
    memory
)

    llm_time = time.time() - start_time

    print("\nLLM response time:", llm_time, "seconds")

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


    print(
        "Confidence:",
        response.get("confidence", 0),
        "%"
    )

    print("\nHouses:")
    print(result)