from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse, HttpResponse
from django.template.loader import get_template
from django.templatetags.static import static
from django.conf import settings

from datetime import datetime
import os



from boletines_app.models import Estudiante

logo_path = os.path.join(settings.STATIC_ROOT, 'boletines_app/img/s.png')


@login_required
def logout_view(request):
    logout(request)
    return redirect('login')


def login_view(request):
    if request.method == "POST":
        dni_input = request.POST.get("dni")
        password = request.POST.get("password")

        try:
            # Convertimos el valor a entero para evitar errores en IntegerField
            dni = int(dni_input)
        except (ValueError, TypeError):
            messages.error(request, "El DNI ingresado no es válido.")
            return redirect("login")

        try:
            user = Estudiante.objects.get(dni=dni)
            if user.check_password(password):
                login(request, user)
                return redirect("perfil")
            else:
                messages.error(request, "Contraseña incorrecta.")
        except Estudiante.DoesNotExist:
            messages.error(request, "Usuario no encontrado.")

        return redirect("login")

    return render(request, "boletines_app/login.html")


@login_required
def perfil_view(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Contraseña actualizada correctamente')
            return redirect('perfil')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'boletines_app/perfil.html', {'form': form})

LABELS_KINDER = {
    "PARTICIPACION": "Participación en clase",
    "CONDUCTA": "Conducta",
    "TAREA": "Tareas",
    "VOCABULARIO": "Vocabulario",
    "COMPRENSION": "Comprensión",
    "EXPRESION": "Expresión",
    "ASISTENCIA": "Asistencia",
    "OBS": "Observaciones",
    "WP": "WORKS AND PLAYS WELL WITH OTHERS",
    "SR": "SHOWS RESPECT FOR OTHERS",
    "FC": "FOLLOW CLASSROOM RULES",
    "FD": "FOLLOWS DIRECTIONS",
    "CT": "COMPLETES TASKS IN APPROPIATE AMOUNT OF TIME",
    "CIC": "COOPERATE IN CLASS ROUTINE",
    "CLASSES": "Total Classes",
    # Agregá más si es necesario
}
ORDEN_TRIMESTRES = ['1T', '2T', '3T']
@login_required
def boletin_view(request, trimestre=None):
    estudiante = request.user
    boletin_data = estudiante.boletin_data or {}

    # Obtener el nombre del curso (asumimos que solo tiene uno)
    nombre_curso = list(boletin_data.keys())[0] if boletin_data else "Sin curso"

    # Accedemos al contenido del curso
    boletin_completo = boletin_data.get(nombre_curso, {})

    # Filtrar solo trimestres con contenido útil
    def tiene_info(tr_data):
        datos = {k: v for k, v in tr_data.items() if k not in ['DNI', 'STUDENT', 'TEACHER']}
        return any(v not in [None, '', '-', '-nohay-', 'falta'] for v in datos.values())

    trimestres_validos = {
        k: v for k, v in boletin_completo.items() if tiene_info(v)
    }

    # Ordenar trimestres válidos como 1T, 2T, 3T
    trimestres = sorted(
        trimestres_validos.keys(),
        key=lambda t: ORDEN_TRIMESTRES.index(t) if t in ORDEN_TRIMESTRES else 99
    )

    # Elegir trimestre a mostrar
    trimestre_actual = trimestre or (trimestres[0] if trimestres else None)
    boletin_raw = boletin_completo.get(trimestre_actual, {}) if trimestre_actual else {}

    # Excluir campos no mostrables
    excluir = ['DNI', 'STUDENT', 'TEACHER']
    boletin = {k: v for k, v in boletin_raw.items() if k not in excluir}

    # Adaptar formato según nivel
    if estudiante.formato_boletin == "kinder":
        LABELS_KINDER_SIGLAS = {
            "WP": "Written Production",
            "SR": "Sound Recognition",
            "FC": "Flashcards",
            "FD": "Following Directions",
            "CT": "Circle Time",
            "CIC": "Comprehension in Class",
            "CLASSES": "Total Classes",
            "ABSENT": "Days Absent",
        }
        boletin_con_etiquetas = {
            LABELS_KINDER_SIGLAS.get(k.upper(), k.replace("_", " ").title()): v
            for k, v in boletin.items()
        }
        template_name = "boletines_app/boletin_kinder.html"
    else:
        boletin_con_etiquetas = boletin
        template_name = "boletines_app/boletin_general.html"

    return render(request, template_name, {
        "curso": nombre_curso,
        "boletin": boletin_con_etiquetas,
        "trimestres": trimestres,
        "trimestre_actual": trimestre_actual,
    })
