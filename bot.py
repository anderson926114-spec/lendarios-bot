from flask import Flask, request
import requests

app = Flask(__name__)

# CONFIGURAÇÕES
VERIFY_TOKEN = "lendarios_token"
TOKEN = "EAAsCShhhFUoBRO66HuKZCcs6gfPlPDDtSD3vZBuHRScteFn3RnuMzzqNh2P2Ow4bIU5QSvYGNNeiZCapCxQZB56sZBbxEPwaUzj89QVE16yWhbjBQIw0fRAI7iTjwoLZAklZBii6n3fmPYzCQ5X2wEeZBDDoYNmamJyVxsLrLjHZCBJoQKW6ruSn3W76gFiuTosH5gc9KTl5lSZCfrIn6POecy2FmeGry9Enn4JHBpdPNq9tCLNI689g7eESj441RZC6cU9ZBVQPieTkrrBattkUVdyWFPyggAZDZD"
PHONE_NUMBER_ID = "1094450353745202"

# Variável global para armazenar os cadastros em andamento
usuarios = {}

# FUNÇÃO PARA ENVIAR MENSAGEM
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


# WEBHOOK
@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    # Validação do Webhook (GET)
    if request.method == "GET":
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if token == VERIFY_TOKEN:
            return challenge
        return "Token de verificação inválido", 403

    # Processamento de Mensagens (POST)
    if request.method == "POST":
        data = request.get_json()
        try:
            # Verifica se há uma mensagem válida no JSON
            if "messages" in data["entry"][0]["changes"][0]["value"]:
                numero = data["entry"][0]["changes"][0]["value"]["messages"][0]["from"]
                mensagem = data["entry"][0]["changes"][0]["value"]["messages"][0]["text"]["body"]

                # Ajuste de DDD para Santa Catarina
                if numero.startswith("5548") and len(numero) == 12:
                    numero = "55489" + numero[4:]

                mensagem_limpa = mensagem.lower().strip()
                print(f"Recebido: {numero} -> {mensagem_limpa}")

                # --- 1º PRIORIDADE: SE O USUÁRIO JÁ ESTÁ NO MEIO DO CADASTRO ---
                if numero in usuarios:
                    etapa = usuarios[numero]["etapa"]

                    if etapa == "nome":
                        usuarios[numero]["nome"] = mensagem # Salva o nome como o usuário digitou
                        usuarios[numero]["etapa"] = "cidade"
                        enviar(numero, "📍 Qual sua cidade?")
                        return "ok"

                    elif etapa == "cidade":
                        usuarios[numero]["cidade"] = mensagem
                        usuarios[numero]["etapa"] = "tipo"
                        enviar(numero, "⚽ Tipo:\n1 Goleiro\n2 Linha\n3 Árbitro")
                        return "ok"

                    elif etapa == "tipo":
                        tipos = {"1": "Goleiro", "2": "Linha", "3": "Árbitro"}
                        if mensagem_limpa in tipos:
                            usuarios[numero]["tipo"] = tipos[mensagem_limpa]
                            dados = usuarios[numero]
                            enviar(numero, f"✅ Cadastro concluído!\n\nNome: {dados['nome']}\nCidade: {dados['cidade']}\nTipo: {dados['tipo']}")
                            del usuarios[numero] # Remove da memória após finalizar
                        else:
                            enviar(numero, "Por favor, escolha uma opção válida:\n1 Goleiro\n2 Linha\n3 Árbitro")
                        return "ok"

                # --- 2º PRIORIDADE: MENU INICIAL (Se não estiver cadastrando) ---
                if mensagem_limpa == "cadastro" or mensagem_limpa == "1":
                    usuarios[numero] = {"etapa": "nome"}
                    enviar(numero, "📝 Vamos começar! Qual o seu nome completo?")
                else:
                    # Se ele digitar qualquer outra coisa fora do cadastro
                    enviar(numero, "🤖 *BOT LENDÁRIOS*\n\nDigite *1* ou *Cadastro* para iniciar seu registro.")

        except Exception as e:
            print(f"Erro no processamento: {e}")

        return "ok", 200


# ROTA PRINCIPAL
@app.route("/")
def home():
    return "BOT LENDÁRIOS ONLINE"

if __name__ == "__main__":
    app.run(port=5000)
    
