# Search Effectors 🔍🧬

[![Status](https://img.shields.io/badge/status-em%20desenvolvimento-yellow)]()
[![Python](https://img.shields.io/badge/python-3.11-blue?logo=python)]()
[![Flask](https://img.shields.io/badge/flask-web%20framework-lightgrey?logo=flask)]()
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)]()

Web application for search and store effectors in a determined aminoacids/nucleotide sequences, with interactive visualization and DB integration 

Stacks
| Back-end | Front-end | Banco de Dados | Outros |
|----------|-----------|----------------|--------|
| [Flask](https://flask.palletsprojects.com/) | HTML, CSS, JS | MySQL | dotenv, PyMySQL |

Some DEMO below:

    ❗ Clone this repo
        git clone https://github.com/jampani1/seq.search.git
        cd seq_search

    ❗ Activate the virtual environment
        (Windows)
        python -m venv venv
        .\venv\Scripts\activate

        (Linux/macOS)
        python3 -m venv venv
        source venv/bin/activate

    ❗ Install the dependencies
        pip install -r requirements.txt

    ❗ And a /db/db.py with:
        import pymysql
        # Configuração da conexão
        def conectar_db():
        return pymysql.connect(
        host='localhost',
        user='your_user',
        password='your_pwd',
        database='search_effectors',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
    
    ⚠️ DONT FORGET to create in MySQL
        CREATE TABLE sequencias (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nome VARCHAR(100),
            tipo ENUM('nucleo', 'amino') NOT NULL,
            conteudo TEXT NOT NULL,
            data_upload DATETIME NOT NULL
        );

        CREATE TABLE efetores (
            id INT AUTO_INCREMENT PRIMARY KEY,
            id_sequencia INT NOT NULL,
            nome VARCHAR(100),
            sequencia_efetor TEXT NOT NULL,
            posicao_inicio INT NOT NULL,
            posicao_fim INT NOT NULL,
            FOREIGN KEY (id_sequencia) REFERENCES sequencias(id)
                ON DELETE CASCADE
                ON UPDATE CASCADE
        );    
🧪 Soon  
Result exports  
More bioinfo tools  
  
📝 License  
This project is licensed under the MIT License — you are free to use, modify, and distribute this code for any purpose, but it comes without any warranty.  
For more details, see the <a href="https://opensource.org/licenses/MIT">MIT License</a>.  
  
Enjoy and lets talk about it!  
[![X](https://img.shields.io/badge/X-000000?style=flat&logoColor=white)](https://x.com/jampaninho)  
- 💼 [LinkedIn](https://www.linkedin.com/in/mauriciojampani)  


