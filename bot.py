from flask import Flask, request
import requests
import sqlite3

app = Flask(__name__)

TOKEN = "EAAsCShhhFUoBRNRnA9Y6C45qzxLQKBAI8ONFDHTGQAwPrquuZCZBCQ2IbMuyjzAEQeo711RNSjO01vxzENl8tpazlDOligh6WoZBl3qodphq40niZCcZBDiEmLt5vAEHyMFsG9cy1zU0n4HKwMrQ5qHTxpyxUp5ZCzZB0KsV5ZA9Jdu7zuuZC0GQ5Wqo6rPmcKMtNM8gJ9RHYyJFtyVbhrRlUZBlD2kyuGv59wrJra55JyaxDPuPZABsn50gi8Wv9JNhsetxjJETmMEM0EaK0NU37DH2naK"
PHONE_NUMBER_ID = "1094450353745202"
VERIFY_TOKEN = "lendarios_token"

usuarios = {}
solicitacoes_fluxo = {}
convites = {}
vagas = {}
pagamentos = {}

# =========================
# FUNÇÕES
# =========================
def sn(texto):
    return texto.strip().lower()

def normalizar(numero):
    numero = "".join(filter(str.isdigit, numero))
    if numero.startswith("55") and len(numero) == 12:
        numero = numero[:4] + "9" + numero[4:]
    return numero

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

def conectar():
    return sqlite3.connect("lendarios.db")

