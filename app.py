from flask import Flask, request, send_file
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
        linha_dia = limpar_acentos_rtf(f"{item['dia_semana']}: {item['data']}")
        rtf += r"{\b *" + linha_dia + r" \'e0s " + f"{item['hora']}.*" + r"} \par "
        rtf += f"PROC {item['proc']}. \par "
        rtf += f"SENHA: {item['senha']}. \par "
        rtf += f"VARA: {limpar_acentos_rtf(item['vara'])}. \par "
        rtf += f"MEDIADOR(A) {limpar_acentos_rtf(item['mediador_original'])}. \par\par "
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
            linha_limpa = linha.strip()
            if not linha_limpa: continue
            
            # Divide a linha por TAB ou múltiplos espaços
            partes = re.split(r'\t+', linha_limpa)
            
            # Se não encontrar tabs, tenta por espaços duplos (fallback)
            if len(partes) < 6:
                partes = re.split(r'\s{2,}', linha_limpa)

            # Verifica se temos as colunas necessárias
            if len(partes) >= 6:
                data = partes[0].strip()
                hora = partes[1].strip()
                proc = partes[2].strip()
                senha = partes[3].strip()
                vara = partes[4].strip()
                mediador_nome = partes[5].strip()

                # Identifica cancelamento
                is_cancelada = any(x in linha_limpa.upper() for x in ["CANCELADA", "CANCELADO"])

                # Tratamento do dia da semana
                try:
                    d_obj = datetime.strptime(data, "%d/%m/%Y")
                    dias = ["SEGUNDA-FEIRA", "TERÇA-FEIRA", "QUARTA-FEIRA", "QUINTA-FEIRA", "SEXTA-FEIRA", "SÁBADO", "DOMINGO"]
                    dia_semana = dias[d_obj.weekday()]
                except: 
                    dia_semana = "DIA"

                dados_audiencia = {
                    'data': data, 'hora': hora, 'proc': proc, 
                    'senha': senha, 'vara': vara, 'dia_semana': dia_semana,
                    'mediador_original': mediador_nome
                }

                # Define para qual arquivo vai (Cancelados ou nome do Mediador)
                if is_cancelada:
                    grupo = "AUDIENCIA CANCELADA"
                else:
                    grupo = mediador_nome

                if grupo not in mediadores_dict:
                    mediadores_dict[grupo] = []
                mediadores_dict[grupo].append(dados_audiencia)

        # Geração do ZIP
        memory_file = io.BytesIO()
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            for grupo, lista in mediadores_dict.items():
                conteudo = criar_conteudo_rtf(grupo, lista)
                # Remove caracteres inválidos para nome de arquivo
                nome_limpo = re.sub(r'[\\/*?:"<>|]', "", grupo).replace(' ', '_')
                nome_arq = f"{nome_limpo}.rtf"
                zf.writestr(nome_arq, conteudo.encode('ascii', errors='ignore'))
        
        memory_file.seek(0)
        return send_file(memory_file, as_attachment=True, download_name="pautas_atualizadas.zip", mimetype='application/zip')

    return '''
    <html><body style="font-family:sans-serif; background:#f0f2f5; padding:50px;">
    <div style="background:white; padding:30px; border-radius:10px; max-width:900px; margin:auto; box-shadow:0 5px 15px rgba(0,0,0,0.1);">
    <h2>Gerador de Pautas - Formato Colunas</h2>
    <p style="font-size:0.9em; color:#666;">Cole as informações copiadas da tabela (Data, Hora, Processo, Senha, Vara, Mediador).</p>
    <form method="post"><textarea name="dados" style="width:100%; height:450px; font-family:monospace; padding:10px;" placeholder="04/05/2026	13:30	1501085-40.2026	ncthsx	2ª FAMÍLIA	LIZANDRA..."></textarea><br>
    <button type="submit" style="width:100%; padding:15px; background:#1a73e8; color:white; border:none; border-radius:5px; font-weight:bold; cursor:pointer; margin-top:10px;">GERAR ZIP</button>
    </form></div></body></html>
    '''

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
