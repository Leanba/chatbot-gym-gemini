# bot_pro.py
# Versión PRO - Bot Telegram "Asistente de Gimnasio IA"
# Autor: [Tu Nombre] - Comentarios y estilo como trabajo de alumno universitario
# Descripción: Bot que usa Google Gemini para responder preguntas de gimnasio,
# realiza análisis de sentimiento, resúmenes, conserva historial y sanitiza
# formatos (convierte **negritas** a viñetas emoji para Telegram).

import os
import asyncio
import json
import re
from typing import Dict, List
from dataclasses import dataclass, asdict
from pathlib import Path

import google.generativeai as genai
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    MessageHandler, filters
)
from dotenv import load_dotenv

# ---------------------------
# CARGA DE CONFIGURACIÓN
# ---------------------------
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
HISTORY_FILE = Path("histories.json")  # archivo opcional para persistir historial

if not TELEGRAM_TOKEN:
    raise RuntimeError("Falta TELEGRAM_TOKEN en variables de entorno.")
if not GEMINI_API_KEY:
    raise RuntimeError("Falta GEMINI_API_KEY en variables de entorno.")

# ---------------------------
# CONFIGURAR GEMINI (IA)
# ---------------------------
# Nota: usamos el modelo indicado en la consigna solicitada
genai.configure(api_key=GEMINI_API_KEY)

# Definimos el objeto 'model' con parámetros de generación
# temperature baja para respuestas más "rápidas/estables"
model = genai.GenerativeModel(
    model_name="models/gemini-2.0-flash-lite-preview-02-05",
    generation_config={
        "temperature": 0.2,
        "top_p": 0.9,
        "top_k": 40,
        "max_output_tokens": 400
    }
)

# ---------------------------
# ESTRUCTURAS PARA HISTORIAL
# ---------------------------
@dataclass
class ConversationContext:
    user_id: int
    username: str
    messages: List[Dict]  # lista de {role: "user"/"assistant"/"system", text: ...}

# Cargamos historiales previos (si existe)
def load_histories() -> Dict[str, ConversationContext]:
    if HISTORY_FILE.exists():
        try:
            raw = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
            out = {}
            for k, v in raw.items():
                out[k] = ConversationContext(
                    user_id=v["user_id"],
                    username=v.get("username", ""),
                    messages=v.get("messages", []))
            return out
        except Exception:
            return {}
    return {}

