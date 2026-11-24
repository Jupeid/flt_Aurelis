import json
import os
from utils.paths import obter_caminho_recurso
from core.item import ItemUnico
from core.npc import NPC


class BancoDeDados:
    """Centraliza o carregamento de todos os JSONs do jogo de acordo com o idioma."""

    def __init__(self, idioma: str = "pt"):
        self.idioma = idioma
        self.itens: dict[str, ItemUnico] = {}
        self.npcs: dict[str, NPC] = {}
        self.cenas: dict = {}
        self.textos_ui: dict[str, str] = {}

    def definir_idioma(self, novo_idioma: str) -> None:
        self.idioma = novo_idioma
        self.carregar_tudo()

    def carregar_tudo(self) -> None:
        """Carrega itens, NPCs, cenas e strings de interface (com fallback para data/)."""
        self.itens = self._carregar_json_com_fallback(
            [f"data/{self.idioma}/itens.json", "data/itens.json"],
            lambda dados: ItemUnico.from_dict(dados),
        )
        self.npcs = self._carregar_json_com_fallback(
            [f"data/{self.idioma}/npcs.json", "data/npcs.json"],
            lambda dados: NPC.from_dict(dados),
        )
        self.cenas = self._carregar_diretorio_cenas_com_fallback(
            [f"data/{self.idioma}/cenas", "data/cenas"]
        )
        self.textos_ui = self._carregar_json_com_fallback(
            [f"data/locales/{self.idioma}.json", f"data/{self.idioma}.json"]
        )

    def obter_texto_ui(self, chave: str, padrao: str | None = None) -> str:
        """Retorna uma string traduzida da interface (ou a própria chave se ausente)."""
        return self.textos_ui.get(chave, padrao if padrao is not None else chave)

    def _carregar_json_com_fallback(self, caminhos_candidatos: list[str], conversor=None) -> dict:
        for caminho_relativo in caminhos_candidatos:
            caminho_completo = obter_caminho_recurso(caminho_relativo)
            if os.path.exists(caminho_completo):
                try:
                    with open(caminho_completo, "r", encoding="utf-8") as f:
                        dados = json.load(f)
                        if conversor:
                            return {
                                chave: conversor({**valor, "id": chave, "id_npc": chave, "id_item": chave})
                                for chave, valor in dados.items()
                            }
                        return dados
                except Exception as e:
                    print(f"[ERRO JSON] Falha ao carregar '{caminho_relativo}': {e}")
                    return {}
        return {}

    def _carregar_diretorio_cenas_com_fallback(self, diretorios_candidatos: list[str]) -> dict:
        for caminho_relativo in diretorios_candidatos:
            diretorio = obter_caminho_recurso(caminho_relativo)
            if os.path.exists(diretorio):
                banco_cenas = {}
                for arquivo in sorted(os.listdir(diretorio)):
                    if arquivo.endswith(".json"):
                        caminho_arquivo = os.path.join(diretorio, arquivo)
                        try:
                            with open(caminho_arquivo, "r", encoding="utf-8") as f:
                                banco_cenas.update(json.load(f))
                        except Exception as e:
                            print(f"[ERRO CENA] Falha ao ler '{arquivo}': {e}")
                return banco_cenas
        return {}