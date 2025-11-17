import asyncio
from telegram import Update, Message
from types import SimpleNamespace
from bot import bot_app

async def test_handle():
    # Simular un mensaje de Telegram
    class DummyMessage:
        def __init__(self, text):
            self.text = text

        async def reply_text(self, text):
            print("Bot responde:", text)

    dummy_update = SimpleNamespace(message=DummyMessage("Hola, qué ejercicio me recomendas para espalda?"))
    dummy_context = None  # Context no lo usamos directamente en tu handle

    # Llamar a la función handle_message
    await bot_app.handlers[1].callback(dummy_update, dummy_context)

if __name__ == "__main__":
    asyncio.run(test_handle())