# =========================
# BANCO
# =========================
def init_db():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS atletas (
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
# MATCH
# =========================
def buscar_atletas(cidade, tipo):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT numero,cidades,tipos FROM atletas")
    dados = cursor.fetchall()
    conn.close()

    resultado = []

    for numero, cidades, tipos in dados:
        if cidade in cidades and tipo in tipos:
            resultado.append(numero)

    return resultado

def disparar_match(solicitacao_id, cidade, tipo, quantidade):

    atletas = buscar_atletas(cidade, tipo)

    if not atletas:
        return

    vagas[solicitacao_id] = {
        "total": quantidade,
        "aceitos": []
    }

    for numero in atletas:
        convites[numero] = {"solicitacao": solicitacao_id}

        enviar(numero, f"""⚽ NOVA PARTIDA!

📍 {cidade}
⚽ {tipo}
👥 Vagas: {quantidade}

1 Aceitar
2 Recusar
""")

# =========================
# MENU
# =========================
def menu(numero):
    enviar(numero, """🏆 LENDÁRIOS

1 Cadastro atleta
2 Solicitar atleta
3 Avaliações
4 Admin
5 Sair
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

        numero = normalizar(msg["from"])
        texto = msg["text"]["body"].strip()

        # =========================
        # PAGAMENTO
        # =========================
        if numero in pagamentos:
            if sn(texto) == "pago":
                enviar(numero, "✅ Pagamento confirmado! Você está no jogo.")
                del pagamentos[numero]
                return "ok"

        # =========================
        # RESPOSTA CONVITE
        # =========================
        if numero in convites:

            solicitacao_id = convites[numero]["solicitacao"]
            controle = vagas.get(solicitacao_id)

            if not controle:
                enviar(numero, "❌ Vaga encerrada.")
                del convites[numero]
                return "ok"

            if texto == "1":

                if numero in controle["aceitos"]:
                    enviar(numero, "⚠ Já aceitou.")
                    return "ok"

                if len(controle["aceitos"]) >= controle["total"]:
                    enviar(numero, "❌ Vagas completas.")
                    del convites[numero]
                    return "ok"

                pagamentos[numero] = True

                enviar(numero, """💰 Para confirmar:

PIX: 48999999999
Valor: R$ 10

Digite PAGO após enviar
""")

                controle["aceitos"].append(numero)
                del convites[numero]
                return "ok"

            elif texto == "2":
                enviar(numero, "❌ Recusado.")
                del convites[numero]
                return "ok"

        # =========================
        # MENU
        # =========================
        if numero not in usuarios and numero not in solicitacoes_fluxo:

            if texto == "1":
                usuarios[numero] = {"etapa": "cpf", "cidades": [], "tipos": []}
                enviar(numero, "CPF:")
                return "ok"

            if texto == "2":
                solicitacoes_fluxo[numero] = {"etapa": "cpf"}
                enviar(numero, "CPF:")
                return "ok"

            menu(numero)
            return "ok"

        # =========================
        # CADASTRO
        # =========================
        if numero in usuarios:
            u = usuarios[numero]

            if u["etapa"] == "cpf":

                conn = conectar()
                cursor = conn.cursor()
                cursor.execute("SELECT cpf FROM atletas WHERE cpf=?", (texto,))
                if cursor.fetchone():
                    enviar(numero, "CPF já cadastrado.")
                    del usuarios[numero]
                    conn.close()
                    return "ok"
                conn.close()

                u["cpf"] = texto
                u["etapa"] = "nome"
                enviar(numero, "Nome:")
                return "ok"

            if u["etapa"] == "nome":
                u["nome"] = texto
                u["etapa"] = "cidade"

                lista = "\n".join([f"{k} {v}" for k,v in CIDADES.items()])
                enviar(numero, "Cidade:\n" + lista)
                return "ok"

            if u["etapa"] == "cidade":
                if texto not in CIDADES:
                    enviar(numero, "Opção inválida")
                    return "ok"

                cidade = CIDADES[texto]

                if cidade not in u["cidades"]:
                    u["cidades"].append(cidade)

                u["etapa"] = "cidade_mais"
                enviar(numero, "Mais cidades? (S/N)")
                return "ok"

            if u["etapa"] == "cidade_mais":
                if sn(texto) == "s":
                    u["etapa"] = "cidade"
                    lista = "\n".join([f"{k} {v}" for k,v in CIDADES.items() if v not in u["cidades"]])
                    enviar(numero, "Outra cidade:\n" + lista)
                elif sn(texto) == "n":
                    u["etapa"] = "tipo"
                    lista = "\n".join([f"{k} {v}" for k,v in TIPOS.items()])
                    enviar(numero, "Tipo:\n" + lista)
                else:
                    enviar(numero, "Digite S ou N")
                return "ok"

            if u["etapa"] == "tipo":
                if texto not in TIPOS:
                    enviar(numero, "Opção inválida")
                    return "ok"

                tipo = TIPOS[texto]

                if tipo not in u["tipos"]:
                    u["tipos"].append(tipo)

                u["etapa"] = "tipo_mais"
                enviar(numero, "Mais tipos? (S/N)")
                return "ok"

            if u["etapa"] == "tipo_mais":
                if sn(texto) == "s":
                    u["etapa"] = "tipo"
                    lista = "\n".join([f"{k} {v}" for k,v in TIPOS.items() if v not in u["tipos"]])
                    enviar(numero, "Outro tipo:\n" + lista)
                elif sn(texto) == "n":
                    u["etapa"] = "campo"
                    enviar(numero, "Tipo campo:\n1 Campo Oficial\n2 Society\n3 Futsal")
                else:
                    enviar(numero, "Digite S ou N")
                return "ok"

            if u["etapa"] == "campo":
                if texto not in TIPO_CAMPO:
                    enviar(numero, "Opção inválida")
                    return "ok"

                u["campo"] = TIPO_CAMPO[texto]
                u["etapa"] = "pix"
                enviar(numero, "Chave PIX:")
                return "ok"

            if u["etapa"] == "pix":

                conn = conectar()
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

                enviar(numero, "Cadastro concluído!")
                del usuarios[numero]
                return "ok"

        # =========================
        # SOLICITAÇÃO
        # =========================
        if numero in solicitacoes_fluxo:
            s = solicitacoes_fluxo[numero]

            if s["etapa"] == "cpf":
                s["cpf"] = texto
                s["etapa"] = "endereco"
                enviar(numero, "Endereço:")
                return "ok"

            if s["etapa"] == "endereco":
                s["endereco"] = texto
                lista = "\n".join([f"{k} {v}" for k,v in CIDADES.items()])
                enviar(numero, "Cidade:\n" + lista)
                s["etapa"] = "cidade"
                return "ok"

            if s["etapa"] == "cidade":
                s["cidade"] = CIDADES.get(texto)
                s["etapa"] = "campo_nome"
                enviar(numero, "Nome do campo:")
                return "ok"

            if s["etapa"] == "campo_nome":
                s["nome_campo"] = texto
                enviar(numero, "Tipo campo:\n1 Campo Oficial\n2 Society\n3 Futsal")
                s["etapa"] = "tipo_campo"
                return "ok"

            if s["etapa"] == "tipo_campo":
                s["tipo_campo"] = TIPO_CAMPO.get(texto)
                enviar(numero, "Tipo:\n1 Goleiro\n2 Jogador Linha\n3 Árbitro")
                s["etapa"] = "tipo"
                return "ok"

            if s["etapa"] == "tipo":
                s["tipo"] = TIPOS.get(texto)
                enviar(numero, "Data:")
                s["etapa"] = "data"
                return "ok"

            if s["etapa"] == "data":
                s["data"] = texto
                enviar(numero, "Hora:")
                s["etapa"] = "hora"
                return "ok"

            if s["etapa"] == "hora":
                s["hora"] = texto
                enviar(numero, "Quantidade:")
                s["etapa"] = "qtd"
                return "ok"

            if s["etapa"] == "qtd":

                qtd = int(texto)
                valor = VALORES[s["tipo"]] * qtd

                conn = conectar()
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

                solicitacao_id = cursor.lastrowid

                conn.commit()
                conn.close()

                disparar_match(solicitacao_id, s["cidade"], s["tipo"], qtd)

                enviar(numero, f"""Solicitação criada!

📍 {s['cidade']}
⚽ {s['tipo']}
👥 {qtd}
💰 R$ {valor}
""")

                del solicitacoes_fluxo[numero]
                return "ok"

        menu(numero)
        return "ok"

    except Exception as e:
        print("ERRO:", e)

    return "ok"

@app.route("/")
def home():
    return "LENDARIOS FULL ONLINE"

if __name__ == "__main__":
    app.run(port=5000)
