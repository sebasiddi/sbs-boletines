# boletines_app/templatetags/etiquetas_extras.py
from django import template
import re

register = template.Library()

# -----------------------------
# 1) Filtro existente: get_item
# -----------------------------
@register.filter(name="get_item")
def get_item(dictionary, key):
    """Devuelve dictionary[key] de forma segura."""
    try:
        return dictionary.get(key)
    except Exception:
        return None


# -----------------------------------------
# 2) Mapping de siglas → texto “amigable”
# -----------------------------------------
_LABELS = {
    "WT": "Written Test",
    "OT": "Oral Test",
    "PP": "Practice Paper",
    "BE": "Behaviour",
    "BH": "Behaviour",
    "PIN": "Participation in Class",
    "HM": "Homework",
    "RP": "Relationship with partners",
    "CL": "Classes",
    "ABS": "Absent",
    "TEACHER": "Teacher",
}

@register.filter(name="label_boletin")
def label_boletin(key, etiquetas=None):
    """
    1) Si hay dict 'etiquetas' en el contexto, lo usa primero (key y KEY).
    2) Si no, usa mapping fijo de siglas.
    """
    k = "" if key is None else str(key).strip()
    ku = k.upper()
    if etiquetas and hasattr(etiquetas, "get"):
        v = etiquetas.get(k) or etiquetas.get(ku)
        if v:
            return v
    return _LABELS.get(ku, k)


# -------------------------------------------------------------
# 3) Extraer la NOTA numérica de strings tipo "Topic 9" / "8."
# -------------------------------------------------------------
@register.filter(name="nota_numeric")
def nota_numeric(value):
    """
    Devuelve float si encuentra un número al final del string (acepta '.' o ',' y también '8.').
    Si no hay número, devuelve None.
    """
    if value is None:
        return None
    s = str(value).strip()

    m = re.search(r'(-?\d+(?:[.,]\d+)?)\s*$', s)
    if not m:
        # Caso "8." → tomar entero
        m2 = re.search(r'(-?\d+)[\.,]?\s*$', s)
        if not m2:
            try:
                return float(s.replace(",", "."))
            except Exception:
                return None
        try:
            return float(m2.group(1))
        except Exception:
            return None

    try:
        return float(m.group(1).replace(",", "."))
    except Exception:
        return None


# ---------------------------------------------------------------------
# 4) smart_label: título “inteligente” para Contenido N y otros casos
# ---------------------------------------------------------------------
@register.simple_tag
def smart_label(key, value, etiquetas=None, grupo=None, contenidos_map=None):
    """
    Orden de preferencia para el label (columna):
    1) Si hay 'contenidos_map' por grupo y mapea 'Contenido N' → usar ese título.
    2) Si la clave es 'Contenido N' y el valor es 'TÍTULO 9', usar 'TÍTULO'
       SOLO si el texto tiene letras (evita '1', '8.' etc.).
    3) Si hay dict 'etiquetas', usarlo.
    4) Si la clave es sigla conocida (WT/OT/PP/…), mapear con _LABELS.
    5) Fallback: devolver la clave tal cual.
    """
    k = "" if key is None else str(key).strip()
    ku = k.upper()

    # 1) Mapping específico por grupo (opcional)
    if contenidos_map and grupo:
        try:
            m = contenidos_map.get(str(grupo), {})  # p.ej. {"KIDS 4": {"CONTENIDO 1": "Greetings", ...}}
            v = m.get(k) or m.get(ku)
            if v:
                return v
        except Exception:
            pass

    # 2) Derivar del valor si es "Contenido N" Y el valor tiene "TÍTULO 9"
    if ku.startswith("CONTENIDO") and value:
        s = str(value).strip()
        mm = re.match(r'(.+?)\s*-?\d+(?:[.,]\d+)?\s*$', s)
        if mm:
            label = mm.group(1).strip(" .-:;")
            # Solo aceptamos si realmente hay letras (evita "1", "8.", etc.)
            if re.search(r'[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]', label):
                return label

    # 3) Etiquetas personalizadas
    if etiquetas and hasattr(etiquetas, "get"):
        v = etiquetas.get(k) or etiquetas.get(ku)
        if v:
            return v

    # 4) Siglas conocidas
    return _LABELS.get(ku, k)


# --------------------------------------------------------------------------------
# 5) normalize_label: si el label final no tiene letras → "Contenido X" por defecto
# --------------------------------------------------------------------------------
@register.filter(name="normalize_label")
def normalize_label(label):
    """
    Si el label no tiene letras (p. ej. '1', '8.', '9'), devuelve 'Contenido <n>'.
    Si tiene letras, lo deja tal cual.
    """
    s = "" if label is None else str(label).strip()
    # ¿tiene alguna letra?
    if re.search(r'[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]', s):
        return s

    # ¿es un número (con o sin punto/coma final)?
    m = re.fullmatch(r'\s*(-?\d+)(?:[.,]\d+)?\.?\s*', s)
    if m:
        n = m.group(1)
        return f"Contenido {n}"

    return s or "Contenido"
