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
        rtf += r"{\b *" + f"{dia}: {item['data']} " + r"\'e0s " + f"{item['hora']}.*" + r"} \par "
        rtf += f"PROC {item['proc']}. \par "
        rtf += f"SENHA: {item['senha']}. \par "
        rtf += f"VARA: {limpar_acentos_rtf(item['vara'])}. \par "
        rtf += f"MEDIADOR(A) {limpar_acentos_rtf(nome_mediador)}. \par\par "
        rtf += "-"*64 + r"\par\par "
    rtf += "}"
    return rtf

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        texto_bruto = request.form['dados']
        linhas = texto_bruto.strip().split('\n')
        mediadores_dict = {}
        
        for linha in linhas:
            linha = linha.strip()
            if not linha: continue
            
            # 1. Encontrar Processo (0000000-00.0000)
            proc_match = re.search(r"(\d{7}-\d{2}\.\d{4})", linha)
            # 2. Encontrar Data (00/00/0000)
            data_match = re.search(r"(\d{2}/\d{2}/\d{4})", linha)
            # 3. Encontrar Hora (00:00)
            hora_match = re.search(r"(\d{2}:\d{2})", linha)
            
            if proc_match and data_match and hora_match:
                proc = proc_match.group(1)
                data = data_match.group(1)
                hora = hora_match.group(1)
                
                # Pegar o que vem DEPOIS do processo
                pos_final_proc = linha.find(proc) + len(proc)
                resto = linha[pos_final_proc:].strip()
                
                # Dividir o resto por TAB ou múltiplos espaços
                partes_depois = [p.strip() for p in re.split(r'\t|\s{2,}', resto) if p.strip()]
                
                if len(partes_depois) >= 2:
                    senha = partes_depois[0]
                    vara = partes_depois[1]
                    # O Mediador é o último elemento da linha inteira
                    mediador = re.split(r'\t|\s{2,}', linha)[-1].strip()
                    
                    if mediador not in mediadores_dict:
                        mediadores_dict[mediador] = []
                    
                    mediadores_dict[mediador].append({
                        'data': data, 'hora': hora, 'proc': proc, 
                        'senha': senha, 'vara': vara,
                        'dia_semana': obter_dia_semana(data)
                    })

        if not mediadores_dict: return "Nenhum dado processado. Verifique se o Processo, Data e Hora est\u00e3o corretos."

        memory_file = io.BytesIO()
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            for nome_med, audiencias in mediadores_dict.items():
                conteudo_rtf = criar_conteudo_rtf(nome_med, audiencias)
                filename = f"{nome_med.replace(' ', '_')}.rtf"
                zf.writestr(filename, conteudo_rtf.encode('ascii', errors='ignore'))
        
        memory_file.seek(0)
        return send_file(memory_file, as_attachment=True, download_name="pautas.zip", mimetype='application/zip')

    return '''
    <html><body style="font-family:sans-serif; padding:40px;">
    <h2>Gerador ZIP - Vers\u00e3o Corrigida</h2>
    <form method="post"><textarea name="dados" style="width:100%; height:400px;"></textarea><br>
    <button type="submit" style="padding:10px 20px; background:#1a73e8; color:white; border:none; border-radius:5px; margin-top:10px;">GERAR ZIP</button>
    </form></body></html>
    '''

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
