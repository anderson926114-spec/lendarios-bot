from flask import Flask, request
import requests

app = Flask(__name__)

# CONFIGURAÇÕES
VERIFY_TOKEN = "lendarios_token"
TOKEN = "EAAsCShhhFUoBRO66HuKZCcs6gfPlPDDtSD3vZBuHRScteFn3RnuMzzqNh2P2Ow4bIU5QSvYGNNeiZCapCxQZB56sZBbxEPwaUzj89QVE16yWhbjBQIw0fRAI7iTjwoLZAklZBii6n3fmPYzCQ5X2wEeZBDDoYNmamJyVxsLrLjHZCBJoQKW6ruSn3W76gFiuTosH5gc9KTl5lSZCfrIn6POecy2FmeGry9Enn4JHBpdPNq9tCLNI689g7eESj441RZC6cU9ZBVQPieTkrrBattkUVdyWFPyggAZDZD"
PHONE_NUMBER_ID = "1094450353745202"

# Dicionário para controlar quem está em processo de cadastro
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
    if request.method == "GET":
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if token == VERIFY_TOKEN:
            return challenge
        return "Token inválido", 403

    if request.method == "POST":
        data = request.get_json()
        try:
            # Verifica se existe mensagem no pacote recebido
            if "messages" in data["entry"][0]["changes"][0]["value"]:
                numero = data["entry"][0]["changes"][0]["value"]["messages"][0]["from"]
                mensagem = data["entry"][0]["changes"][0]["value"]["messages"][0]["text"]["body"]

                if numero.startswith("5548") and len(numero) == 12:
                    numero = "55489" + numero[4:]

                mensagem = mensagem.lower().strip()
                print(numero, mensagem)

                # 🔥 1º PRIORIDADE: VERIFICA SE O USUÁRIO JÁ ESTÁ NO MEIO DO CADASTRO
                if numero in usuarios:
                    etapa = usuarios[numero]["etapa"]

                    if etapa == "nome":
                        usuarios[numero]["nome"] = mensagem
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
                        usuarios[numero]["tipo"] = tipos.get(mensagem, "Não definido")
                        dados = usuarios[numero]
                        
                        enviar(numero, f"✅ Cadastro concluído!\n\nNome: {dados['nome']}\nCidade: {dados['cidade']}\nTipo: {dados['tipo']}")
                        
                        del usuarios[numero] # Finaliza e remove do dicionário
                        return "ok"

                # 🔥 2º PRIORIDADE: MENU INICIAL (CASO NÃO ESTEJA EM CADASTRO)
                if mensagem == "1":
                    usuarios[numero] = {"etapa": "nome"} # Aqui inicia o rastreio do cadastro
                    enviar(numero, "📝 Iniciando cadastro! Por favor, digite seu nome completo:")
                
                elif mensagem in ["2", "3", "4", "0"]:
                    enviar(numero, "Esta opção está em construção... 🛠️")
                
                else:
                    # Menu Principal que aparece quando digita "ola" ou qualquer coisa fora do fluxo
                    enviar(numero, "🤖 *BOT LENDÁRIOS*\n\n1 - Cadastro\n2 - Opção 2\n3 - Opção 3\n4 - Opção 4\n0 - Sair")

        except Exception as e:
            print(f"Erro: {e}")

        return "ok", 200


# ROTA PRINCIPAL
@app.route("/")
def home():
    return "BOT LENDÁRIOS ONLINE"

if __name__ == "__main__":
    app.run(port=5000)
