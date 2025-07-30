from flask import Flask, redirect, render_template, request, url_for, flash
import textwrap
import secrets  # For generating a random secret key
from db import conectar_db  # Assuming you have a db.py file with a conectar_db function

app = Flask(__name__)
app.secret_key = 'SENHASECRETA'
#app.secret_key = secrets.token_hex(16)  # Alternatively, generate a random key, but you need to keep it secret and consistent across sessions

def validar_sequencia(seq, tipo):
    seq = seq.upper()
    if tipo == "dna":
        return all(base in "ATCG" for base in seq)
    elif tipo == "proteina":
        return all(aa in "ACDEFGHIKLMNPQRSTVWY" for aa in seq)
    return False

def validar_efetor(efetor, tipo):
    efetor = efetor.upper()
    if tipo == "dna":
        return all(base in "ATCG" for base in efetor)
    elif tipo == "proteina":
        return all(aa in "ACDEFGHIKLMNPQRSTVWY" for aa in efetor)
    return False

def salvar_sequencia(nome, tipo, conteudo):
    connection = conectar_db()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM sequences WHERE conteudo = %s", (conteudo))
            result = cursor.fetchone()
            if result:
                return result['id']
            
            cursor.execute("""INSERT INTO sequences (nome, tipo, conteudo) VALUES (%s, %s, %s)""", (nome, tipo, conteudo))
            connection.commit()
            return cursor.lastrowid
    finally:
        connection.close()

def salvar_efetor(id_sequencia, nome_efetor, descricao, pos_inicio, pos_fim):
    connection = conectar_db()
    try:
        with connection.cursor() as cursor:            
            cursor.execute("""INSERT INTO efetores (id_sequencia, nome, descricao, posicao_inicio, posicao_fim) VALUES (%s, %s, %s, %s, %s)""", (id_sequencia, nome_efetor, descricao, pos_inicio, pos_fim))
            connection.commit()
            return cursor.lastrowid
    finally:
        connection.close()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        #.request.form.get to get the value from the form 
        #request.form.get(variable name in .html and default value if not found)
        sequencia = request.form.get('sequencia', '').upper().strip() #.upper to a - A / .strip to remove border spaces 
        tipo = request.form.get('tipo')
        efetor = request.form.get('efetor', '').upper().strip()
        arquivo = request.files.get('arquivo')

        if not sequencia and arquivo and arquivo.filename != '':
            try:
                conteudo = arquivo.read().decode('utf-8')
                linhas = conteudo.splitlines()
                sequencia = ''.join(linha.strip() for linha in linhas if not linha.startswith('>')).upper()
            except Exception as e:
                flash(f"Error reading file: {e}", "erro")
                return render_template('index.html')
        if not sequencia:
            flash("Please, input a valid sequence.", "erro")
            return render_template('index.html')
        if not tipo:
            flash("Please, select a sequence type.", "erro")
            return render_template('index.html')
        if not efetor:
            flash("Please, input a valid effector.", "erro")
            return render_template('index.html')    
        
        if not validar_sequencia(sequencia, tipo):
            flash(f"Invalid sequence for type {tipo.upper()}. Please, input a valid sequence.", "erro")
            return render_template('index.html')
        if not validar_efetor(efetor, tipo):
            flash(f"Invalid effector for type {tipo.upper()}. Please, input a valid effector.", "erro")
            return render_template('index.html')
        
        return redirect(url_for('result', sequencia=sequencia, efetor=efetor))
    
    return render_template('index.html')

@app.route('/result')
def result():
    sequencia = request.args.get('sequencia', '')
    efetor = request.args.get('efetor', '')
    pos = sequencia.find(efetor) #to mark and make visible the position of the effector in the sequence

    if efetor not in sequencia:
        resultado = f"O efetor '{efetor}' não foi encontrado na sequência."
        return render_template('result.html', resultado=resultado, sequencia=sequencia, sequencia_marcada=sequencia)
    
    antes = sequencia[:pos]
    encontrado = f"<mark>{sequencia[pos:pos+len(efetor)]}</mark>"
    depois = sequencia[pos+len(efetor):]
    sequencia_marcada = antes + encontrado + depois

    resultado = f"O efetor '{efetor}' foi encontrado na sequência em '{pos}'."
    return render_template('result.html', resultado=resultado, sequencia=sequencia, sequencia_marcada=sequencia_marcada, efetor=efetor, pos=pos)

@app.route('/salvar', methods=['POST'])
def salvar():
    from datetime import datetime
    import pymysql

    def conectar_db():
        return pymysql.connect(
            host='localhost',
            user='root',
            password='Mau18042001!',
            database='search_effectors',
            cursorclass=pymysql.cursors.DictCursor
        )
    
    sequencia = request.form['sequencia']
    nome_sequencia = request.form['nome_sequencia']
    tipo = 'nucleo' if all (base in 'ATCGatcg' for base in sequencia) else 'amino'
    efetor = request.form['efetor']
    pos_inicio = int(request.form['pos_inicio'])
    pos_fim = int(request.form['pos_fim'])
    nome_efetor = request.form['nome_efetor']

    connection = conectar_db()
    try:
        with connection.cursor() as cursor:
            #insere as sequencias
            cursor.execute("SELECT id FROM sequencias WHERE conteudo = %s", (sequencia,))
            result = cursor.fetchone()
            if result:
                id_seq = result['id']
            else:
                cursor.execute("""
                               INSERT INTO sequencias (nome, tipo, conteudo, data_upload)
                               VALUES (%s, %s, %s, %s)
                               """, (nome_sequencia, tipo, sequencia, datetime.now()))
                id_seq = cursor.lastrowid
            
            #insere os efetores
            cursor.execute("""
                           INSERT INTO efetores (id_sequencia, nome, sequencia_efetor, posicao_inicio, posicao_fim)
                           VALUES (%s, %s, %s, %s, %s)
                           """, (id_seq, nome_efetor, efetor, pos_inicio, pos_fim))
            
            connection.commit()
            flash("Sequence and effector saved successfully!", "success")

    except Exception as e:
        flash(f"Error saving data: {e}", "error")
    finally:
        connection.close()

    return redirect(url_for('index'))






if __name__ == '__main__':
    app.run(debug=True)
