from flask import Flask, request
from bot import bot_app

app = Flask(__name__)

@app.route("/", methods=["POST"])
def webhook():
    update = request.get_json(force=True)
    bot_app.update_queue.put(update)
    return "OK", 200

@app.route("/", methods=["GET"])
def home():
    return "Bot funcionando", 200

if __name__ == "__main__":
    app.run(port=3000)
