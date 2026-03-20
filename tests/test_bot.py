"""
🧪 Testes automatizados — Bot UBS v3.0
========================================
Roda com: pytest tests/ -v
"""

import json
import os
import sys
import asyncio
import pytest

# Adiciona raiz do projeto ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ── Fixtures ─────────────────────────────────────

class FakeWhatsApp:
    """Mock do WhatsAppService que captura mensagens enviadas."""

    def __init__(self):
        self.messages = []

    async def send_text(self, to, body):
        self.messages.append({"type": "text", "to": to, "body": body})
        return {}

    async def send_list(self, to, body, button_label, sections, header=None, footer=None):
        self.messages.append({"type": "list", "to": to, "body": body, "sections": sections})
        return {}

    async def send_buttons(self, to, body, buttons, header=None):
        self.messages.append({"type": "buttons", "to": to, "body": body, "buttons": buttons})
        return {}

    async def mark_as_read(self, message_id):
        return {}

    @property
    def last(self):
        return self.messages[-1] if self.messages else None


@pytest.fixture
def wa():
    return FakeWhatsApp()


@pytest.fixture
def config():
    config_path = os.path.join(os.path.dirname(__file__), "..", "config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


PHONE = "5534999990000"


# ── Testes: Config Validator ─────────────────────

def test_config_valido(config):
    """Config.json deve ser válido contra o schema Pydantic."""
    from utils.config_validator import BotConfig
    bot = BotConfig(**config)
    assert "capela" in bot.unidades
    assert "baixa" in bot.unidades
    assert len(bot.profissionais) >= 1


def test_config_campo_faltando():
    """Config com campo faltando deve dar erro claro."""
    from utils.config_validator import BotConfig
    with pytest.raises(Exception):
        BotConfig(**{"unidades": {}})


# ── Testes: Segurança ────────────────────────────

def test_hmac_valido():
    from utils.security import verify_signature
    import hashlib, hmac as hmac_mod
    secret = "test_secret"
    payload = b'{"test": true}'
    sig = "sha256=" + hmac_mod.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    assert verify_signature(payload, sig, secret) is True


def test_hmac_invalido():
    from utils.security import verify_signature
    assert verify_signature(b"payload", "sha256=invalido", "secret") is False


def test_hmac_sem_secret():
    from utils.security import verify_signature
    # Sem secret configurado, deve permitir (modo dev)
    assert verify_signature(b"payload", "", "") is True


def test_rate_limiter():
    from utils.security import RateLimiter
    rl = RateLimiter(max_requests=3, window_seconds=60)
    assert rl.is_allowed("phone1") is True
    assert rl.is_allowed("phone1") is True
    assert rl.is_allowed("phone1") is True
    assert rl.is_allowed("phone1") is False  # Bloqueado
    assert rl.is_allowed("phone2") is True   # Outro número OK


# ── Testes: Database ─────────────────────────────

def test_database_init_e_avaliacao(tmp_path):
    os.environ["DB_PATH"] = str(tmp_path / "test.db")
    # Recarrega módulo com novo DB_PATH
    import importlib
    import utils.database as db_mod
    db_mod.DB_PATH = str(tmp_path / "test.db")
    importlib.reload(db_mod)

    db_mod.init_db()
    db_mod.salvar_avaliacao(5, "Excelente!")
    db_mod.salvar_avaliacao(3, "")

    result = db_mod.listar_avaliacoes()
    assert result["total"] == 2
    assert result["media"] == 4.0


def test_database_avisos(tmp_path):
    import utils.database as db_mod
    db_mod.DB_PATH = str(tmp_path / "test2.db")
    db_mod.init_db()

    assert db_mod.obter_aviso_ativo() is None

    db_mod.salvar_aviso("Campanha de vacinação!")
    assert db_mod.obter_aviso_ativo() == "Campanha de vacinação!"

    db_mod.salvar_aviso(None)  # Limpa
    assert db_mod.obter_aviso_ativo() is None


def test_database_metricas(tmp_path):
    import utils.database as db_mod
    db_mod.DB_PATH = str(tmp_path / "test3.db")
    db_mod.init_db()

    db_mod.registrar_acesso("MENU")
    db_mod.registrar_acesso("MENU")
    db_mod.registrar_acesso("HOJE")

    result = db_mod.obter_metricas(30)
    assert result["total_mensagens"] == 3
    assert result["top_rotas"][0]["rota"] == "MENU"


# ── Testes: Session ──────────────────────────────

def test_session_lifecycle():
    from utils.session import SessionManager
    sm = SessionManager()

    s = sm.get("phone1")
    assert s.state == "MENU"

    sm.set_state("phone1", "PESQUISA_NOTA")
    s = sm.get("phone1")
    assert s.state == "PESQUISA_NOTA"

    sm.reset("phone1")
    s = sm.get("phone1")
    assert s.state == "MENU"


# ── Testes: Handlers ─────────────────────────────

@pytest.mark.asyncio
async def test_handle_menu(wa, config):
    from handlers.menu import handle_menu
    await handle_menu(PHONE, wa, config)
    assert wa.last["type"] == "list"
    assert "ESF" in wa.last["body"]


@pytest.mark.asyncio
async def test_handle_hoje(wa, config):
    from handlers.info import handle_hoje
    await handle_hoje(PHONE, wa, config)
    assert wa.last["type"] == "text"
    # Deve conter dia da semana ou "fechadas"
    assert any(x in wa.last["body"] for x in ["QUEM ATENDE", "fechadas"])


@pytest.mark.asyncio
async def test_handle_unidades(wa, config):
    from handlers.info import handle_unidades
    await handle_unidades(PHONE, wa, config)
    assert "Capelinha" in wa.last["body"]
    assert "Baixa" in wa.last["body"]
    assert "maps" in wa.last["body"].lower() or "Maps" in wa.last["body"]


@pytest.mark.asyncio
async def test_handle_equipe(wa, config):
    from handlers.info import handle_equipe
    await handle_equipe(PHONE, wa, config)
    assert "Lucas Daniel" in wa.last["body"]
    assert "Natalia" in wa.last["body"]


@pytest.mark.asyncio
async def test_handle_emergencia(wa, config):
    from handlers.emergencia import handle_emergencia
    await handle_emergencia(PHONE, wa, config)
    assert "192" in wa.last["body"]  # SAMU
    assert "UPA" in wa.last["body"]
    assert "HC-UFTM" in wa.last["body"]


@pytest.mark.asyncio
async def test_handle_faq(wa, config):
    from handlers.emergencia import handle_faq
    await handle_faq(PHONE, wa, config)
    assert "Cartão SUS" in wa.last["body"]


@pytest.mark.asyncio
async def test_handle_farmacia(wa, config):
    from handlers.exames import handle_farmacia
    await handle_farmacia(PHONE, wa, config)
    assert "sexta" in wa.last["body"].lower()
    assert "receita" in wa.last["body"].lower()


@pytest.mark.asyncio
async def test_handle_grupos(wa, config):
    from handlers.grupos import handle_grupos
    await handle_grupos(PHONE, wa, config)
    assert "Gestantes" in wa.last["body"]
    assert "Tabagismo" in wa.last["body"]


@pytest.mark.asyncio
async def test_handle_saude_bucal(wa, config):
    from handlers.saude import handle_saude_bucal
    await handle_saude_bucal(PHONE, wa, config)
    assert "Michel" in wa.last["body"]


@pytest.mark.asyncio
async def test_handle_saude_mental(wa, config):
    from handlers.saude import handle_saude_mental
    await handle_saude_mental(PHONE, wa, config)
    assert "Queren" in wa.last["body"]


@pytest.mark.asyncio
async def test_handle_unsupported_media(wa, config):
    from handlers.media import handle_unsupported_media
    await handle_unsupported_media(PHONE, wa, config)
    assert "texto" in wa.last["body"].lower()


@pytest.mark.asyncio
async def test_handle_pesquisa(wa, config):
    from handlers.nivel3 import handle_pesquisa
    await handle_pesquisa(PHONE, wa, config)
    assert wa.last["type"] == "buttons"


@pytest.mark.asyncio
async def test_all_programas(wa, config):
    from handlers.programas import (
        handle_hiperdia, handle_prenatal, handle_puericultura,
        handle_vacinacao, handle_saude_mulher,
    )
    for handler in [handle_hiperdia, handle_prenatal, handle_puericultura, handle_vacinacao, handle_saude_mulher]:
        wa.messages.clear()
        await handler(PHONE, wa, config)
        assert wa.last is not None, f"{handler.__name__} não enviou mensagem"
        assert "menu" in wa.last["body"].lower(), f"{handler.__name__} não tem 'menu para voltar'"


@pytest.mark.asyncio
async def test_all_submenus(wa, config):
    from handlers.menu import handle_sub_programas, handle_sub_servicos, handle_sub_orientacoes
    for handler in [handle_sub_programas, handle_sub_servicos, handle_sub_orientacoes]:
        wa.messages.clear()
        await handler(PHONE, wa, config)
        assert wa.last["type"] == "list"


# ── Testes: Sexta alternada ──────────────────────

def test_sexta_alternada_logica():
    from handlers.info import _sexta_local_hoje, SEMANA_REFERENCIA_CAPELA
    # Semana de referência (12) é par e deve ser "capela"
    # A lógica compara paridade da semana atual com a referência
    # Testamos diretamente a paridade
    assert SEMANA_REFERENCIA_CAPELA % 2 == 0  # Semana 12 é par


# ── Testes: Payload parsing ──────────────────────

def test_parse_text():
    from main import parse_webhook_payload
    payload = {
        "entry": [{"changes": [{"value": {"messages": [
            {"from": "5534999", "id": "abc", "type": "text", "text": {"body": "oi"}}
        ]}}]}]
    }
    result = parse_webhook_payload(payload)
    assert result["type"] == "text"
    assert result["content"] == "oi"


def test_parse_list_reply():
    from main import parse_webhook_payload
    payload = {
        "entry": [{"changes": [{"value": {"messages": [
            {"from": "5534999", "id": "abc", "type": "interactive",
             "interactive": {"type": "list_reply", "list_reply": {"id": "HOJE", "title": "Hoje"}}}
        ]}}]}]
    }
    result = parse_webhook_payload(payload)
    assert result["type"] == "list"
    assert result["content"] == "HOJE"


def test_parse_unsupported():
    from main import parse_webhook_payload
    payload = {
        "entry": [{"changes": [{"value": {"messages": [
            {"from": "5534999", "id": "abc", "type": "image"}
        ]}}]}]
    }
    result = parse_webhook_payload(payload)
    assert result["type"] == "unsupported"
    assert result["content"] == "image"


def test_parse_empty():
    from main import parse_webhook_payload
    assert parse_webhook_payload({}) is None
    assert parse_webhook_payload({"entry": []}) is None
