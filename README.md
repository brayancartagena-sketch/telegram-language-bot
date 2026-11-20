# Bot de Telegram para aprender inglés y francés

Tutor de idiomas dentro de Telegram: corrige gramática, evalúa pronunciación, propone ejercicios con imágenes y mantiene una conversación adaptada al nivel (A1–C1).

## Arquitectura

```
Telegram → bot.py → agent.py ─┬─ grammar.py        (LLM en Hugging Face)
                              ├─ pronunciation.py  (Whisper en Hugging Face)
                              └─ storage.py        (SQLite: perfil y progreso)
```

- **Texto**: el LLM corrige, explica la regla en español y responde para seguir la conversación.
- **Voz**: con `/practice` el bot da una frase; el audio se transcribe con Whisper y se compara con la frase. Sin `/practice`, el audio se transcribe y se trata como texto.
- **Imágenes**: envía una foto y el bot te invita a describirla con una palabra o una oración en el idioma elegido. Puedes escribir la respuesta o decirla en una nota de voz; el tutor corrige lo que escribas o digas. Para no depender de inferencia visual de pago, el bot no identifica automáticamente el contenido de la foto.
- **Progreso**: `/progress` resume errores promedio y puntaje de pronunciación.

## Instalación

1. Instala Python 3.10 o 3.11. `imageio-ffmpeg` incluye FFmpeg para procesar las notas de voz .ogg de Telegram.
2. `pip install -r requirements.txt`
3. Crea el bot con @BotFather en Telegram y copia el token.
4. Copia `.env.example` a `.env` y completa `TELEGRAM_TOKEN` y `HF_TOKEN`. El token de Hugging Face debe tener permiso **Inference Providers** para el corrector.
5. `python bot.py`

Las fotos recibidas no se envían a un modelo visual; el estudiante las describe por texto o voz y el tutor corrige esa descripción.

## Evaluación

- `python evaluate_jfleg.py --n 100` → GLEU del corrector en inglés (JFLEG).
- `python evaluate_asr_commonvoice.py --lang fr --n 100` → WER del ASR en Common Voice.

## Limitaciones (para el informe)

- JFLEG es solo inglés; para francés hay que construir un conjunto de prueba propio.
- El puntaje de pronunciación es un indicador basado en ASR (inteligibilidad), no un análisis fonético por fonema (GOP). Una mejora futura es usar un modelo de alineación de fonemas.
- Verifica la disponibilidad de Common Voice en Hugging Face y los modelos del LLM, porque pueden cambiar.
- El LLM puede equivocarse; el bot evita inventar correcciones cuando la respuesta no es interpretable.
