from flask import Flask, request
import requests

app = Flask(__name__)

# CONFIGURAÇÕES
VERIFY_TOKEN = "lendarios_token"
TOKEN = "EAAsCShhhFUoBRA8clslnR8NcZApGDKN5o4VBVZBeCQYdDcAG9ruxgQGspQu9YolH2IC0Ng7cLbhsE4mDr9aBwZCLzcQwGmX24FE31xWaZB9nRCZBlqf3RSHZCkJI1BWm3MwkfSkI3tZAjMlzbS42q8QpKy5J2ZBj2Sp7T5N6FFTkmWIrzTnD3VlKe6NuPnYXgN2IkmZBIIZBAafzQojOTEk3a8ZCQ8VO1Lz5qztg3kWjCWe6R8ZBv8w6Ya6LynNoLT01Uida74gBNtDt37awuXWeNhPGuhSl"
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
    print(f"Status Envio: {r.status_code}") # Para debug

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
                # Usei 'texto' como variável padrão
                texto = msg_data["text"]["body"].strip()
                
                if numero.startswith("5548") and len(numero) == 12:
                    numero = "55489" + numero[4:]

                # --- 1º PRIORIDADE: FLUXO DE CADASTRO ATIVO ---
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

                # --- 2º PRIORIDADE: MENU PRINCIPAL ---
                # Corrigido: Agora todas as verificações usam a variável 'texto'
                if texto == "1":
                    usuarios[numero] = {"etapa": "nome"}
                    enviar(numero, "⚽ *Cadastro de Atleta*\n\nDigite seu nome para começar:")

                elif texto == "2":
                    enviar(numero, "📅 Solicitação de jogador em breve!")

                elif texto == "3":
                    enviar(numero, "📋 Lista de jogos em breve!")

                elif texto == "4":
                    enviar(numero, "👑 Fale com o administrador.")

                elif texto == "0":
                    enviar(numero, "👋 Você saiu do menu.")
                
                else:
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
            print(f"Erro no processamento: {e}")
            
        return "ok", 200

@app.route("/")
def home():
    return "BOT ONLINE"

if __name__ == "__main__":
    app.run(port=5000)
