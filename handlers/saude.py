"""
Orientações de saúde: educação, bucal, mental, idoso, fisioterapia.
"""

from services.whatsapp import WhatsAppService


async def handle_educacao(phone: str, wa: WhatsAppService, config: dict) -> None:
    edu = config["saude"]["educacao"]
    topicos = "\n\n".join(
        f"{t['emoji']} *{t['titulo']}*\n{t['dica']}" for t in edu["topicos"]
    )
    msg = (
        f"🍎 *{edu['titulo'].upper()}*\n"
        "─────────────────────\n\n"
        f"{topicos}\n\n"
        "─────────────────────\n"
        "Cuide da sua saúde todos os dias. "
        "Procure a equipe da UBS para mais orientações.\n\n"
        "Digite *menu* para voltar."
    )
    await wa.send_text(to=phone, body=msg)


async def handle_saude_bucal(phone: str, wa: WhatsAppService, config: dict) -> None:
    sb = config["saude"]["bucal"]
    servicos = "\n".join(f"✅ {s}" for s in sb["servicos"])
    dicas = "\n".join(f"🦷 {d}" for d in sb["dicas"])
    msg = (
        f"🦷 *{sb['titulo'].upper()}*\n"
        "─────────────────────\n\n"
        f"👤 *{sb['profissional']}*\n\n"
        f"📋 {sb['descricao']}\n\n"
        "📌 *Serviços disponíveis:*\n"
        f"{servicos}\n\n"
        "💡 *Dicas de cuidado:*\n"
        f"{dicas}\n\n"
        f"📅 {sb['agendamento']}\n"
        "─────────────────────\n"
        "Digite *menu* para voltar."
    )
    await wa.send_text(to=phone, body=msg)


async def handle_saude_mental(phone: str, wa: WhatsAppService, config: dict) -> None:
    sm = config["saude"]["mental"]
    sinais = "\n".join(f"   • {s}" for s in sm["quando_procurar"])
    msg = (
        f"🧠 *{sm['titulo'].upper()}*\n"
        "─────────────────────\n\n"
        f"👤 *{sm['profissional']}*\n\n"
        f"📋 {sm['descricao']}\n\n"
        "📌 *Quando procurar ajuda:*\n"
        f"{sinais}\n\n"
        f"📅 *Como agendar:*\n{sm['como_agendar']}\n\n"
        f"{sm['mensagem']}\n"
        "─────────────────────\n"
        "Digite *menu* para voltar."
    )
    await wa.send_text(to=phone, body=msg)


async def handle_saude_idoso(phone: str, wa: WhatsAppService, config: dict) -> None:
    si = config["saude"]["idoso"]
    cuidados = "\n".join(f"✅ {c}" for c in si["cuidados"])
    direitos = "\n".join(f"⚖️ {d}" for d in si["direitos"])
    msg = (
        f"🧓 *{si['titulo'].upper()}*\n"
        "─────────────────────\n\n"
        f"📋 {si['descricao']}\n\n"
        "📌 *Cuidados importantes:*\n"
        f"{cuidados}\n\n"
        "⚖️ *Direitos da pessoa idosa no SUS:*\n"
        f"{direitos}\n\n"
        f"💡 {si['dica']}\n"
        "─────────────────────\n"
        "Digite *menu* para voltar."
    )
    await wa.send_text(to=phone, body=msg)


async def handle_fisioterapia(phone: str, wa: WhatsAppService, config: dict) -> None:
    fi = config["saude"]["fisioterapia"]
    servicos = "\n".join(f"✅ {s}" for s in fi["servicos"])
    msg = (
        f"🏋️ *{fi['titulo'].upper()}*\n"
        "─────────────────────\n\n"
        f"👤 *{fi['profissional']}*\n\n"
        f"📋 {fi['descricao']}\n\n"
        "📌 *Serviços disponíveis:*\n"
        f"{servicos}\n\n"
        f"📅 {fi['agendamento']}\n\n"
        f"💡 {fi['dica']}\n"
        "─────────────────────\n"
        "Digite *menu* para voltar."
    )
    await wa.send_text(to=phone, body=msg)
