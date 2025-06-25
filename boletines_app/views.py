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
    excluir = ['DNI', 'STUDENT']
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
        """ boletin_con_etiquetas = {
            LABELS_KINDER_SIGLAS.get(k.upper(), k.replace("_", " ").title()): v
            for k, v in boletin.items()
        } """
        boletin_con_etiquetas = boletin  # dejamos las claves técnicas
        template_name = "boletines_app/boletin_kinder.html"
    else:
        boletin_con_etiquetas = boletin  # mantenemos claves técnicas

        template_name = "boletines_app/boletin_general.html"

    # Orden para niveles generales
    orden_general = ['WT', 'OT', 'PP', 'BE','PIN', 'HM', 'RP', 'PIN', 'CLASSES', 'ABSENT',  'TEACHER']
    # Orden para kinder
    orden_kinder = ['WP', 'SR', 'FC', 'FD', 'CT', 'CIC', 'ABSENT', 'CLASSES']

    orden = orden_kinder if estudiante.formato_boletin == "kinder" else orden_general

    """ boletin_ordenado = [(k, boletin_con_etiquetas.get(k)) for k in orden if k in boletin_con_etiquetas] """

    # Campos que queremos que estén siempre al final
    campos_finales = ['CLASSES', 'ABSENT', 'TEACHER']

    # 1. Primero agregamos los campos del orden definido, excluyendo los que van al final
    boletin_ordenado = [
        (k, boletin_con_etiquetas.get(k))
        for k in orden
        if k in boletin_con_etiquetas and k not in campos_finales
    ]

    # 2. Luego agregamos los que no estaban en el orden (como CONTENIDO 1, etc.)
    otros_campos = [
        (k, v) for k, v in boletin_con_etiquetas.items()
        if k not in dict(boletin_ordenado) and k not in campos_finales
    ]
    boletin_ordenado += otros_campos

    # 3. Finalmente agregamos los campos administrativos al final
    finales = [
        (k, boletin_con_etiquetas.get(k))
        for k in campos_finales
        if k in boletin_con_etiquetas
    ]
    boletin_ordenado += finales



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

    for i in range(1, 6):
        labels_kinder[f"CONTENIDO {i}"] = f"Contenido {i}"


    labels = labels_kinder if estudiante.formato_boletin == "kinder" else labels_generales
    # Convertir valores a enteros si corresponde para ABSENT y CLASSES
    boletin_ordenado = [
        (k, int(v) if k in ['ABSENT', 'CLASSES'] and isinstance(v, (int, float)) and v is not None else v)
        for k, v in boletin_ordenado
    ]

    return render(request, template_name, {
        "boletin_ordenado": boletin_ordenado,
        "etiquetas": labels,
        "trimestres": trimestres,
        "trimestre_actual": trimestre_actual,
    })


