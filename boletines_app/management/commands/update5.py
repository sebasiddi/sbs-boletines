# boletines_app/management/commands/update5.py
import json, math, re
from pathlib import Path
from django.conf import settings
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

def parse_dni(val):
    """Devuelve un int DNI válido o None si es inválido (nan/null/empty/etc.)."""
    if val is None:
        return None
    if isinstance(val, int):
        return val
    if isinstance(val, float):
        if math.isnan(val) or math.isinf(val):
            return None
        return int(val)
    s = str(val).strip().lower()
    if s in {"", "nan", "null", "none"}:
        return None
    digits = re.sub(r"\D+", "", s)  # ej: '58.872.952' -> '58872952'
    if not digits:
        return None
    return int(digits)

def clean_json(obj):
    """Normaliza a JSON válido (NaN/±Inf -> None, claves str, recursivo)."""
    if isinstance(obj, dict):
        return {str(k): clean_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [clean_json(x) for x in obj]
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    if obj is None or isinstance(obj, (int, bool, str)):
        return obj
    return str(obj)

def to_valid_json_obj(py_obj):
    """Fuerza JSON estándar sin NaN usando dumps(..., allow_nan=False)."""
    cleaned = clean_json(py_obj)
    s = json.dumps(cleaned, ensure_ascii=False, allow_nan=False)
    return json.loads(s)

class Command(BaseCommand):
    help = "Carga/actualiza boletines: combina 1T/2T/3T por DNI (plano) con JSON válido y DNIs saneados."

    def add_arguments(self, parser):
        parser.add_argument(
            "--json",
            dest="json_path",
            default=None,
            help="Ruta del JSON a cargar. Si se omite, busca un JSON por defecto junto a manage.py.",
        )

    def handle(self, *args, **options):
        # Default: archivo junto a manage.py (BASE_DIR apunta al proyecto)
        default_json = Path(settings.BASE_DIR) / "boletines_actualizado_20251222_desde_excel.json"
        json_path = Path(options["json_path"]) if options.get("json_path") else default_json

        if not json_path.exists():
            raise CommandError(f"No se encontró {json_path.name} junto a manage.py (buscado en: {json_path})")

        self.stdout.write(self.style.NOTICE(f"Cargando: {json_path}"))
        try:
            with open(json_path, encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            raise CommandError(f"No se pudo leer/parsear JSON: {e}")

        # 1) Agrupar por DNI válido y juntar trimestres
        por_dni = {}  # dni_str -> {"formato": str, "first_name": str, "trimestres": {...}}
        skip_count = 0

        for curso, trimestres in data.items():
            curso_norm = str(curso).strip().upper()
            formato = FORMATO_POR_CURSO.get(curso_norm, "general")

            for trimestre, filas in trimestres.items():
                for row in filas:
                    dni_int = parse_dni(row.get("DNI"))
                    if dni_int is None:
                        skip_count += 1
                        continue

                    try:
                        row_clean = to_valid_json_obj(row)
                    except Exception as e:
                        skip_count += 1
                        self.stdout.write(self.style.ERROR(
                            f"[SKIP] DNI {dni_int} {curso_norm} {trimestre}: fila no JSON válida -> {e}"
                        ))
                        continue

                    dni_key = str(dni_int)
                    entry = por_dni.setdefault(dni_key, {"formato": formato, "first_name": "", "trimestres": {}})
                    if not entry["first_name"]:
                        fn = str(row.get("STUDENT") or "").strip()
                        if fn and fn.lower() != "null":
                            entry["first_name"] = fn
                    entry["trimestres"][trimestre] = row_clean

        # 2) Volcar a DB (una sola vez por alumno)
        creados = actualizados = 0
        for dni_str, payload in por_dni.items():
            try:
                boletin_valido = to_valid_json_obj(payload["trimestres"])
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f"[SKIP] DNI {dni_str}: trimestres no JSON válidos -> {e}"
                ))
                continue

            dni_int = int(dni_str)
            est, creado = Estudiante.objects.get_or_create(dni=dni_int)
            est.username = dni_str
            if payload["first_name"]:
                est.first_name = payload["first_name"]
            est.formato_boletin = payload["formato"]
            est.boletin_data = boletin_valido  # {'1T': {...}, '2T': {...}, '3T': {...}}

            if creado:
                est.password = make_password(dni_str)
                creados += 1
                self.stdout.write(self.style.SUCCESS(f"✔ Creado {dni_str} ({list(boletin_valido.keys())})"))
            else:
                actualizados += 1
                self.stdout.write(self.style.WARNING(f"↺ Actualizado {dni_str} ({list(boletin_valido.keys())})"))

            est.save()

        self.stdout.write(self.style.SUCCESS(
            f"✅ Listo. Creados: {creados} | Actualizados: {actualizados} | Filas saltadas (DNI/JSON inválido): {skip_count}"
        ))
