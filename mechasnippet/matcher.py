"""Filtro de snippets en tiempo real.

Búsqueda insensible a mayúsculas y tildes. Cada palabra del query debe
aparecer (en el nombre o el contenido). El ranking prioriza coincidencias en
el nombre por sobre el contenido, para que lo más relevante quede arriba.
"""

import unicodedata


def _norm(text):
    """Minúsculas y sin tildes, para comparar de forma robusta."""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return text.lower()


def filter_snippets(items, query):
    """Devuelve la lista de (nombre, contenido) que coincide con `query`, ordenada.

    Sin query, devuelve todos los items en su orden original.
    """
    q = _norm(query).strip()
    if not q:
        return list(items)

    tokens = q.split()
    scored = []
    for name, content in items:
        norm_name = _norm(name)
        norm_content = _norm(content)
        haystack = norm_name + "\n" + norm_content

        if not all(token in haystack for token in tokens):
            continue

        # Menor score = más relevante.
        if norm_name.startswith(q):
            score = 0
        elif q in norm_name:
            score = 1
        elif all(token in norm_name for token in tokens):
            score = 2
        else:
            score = 3

        scored.append((score, norm_name, (name, content)))

    scored.sort(key=lambda row: (row[0], row[1]))
    return [row[2] for row in scored]
