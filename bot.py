from flask import Flask, request
import requests
import sqlite3

app = Flask(__name__)

TOKEN = "EAAsCShhhFUoBREkjSy3PLHRSctJlnOW1T98MMlhzBXtKzuVhYr3qB9A3MH4Ixf2o5F7SjcxgZBvwDY6rD8aLz0YRS8MVyZBHr7ZBHx8UZCPijtvKrjpXZA5iXu9qS1JZAWgjCUK6qNUPpGHZAtc1gh5M2WrQbkFAYCqB0JjpZCdHZAwZCwGXinJ3zKoROZAcT7HYcw1hcpAD6B67v2oh3V3Uhe5FtZCEyZA8mayO7eif3Kzry1HVV2abNOax0szkZC8TyXDMEmANfydIx0TxaMAxsl2yl7KiFNhwZDZD"
PHONE_NUMBER_ID = "1094450353745202"
VERIFY_TOKEN = "lendarios_token"

usuarios = {}
solicitacoes = {}

# =========================
# FUNÇÕES AUXILIARES
# =========================
def sn(texto):
    return texto.strip().lower()

def normalizar_numero(numero):
    numero = "".join(filter(str.isdigit, numero))
    if numero.startswith("55") and len(numero) == 12:
        numero = numero[:4] + "9" + numero[4:]
    return numero

# =========================
# BANCO
# =========================
def init_db():
    conn = sqlite3.connect("lendarios.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS atletas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero TEXT,
        cpf TEXT UNIQUE,
        nome TEXT,
        cidades TEXT,
        tipos TEXT,
        campo TEXT,
        pix TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS solicitacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero TEXT,
        cpf TEXT,
        endereco TEXT,
        cidade TEXT,
        nome_campo TEXT,
        tipo_campo TEXT,
        tipo TEXT,
        data TEXT,
        hora TEXT,
        quantidade INTEGER,
        valor REAL,
        status TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# =========================
# DADOS
# =========================
CIDADES = {
    "1": "São José",
    "2": "Palhoça",
    "3": "Biguaçu",
    "4": "Florianópolis / Continente",
    "5": "Florianópolis / Ilha"
}

TIPOS = {
    "1": "Goleiro",
    "2": "Jogador Linha",
    "3": "Árbitro"
}

TIPO_CAMPO = {
    "1": "Campo Oficial",
    "2": "Society",
    "3": "Futsal"
}

VALORES = {
    "Goleiro": 40,
    "Jogador Linha": 30,
    "Árbitro": 50
}

# =========================
# ENVIAR
# =========================
def enviar(numero, texto):
    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
    payload = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "text",
        "text": {"body": texto}
    }
    requests.post(url, headers=headers, json=payload)

# =========================
# MENU
# =========================
def menu(numero):
    enviar(numero, """🏆 LENDÁRIOS

1 🧤 Cadastro de atleta
2 ⚽ Solicitar atleta
3 ⭐ Avaliações
4 👑 Admin
5 🚪 Sair
""")

