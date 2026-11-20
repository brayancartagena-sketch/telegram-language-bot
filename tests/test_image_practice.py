import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import agent
import grammar


class ImagePracticeTests(unittest.TestCase):
    def setUp(self):
        agent.PENDING.clear()
        agent.PENDING_IMAGE.clear()

    def tearDown(self):
        agent.PENDING.clear()
        agent.PENDING_IMAGE.clear()

    def test_uploaded_image_starts_text_practice_without_paid_vision(self):
        profile = {"lang": "en", "level": "A2"}
        result = {
            "corrected": "A bicycle",
            "explanation": "«Bicycle» significa bicicleta.",
            "error_count": 0,
            "reply": "What color is it?",
        }
        with (
            patch("agent.storage.get_profile", return_value=profile),
            patch("agent.grammar.correct_and_reply", return_value=result) as correct,
            patch("agent.storage.log_event") as log_event,
        ):
            prompt = agent.start_image_practice(1)
            answer = agent.handle_text(1, "bicycle")

        self.assertIn("una sola palabra o una oración completa", prompt)
        self.assertIn("nota de voz", prompt)
        self.assertIn("No puedo identificar automáticamente", prompt)
        self.assertIn("«Bicycle»", answer)
        correct.assert_called_once()
        self.assertIn(
            "no se analizó visualmente",
            correct.call_args.kwargs["image_context"],
        )
        log_event.assert_called_once_with(1, "grammar", errors=0)

    def test_voice_description_uses_image_exercise_context(self):
        profile = {"lang": "en", "level": "A2"}
        result = {
            "corrected": "A dog is running.",
            "explanation": "",
            "error_count": 0,
            "reply": "What color is the dog?",
        }
        with (
            patch("agent.storage.get_profile", return_value=profile),
            patch(
                "agent.pronunciation.transcribe", return_value="A dog is running"
            ),
            patch("agent.grammar.correct_and_reply", return_value=result) as correct,
            patch("agent.storage.log_event"),
        ):
            agent.start_image_practice(2)
            reply = agent.handle_voice(2, "voice.ogg")

        self.assertIn("A dog is running", reply)
        self.assertIn(
            "no se analizó visualmente",
            correct.call_args.kwargs["image_context"],
        )

    def test_cancel_clears_image_practice_context(self):
        agent.PENDING_IMAGE[3] = "image practice context"
        agent.cancel_practice(3)
        self.assertNotIn(3, agent.PENDING_IMAGE)

    def test_grammar_prompt_accepts_a_single_word(self):
        output = SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content=(
                            '{"corrected":"bicycle","explanation":"Significa bicicleta.",'
                            '"error_count":0,"reply":"What color is it?"}'
                        )
                    )
                )
            ]
        )
        client = SimpleNamespace(chat_completion=Mock(return_value=output))
        with patch("grammar._get_client", return_value=client):
            result = grammar.correct_and_reply(
                "bicycle", "en", "A2", image_context="El usuario envió una imagen."
            )

        messages = client.chat_completion.call_args.kwargs["messages"]
        self.assertIn("una sola palabra", messages[0]["content"])
        self.assertIn("El usuario envió una imagen.", messages[1]["content"])
        self.assertEqual(result["corrected"], "bicycle")


if __name__ == "__main__":
    unittest.main()
