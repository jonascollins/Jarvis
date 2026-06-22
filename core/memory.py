import sqlite3
import os
from datetime import datetime
from contextlib import contextmanager

DB_PATH = os.environ.get("DB_PATH", "database/memory.db")

# Gerenciador de conexão seguro — fecha sempre, mesmo com erro
@contextmanager
def get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    try:
        # Cria tabelas se não existirem
        conn.execute("""
            CREATE TABLE IF NOT EXISTS mensagens (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id   TEXT,
                role      TEXT,
                content   TEXT,
                timestamp TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS memoria (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id   TEXT,
                chave     TEXT UNIQUE,  -- evita duplicatas
                valor     TEXT,
                timestamp TEXT
            )
        """)
        # Índices para buscas rápidas
        conn.execute("CREATE INDEX IF NOT EXISTS idx_msg_user ON mensagens(user_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_mem_user ON memoria(user_id)")
        conn.commit()
        yield conn
    finally:
        conn.close()  # sempre fecha, mesmo com erro

def salvar_mensagem(user_id, role, content):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO mensagens (user_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
            (user_id, role, content, datetime.now().isoformat())
        )
        conn.commit()

def buscar_historico(user_id, limite=10):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT role, content FROM mensagens WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limite)
        ).fetchall()
    return [{"role": r[0], "content": r[1]} for r in reversed(rows)]

def buscar_contexto(user_id, pergunta=None):
    """
    Retorna memórias como texto formatado para o system prompt.
    O parâmetro 'pergunta' está aqui para compatibilidade com app.py
    — futuramente pode ser usado para busca semântica.
    """
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT chave, valor FROM memoria WHERE user_id = ? ORDER BY id DESC LIMIT 20",
            (user_id,)
        ).fetchall()

    if not rows:
        return None

    # Formata como texto para o system prompt
    linhas = [f"- {r[0]}: {r[1]}" for r in rows]
    return "\n".join(linhas)

def salvar_memoria(user_id, chave, valor):
    """Salva ou atualiza uma memória — nunca duplica a mesma chave."""
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO memoria (user_id, chave, valor, timestamp)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(chave) DO UPDATE SET
                valor = excluded.valor,
                timestamp = excluded.timestamp
        """, (user_id, chave, valor, datetime.now().isoformat()))
        conn.commit()

def limpar(user_id):
    """Limpa histórico E memória do usuário."""
    with get_conn() as conn:
        conn.execute("DELETE FROM mensagens WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM memoria WHERE user_id = ?", (user_id,))
        conn.commit()
