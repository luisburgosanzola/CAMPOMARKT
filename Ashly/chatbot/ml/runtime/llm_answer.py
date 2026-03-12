import os
import base64
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=api_key)


def chat_answer(message: str):

    try:

        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """
Eres un asesor agrícola experto.

Ayudas a campesinos a diagnosticar enfermedades en cultivos.

Responde SIEMPRE en este formato:

Diagnóstico probable:
(explicación)

Recomendaciones:
- recomendación 1
- recomendación 2
- recomendación 3
"""
                },
                {
                    "role": "user",
                    "content": message
                }
            ],
            temperature=0.5
        )

        return completion.choices[0].message.content

    except Exception as e:
        print("Error LLM:", e)
        return "⚠️ No pude generar una respuesta en este momento."


def image_answer(image_bytes: bytes, extra_text=""):

    try:

        base64_image = base64.b64encode(image_bytes).decode("utf-8")

        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """
Eres un experto en diagnóstico de enfermedades de plantas.

Analiza la imagen y responde:

Diagnóstico probable:
(explicación)

Recomendaciones:
- acción 1
- acción 2
- acción 3
"""
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": extra_text or "Analiza esta planta"
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
        )

        return completion.choices[0].message.content

    except Exception as e:
        print("Error análisis imagen:", e)
        return "⚠️ No pude analizar la imagen."