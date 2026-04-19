from flask import Flask, request, render_template_string, send_file
import re
import io
from datetime import datetime

app = Flask(__name__)

DIAS_SEMANA = {
    0: "SEGUNDA-FEIRA", 1: "TERÇA-FEIRA", 2: "QUARTA-FEIRA",
    3: "QUINTA-FEIRA", 4: "SEXTA-FEIRA", 5: "SÁBADO", 6: "DOMINGO"
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

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>Gerador RTF</title>
    <style>
        body { font-family: sans-serif; background: #f4f4f9; padding: 40px; display: flex; justify-content: center; }
        .box { width: 100%; max-width: 700px; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
        h2 { color: #2c3e50; margin-top: 0; }
        textarea { width: 100%; border: 1px solid #ddd; border-radius: 8px; padding: 15px; font-family: monospace; font-size: 13px; box-sizing: border-box; }
        button { background: #3498db; color: white; border: none; padding: 12px 25px; border-radius: 6px; cursor: pointer; margin-top: 15px; font-weight: bold; width: 100%; }
        button:hover { background: #2980b9; }
    </style>
</head>
<body>
    <div class="box">
        <h2>Gerador de Pautas</h2>
        <form method="post">
            <textarea name="dados" rows="12" placeholder="Cole os dados aqui..."></textarea>
            <button type="submit">GERAR E BAIXAR .RTF</button>
        </form>
    </div>
</body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        texto_bruto = request.form['dados']
        # Regex ajustada para capturar os dados corretamente
        padrao = re.compile(r"(\d{2}/\d{2}/\d{4})\s+(\d{2}:\d{2})\s+(\d{7}-\d{2}\.\d{4})\s+([\w\.-]+)\s+(.*?)\s+(?:SIM|N\u00c3O)\s+([A-Z\s]+(?:\n|$|  ))")
        matches = padrao.findall(texto_bruto)
        
        if not matches: return "Nenhum dado encontrado no formato correto."

        mediador = matches[0][5].strip()
        
        # Construção do RTF
        rtf = r"{\rtf1\ansi\deff0 {\fonttbl {\f0 Arial;}}\f0\fs24 "
        rtf += "-"*64 + r"\par\par Tudo bem? \par\par "
        rtf += r"Segue(m) \b *NOVA(S) NOMEA\u199?\u195?O(\u213?ES)* \b0 \par "
        rtf += r"Segue(m) \b *CANCELAMENTO(S) DE AUDI\u202?NCIA(S)* \b0 \par\par "
        rtf += "-"*64 + r"\par\par "
        
        for m in matches:
            d, h, p, s, v, med = m
            dia = limpar_acentos_rtf(obter_dia_semana(d))
            vara = limpar_acentos_rtf(v.strip())
            
            # Ajuste no fechamento do negrito para evitar o caractere estranho
            rtf += r"{\b *" + f"{dia}: {d} " + r"\'e0s " + f"{h}" + r"*} \par "
            rtf += f"PROC {p} \par "
            rtf += f"SENHA: {s} \par "
            rtf += f"VARA: {vara} \par "
            rtf += f"MEDIADOR(A) {med.strip()} \par\par "
            rtf += "-"*64 + r"\par\par "
        
        rtf += "}"
        
        return send_file(
            io.BytesIO(rtf.encode('ascii', errors='ignore')),
            as_attachment=True,
            download_name=f"pauta_{mediador.replace(' ', '_')}.rtf",
            mimetype='application/rtf'
        )

    return render_template_string(HTML_TEMPLATE)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
