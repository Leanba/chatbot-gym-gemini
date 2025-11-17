import os
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from telegram import Update
from bot import bot_app
import uvicorn

app = FastAPI()

@app.post("/")
async def webhook(request: Request):
    """
    Webhook de Telegram.
    Recibe los updates y los pasa al Application de PTB.
    """
    try:
        update_data = await request.json()
        update = Update.de_json(update_data, bot_app.bot)

        # Ejecutar el coroutine de PTB sin bloquear
        await bot_app.process_update(update)

        return PlainTextResponse("OK", status_code=200)
    except Exception as e:
        print("Error procesando update:", e)
        return PlainTextResponse("Error", status_code=500)

@app.get("/")
async def home():
    return PlainTextResponse("Bot funcionando", status_code=200)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    # Usamos uvicorn directamente para desarrollo local
    uvicorn.run(app, host="0.0.0.0", port=port)
