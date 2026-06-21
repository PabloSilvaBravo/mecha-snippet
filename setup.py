"""Empaquetado de Mecha Snippet como aplicación .app con py2app.

Uso:
    pip install -r requirements-build.txt
    python setup.py py2app

El .app resultante queda en dist/Mecha Snippet.app
"""

from setuptools import setup

APP = ["run.py"]
DATA_FILES = ["snippets.example.json"]
OPTIONS = {
    "argv_emulation": False,
    # Incluir pynput COMPLETO: sus backends de macOS (_darwin) se cargan de forma
    # dinámica, así que py2app no los detecta por análisis estático y hay que
    # forzar la copia de todo el paquete.
    "packages": ["mechasnippet", "pynput"],
    "plist": {
        "CFBundleName": "Mecha Snippet",
        "CFBundleDisplayName": "Mecha Snippet",
        "CFBundleIdentifier": "io.github.pablosilvabravo.mechasnippet",
        "CFBundleVersion": "1.0.0",
        "CFBundleShortVersionString": "1.0.0",
        # App de fondo: sin ícono en el Dock, solo en la barra de menú.
        "LSUIElement": True,
        "LSMinimumSystemVersion": "12.0",
        "NSHumanReadableCopyright": "Pablo Silva Bravo",
        # Texto que aparece al pedir permisos de automatización.
        "NSAppleEventsUsageDescription": (
            "Mecha Snippet inserta el texto del snippet en la aplicación activa."
        ),
    },
}

setup(
    name="Mecha Snippet",
    app=APP,
    data_files=DATA_FILES,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
