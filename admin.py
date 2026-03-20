"""
🔧 Painel Admin — Bot UBS
===========================
Gerencie o bot direto no terminal, sem precisar de curl.

python admin.py
"""

import os
import sys
import json

# Adiciona raiz ao path
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from utils.database import init_db, listar_avaliacoes, obter_metricas, salvar_aviso, obter_aviso_ativo

init_db()


def menu():
    while True:
        print()
        print("=" * 45)
        print("  🔧 PAINEL ADMIN — BOT UBS")
        print("=" * 45)
        print()
        print("  1) 📢 Criar aviso de campanha")
        print("  2) 🗑️  Remover aviso ativo")
        print("  3) 📢 Ver aviso ativo")
        print("  4) ⭐ Ver avaliações")
        print("  5) 📊 Ver métricas de uso")
        print("  6) ❌ Sair")
        print()

        opcao = input("  Escolha: ").strip()

        if opcao == "1":
            criar_aviso()
        elif opcao == "2":
            remover_aviso()
        elif opcao == "3":
            ver_aviso()
        elif opcao == "4":
            ver_avaliacoes()
        elif opcao == "5":
            ver_metricas()
        elif opcao == "6":
            print("\n  👋 Até mais!")
            break
        else:
            print("\n  ⚠️ Opção inválida.")


def criar_aviso():
    print("\n  📢 CRIAR AVISO DE CAMPANHA")
    print("  (Este aviso aparece no menu de TODOS os pacientes)")
    print()
    msg = input("  Mensagem do aviso: ").strip()
    if not msg:
        print("  ⚠️ Aviso vazio, cancelado.")
        return

    salvar_aviso(msg)
    print(f"\n  ✅ Aviso criado: {msg}")


def remover_aviso():
    aviso = obter_aviso_ativo()
    if not aviso:
        print("\n  ℹ️ Nenhum aviso ativo.")
        return

    print(f"\n  Aviso atual: {aviso}")
    confirmacao = input("  Remover? (s/n): ").strip().lower()
    if confirmacao == "s":
        salvar_aviso(None)
        print("  ✅ Aviso removido.")
    else:
        print("  Cancelado.")


def ver_aviso():
    aviso = obter_aviso_ativo()
    if aviso:
        print(f"\n  📢 Aviso ativo: {aviso}")
    else:
        print("\n  ℹ️ Nenhum aviso ativo no momento.")


def ver_avaliacoes():
    result = listar_avaliacoes(limite=20, pagina=1)
    print(f"\n  ⭐ AVALIAÇÕES (total: {result['total']} | média: {result['media']})")
    print("  " + "─" * 40)

    if not result["avaliacoes"]:
        print("  Nenhuma avaliação ainda.")
        return

    for a in result["avaliacoes"]:
        estrelas = "⭐" * a["nota"]
        comentario = f" — {a['comentario']}" if a["comentario"] else ""
        print(f"  {estrelas}{comentario} ({a['criado_em'][:10]})")


def ver_metricas():
    dias = input("\n  Período em dias (padrão: 30): ").strip()
    dias = int(dias) if dias.isdigit() else 30
    dias = max(1, min(dias, 365))

    result = obter_metricas(dias)
    print(f"\n  📊 MÉTRICAS — últimos {result['periodo_dias']} dias")
    print(f"  Total de mensagens: {result['total_mensagens']}")
    print("  " + "─" * 40)

    if result["top_rotas"]:
        print("  📌 Rotas mais acessadas:")
        for r in result["top_rotas"]:
            bar = "█" * min(r["acessos"], 30)
            print(f"     {r['rota']:25s} {r['acessos']:>4d}  {bar}")

    if result["por_dia"]:
        print("\n  📅 Mensagens por dia (últimos 10):")
        for d in result["por_dia"][:10]:
            bar = "█" * min(d["total"], 30)
            print(f"     {d['dia']}  {d['total']:>4d}  {bar}")


if __name__ == "__main__":
    menu()
