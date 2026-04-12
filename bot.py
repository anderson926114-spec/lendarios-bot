from flask import Flask, request
import requests

app = Flask(__name__)

# CONFIGURAÇÕES
VERIFY_TOKEN = "lendarios_token"
TOKEN = "EAAsCShhhFUoBRO66HuKZCcs6gfPlPDDtSD3vZBuHRScteFn3RnuMzzqNh2P2Ow4bIU5QSvYGNNeiZCapCxQZB56sZBbxEPwaUzj89QVE16yWhbjBQIw0fRAI7iTjwoLZAklZBii6n3fmPYzCQ5X2wEeZBDDoYNmamJyVxsLrLjHZCBJoQKW6ruSn3W76gFiuTosH5gc9KTl5lSZCfrIn6POecy2FmeGry9Enn4JHBpdPNq9tCLNI689g7eESj441RZC6cU9ZBVQPieTkrrBattkUVdyWFPyggAZDZD"
PHONE_NUMBER_ID = "1094450353745202"

# Dicionário de estados (quem está em qual etapa)
usuarios = {}

def enviar(numero, texto):
    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
    data = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "text",
        "text": {"body": texto}
    }
    r = requests.post(url, headers=headers, json=data)

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if token == VERIFY_TOKEN:
            return challenge
        return "Erro", 403

    if request.method == "POST":
        data = request.get_json()
        try:
            if "messages" in data["entry"][0]["changes"][0]["value"]:
                msg_data = data["entry"][0]["changes"][0]["value"]["messages"][0]
                numero = msg_data["from"]
                texto = msg_data["text"]["body"].strip()
                
                # Normalização de número (SC)
                if numero.startswith("5548") and len(numero) == 12:
                    numero = "55489" + numero[4:]

                # --- FLUXO DE CADASTRO ATIVO ---
                if numero in usuarios:
                    etapa = usuarios[numero]["etapa"]

                    if etapa == "nome":
                        usuarios[numero]["nome"] = texto
                        usuarios[numero]["etapa"] = "cidade"
                        enviar(numero, "📍 Qual sua cidade?")
                        return "ok"

                    elif etapa == "cidade":
                        usuarios[numero]["cidade"] = texto
                        usuarios[numero]["etapa"] = "tipo"
                        enviar(numero, "⚽ Tipo:\n1 Goleiro\n2 Linha\n3 Árbitro")
                        return "ok"

                    elif etapa == "tipo":
                        tipos = {"1": "Goleiro", "2": "Linha", "3": "Árbitro"}
                        tipo_escolhido = tipos.get(texto, "Não definido")
                        dados = usuarios[numero]
                        enviar(numero, f"✅ Cadastro concluído!\n\nNome: {dados['nome']}\nCidade: {dados['cidade']}\nTipo: {tipo_escolhido}")
                        del usuarios[numero]
                        return "ok"

                # --- MENU PRINCIPAL (FOTO 1) ---
                if texto == "1":
                    usuarios[numero] = {"etapa": "nome"}
                    # Texto idêntico à Foto 2
                    enviar(numero, "⚽ *Cadastro de Atleta*\n\nDigite seu nome para começar:")
                
                elif texto in ["2", "3", "4", "0"]:
                    enviar(numero, "Opção em construção...")
                
                else:
                    # Texto idêntico à Foto 1
                    menu = (
                        "🏆 *LENDÁRIOS*\n\n"
                        "Escolha uma opção:\n\n"
                        "1️⃣ Sou atleta\n"
                        "2️⃣ Solicitar jogador\n"
                        "3️⃣ Ver jogos\n"
                        "4️⃣ Falar com administrador\n"
                        "0️⃣ Sair"
                    )
                    enviar(numero, menu)

        except Exception as e:
            print(f"Erro: {e}")
        return "ok", 200

@app.route("/")
def home():
    return "BOT ONLINE"

if __name__ == "__main__":
    app.run(port=5000)
