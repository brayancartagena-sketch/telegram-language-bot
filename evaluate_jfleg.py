"""Evalúa el corrector gramatical (inglés) en JFLEG con la métrica GLEU.

Uso: python evaluate_jfleg.py --n 100
"""
import argparse
from datasets import load_dataset
from nltk.translate.gleu_score import sentence_gleu
import grammar


def tok(s: str) -> list:
    return s.lower().split()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--level", default="B1")
    args = ap.parse_args()

    ds = load_dataset("jhu-clsp/jfleg", split=f"validation[:{args.n}]")
    base, model = [], []
    for ex in ds:
        refs = [tok(c) for c in ex["corrections"]]
        out = grammar.correct_and_reply(ex["sentence"], "en", args.level)["corrected"]
        base.append(sentence_gleu(refs, tok(ex["sentence"])))
        model.append(sentence_gleu(refs, tok(out)))
    print(f"GLEU sin corregir : {sum(base) / len(base):.3f}")
    print(f"GLEU con el tutor : {sum(model) / len(model):.3f}")


if __name__ == "__main__":
    main()
