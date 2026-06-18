"""Resolución de rutas de la aplicación.

El snippets.json REAL vive en Application Support (fuera del repo). El repo
solo trae snippets.example.json, que se usa como semilla la primera vez.
"""

import os
import sys

APP_DIR_NAME = "MechaSnippet"
SNIPPETS_FILENAME = "snippets.json"
EXAMPLE_FILENAME = "snippets.example.json"

# Variable de entorno opcional para que cada Mac apunte su snippets.json a una
# ruta propia (carpeta o archivo). Si no está definida, se usa Application Support.
ENV_SNIPPETS = "MECHA_SNIPPET_FILE"


def app_support_dir():
    """Directorio de datos del usuario, creado si no existe."""
    base = os.path.expanduser("~/Library/Application Support")
    path = os.path.join(base, APP_DIR_NAME)
    os.makedirs(path, exist_ok=True)
    return path


def snippets_path():
    """Ruta al snippets.json real y privado del usuario, local a este Mac.

    Prioridad:
      1. Variable de entorno MECHA_SNIPPET_FILE (archivo o carpeta).
      2. ~/Library/Application Support/MechaSnippet/snippets.json (por defecto).
    En ambos casos se asegura que la carpeta contenedora exista.
    """
    override = os.environ.get(ENV_SNIPPETS, "").strip()
    if override:
        path = os.path.abspath(os.path.expanduser(os.path.expandvars(override)))
        if os.path.isdir(path):
            path = os.path.join(path, SNIPPETS_FILENAME)
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        return path

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
