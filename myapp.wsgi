import io
from flask import Flask, render_template, make_response
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import blue

# 1. INICIALIZAÇÃO ÚNICA (O Flask deve ser iniciado uma única vez no arquivo)
app = Flask(__name__)

# 2. ROTAS ORIGINAIS DO SEU SITE
@app.route('/')
def index():
    return render_template("Flower/index.html")

@app.route('/api')
def api():
    return {"status": "sucesso", "framework": "Flask", "servidor": "Apache"}

# 3. ROTA PARA EMISSÃO DA RECEITA
@app.route('/receita')
def gerar_receita():
    # Cria o buffer em memória para não salvar arquivos físicos no disco do Apache
    pdf_buffer = io.BytesIO()
    
    # Configuração do Documento PDF
    doc = SimpleDocTemplate(
        pdf_buffer, 
        pagesize=A4, 
        rightMargin=50, 
        leftMargin=50, 
        topMargin=50, 
        bottomMargin=50
    )

    # Configuração de Estilos de Texto do ReportLab
    styles = getSampleStyleSheet()
    
    estilo_titulo = ParagraphStyle(
        'titulo', parent=styles['Normal'], 
        fontName='Helvetica-Bold', fontSize=18, 
        alignment=1, textColor=blue, spaceAfter=20
    )
    
    estilo_texto = ParagraphStyle(
        'texto', parent=styles['Normal'], 
        fontSize=12, leading=18, spaceAfter=15
    )
    
    estilo_receita = ParagraphStyle(
        'receita', parent=styles['Normal'], 
        fontSize=13, leading=22, spaceAfter=10
    )

    elementos = []

    # Cabeçalho da Receita
    elementos.append(Paragraph("<b>Doutor(a) Gustavo Sá</b>", estilo_titulo))
    elementos.append(Paragraph("Clínica Médica - Endocrinologia e Metabologia", estilo_texto))
    elementos.append(Paragraph("CRM: 123456 / SP", estilo_texto))
    elementos.append(Spacer(1, 25))

    # Identificação do Paciente
    elementos.append(Paragraph("<b>Paciente:</b> João da Silva", estilo_texto))
    elementos.append(Paragraph("<b>Data:</b> 23 de Junho de 2026", estilo_texto))
    elementos.append(Spacer(1, 20))

    # Prescrição Baseada no Medicamento Fornecido
    elementos.append(Paragraph("<b>Prescrição Médica (Uso Subcutâneo):</b>", estilo_texto))
    
    medicamentos = """
    <b>1. Tirzepatida 15 mg / 0,5 mL (Solução Injetável)</b> ---------- 1 Caixa<br/>
    <i>Orientação de uso: Aplicar dose por via subcutânea, uma vez por semana, conforme o plano de escalonamento prescrito e a tolerância metabólica individual.</i>
    """
    elementos.append(Paragraph(medicamentos, estilo_receita))
    elementos.append(Spacer(1, 80))

    # Assinatura
    elementos.append(Paragraph("___________________________________________________", estilo_texto))
    elementos.append(Paragraph("Assinatura do Médico e Carimbo OBRIGATÓRIOS", estilo_texto))

    # Compilação do PDF
    doc.build(elementos)
    
    # Envio da resposta HTTP contendo o PDF binário
    pdf_buffer.seek(0)
    response = make_response(pdf_buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=receita_tirzepatida.pdf'
    
    return response

# 4. EXIGÊNCIA OBRIGATÓRIA DO APACHE MOD_WSGI
application = app
