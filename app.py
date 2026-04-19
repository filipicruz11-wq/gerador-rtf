from flask import Flask, request, render_template_string, send_file
import re
import io
from datetime import datetime

app = Flask(__name__)

DIAS_SEMANA = {
    0: "SEGUNDA-FEIRA", 1: "TERÇA-FEIRA", 2: "QUARTA-FEIRA",
    3: "QUINTA-FEIRA", 4: "SEXTA-FEIRA", 5: "SÁBADO", 6: "DOMINGO"
}

def obter_dia_semana(data_str):
    try:
        data_obj = datetime.strptime(data_str, "%d/%m/%Y")
        return DIAS_SEMANA[data_obj.weekday()]
    except: return "DIA"

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<body>
    <h2>Gerador de RTF para Mediadores</h2>
    <form method="post">
        <textarea name="dados" rows="10" cols="50" placeholder="Cole os dados aqui..."></textarea><br><br>
        <button type="submit">Gerar Arquivo RTF</button>
    </form>
</body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        texto_bruto = request.form['dados']
        # Usando sua lógica de regex
        padrao = re.compile(r"(\d{2}/\d{2}/\d{4})\s+(\d{2}:\d{2})\s+(\d{7}-\d{2}\.\d{4})\s+([\w\.-]+)\s+(.*?)\s+(?:SIM|NÃO)\s+([A-Z\s]+(?:\n|$|  ))")
        matches = padrao.findall(texto_bruto)
        
        if not matches: return "Nenhum dado encontrado no formato correto."

        # Gerando apenas o primeiro mediador encontrado para simplificar o download via web
        data, hora, proc, senha, vara, mediador = matches[0]
        mediador = mediador.strip()
        
        output = io.BytesIO()
        rtf_content = r"{\rtf1\ansi\deff0 {\fonttbl {\f0 Arial;}}\f0\fs24 "
        rtf_content += "-"*60 + r"\par\par Tudo bem? \par\par "
        rtf_content += r"Segue(m) \b *NOVA(S) NOMEA\u195?O(\u213?ES)* \b0 \par "
        rtf_content += r"Segue(m) \b *CANCELAMENTO(S) DE AUDI\u202?NCIA(S)* \b0 \par\par "
        
        for m in matches:
            d, h, p, s, v, med = m
            rtf_content += r"\b *" + f"{obter_dia_semana(d)}: {d} \u00e0s {h}" + r"*\b0 \par "
            rtf_content += f"PROC {p} \par SENHA: {s} \par VARA: {v} \par MEDIADOR(A) {med.strip()} \par\par "
            rtf_content += "-"*60 + r"\par\par "
        
        rtf_content += "}"
        output.write(rtf_content.encode('utf-8'))
        output.seek(0)
        
        return send_file(output, as_attachment=True, download_name=f"pauta_{mediador}.rtf", mimetype='application/rtf')

    return render_template_string(HTML_TEMPLATE)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)