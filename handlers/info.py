"""
Informações da UBS: horário dinâmico com sextas alternadas reais,
unidades, equipe, documentos, saúde da mulher com dias calculados.
"""

from datetime import datetime
from services.whatsapp import WhatsAppService

DIAS_SEMANA = {0: "segunda", 1: "terca", 2: "quarta", 3: "quinta", 4: "sexta", 5: "sabado", 6: "domingo"}
DIAS_DISPLAY = {0: "Segunda-feira", 1: "Terça-feira", 2: "Quarta-feira", 3: "Quinta-feira", 4: "Sexta-feira", 5: "Sábado", 6: "Domingo"}
DIAS_DISPLAY_CURTO = {"segunda": "Segunda", "terca": "Terça", "quarta": "Quarta", "quinta": "Quinta", "sexta": "Sexta"}

# Referência: sexta 20/03/2026 (semana ISO 12, par) = Capela
SEMANA_REFERENCIA_CAPELA = 12


def _sexta_local_hoje() -> str:
    hoje = datetime.now()
    semana_iso = hoje.isocalendar()[1]
    if (semana_iso % 2) == (SEMANA_REFERENCIA_CAPELA % 2):
        return "capela"
    else:
        return "baixa"


def _quem_atende_hoje(config: dict) -> tuple[str, list, list]:
    hoje = datetime.now().weekday()
    dia_key = DIAS_SEMANA[hoje]
    dia_display = DIAS_DISPLAY[hoje]

    if hoje >= 5:
        return dia_display, [], []

    capela = []
    baixa = []

    for p in config["profissionais"]:
        nome_funcao = f"{p['nome']} ({p['funcao']})"

        if dia_key == "sexta":
            if p.get("sexta_alternada"):
                local = _sexta_local_hoje()
                if local == "capela":
                    capela.append(nome_funcao)
                else:
                    baixa.append(nome_funcao)
            else:
                if dia_key in p.get("fixo_capela", []):
                    capela.append(nome_funcao)
                if dia_key in p.get("fixo_baixa", []):
                    baixa.append(nome_funcao)
        else:
            if dia_key in p.get("fixo_capela", []):
                capela.append(nome_funcao)
            if dia_key in p.get("fixo_baixa", []):
                baixa.append(nome_funcao)

    return dia_display, capela, baixa


def _calcular_dias_saude_mulher(config: dict) -> dict[str, list[str]]:
    """
    Calcula em quais dias Lucas (enfermeiro) e Natalia (médica)
    estão na mesma unidade — esses são os dias de saúde da mulher.
    Retorna {"capela": ["Quarta", ...], "baixa": ["Terça", ...]}.
    """
    lucas = None
    natalia = None
    for p in config["profissionais"]:
        if "Lucas" in p["nome"]:
            lucas = p
        if "Natalia" in p["nome"]:
            natalia = p

    if not lucas or not natalia:
        return {"capela": [], "baixa": []}

    result = {"capela": [], "baixa": []}

    for dia_key, dia_nome in DIAS_DISPLAY_CURTO.items():
        if dia_key == "sexta":
            continue  # Sexta é alternada, tratamos separado

        lucas_capela = dia_key in lucas.get("fixo_capela", [])
        natalia_capela = dia_key in natalia.get("fixo_capela", [])
        lucas_baixa = dia_key in lucas.get("fixo_baixa", [])
        natalia_baixa = dia_key in natalia.get("fixo_baixa", [])

        if lucas_capela and natalia_capela:
            result["capela"].append(dia_nome)
        if lucas_baixa and natalia_baixa:
            result["baixa"].append(dia_nome)

    # Sextas alternadas: ambos são sexta_alternada, então sempre juntos
    if lucas.get("sexta_alternada") and natalia.get("sexta_alternada"):
        result["capela"].append("Sextas alternadas")
        result["baixa"].append("Sextas alternadas")

    return result


