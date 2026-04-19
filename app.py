from flask import Flask, request, render_template_string, send_file
import re
import io
from datetime import datetime

app = Flask(__name__)

DIAS_SEMANA = {
    0: "SEGUNDA-FEIRA", 1: "TER\u00c7A-FEIRA", 2: "QUARTA-FEIRA",
    3: "QUINTA-FEIRA", 4: "SEXTA-FEIRA", 5: "S\u00c1BADO", 6: "DOMINGO"
}

def obter_dia_semana(data_str):
    try:
        data_obj = datetime.strptime(data_str, "%d/%m/%Y")
        return DIAS_SEMANA[data_obj.weekday()]
    except: return "DIA"

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head><title>Gerador RTF</title></head>
<body style="font-family: sans-serif; padding: 20px;">
    <h2>Gerador de RTF para Mediadores</h2>
    <form method="post">
        <textarea name="dados" rows="15" cols="80" placeholder="Cole os dados aqui..."></textarea><br><br>
        <button type="submit" style="padding: 10px 20px; cursor: pointer;">Gerar e Baixar Arquivo RTF</button>
    </form>
</body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        texto_bruto = request.form['dados']
        # Regex flexível para capturar colunas separadas por tab ou múltiplos espaços
        padrao = re.compile(r"(\d{2}/\d{2}/\d{4})\s+(\d{2}:\d{2})\s+(\d{7}-\d{2}\.\d{4})\s+([\w\.-]+)\s+(.*?)\s+(?:SIM|N\u00c3O)\s+([A-Z\s]+(?:\n|$))")
        matches = padrao.findall(texto_bruto)
        
        if not matches: return "Nenhum dado encontrado. Verifique se o formato colado está correto."

        mediador_nome = matches[0][5].strip()
        
        # Gerando o conteúdo RTF com escape para caracteres especiais (Acentos)
        rtf_content = r"{\rtf1\ansi\deff0 {\fonttbl {\f0 Arial;}}\f0\fs24 "
        rtf_content += "-"*60 + r"\par\par Tudo bem? \par\par "
        rtf_content += r"Segue(m) \b *NOVA(S) NOMEA\u199?\u195?O(\u213?ES)* \b0 \par "
        rtf_content += r"Segue(m) \b *CANCELAMENTO(S) DE AUDI\u202?NCIA(S)* \b0 \par\par "
        rtf_content += "-"*60 + r"\par\par "
        
        for m in matches:
            d, h, p, s, v, med = m
            # Tratamento de acentos específicos para o RTF
            dia = obter_dia_semana(d).replace("Ç", r"\u199?").replace("Á", r"\u193?")
            vara = v.strip().replace("É", r"\u201?").replace("Í", r"\u205?").replace("ª", r"\u170?")
            
            rtf_content += r"\b *" + f"{dia}: {d} \u00e0s {h}" + r"*\b0 \par "
            rtf_content += f"PROC {p} \par SENHA: {s} \par VARA: {vara} \par MEDIADOR(A) {med.strip()} \par\par "
            rtf_content += "-"*60 + r"\par\par "
        
        rtf_content += "}"
        
        output = io.BytesIO()
        output.write(rtf_content.encode('ascii', errors='ignore')) # RTF prefere ascii com escapes
        output.seek(0)
        
        return send_file(output, as_attachment=True, download_name=f"pauta_{mediador_nome.replace(' ', '_')}.rtf", mimetype='application/rtf')

    return render_template_string(HTML_TEMPLATE)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
