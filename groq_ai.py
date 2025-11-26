from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("❌ GROQ_API_KEY not found in .env")

client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """
Give useful and shortly answers,
Don't forget to add, "sir".
"""

chat_history = []

def get_best_model():
    model_list = client.models.list()

    available = [m.id for m in model_list.data]
    print("Available Groq Models:\n", available)

    priority = [
        "llama-3.3-70b",
        "llama-3.2-90b",
        "llama-3.2-70b",
        "llama-3.1-8b",
        "mixtral-8x7b",
        "gemma2-9b-it"
    ]

    for name in priority:
        for model_id in available:
            if name in model_id.lower():
                print(f"\n✔ Selected model: {model_id}\n")
                return model_id


    return available[0]

BEST_MODEL = get_best_model()

def get_response(user_text):
    global chat_history

    chat_history.append({"role": "user", "content": user_text})

    messages = (
        [{"role": "system", "content": SYSTEM_PROMPT}]
        + chat_history[-5:]
    )

    response = client.chat.completions.create(
        model=BEST_MODEL,
        messages=messages,
        max_tokens=200
    )

    text = response.choices[0].message.content.strip()
    chat_history.append({"role": "assistant", "content": text})
    return text


def reset_history():
    global chat_history
    chat_history = []
