"""
Grupos e atividades coletivas da UBS.
"""

from services.whatsapp import WhatsAppService


async def handle_grupos(phone: str, wa: WhatsAppService, config: dict) -> None:
    grupos = config["grupos"]

    blocos = []
    for g in grupos:
        blocos.append(
            f"{g['emoji']} *{g['nome']}*\n"
            f"   {g['descricao']}\n"
            f"   {g['frequencia']}\n"
            f"   👤 {g['responsavel']}"
        )

    lista = "\n\n".join(blocos)

    msg = (
        "📅 *GRUPOS DA UBS*\n"
        "─────────────────────\n\n"
        f"{lista}\n\n"
        "─────────────────────\n"
        "📌 Para participar, procure a recepção ou "
        "converse com qualquer profissional da equipe.\n\n"
        "Todos os grupos são *gratuitos* e abertos à "
        "comunidade.\n\n"
        "Digite *menu* para voltar."
    )

    await wa.send_text(to=phone, body=msg)
