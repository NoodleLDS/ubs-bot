"""
Validação do config.json com Pydantic.
Se faltar um campo, dá erro claro em vez de KeyError genérico.
"""

import json
import logging
from pydantic import BaseModel, field_validator

logger = logging.getLogger(__name__)


class UnidadeConfig(BaseModel):
    nome: str
    endereco: str
    telefone: str
    horario: str
    maps: str = ""


class ProfissionalConfig(BaseModel):
    nome: str
    funcao: str
    dias_capela: str
    dias_baixa: str
    fixo_capela: list[str] = []
    fixo_baixa: list[str] = []
    sexta_alternada: bool = False
    model_config = {"extra": "allow"}  # Permite campos extras como _obs


class ProgramaConfig(BaseModel):
    nome: str
    descricao: str
    dia: str
    horario: str
    orientacoes: list[str]


class ExameConfig(BaseModel):
    nome: str
    dia: str
    horario: str
    preparo: list[str]


class FarmaciaConfig(BaseModel):
    descricao: str
    dia: str
    horario: str
    opcoes: list[str]
    documentos: list[str]


class GrupoConfig(BaseModel):
    nome: str
    emoji: str
    descricao: str
    frequencia: str
    responsavel: str


class UPAConfig(BaseModel):
    nome: str
    telefone: str = ""
    endereco: str = ""


class EmergenciaConfig(BaseModel):
    upas: list[UPAConfig]
    hospitais_gestante: list[str]
    samu: str = "192"
    bombeiros: str = "193"


class FAQConfig(BaseModel):
    pergunta: str
    resposta: str


class DocumentosConfig(BaseModel):
    titulo: str
    descricao: str
    lista: list[str]


class TopicoSaudeConfig(BaseModel):
    emoji: str
    titulo: str
    dica: str


class EducacaoConfig(BaseModel):
    titulo: str
    topicos: list[TopicoSaudeConfig]


class ServicoSaudeConfig(BaseModel):
    titulo: str
    profissional: str = ""
    descricao: str
    servicos: list[str] = []
    dicas: list[str] = []
    quando_procurar: list[str] = []
    cuidados: list[str] = []
    direitos: list[str] = []
    agendamento: str = ""
    como_agendar: str = ""
    mensagem: str = ""
    dica: str = ""


class SaudeConfig(BaseModel):
    educacao: EducacaoConfig
    bucal: ServicoSaudeConfig
    mental: ServicoSaudeConfig
    idoso: ServicoSaudeConfig
    fisioterapia: ServicoSaudeConfig


class BotConfig(BaseModel):
    """Schema completo do config.json."""

    unidades: dict[str, UnidadeConfig]
    equipe: str
    profissionais: list[ProfissionalConfig]
    programas: dict[str, ProgramaConfig]
    exames: dict[str, ExameConfig]
    farmacia: FarmaciaConfig
    grupos: list[GrupoConfig]
    emergencia: EmergenciaConfig
    faq: list[FAQConfig]
    documentos_cadastro: DocumentosConfig
    saude: SaudeConfig

    @field_validator("unidades")
    @classmethod
    def validar_unidades(cls, v):
        if "capela" not in v or "baixa" not in v:
            raise ValueError("config.json deve ter as unidades 'capela' e 'baixa'")
        return v

    @field_validator("profissionais")
    @classmethod
    def validar_profissionais(cls, v):
        if len(v) == 0:
            raise ValueError("config.json deve ter pelo menos 1 profissional")
        return v


def load_and_validate_config(config_path: str) -> dict:
    """Carrega e valida o config.json. Retorna o dict original."""
    with open(config_path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    try:
        BotConfig(**raw)
        logger.info("✅ config.json validado com sucesso")
    except Exception as exc:
        logger.error("❌ Erro de validação no config.json: %s", exc)
        raise SystemExit(f"Config inválido: {exc}") from exc

    return raw
