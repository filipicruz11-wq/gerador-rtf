from flask import Flask, request, render_template_string, send_file
import re
import io
import zipfile
from datetime import datetime

app = Flask(__name__)

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

def criar_conteudo_rtf(nome_grupo, audiencias):
    rtf = r"{\rtf1\ansi\deff0 {\fonttbl {\f0 Arial;}}\f0\fs24 "
    rtf += "-"*64 + r"\par\par Tudo bem? \par\par "
    rtf += r"Segue(m) \b *NOVA(S) NOMEA\u199?\u195?O(\u213?ES):* \b0 \par "
    rtf += r"Segue(m) \b *CANCELAMENTO(S) DE AUDI\u202?NCIA(S):* \b0 \par\par "
    rtf += "-"*64 + r"\par\par "
    for item in audiencias:
        rtf += r"{\b *" + f"{item['dia_semana']}: {item['data']} " + r"\'e0s " + f"{item['hora']}.*" + r"} \par "
        rtf += f"PROC {item['proc']}. \par "
        rtf += f"SENHA: {item['senha']}. \par "
        rtf += f"VARA: {limpar_acentos_rtf(item['vara'])}. \par "
        rtf += f"MEDIADOR(A) {limpar_acentos_rtf(nome_grupo)}. \par\par "
        rtf += "-"*64 + r"\par\par "
    rtf += "}"
    return rtf

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        texto_bruto = request.form['dados']
        linhas = texto_bruto.strip().split('\n')
        mediadores_dict = {}
        
        # Regex para identificar o processo
        regex_proc = re.compile(r"(\d{7}-\d{2}\.\d{4})")
        
        for linha in linhas:
            linha_limpa = linha.strip()
            if not linha_limpa: continue
            
            match_proc = regex_proc.search(linha_limpa)
            if not match_proc: continue
            
            proc = match_proc.group(1)
            
            # --- LÓGICA DE DEFINIÇÃO DO GRUPO (ARQUIVO) ---
            linha_upper = linha_limpa.upper()
            # Se encontrar qualquer variação de cancelamento em qualquer lugar da linha
            if any(x in linha_upper for x in ["CANCELADA", "CANCELADO", "AUDIENCIA CANCELADA"]):
                nome_grupo = "AUDIENCIA CANCELADA"
            else:
                # Se não for cancelada, pega o mediador na última coluna
                partes_linha = re.split(r'\t|\s{2,}', linha_limpa)
                nome_grupo = partes_linha[-1].strip()

            # --- EXTRAÇÃO DOS DADOS ---
            partes_antes = linha_limpa.split(proc)[0].strip().split()
            partes_depois = [p.strip() for p in re.split(r'\t|\s{2,}', linha_limpa.split(proc)[1].strip()) if p.strip()]
            
            if len(partes_antes) >= 2 and len(partes_depois) >= 1:
                data = partes_antes[0]
                hora = partes_antes[1]
                senha = partes_depois[0]
                # A Vara é sempre a coluna após a senha
                vara = partes_depois[1] if len(partes_depois) > 1 else "---"
                # Evita que a vara seja o próprio nome do mediador
                if vara == nome_grupo: vara = "---"

                if nome_grupo not in mediadores_dict:
                    mediadores_dict[nome_grupo] = []
                
                try:
                    d_obj = datetime.strptime(data, "%d/%m/%Y")
                    dias = ["SEGUNDA-FEIRA", "TER\u00c7A-FEIRA", "QUARTA-FEIRA", "QUINTA-FEIRA", "SEXTA-FEIRA", "S\u00c1BADO", "DOMINGO"]
                    dia_semana = dias[d_obj.weekday()]
                except: dia_semana = "DIA"

                mediadores_dict[nome_grupo].append({
                    'data': data, 'hora': hora, 'proc': proc, 
                    'senha': senha, 'vara': vara, 'dia_semana': dia_semana
                })

        # Geração do ZIP
        memory_file = io.BytesIO()
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            for grupo, lista in mediadores_dict.items():
                conteudo = criar_conteudo_rtf(grupo, lista)
                nome_arq = f"{grupo.replace(' ', '_').replace('/', '-')}.rtf"
                zf.writestr(nome_arq, conteudo.encode('ascii', errors='ignore'))
        
        memory_file.seek(0)
        return send_file(memory_file, as_attachment=True, download_name="pautas.zip", mimetype='application/zip')

    return '''
    <html><body style="font-family:sans-serif; background:#f0f2f5; padding:50px;">
    <div style="background:white; padding:30px; border-radius:10px; max-width:900px; margin:auto; box-shadow:0 5px 15px rgba(0,0,0,0.1);">
    <h2>Gerador de Pautas - Filtro Global de Cancelamento</h2>
    <p>Qualquer linha contendo "CANCELADA" vai para o arquivo de cancelamentos.</p>
    <form method="post"><textarea name="dados" style="width:100%; height:450px; font-family:monospace; padding:10px;"></textarea><br>
    <button type="submit" style="width:100%; padding:15px; background:#1a73e8; color:white; border:none; border-radius:5px; font-weight:bold; cursor:pointer; margin-top:10px;">GERAR ZIP</button>
    </form></div></body></html>
    '''

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
