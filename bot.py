from flask import Flask, request
import requests

app = Flask(__name__)

# CONFIGURAÇÕES
VERIFY_TOKEN = "lendarios_token"
TOKEN = "EAAsCShhhFUoBRO66HuKZCcs6gfPlPDDtSD3vZBuHRScteFn3RnuMzzqNh2P2Ow4bIU5QSvYGNNeiZCapCxQZB56sZBbxEPwaUzj89QVE16yWhbjBQIw0fRAI7iTjwoLZAklZBii6n3fmPYzCQ5X2wEeZBDDoYNmamJyVxsLrLjHZCBJoQKW6ruSn3W76gFiuTosH5gc9KTl5lSZCfrIn6POecy2FmeGry9Enn4JHBpdPNq9tCLNI689g7eESj441RZC6cU9ZBVQPieTkrrBattkUVdyWFPyggAZDZD"
PHONE_NUMBER_ID = "1094450353745202"

# Dicionário para controlar o fluxo de cadastro
usuarios = {}

def enviar(numero, texto):
    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "text",
        "text": {"body": texto}
    }
    r = requests.post(url, headers=headers, json=data)
    print("ENVIO:", r.status_code, r.text)

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if token == VERIFY_TOKEN:
            return challenge
        return "Token inválido", 403

    if request.method == "POST":
        data = request.get_json()
        try:
            # Extração da mensagem
            value = data["entry"][0]["changes"][0]["value"]
            if "messages" in value:
                numero = value["messages"][0]["from"]
                mensagem = value["messages"][0]["text"]["body"].lower().strip()

                # Ajuste para números de SC
                if numero.startswith("5548") and len(numero) == 12:
                    numero = "55489" + numero[4:]

                print(f"Número: {numero} | Mensagem: {mensagem}")

                # --- FLUXO DE CADASTRO ATIVO ---
                if numero in usuarios:
                    etapa = usuarios[numero]["etapa"]

                    if etapa == "nome":
                        usuarios[numero]["nome"] = mensagem.title()
                        usuarios[numero]["etapa"] = "cidade"
                        enviar(numero, "📍 Qual sua cidade?")
                        return "ok"

                    elif etapa == "cidade":
                        usuarios[numero]["cidade"] = mensagem.title()
                        usuarios[numero]["etapa"] = "tipo"
                        enviar(numero, "⚽ Tipo:\n1 Goleiro\n2 Linha\n3 Árbitro")
                        return "ok"

                    elif etapa == "tipo":
                        tipos = {"1": "Goleiro", "2": "Linha", "3": "Árbitro"}
                        if mensagem in tipos:
                            usuarios[numero]["tipo"] = tipos[mensagem]
                            dados = usuarios[numero]
                            enviar(numero, f"✅ Cadastro concluído!\n\nNome: {dados['nome']}\nCidade: {dados['cidade']}\nTipo: {dados['tipo']}")
                            del usuarios[numero] # Finaliza cadastro
                        else:
                            enviar(numero, "Opção inválida. Escolha 1, 2 ou 3.")
                        return "ok"

                # --- MENU INICIAL (Se não estiver no cadastro) ---
                if mensagem == "1": # Exemplo: Opção 1 inicia cadastro
                    usuarios[numero] = {"etapa": "nome"}
                    enviar(numero, "Iniciando cadastro... Qual o seu nome completo?")
                else:
                    # Este é o menu que aparece sempre que não há um cadastro em curso
                    enviar(numero, "🤖 *BOT LENDÁRIOS*\n\n1 - Iniciar Cadastro\n2 - Ver Horários\n3 - Outras Informações")

        except Exception as e:
            print(f"Erro no processamento: {e}")

        return "EVENT_RECEIVED", 200

@app.route("/")
def home():
    return "BOT LENDÁRIOS ONLINE"

if __name__ == "__main__":
    app.run(port=5000)
    
