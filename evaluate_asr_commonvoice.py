"""Mide el WER del ASR sobre Mozilla Common Voice (inglés o francés).

Uso: python evaluate_asr_commonvoice.py --lang fr --n 100

Nota: confirma que el dataset siga disponible en Hugging Face. Si no lo está,
descarga Common Voice desde Mozilla Data Collective y ajusta load_dataset.
"""
import argparse
import jiwer
from datasets import Audio, load_dataset
import config
import pronunciation


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", choices=["en", "fr"], default="en")
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--dataset", default="mozilla-foundation/common_voice_17_0")
    args = ap.parse_args()

    ds = load_dataset(args.dataset, args.lang, split="test", streaming=True, token=config.HF_TOKEN)
    ds = ds.cast_column("audio", Audio(sampling_rate=16000))
    refs, hyps = [], []
    asr = pronunciation._get_asr()
    kwargs = {"language": config.WHISPER_LANG[args.lang], "task": "transcribe"}
    for i, ex in enumerate(ds):
        if i >= args.n:
            break
        text = asr(ex["audio"]["array"], generate_kwargs=kwargs)["text"]
        hyps.append(" ".join(pronunciation._norm(text)))
        refs.append(" ".join(pronunciation._norm(ex["sentence"])))
    print(f"WER ({args.lang}, {len(refs)} audios): {jiwer.wer(refs, hyps):.3f}")


if __name__ == "__main__":
    main()
