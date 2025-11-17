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
Explicá ejercicios, músculos que trabaja, rutinas y recomendaciones seguras.
Si el usuario menciona lesiones, adaptá la respuesta.
Podés sugerir videos de YouTube basados en el ejercicio.

Pregunta del usuario:
{user_message}
"""

    try:
        # Llamada a Gemini en thread para no bloquear
        response = await asyncio.to_thread(model.generate_content, {"text": prompt})

        # Verificar candidatos
        if not response.candidates:
            await update.message.reply_text("⚠️ Error al generar la respuesta. Probá de nuevo.")
            return

        # Acceder al texto generado según la versión actual
        candidate = response.candidates[0]

        # Dependiendo de la versión, puede venir en output_text o content
        if hasattr(candidate, "output_text"):
            gemini_text = candidate.output_text
        elif hasattr(candidate, "content"):
            # 'content' es un objeto, no una lista, se accede a candidate.content[0].text si es lista
            try:
                gemini_text = candidate.content[0].text
            except Exception:
                # fallback: convertir a string
                gemini_text = str(candidate.content)
        else:
            gemini_text = "⚠️ No se pudo obtener la respuesta de Gemini."

        await update.message.reply_text(gemini_text)

    except Exception as e:
        await update.message.reply_text(f"⚠️ Error en el servidor: {str(e)}")

# Inicializar bot
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    return app

bot_app = main()
