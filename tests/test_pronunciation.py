import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import numpy as np

import pronunciation


class TranscriptionTests(unittest.TestCase):
    def test_transcribe_decodes_telegram_ogg_before_whisper(self):
        decoded = np.array([0, 16384, -16384], dtype=np.int16).tobytes()
        asr = Mock(return_value={"text": "hello there"})
        with (
            patch("pronunciation.imageio_ffmpeg.get_ffmpeg_exe", return_value="ffmpeg.exe"),
            patch(
                "pronunciation.subprocess.run",
                return_value=SimpleNamespace(stdout=decoded),
            ) as run_ffmpeg,
            patch("pronunciation._get_asr", return_value=asr),
        ):
            text = pronunciation.transcribe("voice.oga", "en")

        self.assertEqual(text, "hello there")
        self.assertEqual(run_ffmpeg.call_args.args[0][0], "ffmpeg.exe")
        audio_input = asr.call_args.args[0]
        self.assertEqual(audio_input["sampling_rate"], 16000)
        np.testing.assert_allclose(audio_input["raw"], [0.0, 0.5, -0.5])
        self.assertEqual(asr.call_args.kwargs["generate_kwargs"]["language"], "english")

    def test_transcribe_rejects_empty_decoded_audio(self):
        with (
            patch("pronunciation.imageio_ffmpeg.get_ffmpeg_exe", return_value="ffmpeg.exe"),
            patch(
                "pronunciation.subprocess.run",
                return_value=SimpleNamespace(stdout=b""),
            ),
            patch("pronunciation._get_asr") as get_asr,
        ):
            with self.assertRaisesRegex(ValueError, "extraer audio"):
                pronunciation.transcribe("voice.oga", "en")

        get_asr.assert_not_called()


if __name__ == "__main__":
    unittest.main()
