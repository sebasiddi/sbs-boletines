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

    # Filtrar solo trimestres con contenido útil (más allá de DNI, STUDENT, etc.)
    def tiene_info(tr_data):
        datos = {k: v for k, v in tr_data.items() if k not in ['DNI', 'STUDENT', 'TEACHER']}
        return any(v not in [None, '', '-', '-nohay-', 'falta'] for v in datos.values())

    trimestres_validos = {k: v for k, v in boletin_completo.items() if tiene_info(v)}

    # Ordenar trimestres válidos como 1T, 2T, 3T
    trimestres = sorted(
        trimestres_validos.keys(),
        key=lambda t: ORDEN_TRIMESTRES.index(t) if t in ORDEN_TRIMESTRES else 99
    )

    # Elegir trimestre a mostrar
    trimestre_actual = trimestre or (trimestres[0] if trimestres else None)
    boletin_raw = boletin_completo.get(trimestre_actual, {}) if trimestre_actual else {}

    # Excluir campos no mostrables
    excluir = ['DNI', 'STUDENT']  # TEACHER se muestra al final
    boletin = {k: v for k, v in boletin_raw.items() if k not in excluir}

    # ¿Vista/plantilla según formato?
    if estudiante.formato_boletin == "kinder":
        labels_kinder = {
            "WP": "Works and Plays Well with Others",
            "SR": "Shows Respect for Others",
            "FC": "Follow Classroom Rules",
            "FD": "Follows Directions",
            "CT": "Completes Tasks in Appropriate Time",
            "CIC": "Cooperates in Class Routine",
            "CLASSES": "Total Classes",
            "ABSENT": "Days Absent",
        }
        boletin_con_etiquetas = boletin  # mantenemos claves técnicas; los template tags las traducen
        template_name = "boletines_app/boletin_kinder.html"
    else:
        labels_generales = {
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
        boletin_con_etiquetas = boletin
        template_name = "boletines_app/boletin_general.html"

    # Orden para niveles generales y kinder
    # ---- ORDEN ROBUSTO (reemplaza tu bloque de orden actual) ----
    orden_general = ['WT', 'OT', 'PP', 'BE', 'PIN', 'HM', 'RP', 'CLASSES', 'ABSENT', 'TEACHER']
    orden_kinder  = ['WP', 'SR', 'FC', 'FD', 'CT', 'CIC', 'ABSENT', 'CLASSES']
    orden = orden_kinder if estudiante.formato_boletin == "kinder" else orden_general

    campos_finales = ['CLASSES', 'ABSENT', 'TEACHER']

    import re
    def _norm(x): return str(x).strip().upper()
    def _contenido_num(k):
        m = re.match(r'CONTENIDO\s+(\d+)', _norm(k))
        return int(m.group(1)) if m else None

# Mapa normalizado->clave_real presente en boletin
    norm_map = {}
    for k in boletin.keys():
        nk = _norm(k)
    # si hay duplicados normalizados, conservamos la primera aparición
        if nk not in norm_map:
            norm_map[nk] = k

    boletin_ordenado = []
    usados = set()

    # 1) primeros según orden deseado (excluyendo finales)
    for code in orden:
        if code in campos_finales:
            continue
        real_key = norm_map.get(_norm(code))
        if real_key is not None and real_key not in usados:
            boletin_ordenado.append((real_key, boletin.get(real_key)))
            usados.add(real_key)

# 2) luego el resto (p.ej. CONTENIDO 1..N). En Kinder los ordenamos por número.
    otros = [
        (k, v) for k, v in boletin.items()
        if k not in usados and _norm(k) not in {_norm(c) for c in campos_finales}
    ]

    if estudiante.formato_boletin == "kinder":
        # ordenar CONTENIDO N por N, dejando lo demás al final
        otros.sort(key=lambda kv: (_contenido_num(kv[0]) is None,
                                   999 if _contenido_num(kv[0]) is None else _contenido_num(kv[0]),
                                   str(kv[0])))

    boletin_ordenado += otros

# 3) finalmente los campos administrativos en orden fijo
    for code in campos_finales:
        real_key = norm_map.get(_norm(code))
        if real_key is not None and real_key not in usados:
            boletin_ordenado.append((real_key, boletin.get(real_key)))
            usados.add(real_key)
# ---- FIN ORDEN ROBUSTO ----


    # --------- NUEVO: grupo_actual + contenidos_map para KIDS 4 ----------
    # Intentamos deducir el grupo/curso del estudiante de forma robusta
    grupo_actual = (
        getattr(estudiante, "grupo", None)
        or getattr(estudiante, "curso", None)
        or getattr(estudiante, "classroom", None)
        or getattr(estudiante, "division", None)
        or ""
    )
    grupo_upper = str(grupo_actual).upper() if grupo_actual else ""

    contenidos_map = {
        # Permito alias para robustez:
        "KINDER 4": {
            "CONTENIDO 1": "Greetings",
            "CONTENIDO 2": "Weather",
            "CONTENIDO 3": "Colours",
            "CONTENIDO 4": "Numbers",
            "CONTENIDO 5": "Toys",
            "CONTENIDO 6": "Body parts",
            "CONTENIDO 7": "Pets",
        },
        "K4": {
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

    # Labels a pasar al template (según formato)
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
        # (No forzamos "Contenido N" acá: lo resuelve smart_label con contenidos_map)
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

    return render(request, template_name, {
        "boletin_ordenado": boletin_ordenado,
        "etiquetas": labels,
        "trimestres": trimestres,
        "trimestre_actual": trimestre_actual,
        # nuevo para que el template renombre "Contenido N"
        "grupo_actual": grupo_upper,
        "contenidos_map": contenidos_map,
    })
