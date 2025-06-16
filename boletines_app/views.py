

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from boletines_app.models import Estudiante  # Asegurate de tener este import

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
    boletin_completo = estudiante.boletin_data or {}

    # Filtrar solo trimestres con contenido útil (más allá de DNI, STUDENT, etc.)
    def tiene_info(tr_data):
        # Ignoramos claves técnicas, solo dejamos si hay notas o contenido
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
        "boletin": boletin_con_etiquetas,
        "trimestres": trimestres,
        "trimestre_actual": trimestre_actual,
    })
# Diccionario de etiquetas para mostrar nombres más claros
""" def boletin_view(request, trimestre=None):
    estudiante = request.user
    boletin_completo = estudiante.boletin_data or {}
    trimestres = sorted(boletin_completo.keys())
    trimestre_actual = trimestre or trimestres[0] if trimestres else None

    boletin_raw = boletin_completo.get(trimestre_actual, {})

    # Excluir campos que no deben mostrarse
    excluir = ['DNI', 'STUDENT', 'TEACHER']
    boletin = {k: v for k, v in boletin_raw.items() if k not in excluir}

    # Elegir el template según el tipo de curso
    if estudiante.formato_boletin == "kinder":
        template_name = "boletines_app/boletin_kinder.html"
        # Mapeo de claves a etiquetas legibles
        boletin_con_etiquetas = {
            LABELS_KINDER.get(k.upper(), k.replace("_", " ").title()): v
            for k, v in boletin.items()
        }

    else:
        template_name = "boletines_app/boletin_general.html"
        boletin_con_etiquetas = boletin

    return render(request, template_name, {
        "boletin": boletin_con_etiquetas,
        "trimestres": trimestres,
        "trimestre_actual": trimestre_actual,
    }) """

""" def boletin_view(request, trimestre='1T'):
    user = request.user
    boletin = user.boletin_data.get(trimestre, {})

    template_map = {
        'kinder': 'boletines_app/boletin_kinder.html',
        'first': 'boletines_app/boletin_first.html',
        'general': 'boletines_app/boletin_general.html',
    }
    template = template_map.get(user.formato_boletin, 'boletines_app/boletin_general.html')

    return render(request, template, {
        'boletin': boletin,
        'trimestre_actual': trimestre,
        'trimestres': ['1T', '2T', '3T']
    }) """



""" 

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash

def login_view(request):
    if request.method == 'POST':
        dni = request.POST.get('dni')
        password = request.POST.get('password')
        user = authenticate(request, dni=dni, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('perfil')
        else:
            messages.error(request, 'DNI o contraseña incorrectos')
    
    return render(request, 'boletines_app/login.html')

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def perfil_view(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Mantiene la sesión activa
            messages.success(request, 'Contraseña actualizada correctamente')
            return redirect('perfil')
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'boletines_app/perfil.html', {'form': form})

@login_required
def boletin_view(request, trimestre='1T'):
    if not hasattr(request.user, 'boletin_data'):
        messages.warning(request, 'No hay datos de boletines disponibles')
        return redirect('perfil')
    
    boletin = request.user.boletin_data.get(trimestre, {})
    
    return render(request, 'boletines_app/boletin.html', {
        'boletin': boletin,
        'trimestre_actual': trimestre,
        'trimestres': ['1T', '2T', '3T']  # Lista de trimestres disponibles
    }) """