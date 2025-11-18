import os
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from bot import bot_app
from telegram import Update
import uvicorn

app = FastAPI()

# Inicializar el bot al arrancar FastAPI
@app.on_event("startup")
async def startup_event():
    # Inicializamos la aplicación de Telegram
    await bot_app.initialize()

@app.post("/")
async def webhook(request: Request):
    try:
        update_data = await request.json()
        update = Update.de_json(update_data, bot_app.bot)
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
