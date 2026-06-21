"""Carga y recarga de los snippets desde disco, manteniéndolos en memoria.

Formatos aceptados en snippets.json:
  - Objeto:  {"nombre": "contenido", ...}            (formato del ejemplo)
  - Lista:   [{"name": "...", "content": "..."}, ...]  (alternativa)

Los snippets se guardan en memoria como una lista de tuplas (nombre, contenido).
Para miles de entradas el costo es de unos pocos MB y la carga es instantánea.
"""

import json
import os
import shutil
import sys

from . import paths


class SnippetStore:
    def __init__(self):
        self.path = paths.snippets_path()
        self._items = []
        self._ensure_exists()
        self.reload()

    def _ensure_exists(self):
        """Crea snippets.json desde el ejemplo si el usuario aún no tiene uno."""
        if os.path.exists(self.path):
            return
        example = paths.example_path()
        try:
            if example and os.path.exists(example):
                shutil.copyfile(example, self.path)
            else:
                with open(self.path, "w", encoding="utf-8") as fh:
                    json.dump({}, fh, ensure_ascii=False, indent=2)
            os.chmod(self.path, 0o600)  # datos privados: solo el dueño
        except OSError:
            # Si no se puede escribir, seguimos con una lista vacía en memoria.
            pass

    def reload(self):
        """Relee el archivo desde disco.

        Si el JSON está corrupto (p.ej. una coma de más al editar), CONSERVA la
        última versión buena en memoria en vez de borrar todos los snippets.
        """
        try:
            with open(self.path, "r", encoding="utf-8") as fh:
                content = fh.read()
        except OSError:
            return len(self._items)  # ausente/ilegible: conservar lo que haya
        if not content.strip():
            self._items = []  # archivo realmente vacío
            return 0
        try:
            data = json.loads(content)
        except ValueError:
            sys.stderr.write(
                "[mecha] snippets.json inválido: conservo la última versión buena\n"
            )
            sys.stderr.flush()
            return len(self._items)
        self._items = self._normalize(data)
        return len(self._items)

    @staticmethod
    def _normalize(data):
        items = []
        if isinstance(data, dict):
            for key, value in data.items():
                items.append((str(key), str(value)))
        elif isinstance(data, list):
            for entry in data:
                if isinstance(entry, dict):
                    name = entry.get("name") or entry.get("key") or ""
                    content = entry.get("content") or entry.get("value") or ""
                    if name:
                        items.append((str(name), str(content)))
        return items

    @property
    def items(self):
        return self._items

    def __len__(self):
        return len(self._items)