def save_histories(histories: Dict[str, ConversationContext]):
    try:
        dump = {k: asdict(v) for k, v in histories.items()}
        HISTORY_FILE.write_text(json.dumps(dump, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        # No bloquear al bot por errores de persistencia
        pass

# Historial en memoria (clave = str(user_id))
histories: Dict[str, ConversationContext] = load_histories()

# ---------------------------
# UTILIDADES
# ---------------------------
def sanitize_and_convert_format(text: str) -> str:
    """
    Convierte patrones tipo **texto** o *texto* o listas con '-' o '*' en
    viñetas con emojis deportivos. También elimina múltiples saltos de línea.
    - ' ** biceps ** '  -> '🔹 biceps'
    - '- ejercicio' / '* ejercicio' -> '🔸 ejercicio'
    Mantiene frases cortas.
    """
    # 1) Reemplazar patrones de negrita tipo **...**
    def bold_to_bullet(match):
        inner = match.group(1).strip()
        return f"🔹 {inner}"

    text = re.sub(r"\*\*\s*(.+?)\s*\*\*", bold_to_bullet, text, flags=re.DOTALL)
    text = re.sub(r"\*\s*(.+?)\s*\*", bold_to_bullet, text, flags=re.DOTALL)

    # 2) Reemplazar líneas que comienzan con - o * por viñetas
    lines = text.splitlines()
    new_lines = []
    for line in lines:
        stripped = line.lstrip()
        if re.match(r"^[-*]\s+", stripped):
            new_lines.append("🔸 " + re.sub(r"^[-*]\s+", "", stripped))
        else:
            new_lines.append(line)
    text = "\n".join(new_lines)

    # 3) Convertir encabezados con '#' a viñetas (por si el modelo usa markdown)
    text = re.sub(r"^#{1,6}\s*(.+)$", r"🔹 \1", text, flags=re.MULTILINE)

    # 4) Limpiar dobles espacios y limitar saltos de línea excesivos
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()
    return text

async def send_long_message(update: Update, text: str):
    """Envía texto fragmentado a Telegram (límite 4096 caracteres)"""
    MAX_LEN = 4096
    for i in range(0, len(text), MAX_LEN):
        await update.message.reply_text(text[i:i + MAX_LEN])

def ensure_user_history(update: Update) -> ConversationContext:
    uid = str(update.effective_user.id)
    if uid not in histories:
        histories[uid] = ConversationContext(
            user_id=update.effective_user.id,
            username=update.effective_user.username or "",
            messages=[]
        )
    return histories[uid]

# ---------------------------
# PROMPTS BASE
# ---------------------------
SYSTEM_PROMPT = (
    "Sos un Personal Trainer profesional. Respondé siempre de forma clara, resumida y fácil de entender.\n"
    "Reglas estrictas:\n"
    "- Máximo 10 líneas cuando expliques ejercicios.\n"
    "- Usá oraciones cortas. No tecnicismos innecesarios.\n"
    "- Nunca usar negritas (** **), ni Markdown. Solo viñetas con emojis deportivos moderados (🔹 🔸 💪).\n"
    "- No dar diagnósticos médicos ni planes clínicos.\n"
    "- Si el usuario menciona 'estoy en el gym' o 'antes de entrenar', priorizar respuestas cortas y directas.\n"
)

# ---------------------------
# HANDLERS / COMANDOS
# ---------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/start - Saludo inicial"""
    if not update.message:
        return
    ensure_user_history(update)
    await update.message.reply_text(
        "🏋️‍♂️ ¡Hola! Soy tu asistente de gimnasio con IA (Versión PRO).\n"
        "Comandos útiles:\n"
        "/help - ayuda breve\n"
        "/history - ver últimas interacciones (local)\n"
        "/summary <texto> - resumen rápido de un texto\n"
        "/sentiment <texto> - análisis de sentimiento de un texto\n\n"
        "Escribime tu consulta cuando quieras 💪"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/help - Muestra ayuda"""
    if not update.message:
        return
    text = (
        "Guía rápida:\n"
        "• Escribí tu pregunta directamente (ej: 'Cómo entreno dorsal en casa?').\n"
        "• /summary <texto> -> Pide un resumen del texto dado.\n"
        "• /sentiment <texto> -> Devuelve sentimiento: positivo/neutral/negativo.\n"
        "• /history -> Muestra tu historial local.\n"
    )
    await update.message.reply_text(text)

async def history_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/history - muestra historial en memoria (resumido)"""
    if not update.message:
        return
    ctx = ensure_user_history(update)
    lines = []
    for m in ctx.messages[-10:]:
        role = m.get("role", "user")
        t = m.get("text", "")
        prefix = "U: " if role == "user" else "A: "
        # truncar por seguridad
        t = (t[:120] + "...") if len(t) > 120 else t
        lines.append(prefix + t.replace("\n", " "))
    if not lines:
        await update.message.reply_text("No hay historial aún.")
    else:
        await update.message.reply_text("Últimas interacciones:\n" + "\n".join(lines))

# ---------------------------
# FUNCIONES DE IA (SUMMARY / SENTIMENT)
# ---------------------------
async def ai_summary(text: str) -> str:
    """Pide al modelo un resumen corto (máx 5 líneas)"""
    prompt = (
        SYSTEM_PROMPT +
        "\nTAREA: Resumí brevemente el siguiente texto en máximo 5 líneas.\n\nTexto:\n" + text + "\n\nResumen:"
    )
    # Ejecutamos en thread para no bloquear el event loop
    response = await asyncio.to_thread(model.generate_content, prompt)
    # Extraer texto
    gemini_text = ""
    try:
        content = response.candidates[0].content
        for part in content:
            if hasattr(part, "text"):
                gemini_text += part.text
        gemini_text = gemini_text.strip()
    except Exception:
        gemini_text = getattr(response, "text", "⚠ No pude interpretar la respuesta del modelo.")
    return sanitize_and_convert_format(gemini_text)

async def ai_sentiment(text: str) -> str:
    """
    Pide al modelo clasificar sentimiento.
    Respuesta esperada en formato compacto: 'POSITIVE'/'NEUTRAL'/'NEGATIVE' + breve explicación.
    """
    prompt = (
        SYSTEM_PROMPT +
        "\nTAREA: Analizá el sentimiento del siguiente texto. Responda en una sola línea con este formato:\n"
        "SENTIMENT: <positivo|neutral|negativo>\nEXPLICACIÓN: <frase corta>\n\n"
        "Texto:\n" + text + "\n\nResultado:"
    )
    response = await asyncio.to_thread(model.generate_content, prompt)
    gemini_text = ""
    try:
        content = response.candidates[0].content
        for part in content:
            if hasattr(part, "text"):
                gemini_text += part.text
        gemini_text = gemini_text.strip()
    except Exception:
        gemini_text = getattr(response, "text", "⚠ No pude interpretar la respuesta del modelo.")
    gemini_text = gemini_text.replace("\n", " ").strip()
    # Intentamos extraer la etiqueta
    m = re.search(r"(positivo|negativo|neutral|positive|negative|neutral)", gemini_text, flags=re.I)
    label = m.group(1).lower() if m else "neutral"
    explanation = gemini_text
    return f"🔎 Sentimiento: {label}\n💬 {explanation}"

# ---------------------------
# MANEJADOR PRINCIPAL DE MENSAJES
# ---------------------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    1) Guarda el input del usuario en el historial.
    2) Procesa comandos /summary y /sentiment si vienen como mensaje normal.
    3) Envía prompt a Gemini y devuelve respuesta sanitizada (sin **).
    """
    if not update.message or not update.message.text:
        return

    raw_text = update.message.text.strip()
    uid = str(update.effective_user.id)
    ctx = ensure_user_history(update)

    # Guardar el mensaje del usuario en el historial
    ctx.messages.append({"role": "user", "text": raw_text})
    # Persistir (opcional)
    save_histories(histories)

    # Atender shortcuts si usuario escribió: summary <texto> o sentiment <texto>
    lowered = raw_text.lower()
    if lowered.startswith("/summary") or lowered.startswith("summary "):
        # Extraer el texto
        content = raw_text.partition(" ")[2].strip()
        if not content:
            await update.message.reply_text("Usá: /summary <texto> — incluilo para que pueda resumirlo.")
            return
        await update.message.reply_text("⏳ Generando resumen...")
        summary = await ai_summary(content)
        # Guardar assistant reply
        ctx.messages.append({"role": "assistant", "text": summary})
        save_histories(histories)
        await send_long_message(update, summary)
        return

    if lowered.startswith("/sentiment") or lowered.startswith("sentiment "):
        content = raw_text.partition(" ")[2].strip()
        if not content:
            await update.message.reply_text("Usá: /sentiment <texto> — incluilo para que pueda analizarlo.")
            return
        await update.message.reply_text("⏳ Analizando sentimiento...")
        sentiment = await ai_sentiment(content)
        ctx.messages.append({"role": "assistant", "text": sentiment})
        save_histories(histories)
        await send_long_message(update, sentiment)
        return

    # Si el mensaje es un comando conocido ya fue tratado por handlers, seguimos a IA general.
    # Construimos prompt final combinando SYSTEM_PROMPT + historial breve + mensaje actual
    # Para mantener tamaño razonable, solo incluimos últimos 6 intercambios.
    recent_msgs = ctx.messages[-12:]  # alternancia user/assistant -> aproximadamente 6 turnos
    history_for_prompt = ""
    for m in recent_msgs:
        role = m.get("role", "user")
        tag = "Usuario" if role == "user" else "Asistente"
        history_for_prompt += f"{tag}: {m.get('text','')}\n"

    prompt = SYSTEM_PROMPT + "\nHistorial_reciente:\n" + history_for_prompt + "\nPregunta del usuario:\n" + raw_text + "\nRespuesta del asistente:"

    try:
        # Ejecutamos en thread para no bloquear el bot
        response = await asyncio.to_thread(model.generate_content, prompt)

        # Extraer texto del response
        gemini_text = ""
        try:
            content = response.candidates[0].content
            for part in content:
                if hasattr(part, "text"):
                    gemini_text += part.text
            gemini_text = gemini_text.strip()
        except Exception:
            gemini_text = getattr(response, "text", "⚠ No pude interpretar la respuesta del modelo.")

        # Sanitizar (remover **, convertir a bullets con emojis)
        gemini_text = sanitize_and_convert_format(gemini_text)

        # Guardar respuesta en historial
        ctx.messages.append({"role": "assistant", "text": gemini_text})
        save_histories(histories)

        # Enviar al usuario (fragmentando si es necesario)
        await send_long_message(update, gemini_text)

    except Exception as e:
        # Manejo de errores: enviamos mensaje amistoso y no volcamos trace completo
        await update.message.reply_text(f"⚠️ Error en el servidor: {str(e)}")

# ---------------------------
# INICIALIZACIÓN DEL BOT
# ---------------------------
def main():
    # Construyo la aplicación y registro handlers
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # comandos
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("history", history_cmd))

    # summary y sentiment pueden venir como comandos directos
    app.add_handler(CommandHandler("summary", lambda u, c: None))  # placeholder para que no caiga en default
    app.add_handler(CommandHandler("sentiment", lambda u, c: None))

    # Mensajes de texto normales (incluye invocaciones "summary ..." desde texto libre)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    return app

# Instanciamos la app pero no ejecutamos el loop aquí (permite importar el archivo en tests)
bot_app = main()

# Si se ejecuta directamente, arrancamos el bot (modo simple)
if __name__ == "__main__":
    # Arranca el bot en modo sin bloqueo (polling)
    print("Iniciando Bot PRO...")
    bot_app.run_polling()
