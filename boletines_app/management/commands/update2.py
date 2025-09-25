""" import json
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
    # Agregá más si hace falta
}

class Command(BaseCommand):
    help = 'Carga/actualiza boletines desde JSON acumulando 1T/2T/3T (no toca contraseñas)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE(
            'Cargando boletines desde boletines_actualizado_20250921.json...'
        ))

        # El archivo está junto a manage.py (directorio de ejecución)
        with open('boletines_actualizado_20250921.json', encoding='utf-8') as f:
            data = json.load(f)

        total_creados = total_actualizados = 0

        for curso, trimestres in data.items():
            curso_norm = str(curso).strip().upper()
            formato = FORMATO_POR_CURSO.get(curso_norm, 'general')

            for trimestre, estudiantes in trimestres.items():
                for estudiante_data in estudiantes:
                    dni = str(estudiante_data.get('DNI') or '').strip()
                    if not dni or dni.lower() == 'null':
                        continue  # descarta filas vacías/placeholder

                    estudiante, creado = Estudiante.objects.get_or_create(dni=dni)

                    # Campos básicos
                    estudiante.username = dni
                    first_name = str(estudiante_data.get('STUDENT') or '').strip()
                    if first_name and first_name.lower() != 'null':
                        estudiante.first_name = first_name
                    estudiante.formato_boletin = formato

                    # ✅ ACUMULAR: agregar/actualizar el trimestre sin borrar los otros
                    boletin = estudiante.boletin_data or {}
                    boletin[trimestre] = estudiante_data
                    estudiante.boletin_data = boletin

                    if creado:
                        estudiante.password = make_password(dni)
                        total_creados += 1
                        self.stdout.write(self.style.SUCCESS(
                            f'✔ Usuario creado: {dni} (set {trimestre})'
                        ))
                    else:
                        total_actualizados += 1
                        self.stdout.write(self.style.WARNING(
                            f'↺ Usuario actualizado: {dni} (set {trimestre})'
                        ))

                    estudiante.save()

        self.stdout.write(self.style.SUCCESS(
            f'✅ Proceso finalizado. Creados: {total_creados} | Actualizados: {total_actualizados}'
        ))
 """