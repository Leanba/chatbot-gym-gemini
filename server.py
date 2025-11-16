import os
import asyncio
from flask import Flask, request
from telegram import Update
from bot import bot_app

app = Flask(__name__)

@app.route("/", methods=["POST"])
def webhook():
    update_data = request.get_json(force=True)

    # Conversión correcta
    update = Update.de_json(update_data, bot_app.bot)

    # Procesar el update async
    asyncio.get_event_loop().create_task(bot_app.process_update(update))

    return "OK", 200


@app.route("/", methods=["GET"])
def home():
    return "Bot funcionando", 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
