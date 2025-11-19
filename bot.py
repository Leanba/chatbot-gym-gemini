import os
import asyncio
import google.generativeai as genai
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    MessageHandler, filters
)
from dotenv import load_dotenv

# ------------------------------------------------------------
# Carga de variables de entorno
# ------------------------------------------------------------
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ------------------------------------------------------------
# CONFIGURACIÓN DEL MODELO DE IA con Google Gemini
# ------------------------------------------------------------
genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel(
    model_name="models/gemini-2.0-flash-lite-preview-02-05",
    generation_config={
        "temperature": 0.2,  # Respuestas rápidas y estables
        "top_p": 0.9,
        "top_k": 40,
        "max_output_tokens": 400
    }
)

# Diccionario para guardar historial por usuario
USER_HISTORY = {}

# Función auxiliar: dividir textos largos para Telegram

async def send_long_message(update, text):
    MAX_LEN = 4096
    for i in range(0, len(text), MAX_LEN):
        await update.message.reply_text(text[i:i + MAX_LEN])


# FUNCIÓN: Análisis de sentimiento. Uso "tool/function calling" para
# alguna tarea específica. Esta función actúa como herramienta.

def sentiment_tool(text: str):
    text = text.lower()
    if any(w in text for w in ["enojado", "mal", "triste", "estresado"]):
        return "🔸 Parece que estás con una emoción negativa."
    if any(w in text for w in ["bie", "feliz", "motivado", "genial"]):
        return "🔹 Te noto con energía positiva."
    return "🔹 Sentimiento neutro detectado."


# COMANDO /start

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    USER_HISTORY[update.effective_user.id] = []

    await update.message.reply_text(
        "🏋️‍♂️ ¡Bienvenido! Soy tu GYMBRO de gimnasio con IA.\n"
        "Puedo ayudarte con:\n"
        "• Ejercicios y técnicas correctas\n"
        "• Músculos involucrados en cada movimiento\n"
        "• Rutinas recomendadas según objetivo\n"
        "• Consejos si tenés molestias o dudas\n\n"
        "Envíame tu consulta cuando quieras 💪"
    )

# COMANDO /help

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📌 *Comandos disponibles:*\n"
        "/start – Iniciar conversación\n"
        "/help – Mostrar ayuda\n"
        "/reset – Limpiar historial\n"
        "/stats – Ver estadísticas\n\n"
        "Enviá cualquier duda sobre ejercicios, rutinas o entrenamiento."
    )

# COMANDO /reset → limpia historial

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    USER_HISTORY[update.effective_user.id] = []
    await update.message.reply_text("🧹 Historial borrado correctamente.")



# COMANDO /stats → estadísticas del usuario

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    count = len(USER_HISTORY.get(user_id, []))

    await update.message.reply_text(
        f"📊 *Estadísticas personales*\n"
        f"Mensajes enviados: {count}\n"
        f"Modelo IA: Gemini Flash Lite"
    )

# MANEJO DE MENSAJES DEL USUARIO

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text

    # Guardamos mensaje en historial
    USER_HISTORY.setdefault(user_id, []).append(user_message)

    # ----- Herramienta: Análisis de sentimientos -----
    sentimiento = sentiment_tool(user_message)

    # Aca se arma el prompt para la IA
    prompt = f"""
Sos un Personal Trainer profesional.
Tu objetivo es responder claro, corto y como un coach real.
Antes de respoder, hazle preguntas al usuario para optimizar tu respuesta.

Reglas:
- Máximo 10 líneas (si no se pide una explicación más extensa).
- Estilo simple, amable y directo.
- Cuando expliques ejercicios, usá estructura con emojis:
  1. Ejecución
  2. Músculos
  3. Consejos
- Sin negritas ni Markdown.
- Usá viñetas con emojis de forma moderada.
- Nada de tecnicismos innecesarios.
- Nada de diagnósticos médicos.

Sentimiento detectado del usuario:
{sentimiento}

Mensaje del usuario:
{user_message}
"""

    try:
        response = await asyncio.to_thread(model.generate_content, prompt)

        text = ""

        try:
            content = response.candidates[0].content
            for part in content:
                if hasattr(part, "text"):
                    text += part.text
            text = text.strip()
        except:
            text = getattr(response, "text", "No pude interpretar la respuesta.")

        await send_long_message(update, text)

    except Exception as e:
        await update.message.reply_text(f"⚠ Error en servidor: {str(e)}")



# FUNCIÓN PRINCIPAL

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CommandHandler("stats", stats))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    return app


bot_app = main()
