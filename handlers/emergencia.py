"""
Urgência/Emergência e Dúvidas Frequentes.
FAQ enviada como texto (não lista interativa) para evitar limite de 1024 chars.
"""

from services.whatsapp import WhatsAppService

MAX_MSG_LENGTH = 4000  # Limite seguro para mensagens de texto do WhatsApp


async def handle_emergencia(phone: str, wa: WhatsAppService, config: dict) -> None:
    emerg = config["emergencia"]

    upas = "\n".join(
        f"🏥 *{u['nome']}*\n   📞 {u.get('telefone', '')}\n   📍 {u.get('endereco', '')}"
        for u in emerg["upas"]
    )
    hospitais = "\n".join(f"🏥 {h}" for h in emerg["hospitais_gestante"])

    msg = (
        "🚨 *URGÊNCIA E EMERGÊNCIA*\n"
        "─────────────────────\n\n"
        "⚠️ *A UBS NÃO é pronto-socorro.*\n"
        "Atendemos de seg. a sex., 07h às 17h.\n\n"
        "🔴 *Ligue imediatamente se:*\n"
        "   • Dor no peito ou falta de ar intensa\n"
        "   • AVC (boca torta, braço fraco, fala arrastada)\n"
        "   • Convulsão\n"
        "   • Hemorragia que não para\n"
        "   • Acidente grave\n"
        "   • Perda de consciência\n\n"
        f"📞 *SAMU:* {emerg['samu']} (24 horas)\n"
        f"📞 *Bombeiros:* {emerg['bombeiros']}\n\n"
        "─────────────────────\n"
        "🟡 *UPAs de referência:*\n"
        f"{upas}\n\n"
        "─────────────────────\n"
        "🤰 *Gestantes — Porta Aberta:*\n"
        f"{hospitais}\n\n"
        "─────────────────────\n"
        "🟢 *Quando procurar a UBS:*\n"
        "   • Febre leve, gripe, dor de garganta\n"
        "   • Curativo simples\n"
        "   • Acompanhamento de rotina\n"
        "   • Vacinas e exames\n\n"
        "Na dúvida, ligue para a UBS.\n"
        "─────────────────────\n"
        "Digite *menu* para voltar."
    )

    await wa.send_text(to=phone, body=msg)


async def handle_faq(phone: str, wa: WhatsAppService, config: dict) -> None:
    """FAQ enviada como texto simples. Se passar do limite, divide em partes."""
    faqs = config["faq"]

    blocos = []
    for i, faq in enumerate(faqs, 1):
        blocos.append(f"*{i}. {faq['pergunta']}*\n➡️ {faq['resposta']}")

    header = "❓ *DÚVIDAS FREQUENTES*\n─────────────────────\n\n"
    footer = (
        "\n─────────────────────\n"
        "Não encontrou sua dúvida?\n"
        "📞 Capelinha: (34) 3338-1123\n"
        "📞 Baixa: (34) 3326-3071\n\n"
        "Digite *menu* para voltar."
    )

    # Monta mensagem respeitando limite
    msg = header
    for bloco in blocos:
        if len(msg) + len(bloco) + len(footer) + 4 > MAX_MSG_LENGTH:
            # Envia a parte atual e começa nova
            await wa.send_text(to=phone, body=msg + "\n\n_(continua...)_")
            msg = ""
        msg += bloco + "\n\n"

    msg += footer
    await wa.send_text(to=phone, body=msg)
