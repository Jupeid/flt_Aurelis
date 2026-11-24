import json
import os
from core.jogador import Jogador
from utils.paths import obter_diretorio_saves

ARQUIVO_SAVE = "savegame_aurelis.json"


def salvar_progresso(jogador: Jogador, cena_atual: str, arquivo: str = ARQUIVO_SAVE) -> tuple[bool, str]:
    """Converte os dados do jogador em dicionário e grava no arquivo JSON."""
    caminho = os.path.join(obter_diretorio_saves(), arquivo)
    try:
        dados = jogador.para_dicionario(cena_atual)
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=4)
        return True, "Progresso salvo com sucesso!"
    except Exception as e:
        return False, f"Erro ao salvar progresso: {e}"


def carregar_progresso(arquivo: str = ARQUIVO_SAVE) -> tuple[Jogador | None, str | None, str]:
    """Lê o arquivo JSON de salvamento e reconstrói o objeto Jogador."""
    caminho = os.path.join(obter_diretorio_saves(), arquivo)
    if not os.path.exists(caminho):
        return None, None, "Nenhum arquivo de salvamento encontrado."
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            dados = json.load(f)
        jogador, cena_atual = Jogador.do_dicionario(dados)
        return jogador, cena_atual, "Jogo carregado com sucesso!"
    except Exception as e:
        return None, None, f"Erro ao carregar progresso: {e}"
