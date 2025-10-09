# compat.py (versão corrigida)
import asyncio
import os
import csv
from datetime import datetime
from pathlib import Path
import aiohttp

# Caminhos
STPLUG_PATH = Path("C:/Program Files (x86)/Steam/config/stplug-in")
LOG_LOCAL = Path("envios_locais.csv")

# Cores
VERDE = "\033[92m"
VERMELHO = "\033[91m"
AMARELO = "\033[93m"
RESET = "\033[0m"
AZUL = "\033[94m"

def limpar_tela():
    os.system('cls' if os.name == 'nt' else 'clear')

async def fetch_game_name(app_id: str) -> str:
    try:
        url = f"https://store.steampowered.com/api/appdetails?appids={app_id}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                data = await resp.json()
                return data[app_id]['data']['name'] if data[app_id]['success'] else "Desconhecido"
    except:
        return "Desconhecido"

def salvar_log_local(app_id, nome_jogo, status):
    try:
        novo = not LOG_LOCAL.exists()
        with open(LOG_LOCAL, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            if novo:
                writer.writerow(["DataHora", "ID", "Nome", "Status"])
            writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), app_id, nome_jogo, status])
        print(f"{VERDE}Registro local salvo!{RESET}")
    except Exception as e:
        print(f"{VERMELHO}Erro ao salvar log local: {e}{RESET}")

async def avaliar_jogo():
    limpar_tela()
    print("=" * 60)
    print(f"{VERDE}[ AVALIAR JOGOS ]{RESET}".center(60))
    print("=" * 60)
    print("\nEscolha como deseja avaliar:")
    print("1. Avaliar Jogos Instalados")
    print("2. Avaliar Jogo pelo ID")
    print("0. Voltar ao menu principal")
    escolha = input("\nDigite a opção desejada: ").strip()

    if escolha == "1":
        await avaliar_varios_jogos()
    elif escolha == "2":
        await avaliar_jogo_pelo_id()
    elif escolha == "0":
        return
    else:
        print(f"{VERMELHO}Opção inválida!{RESET}")
        input("\nPressione Enter para voltar...")

async def avaliar_varios_jogos():
    arquivos = list(STPLUG_PATH.glob("*.lua"))
    if not arquivos:
        print(f"{VERMELHO}Nenhum jogo encontrado.{RESET}")
        input("\nPressione Enter para sair...")
        return

    while True:
        limpar_tela()
        print("\nJogos encontrados:\n")
        id_map = {}
        for idx, arq in enumerate(arquivos, 1):
            app_id = arq.stem
            nome = await fetch_game_name(app_id)
            id_map[str(idx)] = (app_id, nome)
            print(f"{idx}. {app_id} - {nome}")

        escolha = input("\nDigite o número do jogo que deseja avaliar (ou 0 para voltar): ").strip()

        if escolha == "0":
            break

        if escolha not in id_map:
            print(f"{AMARELO}Número inválido.{RESET}")
            input("\nPressione Enter para tentar novamente...")
            continue

        app_id, nome_jogo = id_map[escolha]

        status_novo = escolher_status()
        if not status_novo:
            print(f"{VERMELHO}Nenhum status selecionado. Cancelando operação.{RESET}")
            input("\nPressione Enter para voltar...")
            return

        # Agora salva apenas localmente
        salvar_log_local(app_id, nome_jogo, status_novo)
        print(f"{VERDE}Avaliação salva localmente!{RESET}")

        continuar = input("\nDeseja avaliar outro jogo instalado? (S/N): ").strip().lower()
        if continuar != "s":
            break

async def avaliar_jogo_pelo_id():
    while True:
        limpar_tela()
        app_id = input("Digite o ID do jogo (ou 0 para voltar): ").strip()
        if app_id == "0":
            break

        nome_jogo = await fetch_game_name(app_id)

        print(f"\nID: {app_id}")
        print(f"Nome: {nome_jogo}")
        confirmar = input("\nÉ este jogo? (S/N): ").strip().lower()

        if confirmar == "s":
            status_novo = escolher_status()
            if not status_novo:
                print(f"{VERMELHO}Nenhum status selecionado. Cancelando operação.{RESET}")
                input("\nPressione Enter para voltar...")
                return

            # Agora salva apenas localmente
            salvar_log_local(app_id, nome_jogo, status_novo)
            print(f"{VERDE}Avaliação salva localmente!{RESET}")

            continuar = input("\nDeseja avaliar outro jogo por ID? (S/N): ").strip().lower()
            if continuar != "s":
                break
        else:
            print(f"{AMARELO}Vamos tentar novamente.{RESET}")
            input("\nPressione Enter para digitar outro ID...")

