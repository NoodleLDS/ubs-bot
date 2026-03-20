"""
Menu principal e submenus da UBS.
Aviso ativo vem do banco de dados (SQLite).
"""

from services.whatsapp import WhatsAppService
from utils.database import obter_aviso_ativo


async def handle_menu(phone: str, wa: WhatsAppService, config: dict) -> None:
    equipe = config["equipe"]

    aviso = obter_aviso_ativo()
    aviso_txt = f"\n\n📢 *AVISO:* {aviso}\n" if aviso else ""

    body = (
        f"🏥 *{equipe}*\n"
        "─────────────────────\n"
        "Olá! Bem-vindo(a) ao atendimento virtual.\n\n"
        "📍 Capelinha do Barreiro\n"
        "📍 Distrito da Baixa"
        f"{aviso_txt}\n\n"
        "Selecione uma opção:"
    )

    sections = [
        {
            "title": "📋 Informações",
            "rows": [
                {"id": "HOJE", "title": "📅 Quem atende hoje", "description": "Profissionais do dia"},
                {"id": "UNIDADES", "title": "📍 Nossas unidades", "description": "Endereço, telefone, como chegar"},
                {"id": "EQUIPE", "title": "👩‍⚕️ Equipe completa", "description": "Todos os profissionais"},
            ],
        },
        {
            "title": "🏥 Saúde",
            "rows": [
                {"id": "SUB_PROGRAMAS", "title": "💊 Programas de saúde", "description": "HiperDia, Pré-Natal, Vacina..."},
                {"id": "SUB_SERVICOS", "title": "🔬 Exames e farmácia", "description": "Coleta, medicamentos, docs"},
                {"id": "SUB_ORIENTACOES", "title": "📚 Orientações de saúde", "description": "Bucal, mental, idoso, fisio..."},
                {"id": "GRUPOS", "title": "📅 Grupos da UBS", "description": "Gestantes, HiperDia, Tabagismo"},
            ],
        },
        {
            "title": "❓ Ajuda",
            "rows": [
                {"id": "EMERGENCIA", "title": "🚨 Urgência/Emergência", "description": "UPA, SAMU, hospitais"},
                {"id": "FAQ", "title": "❓ Dúvidas frequentes", "description": "Cartão SUS, agendamento..."},
                {"id": "PESQUISA", "title": "⭐ Avalie o atendimento", "description": "Sua opinião é importante"},
            ],
        },
    ]

    await wa.send_list(
        to=phone,
        body=body,
        button_label="📌 Ver opções",
        sections=sections,
        footer="Digite *menu* a qualquer momento para voltar.",
    )


async def handle_sub_programas(phone: str, wa: WhatsAppService, config: dict) -> None:
    sections = [
        {
            "title": "💊 Programas de Saúde",
            "rows": [
                {"id": "PROG_HIPERDIA", "title": "❤️ HiperDia", "description": "Hipertensão e Diabetes"},
                {"id": "PROG_PRENATAL", "title": "🤰 Pré-Natal", "description": "Acompanhamento da gestante"},
                {"id": "PROG_PUERICULTURA", "title": "👶 Puericultura", "description": "Saúde da criança (0–2 anos)"},
                {"id": "PROG_VACINACAO", "title": "💉 Vacinação", "description": "Calendário e sala de vacina"},
                {"id": "PROG_SAUDE_MULHER", "title": "🩷 Saúde da Mulher", "description": "Preventivo / Papanicolau"},
            ],
        },
    ]
    await wa.send_list(
        to=phone,
        body="💊 *PROGRAMAS DE SAÚDE*\n─────────────────────\nEscolha o programa para ver informações:",
        button_label="📌 Ver programas",
        sections=sections,
        footer="Digite *menu* para voltar ao início.",
    )


async def handle_sub_servicos(phone: str, wa: WhatsAppService, config: dict) -> None:
    sections = [
        {
            "title": "🔬 Serviços",
            "rows": [
                {"id": "EXAME_SANGUE", "title": "🩸 Coleta de sangue", "description": "Orientações e preparo"},
                {"id": "FARMACIA", "title": "💊 Farmácia / Medicamentos", "description": "Retirada de remédios"},
                {"id": "DOCUMENTOS", "title": "📄 Documentos p/ cadastro", "description": "O que trazer na UBS"},
            ],
        },
    ]
    await wa.send_list(
        to=phone,
        body="🔬 *EXAMES, FARMÁCIA E DOCUMENTOS*\n─────────────────────\nEscolha uma opção:",
        button_label="📌 Ver serviços",
        sections=sections,
        footer="Digite *menu* para voltar ao início.",
    )


async def handle_sub_orientacoes(phone: str, wa: WhatsAppService, config: dict) -> None:
    sections = [
        {
            "title": "📚 Orientações de Saúde",
            "rows": [
                {"id": "EDUCACAO", "title": "🍎 Dicas de saúde", "description": "Alimentação, exercícios, prevenção"},
                {"id": "SAUDE_BUCAL", "title": "🦷 Saúde bucal", "description": "Dentista Michel Vanderlei"},
                {"id": "SAUDE_MENTAL", "title": "🧠 Saúde mental", "description": "Psicóloga Queren Hapuque"},
                {"id": "SAUDE_IDOSO", "title": "🧓 Saúde do idoso", "description": "Acompanhamento 60+"},
                {"id": "FISIOTERAPIA", "title": "🏋️ Fisioterapia", "description": "Fisioterapeuta Gilda Mayumi"},
            ],
        },
    ]
    await wa.send_list(
        to=phone,
        body="📚 *ORIENTAÇÕES DE SAÚDE*\n─────────────────────\nEscolha um tema:",
        button_label="📌 Ver orientações",
        sections=sections,
        footer="Digite *menu* para voltar ao início.",
    )
