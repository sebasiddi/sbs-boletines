""" import json
from django.core.management.base import BaseCommand, CommandError
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
}

class Command(BaseCommand):
    help = "Carga/actualiza boletines: combina 1T/2T/3T por DNI y guarda plano (no toca contraseñas)."

    def handle(self, *args, **options):
        fname = "boletines_actualizado_20250921.json"  # junto a manage.py
        self.stdout.write(self.style.NOTICE(f"Cargando: {fname}"))
        try:
            with open(fname, encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            raise CommandError(f"No se encontró {fname} junto a manage.py")
        except Exception as e:
            raise CommandError(f"No se pudo leer/parsear JSON: {e}")

        # 1) Acumular por DNI
        por_dni = {}  # dni -> {"formato": str, "first_name": str, "trimestres": {...}}
        for curso, trimestres in data.items():
            curso_norm = str(curso).strip().upper()
            formato = FORMATO_POR_CURSO.get(curso_norm, "general")
            for trimestre, filas in trimestres.items():
                for row in filas:
                    dni = str(row.get("DNI") or "").strip()
                    if not dni or dni.lower() == "null":
                        continue
                    entry = por_dni.setdefault(dni, {"formato": formato, "first_name": "", "trimestres": {}})
                    if not entry["first_name"]:
                        fn = str(row.get("STUDENT") or "").strip()
                        if fn and fn.lower() != "null":
                            entry["first_name"] = fn
                    entry["trimestres"][trimestre] = row  # 1T/2T/3T plano

        # 2) Volcar a DB (una sola escritura por alumno)
        creados = actualizados = 0
        for dni, payload in por_dni.items():
            est, creado = Estudiante.objects.get_or_create(dni=dni)
            est.username = dni
            if payload["first_name"]:
                est.first_name = payload["first_name"]
            est.formato_boletin = payload["formato"]
            est.boletin_data = payload["trimestres"]  # guarda juntos 1T/2T/3T

            if creado:
                est.password = make_password(dni)
                creados += 1
                self.stdout.write(self.style.SUCCESS(f"✔ Creado {dni} ({list(payload['trimestres'].keys())})"))
            else:
                actualizados += 1
                self.stdout.write(self.style.WARNING(f"↺ Actualizado {dni} ({list(payload['trimestres'].keys())})"))

            est.save()

        self.stdout.write(self.style.SUCCESS(f"✅ Listo. Creados: {creados} | Actualizados: {actualizados}"))
 """