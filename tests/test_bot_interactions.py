import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import bot


class MenuInteractionTests(unittest.IsolatedAsyncioTestCase):
    async def test_topic_button_starts_a_conversation_without_a_command(self):
        query = SimpleNamespace(
            answer=AsyncMock(),
            message=object(),
            data="topic:food",
            edit_message_text=AsyncMock(),
        )
        update = SimpleNamespace(
            callback_query=query,
            effective_user=SimpleNamespace(id=42),
        )
        opener = "What is something you enjoy eating?"

        with patch("bot.agent.start_topic", return_value=opener) as start_topic:
            await bot.on_callback(update, SimpleNamespace())

        start_topic.assert_called_once_with(42, "food")
        query.answer.assert_awaited_once()
        query.edit_message_text.assert_awaited_once_with(opener)


if __name__ == "__main__":
    unittest.main()
