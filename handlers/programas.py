"""
Handler dos programas de saúde da UBS.
"""

from services.whatsapp import WhatsAppService

EMOJIS = {
    "hiperdia": "❤️",
    "prenatal": "🤰",
    "puericultura": "👶",
    "vacinacao": "💉",
    "saude_mulher": "🩷",
}


async def _send_programa(phone, wa, programa, emoji):
    orientacoes = "\n".join(f"✅ {o}" for o in programa["orientacoes"])
    msg = (
        f"{emoji} *{programa['nome'].upper()}*\n"
        "─────────────────────\n\n"
        f"📋 *O que é:*\n{programa['descricao']}\n\n"
        f"📅 *Dia:* {programa['dia']}\n"
        f"🕐 *Horário:* {programa['horario']}\n\n"
        "📌 *O que trazer / orientações:*\n"
        f"{orientacoes}\n\n"
        "─────────────────────\n"
        "Digite *menu* para voltar."
    )
    await wa.send_text(to=phone, body=msg)


async def handle_hiperdia(phone, wa, config):
    await _send_programa(phone, wa, config["programas"]["hiperdia"], EMOJIS["hiperdia"])

async def handle_prenatal(phone, wa, config):
    await _send_programa(phone, wa, config["programas"]["prenatal"], EMOJIS["prenatal"])

async def handle_puericultura(phone, wa, config):
    await _send_programa(phone, wa, config["programas"]["puericultura"], EMOJIS["puericultura"])

async def handle_vacinacao(phone, wa, config):
    await _send_programa(phone, wa, config["programas"]["vacinacao"], EMOJIS["vacinacao"])

async def handle_saude_mulher(phone, wa, config):
    from handlers.info import _calcular_dias_saude_mulher
    prog = config["programas"]["saude_mulher"]
    orientacoes = "\n".join(f"✅ {o}" for o in prog["orientacoes"])

    dias = _calcular_dias_saude_mulher(config)
    dias_capela = ", ".join(dias["capela"]) if dias["capela"] else "Verificar na recepção"
    dias_baixa = ", ".join(dias["baixa"]) if dias["baixa"] else "Verificar na recepção"

    msg = (
        f"🩷 *{prog['nome'].upper()}*\n"
        "─────────────────────\n\n"
        f"📋 *O que é:*\n{prog['descricao']}\n\n"
        "📅 *Dias disponíveis:*\n"
        f"   📍 Capela: {dias_capela}\n"
        f"   📍 Baixa: {dias_baixa}\n\n"
        f"🕐 *Horário:* {prog['horario']}\n\n"
        "📌 *O que trazer / orientações:*\n"
        f"{orientacoes}\n\n"
        "─────────────────────\n"
        "Digite *menu* para voltar."
    )
    await wa.send_text(to=phone, body=msg)
