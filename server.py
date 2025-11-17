import os
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from telegram import Update
from bot import application as bot_app
import asyncio
import uvicorn

app = FastAPI()

# Inicializar Telegram Application antes de recibir updates
asyncio.run(bot_app.initialize())

@app.post("/")
async def webhook(request: Request):
    try:
        update_data = await request.json()
        update = Update.de_json(update_data, bot_app.bot)

        # Procesar update
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
    uvicorn.run(app, host="0.0.0.0", port=port)
