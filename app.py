import os
import json
import pyodbc
import pandas as pd
import numpy as np
from flask import Flask, render_template, jsonify
from datetime import datetime, date

app = Flask(__name__)

# =====================================================
# CONEXÃO SQL SERVER
# =====================================================
def conectar_sql_server():
    try:
        conn_str = (
            "DRIVER={ODBC Driver 17 for SQL Server};"
            f"SERVER={os.getenv('DB_SERVER', 'localhost')};"
            f"DATABASE={os.getenv('DB_NAME', 'seu_banco')};"
            f"UID={os.getenv('DB_USER', 'sa')};"
            f"PWD={os.getenv('DB_PASSWORD', 'sua_senha')}"
        )
        return pyodbc.connect(conn_str)
    except Exception as e:
        print("Erro conexão:", e)
        return None


# =====================================================
# SERIALIZAÇÃO SEGURA
# =====================================================
def json_safe(value):
    if value is None or pd.isna(value):
        return 0
    if isinstance(value, (np.integer, int)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.strftime('%Y-%m-%d')
    return str(value)


# =====================================================
# ROTAS
# =====================================================
@app.route('/')
def index():
    return render_template('index.html')


# =====================================================
# ROTA DATATABLES (OBRIGATÓRIA)
# =====================================================
@app.route('/clientes')
def clientes():
    conn = conectar_sql_server()
    if not conn:
        return jsonify({"data": []})

    try:
        df = pd.read_sql("SELECT * FROM clien", conn)

        data = []
        for _, row in df.iterrows():
            item = {}
            for col in df.columns:
                item[col] = json_safe(row[col])
            data.append(item)

        return jsonify({"data": data})

    except Exception as e:
        print("Erro /clientes:", e)
        return jsonify({"data": []})

    finally:
        conn.close()


# =====================================================
# DASHBOARD (CARDS)
# =====================================================
@app.route('/dashboard')
def dashboard():
    conn = conectar_sql_server()
    if not conn:
        return jsonify({
            "total_clientes": 0,
            "clientes_bloqueados": 0,
            "media_score": 0,
            "utilizacao_media": 0
        })

    try:
        query = """
            SELECT
                COUNT(*) AS total_clientes,
                SUM(CASE WHEN Bloqueado = 1 THEN 1 ELSE 0 END) AS clientes_bloqueados,
                AVG(
                    CASE 
                        WHEN ISNULL(Limite_Credito, 0) > 0
                        THEN (ISNULL(Total_Debito, 0) / Limite_Credito) * 100
                        ELSE 0
                    END
                ) AS utilizacao_media
            FROM clien
        """

        df = pd.read_sql(query, conn)

        utilizacao = df.iloc[0]["utilizacao_media"]
        utilizacao = float(utilizacao) if utilizacao is not None else 0
        utilizacao = round(utilizacao, 2)

        media_score = round(max(0, 100 - utilizacao), 2)

        return jsonify({
            "total_clientes": int(df.iloc[0]["total_clientes"]),
            "clientes_bloqueados": int(df.iloc[0]["clientes_bloqueados"]),
            "media_score": media_score,
            "utilizacao_media": utilizacao
        })

    except Exception as e:
        print("Erro /dashboard:", e)
        return jsonify({
            "total_clientes": 0,
            "clientes_bloqueados": 0,
            "media_score": 0,
            "utilizacao_media": 0
        })

    finally:
        conn.close()


# =====================================================
# MAIN
# =====================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
