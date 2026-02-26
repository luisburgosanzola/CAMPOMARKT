# Ashly/chatbot/views.py
from __future__ import annotations

import os
import json
import logging
import re
import unicodedata
from typing import Optional

from django.conf import settings
from django.core.files.storage import default_storage
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from .models import (
    Crop, Disease, Tool, KnowledgeArticle,
    CropProduction, Region,
    IrrigationGuide, FertilizationPlan,
    CropPractice, UploadedImage, ChatMessage, FAQ
)
from .ml.image_predictor import predict_disease

log = logging.getLogger(__name__)

# ==============================
# HTML
# ==============================


def chat_page(request):
    return render(request, "chatbot/chat.html")

# ==============================
# Utils de texto
# ==============================


def _norm(s: str) -> str:
    if not s:
        return ""
    s = s.lower()
    s = unicodedata.normalize("NFKD", s).encode(
        "ascii", "ignore").decode("ascii")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _tokens(message: str) -> set[str]:
    msg = _norm(message)
    return {t for t in re.split(r"[^a-z0-9]+", msg) if t}


def _keywords(message: str) -> list[str]:
    stop = {
        "de", "del", "la", "el", "los", "las", "para", "por", "con",
        "en", "un", "una", "y", "o", "que", "es", "al", "lo", "tengo",
        "mi", "mis", "se", "me", "ayuda", "como", "qué", "que",
    }
    toks = _tokens(message)
    return [t for t in toks if t not in stop and len(t) >= 3]


# ==============================
# Detección de cultivo
# ==============================
CROP_ALIASES = {
    "cafe": {"cafe", "café"},
    "tomate": {"tomate", "jitomate"},
    "cebolla": {"cebolla"},
    "maracuya": {"maracuya", "maracuyá", "fruta de la pasion", "fruta de la pasión", "passiflora"},
    "papa": {"papa", "patata"},
}


def detect_crop(message: str) -> Optional[Crop]:
    msg = _norm(message)

    for canonical, syns in CROP_ALIASES.items():
        if any(_norm(s) in msg for s in syns):
            c = Crop.objects.filter(name__icontains=canonical).first()
            if c:
                return c

    # fallback: match por nombre en BD
    for c in Crop.objects.all().only("id", "name"):
        if _norm(c.name) in msg:
            return c

    return None


# ==============================
# Detección de tema / intención
# ==============================
INTENT_KEYWORDS = {
    "densidad": {"densidad", "siembra", "espaciamiento", "distancia", "marco"},
    "plagas": {"plaga", "plagas", "enfermedad", "enfermedades", "insecto", "insectos", "hongo", "hongos", "virus", "bacteria", "bacterias", "mancha", "manchas", "roya", "pudricion", "pudrición"},
    "herramientas": {"herramienta", "herramientas", "equipo", "equipos", "azadon", "azadón", "machete", "aspersor", "bomba"},
    "riego": {"riego", "agua", "frecuencia", "regar", "goteo", "aspersion", "aspersión", "humedad"},
    "fertilizacion": {"fertilizacion", "fertilización", "abono", "abonado", "npk", "urea", "fosfato", "potasio", "nutriente", "nutrientes"},
    "produccion": {"produccion", "producción", "rendimiento", "toneladas", "costo", "rentabilidad", "precio"},
    "cultivo": {"clima", "temperatura", "altitud", "altura", "suelo", "terreno", "ciclo", "variedad", "variedades", "epoca", "época"},
}


def detect_topic(message: str) -> Optional[str]:
    msg = _norm(message)
    toks = _tokens(message)

    scores: dict[str, int] = {}
    for topic, kws in INTENT_KEYWORDS.items():
        for kw in kws:
            k = _norm(kw)
            if k in msg:
                scores[topic] = scores.get(topic, 0) + 2
            if k in toks:
                scores[topic] = scores.get(topic, 0) + 1

    if not scores:
        return None

    return sorted(scores.items(), key=lambda x: -x[1])[0][0]