def escolher_status():
    print("\nEscolha a situação:")
    print(f"1.{VERDE} Funciona{RESET}")
    print(f"2.{AMARELO} Funciona Parcialmente{RESET}")
    print(f"3.{VERMELHO} Não Funciona{RESET}")
    status_escolha = input("\nDigite o número correspondente: ").strip()

    status_map = {
        "1": "Funciona",
        "2": "Funciona Parcialmente",
        "3": "Não Funciona"
    }

    return status_map.get(status_escolha)

def visualizar_lista_compatibilidade():
    try:
        if not LOG_LOCAL.exists():
            print(f"{AMARELO}Nenhum registro local encontrado.{RESET}")
            input("\nPressione Enter para voltar...")
            return

        while True:
            limpar_tela()
            print("=" * 60)
            print(f"{VERDE}[ LISTA DE COMPATIBILIDADE DE JOGOS ]{RESET}".center(60))
            print("=" * 60)
            print("\nAqui você pode visualizar a lista de compatibilidade para saber quais jogos funcionam!\n")

            with open(LOG_LOCAL, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                registros = list(reader)

            if not registros:
                print(f"{AMARELO}Nenhum registro encontrado.{RESET}")
                input("\nPressione Enter para voltar...")
                return

            termo_pesquisa = input("Digite o " + AZUL + "ID" + RESET + ", parte do " + AZUL + "NOME " + RESET + "do jogo, ou apenas pressione " + AZUL + "[Enter] " + RESET + "para listar tudo. \n\nAguardando: ").strip().lower()

            limpar_tela()
            print("\n+---------------------+----------------------------------------------------+------------------------+")
            print("| {:^19} | {:^50} | {:^22} |".format("Data/Hora", "Nome", "Status"))
            print("+---------------------+----------------------------------------------------+------------------------+")

            encontrou = False

            for registro in registros:
                data_hora = registro.get('DataHora', '')
                nome = registro.get('Nome', 'Sem nome').strip()
                status = registro.get('Status', 'Desconhecido').strip()
                app_id = registro.get('ID', '').strip()

                if termo_pesquisa:
                    if termo_pesquisa not in app_id and termo_pesquisa not in nome.lower():
                        continue

                status_text = status.center(22)
                if status == "Funciona":
                    status_cor = VERDE + status_text + RESET
                elif status == "Funciona Parcialmente":
                    status_cor = AMARELO + status_text + RESET
                elif status == "Não Funciona":
                    status_cor = VERMELHO + status_text + RESET
                else:
                    status_cor = status_text

                nome_exibido = nome[:50] if len(nome) > 50 else nome
                data_exibida = data_hora[:19] if len(data_hora) > 19 else data_hora

                print("| {:^19} | {:50} | {} |".format(data_exibida, nome_exibido, status_cor))
                encontrou = True

            if not encontrou:
                print(f"\n{AMARELO}Nenhum jogo encontrado com essa busca.{RESET}")

            print("+---------------------+----------------------------------------------------+------------------------+")

            # Perguntar se quer fazer outra busca
            outra_busca = input("\nDeseja fazer outra busca? (S/N): ").strip().lower()
            if outra_busca != 's':
                break

    except Exception as e:
        print(f"{VERMELHO}Erro ao visualizar registros locais:{RESET}")
        import traceback
        traceback.print_exc()
        input("\nPressione Enter para voltar...")

async def menu_principal():
    while True:
        limpar_tela()
        print("╔" + "═" * 56 + "╗")
        print("║" + "COMPATIBILIDADE DE JOGOS - STEAM".center(56) + "║")
        print("╚" + "═" * 56 + "╝" + f"{RESET}")
        print("\n1. Visualizar lista de compatibilidade")
        print("\n2. Avaliar Jogos")
        print("\n3. Sair")
        escolha = input("\nEscolha uma opção: ").strip()

        if escolha == "1":
            visualizar_lista_compatibilidade()
        elif escolha == "2":
            await avaliar_jogo()
        elif escolha == "3":
            print(f"{AMARELO}Saindo...{RESET}")
            break
        else:
            print(f"{VERMELHO}Opção inválida.{RESET}")
            input("\nPressione Enter para tentar novamente...")

async def main_flow():
    await menu_principal()# compat.py (versão corrigida)
import asyncio
import os
import csv
from datetime import datetime
from pathlib import Path
import aiohttp

# Caminhos
STPLUG_PATH = Path("C:/Program Files (x86)/Steam/config/stplug-in")
LOG_LOCAL = Path("envios_locais.csv")

# Cores
VERDE = "\033[92m"
VERMELHO = "\033[91m"
AMARELO = "\033[93m"
RESET = "\033[0m"
AZUL = "\033[94m"

def limpar_tela():
    os.system('cls' if os.name == 'nt' else 'clear')

async def fetch_game_name(app_id: str) -> str:
    try:
        url = f"https://store.steampowered.com/api/appdetails?appids={app_id}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                data = await resp.json()
                return data[app_id]['data']['name'] if data[app_id]['success'] else "Desconhecido"
    except:
        return "Desconhecido"

def salvar_log_local(app_id, nome_jogo, status):
    try:
        novo = not LOG_LOCAL.exists()
        with open(LOG_LOCAL, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            if novo:
                writer.writerow(["DataHora", "ID", "Nome", "Status"])
            writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), app_id, nome_jogo, status])
        print(f"{VERDE}Registro local salvo!{RESET}")
    except Exception as e:
        print(f"{VERMELHO}Erro ao salvar log local: {e}{RESET}")

