from flask import Flask, request, render_template_string, send_file
import re
import io
import zipfile
from datetime import datetime

app = Flask(__name__)

DIAS_SEMANA = {
    0: "SEGUNDA-FEIRA", 1: "TER\u00c7A-FEIRA", 2: "QUARTA-FEIRA",
    3: "QUINTA-FEIRA", 4: "SEXTA-FEIRA", 5: "S\u00c1BADO", 6: "DOMINGO"
}

def limpar_acentos_rtf(texto):
    if not texto: return ""
    mapa = {
        'Ç': r'\u199?', 'ç': r'\u231?', 'Ã': r'\u195?', 'ã': r'\u227?',
        'Õ': r'\u213?', 'õ': r'\u245?', 'Á': r'\u193?', 'á': r'\u225?',
        'É': r'\u201?', 'é': r'\u233?', 'Ê': r'\u202?', 'ê': r'\u234?',
        'Í': r'\u205?', 'í': r'\u237?', 'Ó': r'\u211?', 'ó': r'\u243?',
        'Ú': r'\u218?', 'ú': r'\u250?', 'ª': r'\u170?', 'º': r'\u186?'
    }
    for original, rtf_code in mapa.items():
        texto = texto.replace(original, rtf_code)
    return texto

def obter_dia_semana(data_str):
    try:
        data_obj = datetime.strptime(data_str, "%d/%m/%Y")
        return DIAS_SEMANA[data_obj.weekday()]
    except: return "DIA"

def criar_conteudo_rtf(nome_mediador, audiencias):
    rtf = r"{\rtf1\ansi\deff0 {\fonttbl {\f0 Arial;}}\f0\fs24 "
    rtf += "-"*64 + r"\par\par Tudo bem? \par\par "
    # Inserção dos dois-pontos nos cabeçalhos
    rtf += r"Segue(m) \b *NOVA(S) NOMEA\u199?\u195?O(\u213?ES):* \b0 \par "
    rtf += r"Segue(m) \b *CANCELAMENTO(S) DE AUDI\u202?NCIA(S):* \b0 \par\par "
    rtf += "-"*64 + r"\par\par "
    
    for item in audiencias:
        dia = limpar_acentos_rtf(item['dia_semana'])
        vara = limpar_acentos_rtf(item['vara'])
        
        # Inserção de ponto final nas linhas conforme exemplo
        rtf += r"{\b *" + f"{dia}: {item['data']} " + r"\'e0s " + f"{item['hora']}.*" + r"} \par "
        rtf += f"PROC {item['proc']}. \par "
        rtf += f"SENHA: {item['senha']}. \par "
        rtf += f"VARA: {vara}. \par "
        rtf += f"MEDIADOR(A) {limpar_acentos_rtf(nome_mediador)}. \par\par "
        rtf += "-"*64 + r"\par\par "
    
    rtf += "}"
    return rtf

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>Gerador de Pautas ZIP</title>
    <style>
        body { font-family: sans-serif; background: #f0f2f5; padding: 40px; display: flex; justify-content: center; }
        .box { width: 100%; max-width: 800px; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }
        h2 { color: #1a73e8; margin-top: 0; }
        textarea { width: 100%; border: 1px solid #dadce0; border-radius: 8px; padding: 15px; font-family: 'Courier New', monospace; font-size: 13px; box-sizing: border-box; min-height: 300px; }
        button { background: #1a73e8; color: white; border: none; padding: 15px; border-radius: 8px; cursor: pointer; margin-top: 15px; font-weight: bold; width: 100%; font-size: 16px; }
        button:hover { background: #1557b0; }
    </style>
</head>
<body>
    <div class="box">
        <h2>Gerador de Pautas (Pontua\u00e7\u00e3o Ajustada)</h2>
        <form method="post">
            <textarea name="dados" placeholder="Cole a pauta aqui..."></textarea>
            <button type="submit">GERAR E BAIXAR (.ZIP)</button>
        </form>
    </div>
</body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        texto_bruto = request.form['dados']
        linhas = texto_bruto.strip().split('\n')
        mediadores_dict = {}
        
        for linha in linhas:
            if not linha.strip(): continue
            partes = re.split(r'\t|\s{2,}', linha.strip())
            
            if len(partes) >= 5:
                data = partes[0]
                hora = partes[1]
                proc = partes[2]
                senha = partes[3]
                vara = partes[4]
                mediador = partes[-1]
                
                if mediador not in mediadores_dict:
                    mediadores_dict[mediador] = []
                
                mediadores_dict[mediador].append({
                    'data': data, 'hora': hora, 'proc': proc, 
                    'senha': senha, 'vara': vara,
                    'dia_semana': obter_dia_semana(data)
                })

        if not mediadores_dict: return "Erro ao processar dados."

        memory_file = io.BytesIO()
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            for nome_med, audiencias in mediadores_dict.items():
                conteudo_rtf = criar_conteudo_rtf(nome_med, audiencias)
                filename = f"{nome_med.replace(' ', '_').replace('/', '-')}.rtf"
                zf.writestr(filename, conteudo_rtf.encode('ascii', errors='ignore'))
        
        memory_file.seek(0)
        return send_file(memory_file, as_attachment=True, download_name="pautas_corrigidas.zip", mimetype='application/zip')

    return render_template_string(HTML_TEMPLATE)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
