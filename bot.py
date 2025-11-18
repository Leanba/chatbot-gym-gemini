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
model = genai.GenerativeModel("models/gemini-2.5-pro")

# Función para enviar mensajes largos a Telegram
async def send_long_message(update, text):
    MAX_LEN = 4096  # límite Telegram
    for i in range(0, len(text), MAX_LEN):
        await update.message.reply_text(text[i:i + MAX_LEN])

# /start
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

# Mensajes normales
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user_message = update.message.text

    prompt = f"""
Sos un Personal trainer de gimnasio experto en musculación.
Tu objetivo es dar respuestas claras, breves y fáciles de leer, como un coach profesional.

REGLAS OBLIGATORIAS:
- Máximo 10 líneas por respuesta.
- Explicá como un coach profesional: preciso, amable y directo.
- Cuando expliques ejercicios, usa esta estructura:
  1. Ejecución simple
  2. Músculos principales
  3. Consejos o errores comunes (opcional)
- Usá oraciones cortas y lenguaje accesible.
- Evitá tecnicismos innecesarios.
- No des diagnósticos médicos ni planes clínicos.
- Formato siempre en Markdown simple:
  - Viñetas con "-"
  - Nada de párrafos largos
  - Usar emojis de forma moderada
No uses formato raro ni JSON, solo texto directo.

Pregunta del usuario:
{user_message}
"""

    try:
        # Ejecutar Gemini en un thread aparte
        response = await asyncio.to_thread(model.generate_content, prompt)

        # Extraer texto limpio
        gemini_text = ""

        try:
            content = response.candidates[0].content
            for part in content:
                if hasattr(part, "text"):
                    gemini_text += part.text
            gemini_text = gemini_text.strip()
        except Exception:
            # Backup por si cambia el formato
            if hasattr(response, "text"):
                gemini_text = response.text.strip()
            else:
                gemini_text = "⚠ No pude interpretar la respuesta del modelo."

        # Enviar respuesta limpia
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
