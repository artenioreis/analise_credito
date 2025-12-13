import os
import json
import pyodbc
import pandas as pd
import numpy as np
from flask import Flask, render_template
from datetime import datetime, date

# =====================================================
# APP
# =====================================================
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
# SERIALIZAÇÃO 100% SEGURA PARA JSON
# =====================================================
def to_json_safe(value):
    if pd.isna(value):
        return ""
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


@app.route('/clientes')
def clientes():
    """
    ENDPOINT EXCLUSIVO PARA DATATABLES
    RETORNA SOMENTE JSON PURO
    """
    conn = conectar_sql_server()
    if not conn:
        return app.response_class(
            response=json.dumps({"data": []}),
            status=200,
            mimetype='application/json'
        )

    try:
        query = """
            SELECT TOP 100
                Codigo,
                Razao_Social,
                Fantasia,
                Limite_Credito,
                Total_Debito,
                Atraso_Atual,
                Maior_Atraso,
                Bloqueado,
                Data_Cadastro
            FROM clien
            ORDER BY Codigo
        """

        df = pd.read_sql(query, conn)

        data = []
        for _, row in df.iterrows():
            item = {}
            for col in df.columns:
                item[col] = to_json_safe(row[col])
            data.append(item)

        # ⚠️ RETORNO ÚNICO E LIMPO
        return app.response_class(
            response=json.dumps({"data": data}, ensure_ascii=False),
            status=200,
            mimetype='application/json'
        )

    except Exception:
        # ⚠️ NUNCA retorne erro em HTML para DataTables
        return app.response_class(
            response=json.dumps({"data": []}),
            status=200,
            mimetype='application/json'
        )

    finally:
        try:
            conn.close()
        except:
            pass


@app.route('/dashboard')
def dashboard():
    conn = conectar_sql_server()
    if not conn:
        return {}

    try:
        query = """
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN Bloqueado = '1' THEN 1 ELSE 0 END) AS bloqueados
            FROM clien
        """
        df = pd.read_sql(query, conn)

        result = {
            "total_clientes": int(df.iloc[0]["total"]),
            "clientes_bloqueados": int(df.iloc[0]["bloqueados"])
        }

        return result

    except Exception:
        return {}

    finally:
        try:
            conn.close()
        except:
            pass


# =====================================================
# MAIN
# =====================================================
if __name__ == "__main__":
    # 🔴 IMPORTANTE: DEBUG DESLIGADO PARA DATATABLES
    app.run(host="0.0.0.0", port=5000, debug=False)