# ==============================
# Detección de etapa
# ==============================
STAGE_KEYWORDS = {
    "establecimiento": {"siembra", "plantula", "plántula", "trasplante", "transplante"},
    "vegetativo": {"vegetativo", "crecimiento", "hojas"},
    "floracion": {"floracion", "floración", "flores", "boton", "botón", "boton floral", "botón floral"},
    "cuajado": {"cuajado", "cuaje"},
    "fructificacion": {"fructificacion", "fructificación", "fruto", "frutos", "llenado"},
    "madurez": {"madurez", "cosecha", "precosecha", "pre-cosecha"},
}


def detect_stage(message: str) -> str:
    msg = _norm(message)
    for stage, kws in STAGE_KEYWORDS.items():
        for kw in kws:
            if _norm(kw) in msg:
                return stage
    return ""

# ==============================
# Detección de región
# ==============================


def detect_region(message: str) -> Optional[Region]:
    msg = _norm(message)
    toks = _tokens(message)
    for r in Region.objects.all():
        name_n = _norm(r.name)
        if name_n in msg or any(t in name_n for t in toks):
            return r
    return None


# ==============================
# UX PRO: Plagas comunes por nombre
# ==============================
COMMON_PESTS = {
    "mosca blanca": {"mosca blanca", "whitefly", "bemisia", "aleurodidos"},
    "trips": {"trips", "thrips"},
    "broca": {"broca", "broca del cafe", "broca del café", "hypothenemus"},
    "minador": {"minador", "minador de la hoja", "leafminer"},
    "pulgones": {"pulgon", "pulgones", "afidos", "áfidos", "aphids"},
    "acaros": {"acaro", "acaros", "ácaro", "ácaros", "mites"},
    "tizon tardio": {"tizon tardio", "tizón tardío", "phytophthora"},
    "antracnosis": {"antracnosis", "anthracnose"},
    "oidio": {"oidio", "oídio", "powdery mildew"},
    "mildiu": {"mildiu", "mildiú", "downy mildew"},
}


def detect_pest_name(message: str) -> Optional[str]:
    msg = _norm(message)
    for canonical, syns in COMMON_PESTS.items():
        if any(_norm(s) in msg for s in syns):
            return canonical
    return None


def followup_questions_for_pest(pest: str) -> list[str]:
    # Top preguntas cortas, útiles en campo
    base = [
        "¿Ves insectos pequeños en el envés (parte de atrás) de la hoja?",
        "¿La hoja está pegajosa (melaza) o se pone negra (fumagina)?",
        "¿El daño es más en hojas nuevas o viejas?",
        "¿El clima está más seco o húmedo estos días?",
    ]
    if pest == "mosca blanca":
        return [
            "¿Ves mosquitas blancas que vuelan al mover la planta?",
            "¿Las hojas están amarillas y pegajosas?",
            "¿Hay punticos blancos o ninfas pegadas en el envés?",
        ]
    if pest == "trips":
        return [
            "¿Ves puntos negros (excremento) y rayas plateadas en la hoja?",
            "¿La hoja queda como “raspada” o con brillo plateado?",
            "¿Hay deformación en brotes o flores?",
        ]
    if pest == "broca":
        return [
            "¿Ves orificios en el fruto/grano?",
            "¿Hay aserrín/polvo cerca del hueco?",
            "¿El daño es en frutos maduros o también verdes?",
        ]
    return base[:3]


def general_pest_answer(pest: str, crop: Optional[Crop]) -> str:
    crop_txt = f" en **{crop.name}**" if crop else ""
    return (
        f"🪲 Entiendo: preguntas por **{pest}**{crop_txt}.\n\n"
        f"🔍 Para afinar el diagnóstico necesito 2-3 datos:\n"
        f"- ¿Dónde está el daño? (hoja/tallo/fruto/raíz)\n"
        f"- ¿Qué ves? (insectos, manchas, polvillo blanco, amarillamiento, mordidas)\n"
        f"- ¿En qué etapa está el cultivo? (plántula/vegetativo/floración/fruto)\n\n"
        f"✅ Manejo integrado (general):\n"
        f"1) Monitoreo constante (envés de hojas).\n"
        f"2) Cultural: eliminar malezas hospederas, mejorar ventilación, evitar exceso de nitrógeno.\n"
        f"3) Biológico: proteger enemigos naturales.\n"
        f"4) Si es fuerte: químico **rotando modos de acción** (según etiqueta y técnico local).\n"
    )

