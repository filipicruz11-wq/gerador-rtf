from flask import Flask, request, render_template_string, send_file
import re
import io
from datetime import datetime

app = Flask(__name__)

# Dias da semana escritos normalmente (o script converterá para RTF depois)
DIAS_SEMANA = {
    0: "SEGUNDA-FEIRA", 1: "TERÇA-FEIRA", 2: "QUARTA-FEIRA",
    3: "QUINTA-FEIRA", 4: "SEXTA-FEIRA", 5: "SÁBADO", 6: "DOMINGO"
}

def limpar_acentos_rtf(texto):
    """Converte acentos comuns para códigos que o RTF entende perfeitamente."""
    if not texto: return ""
    mapa = {
        'Ç': r'\u199?', 'ç': r'\u231?',
        'Ã': r'\u195?', 'ã': r'\u227?',
        'Õ': r'\u213?', 'õ': r'\u245?',
        'Á': r'\u193?', 'á': r'\u225?',
        'É': r'\u201?', 'é': r'\u233?',
        'Ê': r'\u202?', 'ê': r'\u234?',
        'Í': r'\u205?', 'í': r'\u237?',
        'Ó': r'\u211?', 'ó': r'\u243?',
        'Ú': r'\u218?', 'ú': r'\u250?',
        'ª': r'\u170?', 'º': r'\u186?'
    }
    for original, rtf in mapa.items():
        texto = texto.replace(original, rtf)
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
        body { font-family: sans-serif; background: #f4f4f9; padding: 40px; }
        .box { max-width: 700px; margin: auto; background: white; padding: 25px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        textarea { width: 100%; border: 1px solid #ddd; border-radius: 4px; padding: 10px; font-family: monospace; }
        button { background: #3498db; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="box">
        <h2>Gerador de Pautas Mediador</h2>
        <form method="post">
            <textarea name="dados" rows="10" placeholder="Cole os dados aqui..."></textarea>
            <button type="submit">Gerar Arquivo .RTF</button>
        </form>
    </div>
</body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        texto_bruto = request.form['dados']
        padrao = re.compile(r"(\d{2}/\d{2}/\d{4})\s+(\d{2}:\d{2})\s+(\d{7}-\d{2}\.\d{4})\s+([\w\.-]+)\s+(.*?)\s+(?:SIM|N\u00c3O)\s+([A-Z\s]+(?:\n|$|  ))")
        matches = padrao.findall(texto_bruto)
        
        if not matches: return "Dados inválidos."

        mediador = matches[0][5].strip()
        
        # Início do Conteúdo RTF
        rtf = r"{\rtf1\ansi\deff0 {\fonttbl {\f0 Arial;}}\f0\fs24 "
        rtf += "-"*64 + r"\par\par Tudo bem? \par\par "
        rtf += r"Segue(m) \b *NOVA(S) NOMEA\u199?\u195?O(\u213?ES)* \b0 \par "
        rtf += r"Segue(m) \b *CANCELAMENTO(S) DE AUDI\u202?NCIA(S)* \b0 \par\par "
        rtf += "-"*64 + r"\par\par "
        
        for m in matches:
            d, h, p, s, v, med = m
            dia = limpar_acentos_rtf(obter_dia_semana(d))
            vara = limpar_acentos_rtf(v.strip())
            
            # Formatação da linha com o 'às' corrigido
            rtf += r"\b *" + f"{dia}: {d} " + r"\'e0s " + f"{h}* \b0 \par "
            rtf += f"PROC {p} \par SENHA: {s} \par VARA: {vara} \par MEDIADOR(A) {med.strip()} \par\par "
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
