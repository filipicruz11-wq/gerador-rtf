from flask import Flask, request, render_template_string, send_file
import re
import io
import zipfile
from datetime import datetime

app = Flask(__name__)

# Mapeamento de acentos para o padrão RTF
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
        
        for linha in linhas:
            linha = linha.strip()
            if not linha: continue
            
            # 1. Localiza o processo como âncora principal
            match_proc = re.search(r"(\d{7}-\d{2}\.\d{4})", linha)
            if not match_proc: continue
            
            proc = match_proc.group(1)
            
            # 2. Divide a linha em 'antes do processo' e 'depois do processo'
            partes_antes = linha.split(proc)[0].strip().split()
            # Divide o depois por Tabs ou múltiplos espaços
            partes_depois = [p.strip() for p in re.split(r'\t|\s{2,}', linha.split(proc)[1].strip()) if p.strip()]
            
            if len(partes_antes) >= 2 and len(partes_depois) >= 1:
                data = partes_antes[0]
                hora = partes_antes[1]
                senha = partes_depois[0]
                
                # A Vara é o que estiver entre a senha e o mediador (geralmente partes_depois[1])
                vara = partes_depois[1] if len(partes_depois) > 2 else (partes_depois[1] if len(partes_depois) == 2 else "---")
                
                # O Mediador é SEMPRE o último bloco de texto da linha inteira
                mediador_raw = re.split(r'\t|\s{2,}', linha)[-1].strip()
                
                # Normalização de Cancelados para evitar múltiplos arquivos de erro
                med_upper = mediador_raw.upper()
                if any(x in med_upper for x in ["CANCELADA", "CANCELADO", "AUDIENCIA CANCELADA"]):
                    nome_grupo = "AUDIENCIA CANCELADA"
                else:
                    nome_grupo = mediador_raw

                if nome_grupo not in mediadores_dict:
                    mediadores_dict[nome_grupo] = []
                
                # Cálculo do dia da semana simplificado
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
        return send_file(memory_file, as_attachment=True, download_name="pautas_completas.zip", mimetype='application/zip')

    return '''
    <html><body style="font-family:sans-serif; background:#f0f2f5; padding:50px;">
    <div style="background:white; padding:30px; border-radius:10px; max-width:900px; margin:auto; box-shadow:0 5px 15px rgba(0,0,0,0.1);">
    <h2>Gerador de Pautas - Garantia Total</h2>
    <p>O script processa cada linha individualmente. O nome na última coluna define o arquivo.</p>
    <form method="post"><textarea name="dados" style="width:100%; height:450px; font-family:monospace; padding:10px;"></textarea><br>
    <button type="submit" style="width:100%; padding:15px; background:#1a73e8; color:white; border:none; border-radius:5px; font-weight:bold; cursor:pointer; margin-top:10px;">GERAR E BAIXAR TODOS OS ARQUIVOS (.ZIP)</button>
    </form></div></body></html>
    '''

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
