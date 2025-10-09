# install.py (com função verificar_drm adicionada)
import os
import io
import sys
import time
import asyncio
import aiohttp
import aiofiles
import httpx
import vdf
import subprocess
import requests
import traceback
from bs4 import BeautifulSoup
from pathlib import Path
from typing import Any, Tuple, List, Dict, Optional
from common import log, variable
from config_manager import get_steam_path
from common.variable import CLIENT, HEADER, STEAM_PATH, REPO_LIST

# Cores ANSI
PRETO = "\033[30m"
VERMELHO = "\033[91m"
VERDE = "\033[92m"
AMARELO = "\033[93m"
AZUL = "\033[94m"
MAGENTA = "\033[95m"
CIANO = "\033[96m"
BRANCO = "\033[97m"
VERMELHO_ESCURO = "\033[31m"
VERDE_ESCURO = "\033[32m"
AMARELO_ESCURO = "\033[33m"
AZUL_ESCURO = "\033[34m"
RESET = "\033[0m"

def formatar_data_brasil(data_iso: str) -> str:
    """Converte data ISO (ex: '2024-05-20T14:30:00Z') para DD/MM/AAAA HH:MM."""
    from datetime import datetime
    try:
        data_obj = datetime.strptime(data_iso.replace('Z', ''), "%Y-%m-%dT%H:%M:%S")
        return data_obj.strftime("%d/%m/%Y %H:%M")  # Formato BR
    except:
        return data_iso  # Mantém o original se falhar

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

STPLUG_PATH = get_steam_path() / "config" / "stplug-in"
DEPOTCACHE_PATH = get_steam_path() / "depotcache"

# Configurações de versionlock por método para controlar se a pergunta sobre versionlock será feita
ASK_VERSION_LOCK_METODO1 = False  # Altere para False para desativar a pergunta
DEFAULT_VERSION_LOCK_METODO1 = True  # Valor padrão quando ASK_VERSION_LOCK1 = False

# --- Função verificar_drm (adicionada do script antigo) ---
def verificar_drm(appid):
    def buscar_drm_steam_store(appid):
        def extrair_drm(texto):
            texto = texto.lower()
            drm = set()
            if "denuvo" in texto:
                drm.add("Denuvo")
            if "steamworks" in texto or "requires steam" in texto or "necessita do steam" in texto:
                drm.add("Steamworks")
            if "third-party drm" in texto or "3rd-party drm" in texto or "drm de terceiros" in texto:
                drm.add("Third-party DRM")
            return drm

        try:
            drm_total = set()
            url_en = f"https://store.steampowered.com/app/{appid}/?cc=us&l=en"
            response_en = requests.get(url_en, headers=HEADERS)
            if response_en.status_code == 200:
                soup_en = BeautifulSoup(response_en.text, "html.parser")
                drm_total.update(extrair_drm(soup_en.get_text()))

            url_pt = f"https://store.steampowered.com/app/{appid}/"
            response_pt = requests.get(url_pt, headers=HEADERS)
            if response_pt.status_code == 200:
                soup_pt = BeautifulSoup(response_pt.text, "html.parser")
                drm_total.update(extrair_drm(soup_pt.get_text()))

            return ", ".join(sorted(drm_total)) if drm_total else "Não especificado"

        except Exception:
            return "Não especificado"

    def get_steam_game_info(appid):
        url = f"https://store.steampowered.com/api/appdetails?appids={appid}&cc=us&l=en"
        try:
            response = requests.get(url)
            response.raise_for_status()
        except requests.RequestException:
            return {"appid": appid, "error": "Erro ao acessar a Steam API."}

        data = response.json()
        game_data = data.get(str(appid), {}).get("data")
        if not game_data:
            return {"appid": appid, "error": "Jogo não encontrado."}

        name = game_data.get("name", "Desconhecido")
        about = game_data.get("about_the_game", "")
        detailed = game_data.get("detailed_description", "")
        drm = []

        about_lower = about.lower()
        detailed_lower = detailed.lower()

        if "denuvo" in about_lower or "denuvo" in detailed_lower:
            drm.append("Denuvo")
        if "third-party drm" in about_lower or "3rd-party drm" in about_lower:
            drm.append("Third-party DRM")
        if "steamworks" in about_lower or "requires steam" in about_lower:
            drm.append("Steamworks")

        drm_info = ", ".join(drm) if drm else buscar_drm_steam_store(appid)

        return {"appid": appid, "name": name, "drm": drm_info}

    info = get_steam_game_info(appid)
    if "error" in info:
        print(f"\n❌ [{appid}] ERRO: {info['error']}")
        return None

    print(f"\n📌 AppID: {appid}")
    print(f"🎮 Nome : {info['name']}")
    print(f"🔐 DRM  : {info['drm']}")
    print(f"⚠️ Obs.: Essa informação é puramente informativa, não é {AZUL}100%{RESET} precisa.")
    
    drm_text = info['drm'].lower()
    if "denuvo" in drm_text:
        print("🚫 Situação: ❌ O jogo não funciona atualmente (Denuvo), mas pode funcionar no futuro.\n")
    elif "steamworks" in drm_text and ("third-party" in drm_text or "," in drm_text):
        print("⚠️ Situação: ⚠️ O jogo talvez funcione (Steamworks + outro DRM).\n")
    elif "steamworks" in drm_text:
        print("✅ Situação: ✔️ O jogo deve funcionar normalmente.\n")
    elif drm_text in ["", "não especificado"]:
        print("✅ Situação: ✔️ O jogo deve funcionar (sem DRM detectado).\n")
    else:
        print("❓ Situação: ❓ DRM não identificado claramente. Talvez funcione.\n")
    
    return info['name']

