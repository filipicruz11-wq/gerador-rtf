from flask import Flask, request, render_template_string, send_file
import re
import io
from datetime import datetime

app = Flask(__name__)

# Mapeamento de dias da semana com escape RTF para o 'Ç' e 'Á'
DIAS_SEMANA = {
    0: "SEGUNDA-FEIRA", 1: "TER\u199?A-FEIRA", 2: "QUARTA-FEIRA",
    3: "QUINTA-FEIRA", 4: "SEXTA-FEIRA", 5: "S\u193?BADO", 6: "DOMINGO"
}

def obter_dia_semana(data_str):
    try:
        data_obj = datetime.strptime(data_str, "%d/%m/%Y")
        return DIAS_SEMANA[data_obj.weekday()]
    except:
        return "DIA"

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>Gerador de Pautas RTF</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f4f9; padding: 40px; color: #333; }
        .container { max-width: 800px; margin: auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h2 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
        textarea { width: 100%; padding: 15px; border: 1px solid #ccc; border-radius: 4px; font-family: monospace; font-size: 14px; resize: vertical; }
        button { background-color: #3498db; color: white; padding: 12px 24px; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; margin-top: 15px; }
        button:hover { background-color: #2980b9; }
        .instrucoes { font-size: 0.9em; color: #666; margin-bottom: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <h2>Gerador de RTF para Mediadores</h2>
        <p class="instrucoes">Cole as linhas da planilha abaixo. O sistema gerar\u00e1 um arquivo formatado para o mediador encontrado.</p>
        <form method="post">
            <textarea name="dados" rows="12" placeholder="Exemplo: 29/04/2026 15:30 1001348-32.2026 CANCELADA..."></textarea>
            <br>
            <button type="submit">Gerar e Baixar .RTF</button>
        </form>
    </div>
</body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        texto_bruto = request.form['dados']
        
        # Regex para capturar os campos: Data, Hora, Processo, Senha/Status, Vara, Mediador
        # Suporta SIM/NÃO e captura o nome do mediador corretamente
        padrao = re.compile(r"(\d{2}/\d{2}/\d{4})\s+(\d{2}:\d{2})\s+(\d{7}-\d{2}\.\d{4})\s+([\w\.-]+)\s+(.*?)\s+(?:SIM|N\u00c3O)\s+([A-Z\s]+(?:\n|$|  ))")
        matches = padrao.findall(texto_bruto)
        
        if not matches:
            return "Nenhum dado v\u00e1lido encontrado. Verifique o formato do texto colado."

        nome_mediador = matches[0][5].strip()
        
        # Cabe\u00e7alho RTF com suporte a acentua\u00e7\u00e3o Windows
        rtf_content = r"{\rtf1\ansi\deff0 {\fonttbl {\f0 Arial;}}\f0\fs24 "
        rtf_content += "-"*64 + r"\par\par Tudo bem? \par\par "
        rtf_content += r"Segue(m) \b *NOVA(S) NOMEA\u199?\u195?O(\u213?ES)* \b0 \par "
        rtf_content += r"Segue(m) \b *CANCELAMENTO(S) DE AUDI\u202?NCIA(S)* \b0 \par\par "
        rtf_content += "-"*64 + r"\par\par "
        
        for m in matches:
            data, hora, proc, senha, vara_bruta, mediador = m
            
            # Tratamento de caracteres especiais na Vara (\u170? \u00e9 o s\u00edmbolo de 2\u00aa)
            vara = vara_bruta.strip().replace("É", r"\u201?").replace("Í", r"\u205?").replace("ª", r"\u170?")
            dia_semana = obter_dia_semana(data)
            
            # Formata\u00e7\u00e3o da pauta com a crase corrigida (\'e0s)
            rtf_content += r"\b *" + f"{dia_semana}: {data} " + r"\'e0s " + f"{hora}* \b0 \par "
            rtf_content += f"PROC {proc} \par "
            rtf_content += f"SENHA: {senha} \par "
            rtf_content += f"VARA: {vara} \par "
            rtf_content += f"MEDIADOR(A) {mediador.strip()} \par\par "
            rtf_content += "-"*64 + r"\par\par "
        
        rtf_content += "}"
        
        # Envio do arquivo sem erros de encoding
        output = io.BytesIO()
        output.write(rtf_content.encode('ascii', errors='ignore'))
        output.seek(0)
        
        return send_file(
            output, 
            as_attachment=True, 
            download_name=f"pauta_{nome_mediador.replace(' ', '_')}.rtf", 
            mimetype='application/rtf'
        )

    return render_template_string(HTML_TEMPLATE)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
