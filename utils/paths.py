import os
import sys


def obter_diretorio_recursos() -> str:
    """Retorna a raiz onde ficam os arquivos fixos do jogo (ex: pasta data/)."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return sys._MEIPASS

    pasta_utils = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(pasta_utils, ".."))


def obter_diretorio_saves() -> str:
    """Retorna a pasta persistente e gravável onde o savegame será armazenado."""
    # 1. Ambiente Flet (Android / iOS / Desktop empacotado com Flet)
    storage_flet = os.environ.get("FLET_APP_STORAGE_DATA")
    if storage_flet:
        os.makedirs(storage_flet, exist_ok=True)
        return storage_flet

    # 2. Executável standalone (PyInstaller / Windows)
    if getattr(sys, "frozen", False):
        pasta_exe = os.path.dirname(sys.executable)
        os.makedirs(pasta_exe, exist_ok=True)
        return pasta_exe

    # 3. Execução direta via código-fonte (Colab / VS Code)
    pasta_utils = os.path.dirname(os.path.abspath(__file__))
    pasta_raiz = os.path.abspath(os.path.join(pasta_utils, ".."))
    pasta_saves = os.path.join(pasta_raiz, "saves")
    os.makedirs(pasta_saves, exist_ok=True)
    return pasta_saves


def obter_caminho_recurso(caminho_relativo: str) -> str:
    """Converte um caminho relativo de recurso (ex: 'data/pt/itens.json') em absoluto."""
    return os.path.join(obter_diretorio_recursos(), caminho_relativo)
