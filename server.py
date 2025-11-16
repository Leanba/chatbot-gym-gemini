import os
import asyncio
from flask import Flask, request
from bot import bot_app

app = Flask(__name__)

# Usamos el loop del bot
loop = asyncio.get_event_loop()

@app.route("/", methods=["POST"])
def webhook():
    update = request.get_json()

    # Procesamos update con el bot
    loop.create_task(bot_app.process_update(update))

    return "OK", 200

@app.route("/", methods=["GET"])
def home():
    return "Bot funcionando", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port)
