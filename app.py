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
    rtf += r"Segue(m) \b *NOVA(S) NOMEA\u199?\u195?O(\u213?ES):* \b0 \par "
    rtf += r"Segue(m) \b *CANCELAMENTO(S) DE AUDI\u202?NCIA(S):* \b0 \par\par "
    rtf += "-"*64 + r"\par\par "
    for item in audiencias:
        dia = limpar_acentos_rtf(item['dia_semana'])
        vara = limpar_acentos_rtf(item['vara'])
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
        textarea { width: 100%; border: 1px solid #dadce0; border-radius: 8px; padding: 15px; font-family: monospace; min-height: 400px; box-sizing: border-box; }
        button { background: #1a73e8; color: white; border: none; padding: 15px; border-radius: 8px; cursor: pointer; margin-top: 15px; font-weight: bold; width: 100%; font-size: 16px; }
    </style>
</head>
<body>
    <div class="box">
        <h2>Gerador de Pautas (Vers\u00e3o Anti-Falha)</h2>
        <form method="post">
            <textarea name="dados" placeholder="Cole a pauta aqui..."></textarea>
            <button type="submit">GERAR E BAIXAR ZIP</button>
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
        
        # Regex para encontrar o padrão de processo 0000000-00.0000
        regex_proc = re.compile(r"(\d{7}-\d{2}\.\d{4})")
        
        for linha in linhas:
            linha = linha.strip()
            if not linha: continue
            
            match_proc = regex_proc.search(linha)
            if match_proc:
                proc = match_proc.group(1)
                # Divide a linha em antes e depois do processo
                parte_antes = linha.split(proc)[0].strip().split()
                parte_depois = linha.split(proc)[1].strip().split('\t') 
                # Se não houver tabulação, tenta por espaços múltiplos
                if len(parte_depois) < 2:
                    parte_depois = [p.strip() for p in re.split(r'\s{2,}', linha.split(proc)[1].strip()) if p.strip()]

                try:
                    # Data e Hora estão sempre antes do processo
                    data = parte_antes[0]
                    hora = parte_antes[1]
                    
                    # Senha/Cancelada e Vara estão sempre depois do processo
                    # Usamos a lógica: Pós-Processo(0)=Senha, Pós-Processo(1)=Vara
                    senha = parte_depois[0]
                    vara = parte_depois[1] if len(parte_depois) > 1 else "---"
                    
                    # Mediador é sempre o último elemento da linha
                    mediador = linha.split()[-1]

                    if mediador not in mediadores_dict:
                        mediadores_dict[mediador] = []
                    
                    mediadores_dict[mediador].append({
                        'data': data, 'hora': hora, 'proc': proc, 
                        'senha': senha, 'vara': vara,
                        'dia_semana': obter_dia_semana(data)
                    })
                except:
                    continue

        if not mediadores_dict: return "Nenhum dado processado. Verifique o formato do Processo."

        memory_file = io.BytesIO()
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            for nome_med, audiencias in mediadores_dict.items():
                conteudo_rtf = criar_conteudo_rtf(nome_med, audiencias)
                safe_name = nome_med.replace(' ', '_').replace('/', '-').replace('\\', '-')
                zf.writestr(f"{safe_name}.rtf", conteudo_rtf.encode('ascii', errors='ignore'))
        
        memory_file.seek(0)
        return send_file(memory_file, as_attachment=True, download_name="pautas.zip", mimetype='application/zip')

    return render_template_string(HTML_TEMPLATE)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
