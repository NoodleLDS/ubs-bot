"""
Persistência com SQLite: avaliações, métricas e avisos.
- Queries SQL agregadas (não carrega tudo em memória)
- Paginação nas listagens
- Fallback em todas as leituras (banco travado ≠ bot travado)
- Auto-purge de dados antigos
"""

import logging
import os
import sqlite3
from datetime import datetime
from contextlib import contextmanager

logger = logging.getLogger(__name__)

DB_PATH = os.getenv("DB_PATH", os.path.join(os.path.dirname(os.path.dirname(__file__)), "bot_ubs.db"))

PURGE_DAYS = 90  # Métricas mais antigas que isso são apagadas no cleanup


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS avaliacoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nota INTEGER NOT NULL,
                comentario TEXT DEFAULT '',
                criado_em TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS metricas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rota TEXT NOT NULL,
                tipo TEXT NOT NULL DEFAULT 'acesso',
                criado_em TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS avisos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mensagem TEXT,
                criado_em TEXT,
                ativo INTEGER DEFAULT 1
            );
            CREATE INDEX IF NOT EXISTS idx_metricas_rota ON metricas(rota);
            CREATE INDEX IF NOT EXISTS idx_metricas_data ON metricas(criado_em);
        """)
    logger.info("📦 Banco de dados inicializado: %s", DB_PATH)


# ── Avaliações ───────────────────────────────────

def salvar_avaliacao(nota: int, comentario: str = "") -> None:
    try:
        with get_db() as conn:
            conn.execute(
                "INSERT INTO avaliacoes (nota, comentario, criado_em) VALUES (?, ?, ?)",
                (nota, comentario, datetime.now().isoformat()),
            )
    except Exception as exc:
        logger.error("Erro ao salvar avaliação: %s", exc)


def listar_avaliacoes(limite: int = 50, pagina: int = 1) -> dict:
    """Retorna avaliações paginadas com estatísticas via SQL agregado."""
    try:
        with get_db() as conn:
            # Estatísticas via SQL (não carrega tudo na memória)
            stats = conn.execute(
                "SELECT COUNT(*) as total, COALESCE(AVG(nota), 0) as media FROM avaliacoes"
            ).fetchone()

            total = stats["total"]
            media = round(stats["media"], 1)

            # Paginação
            offset = (pagina - 1) * limite
            rows = conn.execute(
                "SELECT nota, comentario, criado_em FROM avaliacoes ORDER BY criado_em DESC LIMIT ? OFFSET ?",
                (limite, offset),
            ).fetchall()

            return {
                "avaliacoes": [dict(r) for r in rows],
                "total": total,
                "media": media,
                "pagina": pagina,
                "limite": limite,
            }
    except Exception as exc:
        logger.error("Erro ao listar avaliações: %s", exc)
        return {"avaliacoes": [], "total": 0, "media": 0, "pagina": 1, "limite": limite}


# ── Métricas ─────────────────────────────────────

def registrar_acesso(rota: str) -> None:
    try:
        with get_db() as conn:
            conn.execute(
                "INSERT INTO metricas (rota, criado_em) VALUES (?, ?)",
                (rota, datetime.now().isoformat()),
            )
    except Exception as exc:
        logger.warning("Erro ao registrar métrica: %s", exc)


def obter_metricas(dias: int = 30) -> dict:
    """Retorna métricas de uso dos últimos N dias."""
    # Valida range
    dias = max(1, min(dias, 365))

    try:
        with get_db() as conn:
            total = conn.execute(
                "SELECT COUNT(*) FROM metricas WHERE criado_em >= datetime('now', ?)",
                (f"-{dias} days",),
            ).fetchone()[0]

            top_rotas = conn.execute(
                """SELECT rota, COUNT(*) as acessos 
                   FROM metricas WHERE criado_em >= datetime('now', ?)
                   GROUP BY rota ORDER BY acessos DESC LIMIT 10""",
                (f"-{dias} days",),
            ).fetchall()

            por_dia = conn.execute(
                """SELECT DATE(criado_em) as dia, COUNT(*) as total
                   FROM metricas WHERE criado_em >= datetime('now', ?)
                   GROUP BY DATE(criado_em) ORDER BY dia DESC LIMIT 30""",
                (f"-{dias} days",),
            ).fetchall()

            return {
                "total_mensagens": total,
                "periodo_dias": dias,
                "top_rotas": [dict(r) for r in top_rotas],
                "por_dia": [dict(r) for r in por_dia],
            }
    except Exception as exc:
        logger.error("Erro ao obter métricas: %s", exc)
        return {"total_mensagens": 0, "periodo_dias": dias, "top_rotas": [], "por_dia": []}


# ── Avisos ───────────────────────────────────────

def salvar_aviso(mensagem: str | None) -> None:
    try:
        with get_db() as conn:
            conn.execute("UPDATE avisos SET ativo = 0")
            if mensagem:
                conn.execute(
                    "INSERT INTO avisos (mensagem, criado_em, ativo) VALUES (?, ?, 1)",
                    (mensagem, datetime.now().isoformat()),
                )
    except Exception as exc:
        logger.error("Erro ao salvar aviso: %s", exc)


def obter_aviso_ativo() -> str | None:
    """Retorna o aviso ativo ou None. Fallback seguro."""
    try:
        with get_db() as conn:
            row = conn.execute(
                "SELECT mensagem FROM avisos WHERE ativo = 1 ORDER BY id DESC LIMIT 1"
            ).fetchone()
            return row["mensagem"] if row else None
    except Exception as exc:
        logger.warning("Erro ao ler aviso: %s", exc)
        return None


# ── Manutenção ───────────────────────────────────

def purge_metricas_antigas() -> int:
    """Remove métricas mais antigas que PURGE_DAYS. Retorna quantidade removida."""
    try:
        with get_db() as conn:
            cursor = conn.execute(
                "DELETE FROM metricas WHERE criado_em < datetime('now', ?)",
                (f"-{PURGE_DAYS} days",),
            )
            removidas = cursor.rowcount
            if removidas > 0:
                logger.info("🗑️ Purge: %d métricas antigas removidas", removidas)
            return removidas
    except Exception as exc:
        logger.warning("Erro no purge de métricas: %s", exc)
        return 0