# =========================
# WEBHOOK
# =========================
@app.route("/webhook", methods=["GET","POST"])
def webhook():

    if request.method == "GET":
        if request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return request.args.get("hub.challenge")
        return "erro", 403

    data = request.get_json()

    try:
        value = data["entry"][0]["changes"][0]["value"]

        if "messages" not in value:
            return "ok"

        msg = value["messages"][0]
        if msg["type"] != "text":
            return "ok"

        numero = normalizar_numero(msg["from"])
        texto = msg["text"]["body"].strip()

        # =========================
        # MENU INICIAL
        # =========================
        if numero not in usuarios and numero not in solicitacoes:

            if texto == "1":
                usuarios[numero] = {"etapa": "cpf", "cidades": [], "tipos": []}
                enviar(numero, "🧾 Digite seu CPF:")
                return "ok"

            if texto == "2":
                solicitacoes[numero] = {"etapa": "cpf"}
                enviar(numero, "🧾 Digite seu CPF:")
                return "ok"

            if texto == "5":
                enviar(numero, "👋 Até mais!")
                return "ok"

            menu(numero)
            return "ok"

        # =========================
        # CADASTRO
        # =========================
        if numero in usuarios:
            u = usuarios[numero]

            if u["etapa"] == "cpf":
                conn = sqlite3.connect("lendarios.db")
                cursor = conn.cursor()
                cursor.execute("SELECT nome FROM atletas WHERE cpf=?", (texto,))
                if cursor.fetchone():
                    enviar(numero, "⚠ CPF já cadastrado!")
                    conn.close()
                    return "ok"
                conn.close()

                u["cpf"] = texto
                u["etapa"] = "nome"
                enviar(numero, "⚽ Nome:")
                return "ok"

            if u["etapa"] == "nome":
                u["nome"] = texto
                u["etapa"] = "cidade"

            if u["etapa"] == "cidade":
                op = {k:v for k,v in CIDADES.items() if v not in u["cidades"]}
                enviar(numero, "📍 Cidade:\n" + "\n".join([f"{k} {v}" for k,v in op.items()]))
                u["etapa"] = "cidade_escolha"
                return "ok"

            if u["etapa"] == "cidade_escolha":
                cidade = CIDADES.get(texto)
                if not cidade:
                    enviar(numero, "❌ Opção inválida")
                    return "ok"

                u["cidades"].append(cidade)
                enviar(numero, "Adicionar outra cidade? (S/N)")
                u["etapa"] = "cidade_mais"
                return "ok"

            if u["etapa"] == "cidade_mais":
                resposta = sn(texto)

                if resposta not in ["s","n"]:
                    enviar(numero, "❌ Digite S ou N")
                    return "ok"

                u["etapa"] = "cidade" if resposta == "s" else "tipo"
                return "ok"

            if u["etapa"] == "tipo":
                op = {k:v for k,v in TIPOS.items() if v not in u["tipos"]}
                enviar(numero, "⚽ Tipo:\n" + "\n".join([f"{k} {v}" for k,v in op.items()]))
                u["etapa"] = "tipo_escolha"
                return "ok"

            if u["etapa"] == "tipo_escolha":
                tipo = TIPOS.get(texto)
                if not tipo:
                    enviar(numero, "❌ Opção inválida")
                    return "ok"

                u["tipos"].append(tipo)
                enviar(numero, "Adicionar outro tipo? (S/N)")
                u["etapa"] = "tipo_mais"
                return "ok"

            if u["etapa"] == "tipo_mais":
                resposta = sn(texto)

                if resposta not in ["s","n"]:
                    enviar(numero, "❌ Digite S ou N")
                    return "ok"

                u["etapa"] = "tipo" if resposta == "s" else "campo"
                return "ok"

            if u["etapa"] == "campo":
                enviar(numero, "🏟 Tipo de campo:\n1 Campo Oficial\n2 Society\n3 Futsal")
                u["etapa"] = "campo_escolha"
                return "ok"

            if u["etapa"] == "campo_escolha":
                campo = TIPO_CAMPO.get(texto)
                if not campo:
                    enviar(numero, "❌ Opção inválida")
                    return "ok"

                u["campo"] = campo
                u["etapa"] = "pix"
                enviar(numero, "💰 Chave PIX:")
                return "ok"

            if u["etapa"] == "pix":

                conn = sqlite3.connect("lendarios.db")
                cursor = conn.cursor()

                cursor.execute("""
                INSERT INTO atletas (numero,cpf,nome,cidades,tipos,campo,pix)
                VALUES (?,?,?,?,?,?,?)
                """, (
                    numero,
                    u["cpf"],
                    u["nome"],
                    ",".join(u["cidades"]),
                    ",".join(u["tipos"]),
                    u["campo"],
                    texto
                ))

                conn.commit()
                conn.close()

                enviar(numero, f"""🏆 Cadastro realizado com sucesso!

Nome: {u['nome']}
Cidades: {", ".join(u['cidades'])}
Tipos: {", ".join(u['tipos'])}
Campo: {u['campo']}
""")

                del usuarios[numero]
                return "ok"

        # =========================
        # SOLICITAÇÃO
        # =========================
        if numero in solicitacoes:
            s = solicitacoes[numero]

            if s["etapa"] == "cpf":
                s["cpf"] = texto
                enviar(numero, "1 Nova solicitação\n2 Minhas solicitações")
                s["etapa"] = "menu"
                return "ok"

            if s["etapa"] == "menu":
                if texto == "2":
                    conn = sqlite3.connect("lendarios.db")
                    cursor = conn.cursor()
                    cursor.execute("SELECT cidade,data,hora,status FROM solicitacoes WHERE cpf=?", (s["cpf"],))
                    dados = cursor.fetchall()
                    conn.close()

                    enviar(numero, str(dados))
                    del solicitacoes[numero]
                    return "ok"

                s["etapa"] = "endereco"
                enviar(numero, "📍 Endereço:")
                return "ok"

            if s["etapa"] == "endereco":
                s["endereco"] = texto
                enviar(numero, "Cidade:\n" + "\n".join([f"{k} {v}" for k,v in CIDADES.items()]))
                s["etapa"] = "cidade"
                return "ok"

            if s["etapa"] == "cidade":
                s["cidade"] = CIDADES.get(texto)
                enviar(numero, "🏟 Nome do campo:")
                s["etapa"] = "nome_campo"
                return "ok"

            if s["etapa"] == "nome_campo":
                s["nome_campo"] = texto
                enviar(numero, "Tipo de campo:\n1 Campo Oficial\n2 Society\n3 Futsal")
                s["etapa"] = "tipo_campo"
                return "ok"

            if s["etapa"] == "tipo_campo":
                s["tipo_campo"] = TIPO_CAMPO.get(texto)
                enviar(numero, "⚽ Tipo:\n1 Goleiro\n2 Jogador Linha\n3 Árbitro")
                s["etapa"] = "tipo"
                return "ok"

            if s["etapa"] == "tipo":
                s["tipo"] = TIPOS.get(texto)
                enviar(numero, "📅 Data:")
                s["etapa"] = "data"
                return "ok"

            if s["etapa"] == "data":
                s["data"] = texto
                enviar(numero, "⏰ Hora:")
                s["etapa"] = "hora"
                return "ok"

            if s["etapa"] == "hora":
                s["hora"] = texto
                enviar(numero, "👥 Quantidade de atletas:")
                s["etapa"] = "qtd"
                return "ok"

            if s["etapa"] == "qtd":
                qtd = int(texto)
                valor = VALORES[s["tipo"]] * qtd

                conn = sqlite3.connect("lendarios.db")
                cursor = conn.cursor()

                cursor.execute("""
                INSERT INTO solicitacoes
                (numero,cpf,endereco,cidade,nome_campo,tipo_campo,tipo,data,hora,quantidade,valor,status)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
                """, (
                    numero,
                    s["cpf"],
                    s["endereco"],
                    s["cidade"],
                    s["nome_campo"],
                    s["tipo_campo"],
                    s["tipo"],
                    s["data"],
                    s["hora"],
                    qtd,
                    valor,
                    "aberto"
                ))

                conn.commit()
                conn.close()

                enviar(numero, f"""⚽ Solicitação realizada com sucesso!

📍 {s['cidade']}
🏟 {s['nome_campo']} ({s['tipo_campo']})
⚽ {s['tipo']}
👥 {qtd}
💰 R$ {valor}
""")

                del solicitacoes[numero]
                return "ok"

        menu(numero)
        return "ok"

    except Exception as e:
        print("ERRO:", e)

    return "ok"

@app.route("/")
def home():
    return "LENDARIOS ONLINE"

if __name__ == "__main__":
    app.run(port=5000)
