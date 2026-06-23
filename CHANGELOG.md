# Changelog

## v2.0.0 — Reescritura nativa en Swift

Mecha Snippet pasó de Python a **Swift nativo** (SwiftUI + AppKit, macOS 26 Tahoe).

- Editor visual de snippets: ventana de gestión (crear, editar, borrar, duplicar, reordenar arrastrando) y mini formulario para sumar uno rápido.
- Panel rediseñado: lista a la izquierda, vista previa a la derecha, recuerda su posición. Liquid Glass nativo.
- Inicio automático al abrir sesión.
- Onboarding que guía los permisos en la primera corrida.
- Robustez: guardado atómico y recuperación de snippets.json dañados (comillas tipográficas).
- App de ~1.2 MB (antes ~23 MB con Python).

## v1.0.0 — Versión inicial (Python)

Primera versión del expansor de texto, escrita en Python + PyObjC.
