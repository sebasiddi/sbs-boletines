# views.py
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.conf import settings

from datetime import datetime
import os
import re

from boletines_app.models import Estudiante

# (lo usás para assets si querés)
logo_path = os.path.join(settings.STATIC_ROOT, 'boletines_app/img/s.png')

# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------
ORDEN_TRIMESTRES = ['1T', '2T', '3T']

def _to_int_if_number(v):
    """Convierte a int si v es numérico (incluyendo '25' o '25,0'); si no, lo deja como está."""
    if v is None:
        return v
    try:
        return int(float(str(v).replace(',', '.').strip()))
    except Exception:
        return v

def N(s: str) -> str:
    """Normaliza: mayúsculas, colapsa espacios, quita signos de puntuación."""
    s = re.sub(r'\s+', ' ', str(s).strip()).upper()
    s = re.sub(r'[^A-Z0-9 ]', '', s)
    return s.replace('  ', ' ')

def contenido_num(k: str):
    m = re.match(r'CONTENIDO\s+(\d+)', N(k))
    return int(m.group(1)) if m else None

# Sinónimos normalizados → grupos canónicos
G = {
    'WT': {N('WT'), N('Written Test')},
    'OT': {N('OT'), N('Oral Test')},
    'PP': {N('PP'), N('Practice Paper')},
    'BE': {N('BE'), N('Behaviour'), N('Behavior')},
    'PIN': {N('PIN'), N('Participation in Class')},
    'HM': {N('HM'), N('Homework')},
    'RP': {N('RP'), N('Relationship with partners'), N('Relationship With Partners')},
    'CLASSES': {N('CLASSES'), N('Total Classes')},
    'ABSENT': {N('ABSENT'), N('Days Absent')},
    'TEACHER': {N('TEACHER'), N('Docente'), N('Teacher')},

    # Kinder (por si alguna vez llegan como texto)
    'WP': {N('WP'), N('Works and Plays Well with Others')},
    'SR': {N('SR'), N('Shows Respect for Others')},
    'FC': {N('FC'), N('Follow Classroom Rules')},
    'FD': {N('FD'), N('Follows Directions')},
    'CT': {N('CT'), N('Completes Tasks in Appropriate Time')},
    'CIC': {N('CIC'), N('Cooperates in Class Routine')},
}

GENERAL_ORDER = ['WT', 'OT', 'PP', 'BE', 'PIN', 'HM', 'RP']
FINAL_ORDER   = ['CLASSES', 'ABSENT', 'TEACHER']
KINDER_ORDER  = ['WP', 'SR', 'FC', 'FD', 'CT', 'CIC']

# -------------------------------------------------------------------
# Auth / Perfil
# -------------------------------------------------------------------
@login_required
def logout_view(request):
    logout(request)
    return redirect('login')


def login_view(request):
    if request.method == "POST":
        dni_input = request.POST.get("dni")
        password = request.POST.get("password")

        try:
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
def class_log_view(request):
    logs = [
        {
            "date": "2026-02-10",
            "topic": "Present Simple: routines",
            "homework": "Workbook p.12 ex 1–3",
            "notes": "Bring your book next class",
            "created_by": "Teacher Ana",
        },
        {
            "date": "2026-02-07",
            "topic": "Listening practice: daily activities",
            "homework": "Audio track 3 + notes",
            "notes": "",
            "created_by": "Teacher Ana",
        },
    ]

    return render(
        request,
        "boletines_app/class_log.html",
        {
            "logs": logs,
        },
    )


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

