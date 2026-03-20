"""
Nível 3 — Funcionalidades inteligentes:
  - Pesquisa de satisfação (SQLite)
  - Avisos/campanhas (SQLite)
  - IA para dúvidas (placeholder)
"""

import logging
from services.whatsapp import WhatsAppService
from utils.session import session_manager
from utils.database import salvar_avaliacao, salvar_aviso

logger = logging.getLogger(__name__)


# ── Pesquisa de satisfação ───────────────────────

async def handle_pesquisa(phone: str, wa: WhatsAppService, config: dict) -> None:
    session_manager.set_state(phone, "PESQUISA_NOTA")

    await wa.send_buttons(
        to=phone,
        body=(
            "⭐ *AVALIE NOSSO ATENDIMENTO*\n"
            "─────────────────────\n\n"
            "Sua opinião nos ajuda a melhorar!\n\n"
            "De 1 a 5, como você avalia o atendimento "
            "da nossa equipe?\n\n"
            "1⭐ = Ruim\n"
            "3⭐ = Regular\n"
            "5⭐ = Excelente"
        ),
        buttons=[
            {"id": "NOTA_1", "title": "1 ⭐"},
            {"id": "NOTA_3", "title": "3 ⭐⭐⭐"},
            {"id": "NOTA_5", "title": "5 ⭐⭐⭐⭐⭐"},
        ],
    )


async def handle_pesquisa_nota(phone: str, wa: WhatsAppService, content: str, config: dict) -> None:
    notas = {"NOTA_1": 1, "NOTA_3": 3, "NOTA_5": 5}
    nota = notas.get(content, 0)

    if nota == 0:
        try:
            nota = int(content)
            if nota < 1 or nota > 5:
                nota = 0
        except ValueError:
            nota = 0

    if nota == 0:
        await wa.send_text(
            to=phone,
            body="⚠️ Nota inválida. Escolha uma das opções acima ou digite um número de 1 a 5."
        )
        return

    session = session_manager.get(phone)
    session.data["nota"] = nota
    session_manager.set_state(phone, "PESQUISA_COMENTARIO")

    await wa.send_text(
        to=phone,
        body=(
            f"Você deu nota *{nota}* {'⭐' * nota}\n\n"
            "Gostaria de deixar um comentário ou sugestão?\n\n"
            "📝 Digite seu comentário ou *pular* para finalizar."
        ),
    )


async def handle_pesquisa_comentario(phone: str, wa: WhatsAppService, content: str, config: dict) -> None:
    session = session_manager.get(phone)
    nota = session.data.get("nota", 0)
    comentario = "" if content.lower() in ("pular", "nao", "não", "n") else content

    # Salva no SQLite (anônimo)
    salvar_avaliacao(nota, comentario)
    session_manager.reset(phone)

    msg = (
        "✅ *Obrigado pela sua avaliação!*\n"
        "─────────────────────\n\n"
        f"Nota: {'⭐' * nota}\n"
    )
    if comentario:
        msg += f"Comentário: {comentario}\n\n"
    else:
        msg += "\n"

    msg += (
        "Sua opinião nos ajuda a melhorar o atendimento "
        "para toda a comunidade. 💛\n\n"
        "─────────────────────\n"
        "Digite *menu* para voltar."
    )

    await wa.send_text(to=phone, body=msg)


# ── IA para dúvidas (placeholder) ────────────────

async def handle_ia_duvida(phone: str, wa: WhatsAppService, content: str, config: dict) -> None:
    msg = (
        "🤖 *ASSISTENTE VIRTUAL*\n"
        "─────────────────────\n\n"
        "Essa funcionalidade está sendo preparada!\n\n"
        "Em breve você poderá fazer perguntas sobre saúde "
        "e receber orientações automáticas.\n\n"
        "Por enquanto, confira nossas opções no menu ou "
        "entre em contato:\n\n"
        "📞 Capelinha: (34) 3338-1123\n"
        "📞 Baixa: (34) 3326-3071\n"
        "─────────────────────\n"
        "Digite *menu* para voltar."
    )
    await wa.send_text(to=phone, body=msg)