async def handle_hoje(phone: str, wa: WhatsAppService, config: dict) -> None:
    dia_display, capela, baixa = _quem_atende_hoje(config)

    if not capela and not baixa:
        msg = (
            f"📅 *{dia_display}*\n"
            "─────────────────────\n\n"
            "🔒 Hoje as unidades estão *fechadas*.\n\n"
            "Funcionamos de segunda a sexta, das 07:00 às 17:00.\n\n"
            "🚨 Em caso de urgência, ligue *192* (SAMU).\n"
            "─────────────────────\n"
            "Digite *menu* para voltar."
        )
    else:
        txt_capela = "\n".join(f"   👤 {p}" for p in capela) if capela else "   Nenhum profissional hoje"
        txt_baixa = "\n".join(f"   👤 {p}" for p in baixa) if baixa else "   Nenhum profissional hoje"

        sexta_info = ""
        if datetime.now().weekday() == 4:
            local = _sexta_local_hoje()
            outra = "Baixa" if local == "capela" else "Capela"
            sexta_info = (
                f"\n📌 Hoje é *sexta alternada*.\n"
                f"Profissionais alternados estão na *{local.capitalize()}*.\n"
                f"Próxima sexta estarão na *{outra}*.\n"
            )

        msg = (
            f"📅 *QUEM ATENDE HOJE — {dia_display.upper()}*\n"
            "─────────────────────\n\n"
            "📍 *Capelinha do Barreiro:*\n"
            f"{txt_capela}\n\n"
            "📍 *Distrito da Baixa:*\n"
            f"{txt_baixa}\n"
            f"{sexta_info}\n"
            "🕐 Horário: 07:00 às 17:00\n"
            "─────────────────────\n"
            "Digite *menu* para voltar."
        )

    await wa.send_text(to=phone, body=msg)


async def handle_unidades(phone: str, wa: WhatsAppService, config: dict) -> None:
    cap = config["unidades"]["capela"]
    bx = config["unidades"]["baixa"]

    msg = (
        "📍 *NOSSAS UNIDADES*\n"
        "─────────────────────\n\n"
        f"🏥 *{cap['nome']}*\n"
        f"📍 {cap['endereco']}\n"
        f"📞 {cap['telefone']}\n"
        f"🕐 {cap['horario']}\n"
        f"🗺️ Google Maps: {cap['maps']}\n\n"
        "─────────────────────\n\n"
        f"🏥 *{bx['nome']}*\n"
        f"📍 {bx['endereco']}\n"
        f"📞 {bx['telefone']}\n"
        f"🕐 {bx['horario']}\n"
        f"🗺️ Google Maps: {bx['maps']}\n\n"
        "─────────────────────\n"
        "Digite *menu* para voltar."
    )

    await wa.send_text(to=phone, body=msg)


async def handle_equipe(phone: str, wa: WhatsAppService, config: dict) -> None:
    profissionais = config["profissionais"]
    linhas = []
    for p in profissionais:
        linhas.append(
            f"👤 *{p['nome']}* — {p['funcao']}\n"
            f"   📍 Capela: {p['dias_capela']}\n"
            f"   📍 Baixa: {p['dias_baixa']}"
        )

    lista = "\n\n".join(linhas)
    msg = (
        "👩‍⚕️ *EQUIPE DE PROFISSIONAIS*\n"
        f"👥 {config['equipe']}\n"
        "─────────────────────\n\n"
        f"{lista}\n\n"
        "─────────────────────\n"
        "📍 *Capela* = Capelinha do Barreiro\n"
        "📍 *Baixa* = Distrito da Baixa\n\n"
        "Digite *menu* para voltar."
    )
    await wa.send_text(to=phone, body=msg)


async def handle_documentos(phone: str, wa: WhatsAppService, config: dict) -> None:
    docs = config["documentos_cadastro"]
    lista = "\n".join(f"✅ {d}" for d in docs["lista"])
    msg = (
        "📄 *DOCUMENTOS PARA CADASTRO*\n"
        "─────────────────────\n\n"
        f"{docs['descricao']}\n\n"
        f"{lista}\n\n"
        "📍 Procure a recepção de qualquer uma das unidades.\n"
        "─────────────────────\n"
        "Digite *menu* para voltar."
    )
    await wa.send_text(to=phone, body=msg)
