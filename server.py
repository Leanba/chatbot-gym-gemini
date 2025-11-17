# server.py
import os
import asyncio
from flask import Flask, request
from telegram import Update
from bot import bot_app

app = Flask(__name__)

@app.route("/", methods=["POST"])
def webhook():
    update_data = request.get_json(force=True)
    update = Update.de_json(update_data, bot_app.bot)

    try:
        # Ejecutamos la coroutine correctamente
        asyncio.run(bot_app.process_update(update))
    except RuntimeError:
        # Si ya hay un loop corriendo (por ejemplo en dev), usamos ensure_future
        loop = asyncio.get_event_loop()
        loop.create_task(bot_app.process_update(update))

    return "OK", 200


@app.route("/", methods=["GET"])
def home():
    return "Bot funcionando", 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
