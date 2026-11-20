"""Corrección gramatical y respuesta conversacional con un LLM de Hugging Face."""
import json
import re
from huggingface_hub import InferenceClient
import config

_client = None

SYSTEM = (
    "Eres un tutor amable de {lang} para estudiantes hispanohablantes de nivel {level}. "
    "Recibes un mensaje del estudiante. Responde SOLO con un objeto JSON con estas claves: "
    '"corrected" (el mensaje corregido y fluido en {lang}; igual al original si no hay errores), '
    '"explanation" (en español, máximo 2 frases: explica el error o, si es una sola palabra correcta, su significado o uso; cadena vacía si no hay comentario útil), '
    '"error_count" (entero), '
    '"reply" (respuesta breve y natural en {lang}, adecuada al nivel {level}, que termine con una pregunta). '
    "Si el estudiante responde con una sola palabra, considérala una respuesta válida: corrige su "
    "ortografía si hace falta y explica brevemente su significado o uso en español. "
    "Si recibes contexto de una imagen, acepta una palabra o una oración relacionada con ella."
)


def _get_client() -> InferenceClient:
    global _client
    if _client is None:
        _client = InferenceClient(model=config.LLM_MODEL, token=config.HF_TOKEN)
    return _client


def _parse(raw: str) -> dict:
    if not isinstance(raw, str):
        raise ValueError("La respuesta del modelo no es texto.")
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match is None:
        raise ValueError("La respuesta del modelo no contiene JSON.")
    data = json.loads(match.group(0))
    if not isinstance(data, dict):
        raise ValueError("La respuesta JSON no es un objeto.")
    return {
        "corrected": str(data.get("corrected", "")).strip(),
        "explanation": str(data.get("explanation", "")).strip(),
        "error_count": int(data.get("error_count", 0)),
        "reply": str(data.get("reply", "")).strip(),
    }


def correct_and_reply(
    text: str,
    lang: str,
    level: str,
    image_context: str | None = None,
) -> dict:
    user_text = text
    if image_context:
        user_text = (
            f"Contexto aproximado de la imagen: {image_context}\n"
            f"Respuesta del estudiante sobre la imagen: {text}"
        )
    messages = [
        {"role": "system", "content": SYSTEM.format(lang=config.LANGS[lang], level=level)},
        {"role": "user", "content": user_text},
    ]
    out = _get_client().chat_completion(messages=messages, max_tokens=400, temperature=0.2)
    raw = out.choices[0].message.content
    try:
        return _parse(raw)
    except (AttributeError, TypeError, ValueError):
        # Baja confianza: no inventamos una corrección.
        reply = raw.strip()[:500] if isinstance(raw, str) else ""
        if not reply:
            reply = (
                "Could you tell me a little more?"
                if lang == "en"
                else "Peux-tu m'en dire un peu plus ?"
            )
        return {"corrected": text, "explanation": "", "error_count": 0, "reply": reply}
