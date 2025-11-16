import os
import asyncio
from flask import Flask, request
from bot import bot_app

app = Flask(__name__)

# Telegram usará este endpoint
@app.post("/")
async def webhook():
    update_data = request.get_json(force=True)
    update = bot_app.bot._factory.update(update_data, bot_app.bot)
    await bot_app.process_update(update)
    return "OK", 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