# -------------------------------------------------------------------
# Boletín
# -------------------------------------------------------------------
@login_required
def boletin_view(request, trimestre=None):
    estudiante = request.user
    boletin_completo = estudiante.boletin_data or {}

    # Filtrar trimestres con contenido real
    def tiene_info(tr_data):
        datos = {k: v for k, v in tr_data.items() if k not in ['DNI', 'STUDENT', 'TEACHER']}
        return any(v not in [None, '', '-', '-nohay-', 'falta'] for v in datos.values())

    tr_validos = {k: v for k, v in boletin_completo.items() if tiene_info(v)}

    trimestres = sorted(
        tr_validos.keys(),
        key=lambda t: ORDEN_TRIMESTRES.index(t) if t in ORDEN_TRIMESTRES else 99
    )

    trimestre_actual = trimestre or (trimestres[0] if trimestres else None)
    boletin_raw = tr_validos.get(trimestre_actual, {}) if trimestre_actual else {}

    # Excluir campos no mostrables
    boletin = {k: v for k, v in boletin_raw.items() if k not in ['DNI', 'STUDENT']}

    # Labels y plantilla
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
        codes_first = KINDER_ORDER
    else:
        labels = {
            "WT": "Written Test",
            "OT": "Oral Test",
            "PP": "Practice Paper",
            "BE": "Behaviour",
            "PIN": "Participation in Class",
            "HM": "Homework",
            "RP": "Relationship with partners",
            "CLASSES": "Classes",
            "ABSENT": "Absent",
            "TEACHER": "Teacher",
        }
        template_name = "boletines_app/boletin_general.html"
        codes_first = GENERAL_ORDER

    # ---------- ORDEN EXACTO ----------
    remaining = dict(boletin)   # copia de trabajo
    boletin_ordenado = []

    def pick_first(code):
        """Mueve al ordenado la primera clave de 'remaining' que matchee el grupo 'code'."""
        if code not in G:
            return
        ks = list(remaining.keys())
        for k in ks:
            if N(k) in G[code]:
                boletin_ordenado.append((k, remaining.pop(k)))
                return

    # 1) Códigos fijos primero (WP.. o WT..)
    for code in codes_first:
        pick_first(code)

    # 2) Kinder: Contenido 1..N en orden numérico
    if estudiante.formato_boletin == 'kinder':
        conts = [(k, v) for k, v in remaining.items() if contenido_num(k) is not None]
        conts.sort(key=lambda kv: contenido_num(kv[0]))
        boletin_ordenado += conts
        for k, _ in conts:
            remaining.pop(k, None)

    # 3) El resto (no finales) en orden alfabético estable
    finales_norm = set().union(*[G[c] for c in FINAL_ORDER])
    resto = [(k, v) for k, v in remaining.items() if N(k) not in finales_norm]
    resto.sort(key=lambda kv: N(kv[0]))
    boletin_ordenado += resto
    for k, _ in resto:
        remaining.pop(k, None)

    # 4) Campos finales en orden fijo
    for code in FINAL_ORDER:
        pick_first(code)

    # 5) Conversión ABSENT/CLASSES a int
    abs_or_cls_norm = G['ABSENT'] | G['CLASSES']
    boletin_ordenado = [
        (k, _to_int_if_number(v) if N(k) in abs_or_cls_norm else v)
        for k, v in boletin_ordenado
    ]
    # ---------- FIN ORDEN ----------

    # ------- Mapeo de contenidos para Kinder 4 (para smart_label en el template) -------
    grupo_actual = (
        getattr(estudiante, "grupo", None)
        or getattr(estudiante, "curso", None)
        or getattr(estudiante, "classroom", None)
        or getattr(estudiante, "division", None)
        or ""
    )
    grupo_upper = str(grupo_actual).upper() if grupo_actual else ""

    # Autodetección si es kinder y hay Contenido 1..7
    if estudiante.formato_boletin == "kinder" and not grupo_upper:
        claves_norm = {N(k) for k, _ in boletin_ordenado}
        if all(N(f"Contenido {i}") in claves_norm for i in range(1, 8)):
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
    # -------------------------------------------------------------------------------

    return render(request, template_name, {
        "boletin_ordenado": boletin_ordenado,
        "etiquetas": labels,
        "trimestres": trimestres,
        "trimestre_actual": trimestre_actual,
        "grupo_actual": grupo_upper,
        "contenidos_map": contenidos_map,
    })
