import os
import asyncio
from flask import Flask, request
from telegram import Update
from bot import bot_app

app = Flask(__name__)

@app.route("/", methods=["POST"])
def webhook():
    data = request.get_json(force=True)

    # Convertir JSON → Update
    update = Update.de_json(data, bot_app.bot)

    # Procesar el update de manera async
    asyncio.get_event_loop().create_task(bot_app.process_update(update))

    return "OK", 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
