# Bot de Telegram para aprender inglés y francés

Tutor de idiomas dentro de Telegram: corrige gramática, evalúa pronunciación, propone ejercicios con imágenes y mantiene una conversación adaptada al nivel (A1–C1).

## Arquitectura

```
Telegram → bot.py → agent.py ─┬─ grammar.py        (LLM en Hugging Face)
                              ├─ pronunciation.py  (Whisper en Hugging Face)
                              └─ storage.py        (SQLite: perfil y progreso)
```

