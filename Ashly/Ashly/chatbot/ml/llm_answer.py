# chatbot/ml/llm_answer.py
import os
from openai import OpenAI
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from Ashly.chatbot.models import Disease

# ⚙️ Configura tu clave (o usa variable de entorno)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_context_from_db(query_text, top_n=3):
    """
    Busca las enfermedades más relevantes en base de datos (usando TF-IDF)
    y devuelve las top_n con su información concatenada.
    """
    diseases = Disease.objects.all()
    if not diseases.exists():
        return "No hay enfermedades registradas en la base de datos."

    docs = [f"{d.name}. {d.symptoms}. {d.description}. {d.recommendations}" for d in diseases]
    vectorizer = TfidfVectorizer(stop_words='spanish')
    matrix = vectorizer.fit_transform(docs)

    query_vec = vectorizer.transform([query_text])
    sims = cosine_similarity(query_vec, matrix)[0]

    top_idx = sims.argsort()[-top_n:][::-1]
    top_diseases = [diseases[i] for i in top_idx]

    context = "\n\n".join([
        f"🌿 Enfermedad: {d.name}\nSíntomas: {d.symptoms}\nDescripción: {d.description}\nRecomendaciones: {d.recommendations}"
        for d in top_diseases
    ])
    return context

def generate_technical_answer(user_query):
    """
    Crea una respuesta técnica usando GPT con contexto agronómico de tu base de datos.
    """
    context = get_context_from_db(user_query)

    prompt = f"""
Eres un asistente agrónomo especializado en manejo fitosanitario de cultivos.

Consulta del usuario:
"{user_query}"

Información técnica relevante de la base de datos:
{context}

Genera una respuesta técnica breve, clara y profesional en español, incluyendo:
- Diagnóstico probable (si aplica)
- Causas o patógeno implicado
- Recomendaciones de manejo integrado (biológico, cultural y químico)
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",  # puedes usar "gpt-4o" si tienes acceso completo
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4
    )

    return response.choices[0].message.content.strip()
