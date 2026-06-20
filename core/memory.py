import sqlite3
import os
import json
from datetime import datetime

DB_PATH = os.environ.get("DB_PATH", "database/memory.db")

def get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS mensagens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            role TEXT,
            content TEXT,
            timestamp TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS memoria (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            chave TEXT,
            valor TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()
    return conn

def salvar_mensagem(user_id, role, content):
    conn = get_conn()
    conn.execute(
        "INSERT INTO mensagens (user_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
        (user_id, role, content, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

def buscar_historico(user_id, limite=10):
    conn = get_conn()
    rows = conn.execute(
        "SELECT role, content FROM mensagens WHERE user_id = ? ORDER BY id DESC LIMIT ?",
        (user_id, limite)
    ).fetchall()
    conn.close()
    # Inverte para ordem cronológica
    return [{"role": r[0], "content": r[1]} for r in reversed(rows)]

def buscar_contexto(user_id):
    conn = get_conn()
    rows = conn.execute(
        "SELECT chave, valor FROM memoria WHERE user_id = ? ORDER BY id DESC LIMIT 20",
        (user_id,)
    ).fetchall()
    conn.close()
    return {r[0]: r[1] for r in rows}

def salvar_memoria(user_id, chave, valor):
    conn = get_conn()
    conn.execute(
        "INSERT INTO memoria (user_id, chave, valor, timestamp) VALUES (?, ?, ?, ?)",
        (user_id, chave, valor, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

def limpar(user_id):
    conn = get_conn()
    conn.execute("DELETE FROM mensagens WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
