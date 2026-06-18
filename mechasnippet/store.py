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
        except OSError:
            # Si no se puede escribir, seguimos con una lista vacía en memoria.
            pass

    def reload(self):
        """Relee el archivo desde disco. Tolera JSON inválido sin crashear."""
        data = self._read_raw()
        self._items = self._normalize(data)
        return len(self._items)

    def _read_raw(self):
        try:
            with open(self.path, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except (OSError, ValueError):
            return {}

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