# ==============================
# Formateo de enfermedad desde BD
# ==============================


def format_disease_detail(d: Disease) -> str:
    desc = (d.description or "").strip()
    sym = (d.symptoms or "").strip()
    cau = (d.causal_agent or "").strip()
    trn = (d.transmission or "").strip()
    cc = (d.control_cultural or "").strip()
    cb = (d.control_biological or "").strip()
    cq = (d.control_chemical or "").strip()
    rec = (d.recommendations or "").strip()

    parts = [
        f"📌 Detecté en mi base: **{d.name}** en **{d.crop.name}**",
        f"- Tipo: **{d.get_disease_type_display()}**",
    ]
    if cau:
        parts.append(f"- Agente causal: {cau}")
    if desc:
        parts.append(f"\n📝 Descripción:\n{desc}")
    if sym:
        parts.append(f"\n🔍 Síntomas típicos:\n{sym}")
    if trn:
        parts.append(f"\n🚚 Transmisión / condiciones predisponentes:\n{trn}")
    if cc:
        parts.append(f"\n🌱 Control cultural:\n{cc}")
    if cb:
        parts.append(f"\n🦠 Control biológico:\n{cb}")
    if cq:
        parts.append(f"\n🧪 Control químico (general, sin marcas):\n{cq}")
    if rec:
        parts.append(f"\n✅ Manejo integrado recomendado:\n{rec}")

    return "\n".join(parts)


# ==============================
# FAQ / Artículos (fallback)
# ==============================
TOPIC_TO_FAQ_TOPIC = {
    "riego": "riego",
    "fertilizacion": "fertilizacion",
    "plagas": "plagas",
    "herramientas": "herramientas",
    "densidad": "siembra",
    "produccion": "manejo",
    "cultivo": "general",
}


def search_faq(crop: Optional[Crop], topic: Optional[str], kw_list: list[str]) -> Optional[str]:
    if not topic:
        return None

    faq_topic = TOPIC_TO_FAQ_TOPIC.get(topic, "general")
    qs = FAQ.objects.filter(topic=faq_topic)

    if crop:
        qs = qs.filter(Q(crop=crop) | Q(crop__isnull=True))

    if kw_list:
        q = Q()
        for k in kw_list:
            q |= Q(question__icontains=k) | Q(keywords__icontains=k)
        qs = qs.filter(q)

    faqs = list(qs.order_by("-updated_at")[:1])
    if not faqs:
        return None

    f = faqs[0]
    crop_label = f.crop.name if getattr(f, "crop", None) else "general"
    return f"📚 Respuesta técnica para **{crop_label}** ({f.get_topic_display()}):\n\n{f.answer}"


def search_articles(crop: Optional[Crop], topic: Optional[str], kw_list: list[str]) -> Optional[str]:
    qs = KnowledgeArticle.objects.filter(is_published=True)
    if crop:
        qs = qs.filter(crop=crop)

    if kw_list:
        q = Q()
        for t in kw_list:
            if len(t) < 3:
                continue
            q |= Q(title__icontains=t) | Q(content__icontains=t) | Q(
                tags__icontains=t) | Q(key_points__icontains=t)
        qs = qs.filter(q)

    art = qs.order_by("-updated_at").first()
    if not art:
        return None

    summary = art.summary or (art.content or "")[:400]
    summary = summary.strip()
    if len(summary) > 400:
        summary = summary[:400].rsplit(" ", 1)[0] + "…"

    return (
        "📰 Artículo técnico relacionado:\n\n"
        f"▶ **{art.title}** — {art.get_category_display()}\n"
        f"{summary}"
    )

# ==============================
# IMAGEN: endpoint IA (PRO + ML_LABEL)
# ==============================


