import os
from flask import Flask, request
import asyncio
from bot import bot_app

app = Flask(__name__)

@app.route("/", methods=["POST"])
def webhook():
    update_data = request.get_json(force=True)
    
    update = bot_app.bot._factory.update(update_data, bot_app.bot)

    # Ejecutamos el update en el event loop del bot
    asyncio.get_event_loop().create_task(bot_app.process_update(update))

    return "OK", 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
