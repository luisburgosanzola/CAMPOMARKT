from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages

def solo_productor(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("login_page")

        if request.user.rol != "productor":
            messages.error(request, "Solo los productores pueden publicar productos.")
            return redirect("main_page")  # o donde quieras mandarlo
        return view_func(request, *args, **kwargs)
    return _wrapped
