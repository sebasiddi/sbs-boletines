import json
from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from boletines_app.models import Estudiante

FORMATO_POR_CURSO = {
    "KINDER 4": "kinder",
    "KINDER 5": "kinder",
    "PRE KIDS": "kinder",
    "KIDS 1": "kids",
    "KIDS 2 A": "kids",
    "KIDS 2 B": "kids",
    "KIDS 3": "kids",
    "KIDS 4": "kids",
    "KIDS 5": "kids",
    "TEENS 1": "teens",
    "TEENS 2": "teens",
    "TEENS 3": "teens",
    "TEENS 4": "teens",
    "TEENS 5": "teens",
    "FIRST 1": "first",
    "FIRST 2": "first",
    "FIRST 3": "first",
    # Agregá otros cursos si es necesario
}

class Command(BaseCommand):
    help = 'Carga o actualiza boletines desde boletines_250622_actualizado.json sin sobrescribir contraseñas'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Cargando datos desde boletines_250622_actualizado.json...'))

        with open('boletines_250622_actualizado_sin_nan.json', encoding='utf-8') as f:
            data = json.load(f)

        for curso, trimestres in data.items():
            formato = FORMATO_POR_CURSO.get(curso, 'general')
            for trimestre, estudiantes in trimestres.items():
                for estudiante_data in estudiantes:
                    dni = estudiante_data.get('DNI')
                    if not dni:
                        continue

                    estudiante, creado = Estudiante.objects.get_or_create(dni=dni)

                    estudiante.username = str(dni)
                    estudiante.first_name = estudiante_data.get('STUDENT', '')
                    estudiante.formato_boletin = formato

                    if creado:
                        estudiante.password = make_password(str(dni))
                        estudiante.boletin_data = {trimestre: estudiante_data}
                        self.stdout.write(self.style.SUCCESS(f'✔ Usuario creado: {dni}'))
                    else:
                        boletin = estudiante.boletin_data or {}
                        boletin[trimestre] = estudiante_data
                        estudiante.boletin_data = boletin
                        self.stdout.write(self.style.WARNING(f'↺ Usuario actualizado (sin tocar contraseña): {dni}'))

                    estudiante.save()

        self.stdout.write(self.style.SUCCESS('✅ Todos los boletines fueron cargados correctamente.'))
