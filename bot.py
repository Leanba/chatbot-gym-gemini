import os
import asyncio
import google.generativeai as genai
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-pro")

# Mensaje inicial
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🏋️‍♂️ ¡Hola! Soy tu asistente de gimnasio con IA.\n"
        "Puedo ayudarte con:\n"
        "- Explicación de ejercicios\n"
        "- Músculos que trabaja cada movimiento\n"
        "- Rutinas recomendadas\n"
        "- Qué hacer si tenés lesiones\n"
        "- Recomendaciones de videos\n\n"
        "Escribime tu duda cuando quieras 💪"
    )

# Mensaje principal
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text

    prompt = f"""
    Sos un asistente de gimnasio tipo personal trainer.
    Explicá ejercicios, músculos que trabaja, rutinas y recomendaciones seguras.
    Si el usuario menciona lesiones, adaptá la respuesta.
    Podés sugerir videos de YouTube basados en el ejercicio.

    Pregunta del usuario:
    {user_message}
    """

    # Llamada correcta a Gemini en thread
    try:
        response = await asyncio.to_thread(model.generate_content, prompt)

        if not response or not hasattr(response, "text"):
            await update.message.reply_text("⚠️ Error al generar la respuesta. Probá de nuevo.")
            return

        await update.message.reply_text(response.text)

    except Exception as e:
        await update.message.reply_text(f"⚠️ Error en el servidor: {str(e)}")

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    return app

bot_app = main()
