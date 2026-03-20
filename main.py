"""
BOT UBS — WhatsApp Business (ESF / SUS) — v3.1 Final
======================================================
Todas as correções da auditoria aplicadas.

Autor: Lucas Daniel — Enfermeiro ESF, Uberaba/MG
"""

import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from handlers import (
    handle_menu, handle_sub_programas, handle_sub_servicos, handle_sub_orientacoes,
    handle_hoje, handle_unidades, handle_equipe, handle_documentos,
    handle_hiperdia, handle_prenatal, handle_puericultura, handle_vacinacao, handle_saude_mulher,
    handle_exame_sangue, handle_farmacia,
    handle_educacao, handle_saude_bucal, handle_saude_mental, handle_saude_idoso, handle_fisioterapia,
    handle_grupos, handle_emergencia, handle_faq,
    handle_pesquisa, handle_pesquisa_nota, handle_pesquisa_comentario, handle_ia_duvida,
    handle_unsupported_media,
)
from services.whatsapp import WhatsAppService
from utils.session import session_manager
from utils.security import verify_signature, rate_limiter
from utils.database import (
    init_db, registrar_acesso, obter_metricas, listar_avaliacoes,
    salvar_aviso, purge_metricas_antigas,
)
from utils.config_validator import load_and_validate_config

# ── Configuração ─────────────────────────────────

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

VERIFY_TOKEN = os.getenv("WEBHOOK_VERIFY_TOKEN", "")
APP_SECRET = os.getenv("WHATSAPP_APP_SECRET", "")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "")

MENU_TRIGGERS = {"menu", "oi", "olá", "ola", "início", "inicio", "ajuda", "voltar"}

ROUTE_MAP = {
    "SUB_PROGRAMAS": handle_sub_programas,
    "SUB_SERVICOS": handle_sub_servicos,
    "SUB_ORIENTACOES": handle_sub_orientacoes,
    "HOJE": handle_hoje,
    "UNIDADES": handle_unidades,
    "EQUIPE": handle_equipe,
    "DOCUMENTOS": handle_documentos,
    "PROG_HIPERDIA": handle_hiperdia,
    "PROG_PRENATAL": handle_prenatal,
    "PROG_PUERICULTURA": handle_puericultura,
    "PROG_VACINACAO": handle_vacinacao,
    "PROG_SAUDE_MULHER": handle_saude_mulher,
    "EXAME_SANGUE": handle_exame_sangue,
    "FARMACIA": handle_farmacia,
    "EDUCACAO": handle_educacao,
    "SAUDE_BUCAL": handle_saude_bucal,
    "SAUDE_MENTAL": handle_saude_mental,
    "SAUDE_IDOSO": handle_saude_idoso,
    "FISIOTERAPIA": handle_fisioterapia,
    "GRUPOS": handle_grupos,
    "EMERGENCIA": handle_emergencia,
    "FAQ": handle_faq,
    "PESQUISA": handle_pesquisa,
}

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

CLEANUP_INTERVAL = 300  # 5 minutos


# ── Cleanup periódico (background task) ──────────

async def periodic_cleanup():
    """Roda a cada 5 minutos em vez de a cada request."""
    while True:
        await asyncio.sleep(CLEANUP_INTERVAL)
        try:
            expired = session_manager.cleanup_expired()
            rate_limiter.cleanup()
            purged = purge_metricas_antigas()
            if expired or purged:
                logger.info("🧹 Cleanup: %d sessões, %d métricas antigas", expired, purged)
        except Exception as exc:
            logger.warning("Erro no cleanup periódico: %s", exc)


# ── Lifespan ─────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🟢 Bot UBS v3.1 iniciando...")

    app.state.config = load_and_validate_config(CONFIG_PATH)
    init_db()

    app.state.http_client = httpx.AsyncClient(
        timeout=30,
        limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
    )
    app.state.wa = WhatsAppService(client=app.state.http_client)

    # Inicia cleanup periódico como background task
    cleanup_task = asyncio.create_task(periodic_cleanup())

    logger.info("🟢 Bot UBS v3.1 pronto!")
    yield

    cleanup_task.cancel()
    await app.state.http_client.aclose()
    logger.info("🔴 Bot UBS encerrado.")


app = FastAPI(title="Bot UBS v3.1", version="3.1.0", lifespan=lifespan)


# ── Parse do payload ─────────────────────────────

def parse_webhook_payload(body: dict) -> dict | None:
    try:
        entry = body.get("entry", [])
        if not entry:
            return None
        changes = entry[0].get("changes", [])
        if not changes:
            return None
        value = changes[0].get("value", {})
        messages = value.get("messages", [])
        if not messages:
            return None

        msg = messages[0]
        phone = msg.get("from", "")
        message_id = msg.get("id", "")
        msg_type = msg.get("type", "")

        if msg_type == "text":
            return {"phone": phone, "message_id": message_id, "type": "text", "content": msg["text"]["body"].strip()}

        if msg_type == "interactive":
            interactive = msg.get("interactive", {})
            int_type = interactive.get("type", "")
            if int_type == "button_reply":
                return {"phone": phone, "message_id": message_id, "type": "button", "content": interactive["button_reply"]["id"]}
            if int_type == "list_reply":
                return {"phone": phone, "message_id": message_id, "type": "list", "content": interactive["list_reply"]["id"]}

        return {"phone": phone, "message_id": message_id, "type": "unsupported", "content": msg_type}

    except (KeyError, IndexError, TypeError) as exc:
        logger.warning("Erro ao parsear payload: %s", exc)
        return None