async def avaliar_jogo():
    limpar_tela()
    print("=" * 60)
    print(f"{VERDE}[ AVALIAR JOGOS ]{RESET}".center(60))
    print("=" * 60)
    print("\nEscolha como deseja avaliar:")
    print("1. Avaliar Jogos Instalados")
    print("2. Avaliar Jogo pelo ID")
    print("0. Voltar ao menu principal")
    escolha = input("\nDigite a opção desejada: ").strip()

    if escolha == "1":
        await avaliar_varios_jogos()
    elif escolha == "2":
        await avaliar_jogo_pelo_id()
    elif escolha == "0":
        return
    else:
        print(f"{VERMELHO}Opção inválida!{RESET}")
        input("\nPressione Enter para voltar...")

async def avaliar_varios_jogos():
    arquivos = list(STPLUG_PATH.glob("*.lua"))
    if not arquivos:
        print(f"{VERMELHO}Nenhum jogo encontrado.{RESET}")
        input("\nPressione Enter para sair...")
        return

    while True:
        limpar_tela()
        print("\nJogos encontrados:\n")
        id_map = {}
        for idx, arq in enumerate(arquivos, 1):
            app_id = arq.stem
            nome = await fetch_game_name(app_id)
            id_map[str(idx)] = (app_id, nome)
            print(f"{idx}. {app_id} - {nome}")

        escolha = input("\nDigite o número do jogo que deseja avaliar (ou 0 para voltar): ").strip()

        if escolha == "0":
            break

        if escolha not in id_map:
            print(f"{AMARELO}Número inválido.{RESET}")
            input("\nPressione Enter para tentar novamente...")
            continue

        app_id, nome_jogo = id_map[escolha]

        status_novo = escolher_status()
        if not status_novo:
            print(f"{VERMELHO}Nenhum status selecionado. Cancelando operação.{RESET}")
            input("\nPressione Enter para voltar...")
            return

        # Agora salva apenas localmente
        salvar_log_local(app_id, nome_jogo, status_novo)
        print(f"{VERDE}Avaliação salva localmente!{RESET}")

        continuar = input("\nDeseja avaliar outro jogo instalado? (S/N): ").strip().lower()
        if continuar != "s":
            break

async def avaliar_jogo_pelo_id():
    while True:
        limpar_tela()
        app_id = input("Digite o ID do jogo (ou 0 para voltar): ").strip()
        if app_id == "0":
            break

        nome_jogo = await fetch_game_name(app_id)

        print(f"\nID: {app_id}")
        print(f"Nome: {nome_jogo}")
        confirmar = input("\nÉ este jogo? (S/N): ").strip().lower()

        if confirmar == "s":
            status_novo = escolher_status()
            if not status_novo:
                print(f"{VERMELHO}Nenhum status selecionado. Cancelando operação.{RESET}")
                input("\nPressione Enter para voltar...")
                return

            # Agora salva apenas localmente
            salvar_log_local(app_id, nome_jogo, status_novo)
            print(f"{VERDE}Avaliação salva localmente!{RESET}")

            continuar = input("\nDeseja avaliar outro jogo por ID? (S/N): ").strip().lower()
            if continuar != "s":
                break
        else:
            print(f"{AMARELO}Vamos tentar novamente.{RESET}")
            input("\nPressione Enter para digitar outro ID...")

