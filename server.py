from flask import Flask, request
from bot import bot_app

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "Bot funcionando", 200

@app.route("/", methods=["POST"])
def webhook():
    update = request.get_json(force=True)
    bot_app.update_queue.put_nowait(update)
    return "OK", 200

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port)
