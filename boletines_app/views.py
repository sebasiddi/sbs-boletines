# views.py
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


# Etiquetas de apoyo (si las usás en algún otro lado)
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
}

ORDEN_TRIMESTRES = ['1T', '2T', '3T']


def _to_int_if_number(v):
    """Convierte v a int si es número (int/float/str numérica). Si no, lo deja igual."""
    if v is None:
        return v
    try:
        f = float(str(v).replace(',', '.').strip())
        return int(f)
    except Exception:
        return v

@login_required
def boletin_view(request, trimestre=None):
    estudiante = request.user
    boletin_completo = estudiante.boletin_data or {}

    def tiene_info(tr_data):
        datos = {k: v for k, v in tr_data.items() if k not in ['DNI', 'STUDENT', 'TEACHER']}
        return any(v not in [None, '', '-', '-nohay-', 'falta'] for v in datos.values())

    ORDEN_TRIMESTRES = ['1T', '2T', '3T']
    trimestres_validos = {k: v for k, v in boletin_completo.items() if tiene_info(v)}
    trimestres = sorted(trimestres_validos.keys(),
                        key=lambda t: ORDEN_TRIMESTRES.index(t) if t in ORDEN_TRIMESTRES else 99)

    trimestre_actual = trimestre or (trimestres[0] if trimestres else None)
    boletin_raw = boletin_completo.get(trimestre_actual, {}) if trimestre_actual else {}

    excluir = ['DNI', 'STUDENT']
    boletin = {k: v for k, v in boletin_raw.items() if k not in excluir}

    # Plantilla + labels base
    if estudiante.formato_boletin == "kinder":
        labels = {
            "WP": "Works and Plays Well with Others",
            "SR": "Shows Respect for Others",
            "FC": "Follow Classroom Rules",
            "FD": "Follows Directions",
            "CT": "Completes Tasks in Appropriate Time",
            "CIC": "Cooperates in Class Routine",
            "CLASSES": "Total Classes",
            "ABSENT": "Days Absent",
        }
        template_name = "boletines_app/boletin_kinder.html"
    else:
        labels = {
            "WT": "Written Test",
            "OT": "Oral Test",
            "PP": "Practice Paper",
            "BE": "Behaviour",
            "PIN": "Participation in Class",
            "HM": "Homework",
            "RP": "Relationship with partners",
            "ABSENT": "Absent",
            "CLASSES": "Classes",
            "TEACHER": "Teacher",
        }
        template_name = "boletines_app/boletin_general.html"

    # Orden
    orden_general = ['WT', 'OT', 'PP', 'BE', 'PIN', 'HM', 'RP', 'PIN', 'CLASSES', 'ABSENT', 'TEACHER']
    orden_kinder  = ['WP', 'SR', 'FC', 'FD', 'CT', 'CIC', 'ABSENT', 'CLASSES']
    orden = orden_kinder if estudiante.formato_boletin == "kinder" else orden_general
    campos_finales = ['CLASSES', 'ABSENT', 'TEACHER']

    boletin_ordenado = [
        (k, boletin.get(k))
        for k in orden
        if k in boletin and k not in campos_finales
    ]
    otros_campos = [(k, v) for k, v in boletin.items()
                    if k not in dict(boletin_ordenado) and k not in campos_finales]
    boletin_ordenado += otros_campos
    finales = [(k, boletin.get(k)) for k in campos_finales if k in boletin]
    boletin_ordenado += finales

    def _to_int_if_number(v):
        if v is None: return v
        try:
            return int(float(str(v).replace(',', '.').strip()))
        except Exception:
            return v
    boletin_ordenado = [
        (k, _to_int_if_number(v) if k in ['ABSENT', 'CLASSES'] else v)
        for k, v in boletin_ordenado
    ]

    # -------- mapa de contenidos y detección automática de KIDS 4 --------
    # 1) Intentar leer grupo del modelo
    grupo_actual = (
        getattr(estudiante, "grupo", None)
        or getattr(estudiante, "curso", None)
        or getattr(estudiante, "classroom", None)
        or getattr(estudiante, "division", None)
        or ""
    )
    grupo_upper = str(grupo_actual).upper() if grupo_actual else ""

    # 2) Si no hay grupo claro pero es KINDER y hay CONTENIDO 1..7 → asumir KIDS 4
    if estudiante.formato_boletin == "kinder" and not grupo_upper:
        claves = {k.upper() for k, _ in boletin_ordenado}
        if all(f"CONTENIDO {i}" in claves for i in range(1, 8)):  # 1..7 presentes
            grupo_upper = "KIDS 4"

    contenidos_map = {
        "KIDS 4": {
            "CONTENIDO 1": "Greetings",
            "CONTENIDO 2": "Weather",
            "CONTENIDO 3": "Colours",
            "CONTENIDO 4": "Numbers",
            "CONTENIDO 5": "Toys",
            "CONTENIDO 6": "Body parts",
            "CONTENIDO 7": "Pets",
        },
        "KINDER 4": {  # alias por si tu modelo usa otro nombre
            "CONTENIDO 1": "Greetings",
            "CONTENIDO 2": "Weather",
            "CONTENIDO 3": "Colours",
            "CONTENIDO 4": "Numbers",
            "CONTENIDO 5": "Toys",
            "CONTENIDO 6": "Body parts",
            "CONTENIDO 7": "Pets",
        },
        "K4": {       # otro alias
            "CONTENIDO 1": "Greetings",
            "CONTENIDO 2": "Weather",
            "CONTENIDO 3": "Colours",
            "CONTENIDO 4": "Numbers",
            "CONTENIDO 5": "Toys",
            "CONTENIDO 6": "Body parts",
            "CONTENIDO 7": "Pets",
        },
    }
    # --------------------------------------------------------------------

    return render(request, template_name, {
        "boletin_ordenado": boletin_ordenado,
        "etiquetas": labels,
        "trimestres": trimestres,
        "trimestre_actual": trimestre_actual,
        # claves para smart_label
        "grupo_actual": grupo_upper,
        "contenidos_map": contenidos_map,
    })