def escolher_status():
    print("\nEscolha a situação:")
    print(f"1.{VERDE} Funciona{RESET}")
    print(f"2.{AMARELO} Funciona Parcialmente{RESET}")
    print(f"3.{VERMELHO} Não Funciona{RESET}")
    status_escolha = input("\nDigite o número correspondente: ").strip()

    status_map = {
        "1": "Funciona",
        "2": "Funciona Parcialmente",
        "3": "Não Funciona"
    }

    return status_map.get(status_escolha)

def visualizar_lista_compatibilidade():
    try:
        if not LOG_LOCAL.exists():
            print(f"{AMARELO}Nenhum registro local encontrado.{RESET}")
            input("\nPressione Enter para voltar...")
            return

        while True:
            limpar_tela()
            print("=" * 60)
            print(f"{VERDE}[ LISTA DE COMPATIBILIDADE DE JOGOS ]{RESET}".center(60))
            print("=" * 60)
            print("\nAqui você pode visualizar a lista de compatibilidade para saber quais jogos funcionam!\n")

            with open(LOG_LOCAL, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                registros = list(reader)

            if not registros:
                print(f"{AMARELO}Nenhum registro encontrado.{RESET}")
                input("\nPressione Enter para voltar...")
                return

            termo_pesquisa = input("Digite o " + AZUL + "ID" + RESET + ", parte do " + AZUL + "NOME " + RESET + "do jogo, ou apenas pressione " + AZUL + "[Enter] " + RESET + "para listar tudo. \n\nAguardando: ").strip().lower()

            limpar_tela()
            print("\n+---------------------+----------------------------------------------------+------------------------+")
            print("| {:^19} | {:^50} | {:^22} |".format("Data/Hora", "Nome", "Status"))
            print("+---------------------+----------------------------------------------------+------------------------+")

            encontrou = False

            for registro in registros:
                data_hora = registro.get('DataHora', '')
                nome = registro.get('Nome', 'Sem nome').strip()
                status = registro.get('Status', 'Desconhecido').strip()
                app_id = registro.get('ID', '').strip()

                if termo_pesquisa:
                    if termo_pesquisa not in app_id and termo_pesquisa not in nome.lower():
                        continue

                status_text = status.center(22)
                if status == "Funciona":
                    status_cor = VERDE + status_text + RESET
                elif status == "Funciona Parcialmente":
                    status_cor = AMARELO + status_text + RESET
                elif status == "Não Funciona":
                    status_cor = VERMELHO + status_text + RESET
                else:
                    status_cor = status_text

                nome_exibido = nome[:50] if len(nome) > 50 else nome
                data_exibida = data_hora[:19] if len(data_hora) > 19 else data_hora

                print("| {:^19} | {:50} | {} |".format(data_exibida, nome_exibido, status_cor))
                encontrou = True

            if not encontrou:
                print(f"\n{AMARELO}Nenhum jogo encontrado com essa busca.{RESET}")

            print("+---------------------+----------------------------------------------------+------------------------+")

            # Perguntar se quer fazer outra busca
            outra_busca = input("\nDeseja fazer outra busca? (S/N): ").strip().lower()
            if outra_busca != 's':
                break

    except Exception as e:
        print(f"{VERMELHO}Erro ao visualizar registros locais:{RESET}")
        import traceback
        traceback.print_exc()
        input("\nPressione Enter para voltar...")

async def menu_principal():
    while True:
        limpar_tela()
        print("╔" + "═" * 56 + "╗")
        print("║" + "COMPATIBILIDADE DE JOGOS - STEAM".center(56) + "║")
        print("╚" + "═" * 56 + "╝" + f"{RESET}")
        print("\n1. Visualizar lista de compatibilidade")
        print("\n2. Avaliar Jogos")
        print("\n3. Sair")
        escolha = input("\nEscolha uma opção: ").strip()

        if escolha == "1":
            visualizar_lista_compatibilidade()
        elif escolha == "2":
            await avaliar_jogo()
        elif escolha == "3":
            print(f"{AMARELO}Saindo...{RESET}")
            break
        else:
            print(f"{VERMELHO}Opção inválida.{RESET}")
            input("\nPressione Enter para tentar novamente...")

async def main_flow():
    await menu_principal()