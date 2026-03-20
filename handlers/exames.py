"""
Exames laboratoriais e dispensação de medicamentos.
"""

from services.whatsapp import WhatsAppService


async def handle_exame_sangue(phone: str, wa: WhatsAppService, config: dict) -> None:
    exame = config["exames"]["sangue"]
    preparo = "\n".join(f"✅ {item}" for item in exame["preparo"])
    msg = (
        "🩸 *COLETA DE SANGUE*\n"
        "─────────────────────\n\n"
        f"📋 *{exame['nome']}*\n\n"
        f"📅 *Dias:* {exame['dia']}\n"
        f"🕐 *Horário:* {exame['horario']}\n\n"
        "📌 *Preparo para o exame:*\n"
        f"{preparo}\n\n"
        "⚠️ Compareça no horário indicado. "
        "Caso perca o horário, será necessário reagendar.\n"
        "─────────────────────\n"
        "Digite *menu* para voltar."
    )
    await wa.send_text(to=phone, body=msg)


async def handle_farmacia(phone: str, wa: WhatsAppService, config: dict) -> None:
    farm = config["farmacia"]
    opcoes = "\n".join(f"  {i+1}️⃣ {o}" for i, o in enumerate(farm["opcoes"]))
    docs = "\n".join(f"✅ {d}" for d in farm["documentos"])

    msg = (
        "💊 *FARMÁCIA / MEDICAMENTOS*\n"
        "─────────────────────\n\n"
        f"📋 {farm['descricao']}\n\n"
        f"📅 *Dia:* {farm['dia']}\n"
        f"🕐 *Horário:* {farm['horario']}\n\n"
        "📌 *Como retirar sua medicação:*\n"
        f"{opcoes}\n\n"
        "📄 *Documentos necessários:*\n"
        f"{docs}\n\n"
        "⚠️ Antes de deixar a receita, confirme com a "
        "recepcionista se a medicação está disponível na "
        "prefeitura e se pode aguardar até sexta.\n"
        "─────────────────────\n"
        "Digite *menu* para voltar."
    )
    await wa.send_text(to=phone, body=msg)
