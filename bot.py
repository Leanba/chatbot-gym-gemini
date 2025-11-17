import os
import asyncio
import google.generativeai as genai
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configurar Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("models/gemini-2.5-pro")  # Modelo correcto

# Mensaje inicial
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
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

# Manejo de mensajes de texto
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user_message = update.message.text
    prompt = f"""
Sos un asistente de gimnasio tipo personal trainer.
Respondé de forma concisa, máximo 2-3 frases.
Explicá ejercicios, músculos que trabaja y recomendaciones básicas.
Si el usuario menciona lesiones, adaptá la respuesta.
Pregunta del usuario:
{user_message}
"""

    try:
        # Llamada a Gemini en thread para no bloquear
        response = await asyncio.to_thread(model.generate_content, prompt)

        # Extraer el texto de forma segura
        text = ""
        if hasattr(response, "candidates") and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, "content"):
                for part in candidate.content:
                    if hasattr(part, "text"):
                        text += part.text

        if not text:
            await update.message.reply_text("⚠️ No pude generar la respuesta, probá otra vez.")
            return

        await update.message.reply_text(text)

    except Exception as e:
        await update.message.reply_text(f"⚠️ Error en el servidor: {str(e)}")

# Inicializar bot
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    return app

bot_app = main()