# --- Funções auxiliares ---

async def buscar_nome_jogo(appid):
    url = f"https://store.steampowered.com/api/appdetails?appids={appid}&l=english"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()
            if data and str(appid) in data and data[str(appid)]['success']:
                return data[str(appid)]['data']['name']
            return None

async def pesquisar_jogo_por_nome(nome: str) -> List[Dict[str, Any]]:
    """Pesquisa jogos na Steam por nome e retorna lista de resultados."""
    url = "https://store.steampowered.com/api/storesearch"
    params = {
        "term": nome,
        "l": "english",
        "cc": "us"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                data = await resp.json()
                return data.get('items', [])
    except Exception:
        return []

async def selecionar_jogo_por_nome(nome: str):
    """Permite ao usuário selecionar um jogo da lista de resultados com paginação."""
    resultados = await pesquisar_jogo_por_nome(nome)
    if not resultados:
        print(f"\n{VERMELHO}❌ Nenhum jogo encontrado com o nome '{nome}'.{RESET}")
        return None
    
    # Configuração de paginação
    resultados_por_pagina = 10
    total_paginas = (len(resultados) + resultados_por_pagina - 1) // resultados_por_pagina
    pagina_atual = 1
    
    while True:
        # Calcular índices para a página atual
        inicio = (pagina_atual - 1) * resultados_por_pagina
        fim = inicio + resultados_por_pagina
        resultados_pagina = resultados[inicio:fim]
        
        print(f"\n{VERDE}🎮 Jogos encontrados (Página {pagina_atual}/{total_paginas}):{RESET}\n")
        
        for idx, jogo in enumerate(resultados_pagina, inicio + 1):
            print(f"{AZUL}[{idx}]{RESET} {jogo['name']} (ID: {jogo['id']})")
        
        # Opções de navegação
        print(f"\n{CIANO}Opções de navegação:{RESET}")
        if pagina_atual > 1:
            print(f"{AZUL}[A]{RESET} - Página anterior")
        if pagina_atual < total_paginas:
            print(f"{AZUL}[D]{RESET} - Próxima página")
        print(f"{AZUL}[0]{RESET} - Cancelar pesquisa")
        
        while True:
            escolha = input(f"\n{CIANO}👉 Digite o número do jogo desejado ou opção de navegação:{RESET} ").strip().upper()
            
            if escolha == "0":
                return None
            elif escolha == "A" and pagina_atual > 1:
                pagina_atual -= 1
                break
            elif escolha == "D" and pagina_atual < total_paginas:
                pagina_atual += 1
                break
            elif escolha.isdigit():
                idx_escolhido = int(escolha)
                if 1 <= idx_escolhido <= len(resultados):
                    return str(resultados[idx_escolhido-1]['id'])
                else:
                    print(f"{VERMELHO}❌ Número fora do intervalo. Tente novamente.{RESET}")
            else:
                print(f"{VERMELHO}❌ Escolha inválida. Tente novamente.{RESET}")


async def get_repos():
    """Retorna a lista de repositórios para buscar as keys"""
    return REPO_LIST

def parse_manifest_filename(filename: str):
    """Analisa o nome do arquivo manifest para extrair depot_id e manifest_id"""
    try:
        # Formato esperado: "depotid_manifestid.manifest"
        parts = filename.split('_')
        if len(parts) >= 2 and filename.endswith('.manifest'):
            depot_id = parts[0]
            manifest_id = '_'.join(parts[1:]).replace('.manifest', '')
            return depot_id, manifest_id
    except:
        pass
    return None, None

def encerrar_e_reiniciar_steam():
    """Função para encerrar e reiniciar a Steam"""
    try:
        import fecharsteam
        fecharsteam.encerrar_steam_processos()
        print(f"{VERDE}✅ Steam reiniciada com sucesso!{RESET}")
    except Exception as e:
        print(f"{VERMELHO}❌ Erro ao reiniciar Steam: {e}{RESET}")

# --- Nova função para baixar dos repositórios ---
async def download_luafast(app_id: str):
    try:
        BRUHHUB_REPOS = await get_repos()
        
        async def fetch_from_repo(repo: str, sha: str, path: str):
            url = f"https://raw.githubusercontent.com/{repo}/{sha}/{path}"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=HEADERS, timeout=30) as resp:
                    resp.raise_for_status()
                    return await resp.read()

        async def get_most_recent_repo(app_id: str) -> Tuple[str, str]:
            most_recent_repo = None
            most_recent_date = None
            most_recent_sha = None
            
            for repo in BRUHHUB_REPOS:
                try:
                    branch_url = f"https://api.github.com/repos/{repo}/branches/{app_id}"
                    async with aiohttp.ClientSession() as session:
                        async with session.get(branch_url, headers=HEADERS) as resp:
                            if resp.status != 200:
                                continue
                            branch_info = await resp.json()
                    
                    commit_date = branch_info['commit']['commit']['author']['date']
                    if not most_recent_date or commit_date > most_recent_date:
                        most_recent_date = commit_date
                        most_recent_repo = repo
                        most_recent_sha = branch_info['commit']['sha']
                        
                except Exception:
                    continue
                    
            if not most_recent_repo:
                return None, None
            return most_recent_repo, most_recent_sha

        repo, sha = await get_most_recent_repo(app_id)
        if not repo:
            return None, None
            
        tree_url = f"https://api.github.com/repos/{repo}/git/trees/{sha}?recursive=1"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(tree_url, headers=HEADERS) as resp:
                tree_info = await resp.json()
        
        arquivos = [item for item in tree_info.get('tree', []) 
                   if item['path'].endswith('.manifest') or item['path'].endswith('.lua')]
        
        if not arquivos:
            return None, None
            
        total = len(arquivos)
        print(f"\n🔎 Baixando {total} arquivos...\n")
        
        # Estruturas para coletar informações necessárias para o versionlock
        depot_map = {}   # Mapa de depots para manifestos
        
        # Lista de arquivos .lua baixados
        lua_files = []
        
        for idx, item in enumerate(arquivos, 1):
            path = item['path']
            conteudo = await fetch_from_repo(repo, sha, path)
            
            destino = STPLUG_PATH if path.endswith('.lua') else DEPOTCACHE_PATH
            os.makedirs(destino, exist_ok=True)
            file_path = destino / Path(path).name
            
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(conteudo)
            
            # Registrar arquivos .lua
            if path.endswith('.lua'):
                lua_files.append(file_path)
            
            # Processar manifestos para versionlock
            if path.endswith('.manifest'):
                filename = Path(path).name
                depot_id, manifest_id = parse_manifest_filename(filename)
                if depot_id and manifest_id:
                    if depot_id not in depot_map:
                        depot_map[depot_id] = []
                    depot_map[depot_id].append(manifest_id)
            
            # Barra de progresso
            progresso = int((idx / total) * 50)
            porcentagem = int((idx / total) * 100)
            print(f"\r[{'=' * progresso}{' ' * (50 - progresso)}] {porcentagem}%", end="", flush=True)
        
        print("\n")  # Nova linha após conclusão
        
        # Ordenar manifestos em cada depot (mais recente primeiro)
        for depot_id in depot_map:
            try:
                # Converter para inteiros para ordenação numérica
                depot_map[depot_id] = sorted(
                    [manifest for manifest in depot_map[depot_id] if manifest.isdigit()],
                    key=lambda x: int(x),
                    reverse=True
                )
            except ValueError:
                # Se não forem numéricos, usar ordenação alfabética reversa
                depot_map[depot_id] = sorted(depot_map[depot_id], reverse=True)
        
        # Perguntar se deseja bloquear updates
        versionlock = DEFAULT_VERSION_LOCK_METODO1
        if ASK_VERSION_LOCK_METODO1:
            escolha = input(f"Deseja {VERMELHO}BLOQUEAR{RESET} os UPDATES? (s/n): ").lower()
            versionlock = (escolha == "s")
        
        # Aplicar versionlock modificando os arquivos .lua existentes
        if versionlock:
            for lua_file in lua_files:
                async with aiofiles.open(lua_file, 'r') as f:
                    content = await f.read()
                
                # Adicionar comandos de versionlock para cada depot
                new_content = content
                for depot_id, manifest_ids in depot_map.items():
                    if manifest_ids:
                        latest_manifest = manifest_ids[0]
                        versionlock_cmd = f'\nsetManifestid({depot_id},"{latest_manifest}")'
                        
                        # Verificar se o comando já existe
                        if f'setManifestid({depot_id}' not in new_content:
                            new_content += versionlock_cmd
                
                # Salvar modificações se houver alterações
                if new_content != content:
                    async with aiofiles.open(lua_file, 'w') as f:
                        await f.write(new_content)
        
        commit_url = f"https://api.github.com/repos/{repo}/commits/{sha}"
        async with aiohttp.ClientSession() as session:
            async with session.get(commit_url, headers=HEADERS) as resp:
                commit_info = await resp.json()
                return commit_info['commit']['author']['date'], len(arquivos)
                
    except Exception as e:
        print(f"Erro durante o download: {str(e)}")
        traceback.print_exc()
        return None, None

