# Bot de Telegram para aprender inglés y francés

Tutor de idiomas dentro de Telegram: corrige gramática, evalúa pronunciación, propone ejercicios con imágenes y mantiene una conversación adaptada al nivel (A1–C1).

## Arquitectura

```
Telegram → bot.py → agent.py ─┬─ grammar.py        (LLM en Hugging Face)
                              ├─ pronunciation.py  (Whisper en Hugging Face)
                              └─ storage.py        (SQLite: perfil y progreso)
```

## Conversación interactiva

- Puedes escribir libremente; el tutor usa los últimos cuatro turnos para mantener el contexto y variar sus respuestas, sin terminar siempre con una pregunta.
- `/start` muestra botones para elegir idioma, nivel, tema, pronunciación y progreso. Los comandos `/lang`, `/level`, `/practice` y `/progress` siguen disponibles como atajos.
- El historial conversacional se mantiene solo en memoria y se reinicia al reiniciar el bot o cambiar de idioma.

