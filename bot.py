from flask import Flask, request

app = Flask(__name__)

VERIFY_TOKEN = "lendarios_token"

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    
    if request.method == "GET":
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        if token == VERIFY_TOKEN:
            return challenge
        return "Token inválido"

    if request.method == "POST":
        data = request.get_json()
        print(data)
        return "ok"

@app.route("/")
def home():
    return "Bot Lendários Online"

if __name__ == "__main__":
    app.run()
