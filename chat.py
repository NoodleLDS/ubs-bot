"""
💬 Simulador de Chat — Bot UBS v3.0
"""

import json
import os
import asyncio

def load_config():
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

CONFIG = load_config()

# Inicializa banco SQLite
from utils.database import init_db
init_db()


class FakeWhatsApp:
    async def send_text(self, to, body):
        _print_msg(body)
        return {}

    async def send_list(self, to, body, button_label, sections, header=None, footer=None):
        _print_msg(body)
        print("│                                     │")
        print(f"│  📌 {button_label}")
        print("├─────────────────────────────────────┤")
        n = 1
        for section in sections:
            print(f"│  ── {section['title']} ──")
            for row in section["rows"]:
                desc = row.get("description", "")
                print(f"│   {n}) {row['title']}")
                if desc:
                    print(f"│      {desc}")
                n += 1
        if footer:
            print("│")
            _print_line(footer)
        print("└─────────────────────────────────────┘")
        return {}

    async def send_buttons(self, to, body, buttons, header=None):
        _print_msg(body)
        print("├─────────────────────────────────────┤")
        for i, btn in enumerate(buttons, 1):
            print(f"│   {i}) {btn['title']}")
        print("└─────────────────────────────────────┘")
        return {}

    async def mark_as_read(self, message_id):
        return {}


def _print_msg(body):
    print()
    print("┌─────────────────────────────────────┐")
    print("│  🤖 BOT UBS                         │")
    print("├─────────────────────────────────────┤")
    for line in body.split("\n"):
        _print_line(line)

def _print_line(line):
    formatted = line
    while "*" in formatted:
        formatted = formatted.replace("*", "[", 1).replace("*", "]", 1)
    print(f"│  {formatted}")


from handlers.menu import handle_menu, handle_sub_programas, handle_sub_servicos, handle_sub_orientacoes
from handlers.info import handle_hoje, handle_unidades, handle_equipe, handle_documentos
from handlers.programas import handle_hiperdia, handle_prenatal, handle_puericultura, handle_vacinacao, handle_saude_mulher
from handlers.exames import handle_exame_sangue, handle_farmacia
from handlers.saude import handle_educacao, handle_saude_bucal, handle_saude_mental, handle_saude_idoso, handle_fisioterapia
from handlers.grupos import handle_grupos
from handlers.emergencia import handle_emergencia, handle_faq
from handlers.nivel3 import handle_pesquisa, handle_pesquisa_nota, handle_pesquisa_comentario
from handlers.media import handle_unsupported_media
from utils.session import session_manager

MENU_TRIGGERS = {"menu", "oi", "olá", "ola", "início", "inicio", "ajuda", "voltar", ""}

MAIN_MENU = [
    ("HOJE", handle_hoje),
    ("UNIDADES", handle_unidades),
    ("EQUIPE", handle_equipe),
    ("SUB_PROGRAMAS", handle_sub_programas),
    ("SUB_SERVICOS", handle_sub_servicos),
    ("SUB_ORIENTACOES", handle_sub_orientacoes),
    ("GRUPOS", handle_grupos),
    ("EMERGENCIA", handle_emergencia),
    ("FAQ", handle_faq),
    ("PESQUISA", handle_pesquisa),
]

SUB_PROGRAMAS = [
    ("PROG_HIPERDIA", handle_hiperdia),
    ("PROG_PRENATAL", handle_prenatal),
    ("PROG_PUERICULTURA", handle_puericultura),
    ("PROG_VACINACAO", handle_vacinacao),
    ("PROG_SAUDE_MULHER", handle_saude_mulher),
]

SUB_SERVICOS = [
    ("EXAME_SANGUE", handle_exame_sangue),
    ("FARMACIA", handle_farmacia),
    ("DOCUMENTOS", handle_documentos),
]

SUB_ORIENTACOES = [
    ("EDUCACAO", handle_educacao),
    ("SAUDE_BUCAL", handle_saude_bucal),
    ("SAUDE_MENTAL", handle_saude_mental),
    ("SAUDE_IDOSO", handle_saude_idoso),
    ("FISIOTERAPIA", handle_fisioterapia),
]


async def main():
    wa = FakeWhatsApp()
    phone = "5534999990000"
    current_submenu = None

    os.system("cls" if os.name == "nt" else "clear")

    print("=" * 45)
    print("  💬 SIMULADOR DE CHAT — BOT UBS v3.0")
    print("  Converse como se fosse um paciente")
    print("=" * 45)
    print()
    print("  Comandos:")
    print("    [número]  → seleciona opção")
    print("    menu      → volta ao menu principal")
    print("    voltar    → volta ao menu/submenu")
    print("    sair      → encerra o chat")
    print()
    print("─" * 45)

    await handle_menu(phone, wa, CONFIG)

    while True:
        print()
        try:
            user_input = input("  📱 Você: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\n  👋 Até mais! Cuide-se.")
            break

        if user_input.lower() == "sair":
            print("\n  👋 Até mais! Cuide-se.")
            break

        session = session_manager.get(phone)

        if session.state == "PESQUISA_NOTA":
            if user_input.lower() in MENU_TRIGGERS:
                session_manager.reset(phone)
                current_submenu = None
                await handle_menu(phone, wa, CONFIG)
                continue
            nota_map = {"1": "NOTA_1", "2": "NOTA_3", "3": "NOTA_5"}
            content = nota_map.get(user_input, user_input)
            await handle_pesquisa_nota(phone, wa, content, CONFIG)
            continue

        if session.state == "PESQUISA_COMENTARIO":
            if user_input.lower() in MENU_TRIGGERS:
                session_manager.reset(phone)
                current_submenu = None
                await handle_menu(phone, wa, CONFIG)
                continue
            await handle_pesquisa_comentario(phone, wa, user_input, CONFIG)
            current_submenu = None
            continue

        if user_input.lower() in MENU_TRIGGERS:
            current_submenu = None
            await handle_menu(phone, wa, CONFIG)
            continue

        if user_input.isdigit():
            num = int(user_input)

            if current_submenu == "programas":
                if 1 <= num <= len(SUB_PROGRAMAS):
                    _, handler = SUB_PROGRAMAS[num - 1]
                    await handler(phone, wa, CONFIG)
                    continue
            elif current_submenu == "servicos":
                if 1 <= num <= len(SUB_SERVICOS):
                    _, handler = SUB_SERVICOS[num - 1]
                    await handler(phone, wa, CONFIG)
                    continue
            elif current_submenu == "orientacoes":
                if 1 <= num <= len(SUB_ORIENTACOES):
                    _, handler = SUB_ORIENTACOES[num - 1]
                    await handler(phone, wa, CONFIG)
                    continue
            else:
                if 1 <= num <= len(MAIN_MENU):
                    route_id, handler = MAIN_MENU[num - 1]
                    if route_id == "SUB_PROGRAMAS":
                        current_submenu = "programas"
                    elif route_id == "SUB_SERVICOS":
                        current_submenu = "servicos"
                    elif route_id == "SUB_ORIENTACOES":
                        current_submenu = "orientacoes"
                    else:
                        current_submenu = None
                    await handler(phone, wa, CONFIG)
                    continue

            print("\n  ⚠️  Opção inválida. Digite *menu* para ver as opções.")
            continue

        print("\n  💡 Não entendi. Mostrando o menu...")
        current_submenu = None
        await handle_menu(phone, wa, CONFIG)


if __name__ == "__main__":
    asyncio.run(main())