@csrf_exempt
def upload_image_api(request):
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    if "image" not in request.FILES:
        return JsonResponse({"error": "No se envió ninguna imagen"}, status=400)

    try:
        image_file = request.FILES["image"]
        saved_path = default_storage.save(
            "uploads/" + image_file.name, image_file)
        image_path = os.path.join(settings.MEDIA_ROOT, saved_path)

        results = predict_disease(image_path, top_k=3)  # lista de dicts
        if not results:
            return JsonResponse({"success": False, "message": "No se pudo generar predicción."}, status=200)

        best = results[0]
        predicted_label = (best.get("label") or "").strip()
        confidence = float(best.get("confidence", 0))

        # Buscar en BD por ml_label
        disease_match = Disease.objects.filter(
            ml_label=predicted_label).first()

        THRESHOLD = 25.0
        if confidence < THRESHOLD:
            return JsonResponse({
                "success": False,
                "message": "No estoy 100% seguro con la foto. Te muestro el Top-3 y te hago una pregunta rápida.",
                "top_predictions": [
                    {"label": (r.get("label") or "").strip(),
                     "confidence": float(r.get("confidence", 0))}
                    for r in results
                ],
                "questions": [
                    "¿La hoja presenta manchas o polvillo blanco?",
                    "¿Ves insectos pequeños en el envés (parte de atrás) de la hoja?",
                    "¿La hoja está amarilla o pegajosa?",
                ],
            }, status=200)

        # Si el label existe en ML pero no está registrado en BD
        if not disease_match:
            return JsonResponse({
                "success": False,
                "message": f"Predicción: {predicted_label}, pero no existe en la BD.",
                "top_predictions": [
                    {"label": (r.get("label") or "").strip(),
                     "confidence": float(r.get("confidence", 0))}
                    for r in results
                ],
                "hint": "Registra esta enfermedad en Admin → Diseases y coloca el ml_label exactamente igual.",
            }, status=200)

        # Guardar imagen y predicción
        uploaded = UploadedImage.objects.create(
            user=request.user if getattr(
                request, "user", None) and request.user.is_authenticated else None,
            image=saved_path,
            predicted_disease=disease_match,
            confidence=confidence
        )

        # Guardar en sesión para menú (1/2/3/4) posterior
        request.session["last_disease_id"] = disease_match.id
        request.session["last_uploaded_image_id"] = uploaded.id

        # Respuesta corta + opciones (como asesor)
        response = (
            f"🌱 Según la imagen, lo más probable es **{disease_match.name}**.\n"
            f"(Confianza: {confidence:.1f}%)\n\n"
            f"¿Qué quieres consultar ahora?\n"
            f"1️⃣ Control recomendado\n"
            f"2️⃣ Síntomas\n"
            f"3️⃣ Causas / condiciones\n"
            f"4️⃣ Manejo completo"
        )

        return JsonResponse({
            "success": True,
            "predicted_label": predicted_label,
            "confidence": confidence,
            "disease_id": disease_match.id,
            "disease_name": disease_match.name,
            "crop": disease_match.crop.name,
            "crop_name": disease_match.crop.name,
            "cropName": disease_match.crop.name,
            "response": response,
            "top_predictions": [
                {"label": (r.get("label") or "").strip(),
                 "confidence": float(r.get("confidence", 0))}
                for r in results
            ],
        }, status=200)

    except Exception as e:
        log.exception("❌ Error en upload_image_api")
        return JsonResponse({"error": str(e)}, status=500)


