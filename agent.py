"""Agente: decide qué herramienta usar según el tipo de entrada y el estado del usuario."""
import random

import config
import grammar
import pronunciation
import storage

PENDING = {}  # user_id -> frase de referencia que el usuario debe leer en voz alta
PENDING_IMAGE = {}  # user_id -> descripción de la imagen para el siguiente ejercicio
CONVERSATION_HISTORY = {}  # user_id -> últimos turnos de texto en memoria
MAX_CONVERSATION_MESSAGES = 8

TOPIC_OPENERS = {
    "daily": {
        "en": [
            "What has been the most interesting part of your day so far?",
            "Tell me about something that made you smile recently.",
        ],
        "fr": [
            "Quel a été le moment le plus intéressant de ta journée ?",
            "Raconte-moi quelque chose qui t'a fait sourire récemment.",
        ],
    },
    "food": {
        "en": [
            "What is something you enjoy eating, and why?",
            "Is there a dish that reminds you of home?",
        ],
        "fr": [
            "Qu'est-ce que tu aimes manger, et pourquoi ?",
            "Y a-t-il un plat qui te rappelle la maison ?",
        ],
    },
    "travel": {
        "en": [
            "If you could spend a weekend anywhere, where would you go?",
            "Tell me about a place you'd like to visit one day.",
        ],
        "fr": [
            "Si tu pouvais passer un week-end n'importe où, où irais-tu ?",
            "Parle-moi d'un endroit que tu aimerais visiter un jour.",
        ],
    },
    "hobbies": {
        "en": [
            "What do you enjoy doing when you have free time?",
            "Have you discovered any new hobby recently?",
        ],
        "fr": [
            "Qu'est-ce que tu aimes faire pendant ton temps libre ?",
            "As-tu découvert un nouveau passe-temps récemment ?",
        ],
    },
}


def _format_grammar(res: dict) -> str:
    if res["error_count"] == 0:
        head = "✅ Muy bien, no encontré errores."
    else:
        head = f"✏️ Corrección: {res['corrected']}"
    if res["explanation"]:
        head += f"\n📘 {res['explanation']}"
    return f"{head}\n\n💬 {res['reply']}"


def handle_text(user_id: int, text: str) -> str:
    prof = storage.get_profile(user_id)
    image_context = PENDING_IMAGE.get(user_id)
    history = CONVERSATION_HISTORY.get(user_id, [])
    res = grammar.correct_and_reply(
        text,
        prof["lang"],
        prof["level"],
        image_context=image_context,
        history=history,
    )
    storage.log_event(user_id, "grammar", errors=res["error_count"])
    PENDING_IMAGE.pop(user_id, None)
    CONVERSATION_HISTORY[user_id] = (
        history
        + [
            {"role": "user", "content": text},
            {"role": "assistant", "content": res["reply"]},
        ]
    )[-MAX_CONVERSATION_MESSAGES:]
    return _format_grammar(res)


def reset_conversation(user_id: int) -> None:
    CONVERSATION_HISTORY.pop(user_id, None)


def start_topic(user_id: int, topic: str) -> str:
    prof = storage.get_profile(user_id)
    try:
        options = TOPIC_OPENERS[topic][prof["lang"]]
    except KeyError:
        raise ValueError("Tema o idioma de conversación no válido.") from None

    opener = random.choice(options)
    PENDING.pop(user_id, None)
    PENDING_IMAGE.pop(user_id, None)
    CONVERSATION_HISTORY[user_id] = [{"role": "assistant", "content": opener}]
    return opener


def start_image_practice(user_id: int) -> str:
    prof = storage.get_profile(user_id)
    PENDING.pop(user_id, None)
    PENDING_IMAGE[user_id] = (
        "El usuario envió una imagen, pero no se analizó visualmente. "
        "No afirmes qué aparece en ella. Corrige la palabra u oración que escriba "
        "el estudiante basándote solo en su respuesta."
    )
    return (
        f"🖼️ Recibí tu imagen. Practiquemos {config.LANGS[prof['lang']]}: "
        "descríbela con una sola palabra o una oración completa. "
        "Puedes responder por texto o con una nota de voz. "
        "No puedo identificar automáticamente los objetos de la foto, pero corregiré "
        "tu descripción."
    )


def cancel_practice(user_id: int) -> None:
    PENDING.pop(user_id, None)
    PENDING_IMAGE.pop(user_id, None)


def start_practice(user_id: int) -> str:
    prof = storage.get_profile(user_id)
    phrase = pronunciation.random_phrase(prof["lang"])
    PENDING_IMAGE.pop(user_id, None)
    PENDING[user_id] = phrase
    return f"🎙️ Envíame una nota de voz leyendo esta frase:\n\n{phrase}"


def handle_voice(user_id: int, audio_path: str) -> str:
    prof = storage.get_profile(user_id)
    if user_id in PENDING:
        ref = PENDING.pop(user_id)
        res = pronunciation.assess(audio_path, ref, prof["lang"])
        storage.log_event(user_id, "pronunciation", score=res["score"])
        msg = f"🎯 Pronunciación: {res['score']}/100\nEscuché: {res['heard']}"
        if res["wrong"]:
            tips = "\n".join(f"• dijiste «{h}» en lugar de «{e}»" for e, h in res["wrong"])
            msg += f"\n\nPalabras para repasar:\n{tips}"
        return msg + "\n\nEscribe /practice para otra frase."
    heard = pronunciation.transcribe(audio_path, prof["lang"])
    if not heard:
        return "No pude entender el audio. ¿Puedes repetirlo en un lugar con menos ruido?"
    return f"🎙️ Entendí: {heard}\n\n" + handle_text(user_id, heard)


def progress(user_id: int) -> str:
    s = storage.summary(user_id)
    return (
        f"📊 Tu progreso\n"
        f"• Mensajes corregidos: {s['grammar_n']} (errores promedio: {s['avg_errors']:.1f})\n"
        f"• Prácticas de pronunciación: {s['pron_n']} (puntaje promedio: {s['avg_score']:.0f}/100)"
    )
