"""
Handler para tipos de mensagem não suportados (áudio, foto, sticker, etc).
"""

from services.whatsapp import WhatsAppService


async def handle_unsupported_media(phone: str, wa: WhatsAppService, config: dict) -> None:
    """Informa que o bot só entende texto e mostra opções."""

    msg = (
        "⚠️ *Desculpe, só consigo entender mensagens de texto.*\n"
        "─────────────────────\n\n"
        "Não é possível processar áudios, fotos, vídeos ou stickers.\n\n"
        "📝 Por favor, digite sua dúvida ou escolha uma opção do menu.\n\n"
        "Se precisar falar com a equipe:\n"
        "📞 Capelinha: (34) 3338-1123\n"
        "📞 Baixa: (34) 3326-3071\n"
        "─────────────────────\n"
        "Digite *menu* para ver as opções."
    )

    await wa.send_text(to=phone, body=msg)