# ==============================
# TEXTO: endpoint chat (UX PRO)
# ==============================
@csrf_exempt
def ask_api(request):
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    try:
        payload = json.loads(request.body.decode("utf-8"))
        user_message = (payload.get("message") or "").strip()
        if not user_message:
            return JsonResponse({"error": "Mensaje vacío"}, status=400)

        # ==============================
        # UX: Saludos y cortesía
        # ==============================
        msg_norm = _norm(user_message)

        SALUDOS = [
            "hola", "buenas", "buenos dias", "buenas tardes",
            "buenas noches", "hey", "que tal", "holi"
        ]

        AGRADECIMIENTOS = [
            "gracias", "muchas gracias", "mil gracias",
            "te agradezco", "grx", "thanks"
        ]

        # 👉 Saludo
        if any(s in msg_norm for s in SALUDOS):
            return JsonResponse({
                "response": (
                    "👋 ¡Hola! Soy tu asesor agrícola 🌱\n\n"
                    "Puedo ayudarte a identificar **plagas y enfermedades**, "
                    "o darte recomendaciones sobre **riego y fertilización**.\n\n"
                    "Cuéntame:\n"
                    "👉 ¿Qué cultivo tienes y qué problema estás observando?"
                ),
                "success": True
            }, status=200)

        # 👉 Agradecimiento
        if any(a in msg_norm for a in AGRADECIMIENTOS):
            return JsonResponse({
                "response": (
                    "😊 ¡Con gusto! Me alegra poder ayudarte.\n\n"
                    "Si tienes otra duda sobre tu cultivo, aquí estoy 🌱"
                ),
                "success": True
            }, status=200)

        crop = detect_crop(user_message)
        topic = detect_topic(user_message) or "plagas"
        stage = detect_stage(user_message)
        region = detect_region(user_message)
        kw = _keywords(user_message)
        pest = detect_pest_name(user_message)

        response_parts: list[str] = []

        # 1) FAQ primero (si hay)
        faq_resp = search_faq(crop, topic, kw)
        if faq_resp:
            response_parts.append(faq_resp)

        # 2) Si menciona plaga común explícita
        disease_qs = Disease.objects.all()
        if crop:
            disease_qs = disease_qs.filter(crop=crop)

        if pest:
            d = disease_qs.filter(
                Q(name__icontains=pest) |
                Q(description__icontains=pest) |
                Q(symptoms__icontains=pest)
            ).first()

            if d:
                response_parts.append(format_disease_detail(d))
            else:
                # UX PRO: respuesta general + preguntas
                response_parts.append(general_pest_answer(pest, crop))

                return JsonResponse({
                    "response": "\n\n".join(response_parts).strip(),
                    "success": False,
                    "questions": followup_questions_for_pest(pest),
                    "hint": "Respóndeme 1-2 preguntas y te doy el control exacto (cultural/biológico/químico)."
                }, status=200)

        # 3) Si NO hay plaga explícita: inferir por keywords en BD
        if not response_parts:
            if kw:
                q = Q()
                for t in kw[:10]:
                    q |= Q(name__icontains=t) | Q(
                        description__icontains=t) | Q(symptoms__icontains=t)
                d = disease_qs.filter(q).first()
            else:
                d = None

            if d:
                response_parts.append(format_disease_detail(d))
            else:
                # UX PRO fallback: pedir contexto bien
                crop_txt = f" en **{crop.name}**" if crop else ""
                response = (
                    f"No encontré una plaga exacta{crop_txt}.\n\n"
                    f"Para ayudarte bien, dime:\n"
                    f"1) ¿Qué cultivo es?\n"
                    f"2) ¿Qué síntomas ves? (manchas, polvillo blanco, insectos, amarillamiento, mordidas)\n"
                    f"3) ¿Dónde? (hoja/tallo/fruto/raíz)\n"
                    f"4) ¿Clima seco o húmedo? (y etapa si puedes: {stage or 'N/D'})\n\n"
                    f"📸 Si puedes, sube una foto y lo cruzo con el modelo."
                )

                # guardo chat igual
                ChatMessage.objects.create(
                    user=request.user if getattr(
                        request, "user", None) and request.user.is_authenticated else None,
                    message=user_message,
                    response=response,
                    detected_crop=crop,
                    detected_intent=topic or "",
                    detected_stage=stage or "",
                )

                return JsonResponse({
                    "response": response,
                    "success": False,
                    "questions": [
                        "¿Qué cultivo es?",
                        "¿Qué ves exactamente (insectos/manchas/polvillo/amarillo)?",
                        "¿En qué parte (hoja/tallo/fruto/raíz)?"
                    ]
                }, status=200)

        # 4) fallback artículos si hay poco contenido
        if len(response_parts) == 1:
            art = search_articles(crop, topic, kw)
            if art:
                response_parts.append(art)

        final_response = "\n\n".join(response_parts).strip()

        # guardar historial
        ChatMessage.objects.create(
            user=request.user if getattr(
                request, "user", None) and request.user.is_authenticated else None,
            message=user_message,
            response=final_response,
            detected_crop=crop,
            detected_intent=topic or "",
            detected_stage=stage or "",
        )

        return JsonResponse({"response": final_response, "success": True}, status=200)

    except Exception as e:
        log.exception("Error en ask_api")
        return JsonResponse({"error": str(e)}, status=500)

# ==============================
# Alias para no romper rutas viejas
# ==============================


@csrf_exempt
def chat_api(request):
    return ask_api(request)