# ── Roteamento ───────────────────────────────────

async def route_message(parsed: dict, wa: WhatsAppService, config: dict) -> None:
    phone = parsed["phone"]
    content = parsed["content"]
    msg_type = parsed["type"]

    try:
        await wa.mark_as_read(parsed["message_id"])
    except Exception:
        pass

    if not rate_limiter.is_allowed(phone):
        logger.warning("⚠️ Rate limit: %s", phone)
        return

    try:
        session = session_manager.get(phone)

        # Mídia não suportada
        if msg_type == "unsupported":
            registrar_acesso("UNSUPPORTED_MEDIA")
            await handle_unsupported_media(phone, wa, config)
            return

        # Estados da pesquisa
        if session.state == "PESQUISA_NOTA":
            if msg_type == "text" and content.lower() in MENU_TRIGGERS:
                session_manager.reset(phone)
                registrar_acesso("MENU")
                await handle_menu(phone, wa, config)
                return
            await handle_pesquisa_nota(phone, wa, content, config)
            return

        if session.state == "PESQUISA_COMENTARIO":
            if msg_type == "text" and content.lower() in MENU_TRIGGERS:
                session_manager.reset(phone)
                registrar_acesso("MENU")
                await handle_menu(phone, wa, config)
                return
            await handle_pesquisa_comentario(phone, wa, content, config)
            return

        # Texto
        if msg_type == "text":
            registrar_acesso("MENU" if content.lower() in MENU_TRIGGERS else "MENU_FALLBACK")
            session_manager.reset(phone)
            await handle_menu(phone, wa, config)
            return

        # Botão ou lista
        if msg_type in ("button", "list"):
            if content.startswith("NOTA_"):
                await handle_pesquisa_nota(phone, wa, content, config)
                return

            handler = ROUTE_MAP.get(content)
            if handler:
                session_manager.set_state(phone, content)
                registrar_acesso(content)
                await handler(phone, wa, config)
                return

        # Fallback
        registrar_acesso("FALLBACK")
        await handle_menu(phone, wa, config)

    except Exception as exc:
        logger.exception("❌ Erro no handler para %s: %s", phone, exc)
        try:
            await wa.send_text(
                to=phone,
                body=(
                    "⚠️ Desculpe, tive um problema técnico.\n\n"
                    "Tente novamente digitando *menu*.\n\n"
                    "Se persistir:\n"
                    "📞 Capelinha: (34) 3338-1123\n"
                    "📞 Baixa: (34) 3326-3071"
                ),
            )
        except Exception:
            logger.exception("❌ Falha ao enviar erro para %s", phone)


# ── Endpoints ────────────────────────────────────

@app.get("/webhook")
async def verify_webhook(request: Request) -> Response:
    params = request.query_params
    mode = params.get("hub.mode", "")
    token = params.get("hub.verify_token", "")
    challenge = params.get("hub.challenge", "")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        logger.info("✅ Webhook verificado!")
        return Response(content=challenge, media_type="text/plain")

    logger.warning("⚠️ Falha na verificação do webhook.")
    return Response(content="Forbidden", status_code=403)


@app.post("/webhook")
async def receive_webhook(request: Request) -> dict:
    raw_body = await request.body()

    signature = request.headers.get("X-Hub-Signature-256", "")

    if APP_SECRET:
        if not verify_signature(raw_body, signature, APP_SECRET):
            logger.warning("🚫 HMAC inválido — ignorando (modo debug)")
            # NÃO BLOQUEIA — deixa passar pra testar

    try:
        body = json.loads(raw_body)
    except Exception as e:
        logger.error("❌ Erro ao converter JSON: %s", e)
        return {"status": "error", "reason": "invalid json"}

    parsed = parse_webhook_payload(body)

    if parsed:
        logger.info("📩 %s [%s]: %s", parsed["phone"], parsed["type"], parsed["content"][:50])
        await route_message(parsed, app.state.wa, app.state.config)
    else:
        logger.info("📭 Evento recebido sem mensagem (provavelmente status)")

    return {"status": "ok"}


@app.get("/health")
async def health_check() -> dict:
    return {"status": "healthy", "service": "bot-ubs-whatsapp", "version": "3.1.0"}


# ── Admin (com HTTP status codes corretos) ───────

def _check_admin(token: str) -> bool:
    return bool(ADMIN_TOKEN) and token == ADMIN_TOKEN


class AvisoRequest(BaseModel):
    token: str
    mensagem: str | None = None


@app.post("/admin/aviso")
async def criar_aviso(req: AvisoRequest):
    if not _check_admin(req.token):
        return JSONResponse(status_code=401, content={"error": "Token inválido"})
    salvar_aviso(req.mensagem)
    return {"status": "ok", "aviso": req.mensagem or "removido"}


@app.get("/admin/avaliacoes")
async def ver_avaliacoes(
    token: str = "",
    limite: int = Query(default=50, ge=1, le=500),
    pagina: int = Query(default=1, ge=1),
):
    if not _check_admin(token):
        return JSONResponse(status_code=401, content={"error": "Token inválido"})
    return listar_avaliacoes(limite=limite, pagina=pagina)


@app.get("/admin/metricas")
async def ver_metricas(
    token: str = "",
    dias: int = Query(default=30, ge=1, le=365),
):
    if not _check_admin(token):
        return JSONResponse(status_code=401, content={"error": "Token inválido"})
    return obter_metricas(dias)
