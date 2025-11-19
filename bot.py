import os
import asyncio
import google.generativeai as genai
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    MessageHandler, filters
)
from dotenv import load_dotenv

# Cargamos variables de entorno (token de Telegram y API Key)
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ------------------------------------------------------------
# CONFIGURACIÓN DEL MODELO DE IA
# Se pide usar una API externa de IA
# Acá usamos Google Gemini y actualizamos al modelo solicitado
# Además, seteamos temperature baja para respuestas rápidas
# ------------------------------------------------------------

genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel(
    model_name="models/gemini-2.0-flash-lite-preview-02-05",
    generation_config={
        "temperature": 0.2,         # Respuestas más rápidas, estables y directas
        "top_p": 0.9,
        "top_k": 40,
        "max_output_tokens": 400
    }
)

# Función para mandar mensajes largos (Telegram limita a 4096 caracteres)
async def send_long_message(update, text):
    MAX_LEN = 4096
    for i in range(0, len(text), MAX_LEN):
        await update.message.reply_text(text[i:i + MAX_LEN])

# ------------------------------------------------------------
# COMANDO /start
# Presentamos el bot como un asistente de gimnasio.
# ------------------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    await update.message.reply_text(
        "🏋️‍♂️ ¡Hola! Soy tu asistente de gimnasio con IA.\n"
        "Puedo ayudarte con:\n"
        "• Ejercicios y técnicas correctas\n"
        "• Músculos involucrados en cada movimiento\n"
        "• Rutinas recomendadas según objetivo\n"
        "• Consejos si tenés molestias o dudas\n\n"
        "Envíame tu consulta cuando quieras 💪"
    )

# ------------------------------------------------------------
# MANEJO DE MENSAJES
# Acá enviamos el texto del usuario al modelo Gemini
# aplicando un prompt que define el estilo del asistente
# ------------------------------------------------------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user_message = update.message.text

    # Prompt detallado para guiar a Gemini (cumple con consigna de 'diseñar el asistente')
    prompt = f"""
Sos un Personal Trainer profesional.
Respondé siempre de forma clara, resumida y fácil de entender.
Preguntá si está por comenzar la sesión de entramiento para saber si responder de forma corta o explicativa si es el caso de que la persona no está en el gym y está en su casa.

REGLAS:
- Máximo 10 líneas para explicar durante el entrenamiento.
- Escribí como un coach real: directo, amable y práctico.
- Cuando expliques ejercicios, usá esta estructura con emojis:
  1. Ejecución
  2. Músculos principales
  3. Consejos / errores comunes
- Usá oraciones cortas.
- No uses tecnicismos innecesarios.
- No des diagnósticos médicos.
- Formato en Markdown simple con viñetas y emojis de gimnasio.
FORMATO ESTRICTO:
- NO usar negritas (** **), ni asteriscos, ni Markdown.
- NO usar títulos en mayúsculas.
- SOLO usar viñetas con emojis deportivos (🔹 💪 🏋️‍♂️ 🔸).
- Frases cortas y fáciles de leer.
- No escribir párrafos largos.
- No diagnósticos médicos ni lenguaje técnico innecesario.
Pregunta del usuario:
{user_message}
"""

    try:
        # Ejecutamos la IA en un thread aparte (evita bloquear el bot)
        response = await asyncio.to_thread(
            model.generate_content,
            prompt
        )

        # Intentamos extraer el texto de forma segura
        gemini_text = ""

        try:
            content = response.candidates[0].content
            for part in content:
                if hasattr(part, "text"):
                    gemini_text += part.text
            gemini_text = gemini_text.strip()
        except Exception:
            # Backup por si cambia el formato en el futuro
            gemini_text = getattr(response, "text", "⚠ No pude interpretar la respuesta.")

        await send_long_message(update, gemini_text)

    except Exception as e:
        await update.message.reply_text(f"⚠️ Error en el servidor: {str(e)}")

# ------------------------------------------------------------
# FUNCIÓN PRINCIPAL PARA INICIAR EL BOT
# ------------------------------------------------------------
def main():
    # Creamos la aplicación del bot de Telegram
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Registramos comandos y eventos
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    return app


# Inicializamos el bot (sin ejecutarlo automáticamente)
bot_app = main()
