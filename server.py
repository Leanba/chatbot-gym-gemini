from flask import Flask, request
import asyncio
from bot import bot_app

app = Flask(__name__)

# Cola asincrónica
queue = asyncio.Queue()

@app.route("/", methods=["POST"])
def webhook():
    update = request.get_json(force=True)

    # Enviar el update a la cola asincrónica
    asyncio.create_task(queue.put(update))

    return "OK", 200

@app.route("/", methods=["GET"])
def home():
    return "Bot funcionando", 200

async def process_updates():
    while True:
        update = await queue.get()
        await bot_app.process_update(update)

if __name__ == "__main__":
    import os

    # Iniciar proceso que maneja los mensajes
    loop = asyncio.get_event_loop()
    loop.create_task(process_updates())

    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port)
