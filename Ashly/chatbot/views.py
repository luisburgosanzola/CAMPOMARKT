import json
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from Ashly.chatbot.ml.runtime.llm_answer import chat_answer, image_answer


def chat_page(request):
    return render(request, "chatbot/chat.html")


@csrf_exempt
def ask_api(request):

    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    try:

        data = json.loads(request.body)

        message = data.get("message", "").strip()

        if not message:
            return JsonResponse({"error": "Mensaje vacío"}, status=400)

        answer = chat_answer(message)

        return JsonResponse({
            "success": True,
            "response": answer
        })

    except Exception as e:

        print(e)

        return JsonResponse({
            "success": False,
            "response": "⚠️ Error procesando el mensaje"
        })


@csrf_exempt
def upload_image_api(request):

    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    if "image" not in request.FILES:
        return JsonResponse({"error": "No se envió imagen"}, status=400)

    try:

        image = request.FILES["image"]

        message = request.POST.get("message", "")

        result = image_answer(image.read(), message)

        return JsonResponse({
            "success": True,
            "response": result
        })

    except Exception as e:

        print(e)

        return JsonResponse({
            "success": False,
            "response": "⚠️ Error analizando imagen"
        })
    
@csrf_exempt
def chat_api(request):
    return ask_api(request)