"""Perfil y progreso de cada usuario en SQLite."""
import sqlite3
import time
import config


def _conn():
    con = sqlite3.connect(config.DB_PATH)
    con.execute(
        "CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, lang TEXT, level TEXT)"
    )
    con.execute(
        "CREATE TABLE IF NOT EXISTS events (user_id INTEGER, ts REAL, kind TEXT, score REAL, errors INTEGER)"
    )
    return con


def get_profile(user_id: int) -> dict:
    with _conn() as con:
        row = con.execute("SELECT lang, level FROM users WHERE user_id=?", (user_id,)).fetchone()
    return {"lang": row[0], "level": row[1]} if row else {"lang": "en", "level": "A2"}


def set_profile(user_id: int, lang=None, level=None) -> None:
    prof = get_profile(user_id)
    prof["lang"] = lang or prof["lang"]
    prof["level"] = level or prof["level"]
    with _conn() as con:
        con.execute(
            "INSERT OR REPLACE INTO users VALUES (?,?,?)", (user_id, prof["lang"], prof["level"])
        )


def log_event(user_id: int, kind: str, score: float = 0.0, errors: int = 0) -> None:
    with _conn() as con:
        con.execute("INSERT INTO events VALUES (?,?,?,?,?)", (user_id, time.time(), kind, score, errors))


def summary(user_id: int) -> dict:
    with _conn() as con:
        g = con.execute(
            "SELECT COUNT(*), COALESCE(AVG(errors),0) FROM events WHERE user_id=? AND kind='grammar'",
            (user_id,),
        ).fetchone()
        p = con.execute(
            "SELECT COUNT(*), COALESCE(AVG(score),0) FROM events WHERE user_id=? AND kind='pronunciation'",
            (user_id,),
        ).fetchone()
    return {"grammar_n": g[0], "avg_errors": g[1], "pron_n": p[0], "avg_score": p[1]}
