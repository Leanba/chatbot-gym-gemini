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

# Función para enviar mensajes largos a Telegram
async def send_long_message(update, text):
    MAX_LEN = 4096  # límite de Telegram
    for i in range(0, len(text), MAX_LEN):
        await update.message.reply_text(text[i:i + MAX_LEN])

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
Respondés de forma corta, concisa y clara, de 2 a 3 frases.
Explicá ejercicios, músculos que trabaja, rutinas y recomendaciones seguras.
Si el usuario menciona lesiones, adaptá la respuesta.
Podés sugerir links de videos de YouTube basados en el ejercicio si el usuario así lo quiere.

Pregunta del usuario:
{user_message}
"""

    try:
        # Llamada a Gemini en thread para no bloquear
        response = await asyncio.to_thread(model.generate_content, prompt)

        if not response or not hasattr(response, "candidates"):
            await update.message.reply_text("⚠️ Error al generar la respuesta. Probá de nuevo.")
            return

        # Extraemos el texto correctamente
        gemini_content = response.candidates[0].content
        gemini_text = ""

        # Convertir la lista de partes en texto
        if isinstance(gemini_content, list):
            for part in gemini_content:
                if hasattr(part, "text"):
                    gemini_text += part.text
        else:
            # Si no es lista, intentar convertir a string directo
            gemini_text = str(gemini_content)

        # Enviar respuesta a Telegram
        await send_long_message(update, gemini_text)

    except Exception as e:
        await update.message.reply_text(f"⚠️ Error en el servidor: {str(e)}")

# Inicializar bot
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    return app

bot_app = main()