# --- Menu principal ---
async def main_flow():
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # Cabeçalho decorativo
        print(f"{AZUL}      \n        ╔══════════════════════════════════════════════════════════════════════════╗")
        print(f"        ║        {BRANCO}         🚀 INSTALADOR DE KEYS LUAFAST v4.0                       {AZUL}║")
        print(f"        ╚══════════════════════════════════════════════════════════════════════════╝{RESET}\n")

        print(f"{VERDE}       📢 Digite o ID ou nome do jogo que deseja ou 0 Voltar para o menu principal. {RESET}\n")
        
        entrada = input(f"\n{AMARELO}🔎 Digite o ID ou nome do jogo:{RESET} ").strip()
        
        # Verificar opções de navegação primeiro
        if entrada == "0":
            return "voltar"
        elif entrada == "00":
            print(f"\n{VERMELHO}❌ Encerrando o programa...{RESET}")
            time.sleep(1)
            sys.exit()
        
        # Se for apenas dígitos, assume que é um AppID
        if entrada.isdigit():
            appid = entrada
        else:
            # Se não for apenas dígitos, assume que é um nome e faz a pesquisa
            appid = await selecionar_jogo_por_nome(entrada)
            if not appid:
                continue  # Volta ao menu se não selecionou um jogo

        # Agora usa a função verificar_drm corretamente
        nome = verificar_drm(appid) # Faz a verificação de DRM
        if nome:            
            if input("Deseja adicionar este jogo a sua Steam❓ (S/N): ").strip().lower() != "s":
                print("\n❌ Instalação cancelada.\n")
                time.sleep(2)
                continue
        else:
            print(f"\n{AMARELO}⚠️ Nome do jogo não encontrado na Steam. Continuando com ID: {appid}{RESET}")
            if input("Deseja adicionar este jogo a sua Steam❓ (S/N): ").strip().lower() != "s":
                print("\n❌ Instalação cancelada.\n")
                time.sleep(2)
                continue
                     
        # Executa diretamente o método 1 (antigo servidor de keys 1)
        data_recente, total = await download_luafast(appid)
        if data_recente:
            print(f"\n✅ {nome if nome else appid} foi adicionado com sucesso!\n")
            data_br = formatar_data_brasil(data_recente)
            print(f"📅 Data da atualização da Key: {VERDE}{data_br}{RESET}")
            print(f"📦 Total de arquivos baixados: {VERDE}{total}{RESET}\n")
        else:
            print(f"\n{VERMELHO}❌ Não foi possível encontrar arquivos para {nome if nome else appid}.{RESET}\n")

        # Perguntar se deseja continuar ou voltar
        print(f"\n{AZUL}O que deseja fazer agora?{RESET}")
        print(f"1. {VERDE}Adicionar outro jogo{RESET}")
        print(f"2. {AMARELO}Reiniciar a Steam{RESET}")
        print(f"3. {VERMELHO}Voltar ao menu principal{RESET}")
        print(f"4. {VERMELHO}Sair do programa{RESET}")
        
        continuar = input(f"\n{CIANO}👉 Escolha uma opção (1-4):{RESET} ").strip()
        
        if continuar == "1":
            continue  # Continua no loop para adicionar outro jogo
        elif continuar == "2":
            encerrar_e_reiniciar_steam()
            print("✅ Steam reiniciada com sucesso!")
            continue
        elif continuar == "3":
            return "voltar"
        elif continuar == "4":
            print(f"\n{VERMELHO}❌ Encerrando o programa...{RESET}")
            time.sleep(1)
            sys.exit()
        else:
            print(f"{VERMELHO}❌ Opção inválida, voltando ao menu principal.{RESET}")
            return "voltar"

if __name__ == "__main__":
    while True:
        try:
            resultado = asyncio.run(main_flow())
            if resultado == "voltar":
                import subprocess
                subprocess.run(["python", "main.py"])
                break
            else:
                break  # Sai do loop se main_flow() terminar sem erros
        except Exception as e:
            print(f"\n{VERMELHO}⚠️ Ocorreu um erro inesperado:{RESET}")
            print(f"{VERMELHO}{traceback.format_exc()}{RESET}")
            print(f"\n{AMARELO}🔄 O programa será reiniciado automaticamente em 5 segundos...{RESET}")
            time.sleep(8)
            continue  # Reinicia o loop e o programa