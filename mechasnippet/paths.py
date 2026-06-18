"""Resolución de rutas de la aplicación.

El snippets.json REAL vive en Application Support (fuera del repo). El repo
solo trae snippets.example.json, que se usa como semilla la primera vez.
"""

import os
import sys

APP_DIR_NAME = "MechaSnippet"
SNIPPETS_FILENAME = "snippets.json"
EXAMPLE_FILENAME = "snippets.example.json"


def app_support_dir():
    """Directorio de datos del usuario, creado si no existe."""
    base = os.path.expanduser("~/Library/Application Support")
    path = os.path.join(base, APP_DIR_NAME)
    os.makedirs(path, exist_ok=True)
    return path


def snippets_path():
    """Ruta al snippets.json real del usuario."""
    return os.path.join(app_support_dir(), SNIPPETS_FILENAME)


def example_path():
    """Ubica el snippets.example.json embebido.

    Busca en el bundle (.app empaquetada con py2app), junto al paquete y en la
    raíz del repo (modo desarrollo). Devuelve None si no lo encuentra.
    """
    candidates = []

    # 1) Recursos del bundle .app (py2app copia data_files a Resources/)
    if getattr(sys, "frozen", False):
        resources = os.path.normpath(
            os.path.join(os.path.dirname(sys.executable), "..", "Resources")
        )
        candidates.append(os.path.join(resources, EXAMPLE_FILENAME))

    here = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(here)

    # 2) Junto al paquete y 3) en la raíz del repo (desarrollo)
    candidates.append(os.path.join(here, EXAMPLE_FILENAME))
    candidates.append(os.path.join(repo_root, EXAMPLE_FILENAME))

    for path in candidates:
        if os.path.exists(path):
            return path
    return None
