import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Configuração do SQL Server
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'mssql+pyodbc://username:password@server/database?driver=ODBC+Driver+17+for+SQL+Server')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv('SECRET_KEY', 'sua-chave-secreta-aqui')