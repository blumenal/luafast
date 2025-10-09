# fecharsteam.py
import subprocess
import time
import os
from pathlib import Path
from main import get_steam_path  # Importa a função do main.py

# Cores ANSI
VERMELHO = "\033[91m"
VERDE = "\033[92m"
AMARELO = "\033[93m"
AZUL = "\033[94m"
RESET = "\033[0m"

# Lista de processos da Steam para encerrar (em ordem de prioridade)
PROCESSOS_STEAM = [
    "Steam.exe",               # Fecha primeiro - processo principal
    "steamwebhelper.exe",      # Processos auxiliares
    "GameOverlayUI.exe",       # Overlay da Steam
    "SteamService.exe",        # Serviço da Steam
    "steamerrorreporter.exe",  # Reportador de erros
    "steamguard.exe"           # Steam Guard
]

def encerrar_steam_processos():
    """Encerra todos os processos da Steam e pergunta se deseja reabrir"""
    
    print(f"\n{AZUL}[*] Iniciando encerramento dos processos da Steam...{RESET}\n")
    
    # Fecha cada processo da lista
    processos_nao_encerrados = []
    for nome_proc in PROCESSOS_STEAM:
        try:
            print(f"{AMARELO}[-] Encerrando {nome_proc}...{RESET}", end=' ')
            subprocess.run(
                ["taskkill", "/F", "/IM", nome_proc],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            print(f"{VERDE}✓{RESET}")
        except Exception as e:
            print(f"{VERMELHO}X (Erro: {e}){RESET}")
            processos_nao_encerrados.append(nome_proc)
    
    time.sleep(2)  # Espera para garantir que todos os processos foram encerrados
    
    # Verificação final
    print(f"\n{AZUL}[*] Verificando processos remanescentes...{RESET}")
    try:
        # Usando encoding 'mbcs' para compatibilidade com sistemas em português
        output = subprocess.check_output("tasklist", shell=True, encoding="mbcs").lower()
        
        processos_ativos = [p for p in PROCESSOS_STEAM if p.lower() in output]
        
        if processos_ativos:
            print(f"{VERMELHO}[!] Ainda há processos ativos:{RESET}")
            for p in processos_ativos:
                print(f"    - {p}")
            return False
        else:
            print(f"{VERDE}[✓] Todos os processos da Steam foram encerrados{RESET}")
            reiniciar_steam()
            # Pergunta se deseja reabrir a Steam
            #resposta = input(f"\n{AMARELO}Deseja abrir a Steam novamente? (s/n): {RESET}").strip().lower()
            #if resposta == 's':
            #    reiniciar_steam()
            return True
            
    except Exception as e:
        print(f"{VERMELHO}[!] Erro ao verificar processos: {e}{RESET}")
        return False

def reiniciar_steam():
    """Reinicia o Steam no diretório configurado com parâmetros otimizados"""
    steam_exe = get_steam_path() / "Steam.exe"
    
    if not steam_exe.exists():
        print(f"\n{VERMELHO}[!] Steam.exe não encontrado em: {steam_exe}{RESET}")
        print(f"{AMARELO}Verifique se o diretório da Steam está configurado corretamente{RESET}")
        return False
    
    try:
        print(f"\n{AZUL}[*] Iniciando Steam com parâmetros otimizados...{RESET}")
        subprocess.Popen(
            [str(steam_exe), "-noverifyfiles", "-nobootstrapupdate", 
            "-skipinitialbootstrap", "-norepairfiles", "-console"],
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.DEVNULL
        )
        print(f"{VERDE}[✓] Steam iniciada com sucesso{RESET}")
        print(f"{AMARELO}Proteção contra atualização do APP Steam {RESET}")
        #print(f"{AMARELO}Parâmetros usados: -noverifyfiles -nobootstrapupdate -skipinitialbootstrap -norepairfiles -console{RESET}")
        return True
    except Exception as e:
        print(f"{VERMELHO}[!] Falha ao iniciar Steam: {e}{RESET}")
        return False

def menu_reiniciar():
    """Menu interativo para reiniciar a Steam"""
    print(f"\n{AZUL}╔════════════════════════════════════════════╗")
    print(f"║           GERENCIADOR DA STEAM           ║")
    print(f"╚════════════════════════════════════════════╝{RESET}")
    
    print(f"\n1. {VERDE}Encerrar e reiniciar a Steam{RESET}")
    print(f"2. {AMARELO}Apenas encerrar a Steam{RESET}")
    print(f"3. {AZUL}Apenas reiniciar a Steam{RESET}")
    print(f"0. {VERMELHO}Voltar{RESET}")
    
    escolha = input("\nEscolha uma opção: ").strip()
    
    if escolha == "1":
        if encerrar_steam_processos():
            reiniciar_steam()
    elif escolha == "2":
        encerrar_steam_processos()
    elif escolha == "3":
        reiniciar_steam()
    elif escolha == "0":
        return
    else:
        print(f"{VERMELHO}Opção inválida!{RESET}")
    
    input("\nPressione Enter para continuar...")

if __name__ == "__main__":
    # Quando executado diretamente, mostra o menu completo
    while True:
        menu_reiniciar()
        break  # Remove este break se quiser que o menu continue em loop