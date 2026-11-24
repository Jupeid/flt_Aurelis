class ItemUnico:
    """
    Representa tanto os 8 Fragmentos divinos dos Campeões (com bônus passivos e lore)
    quanto itens únicos de missão/exploração (chaves, mapas especiais, etc.).
    """
    def __init__(
        self,
        id_item: str,
        nome: str,
        descricao: str,
        tipo: str = "fragmento",  # "fragmento" ou "missao"
        bonus: dict | None = None,
        portador_original: str | None = None,
        historia_origem: str | None = None,
    ):
        self.id_item = id_item
        self.nome = nome
        self.descricao = descricao
        self.tipo = tipo
        self.bonus = bonus if bonus is not None else {}
        self.portador_original = portador_original
        self.historia_origem = historia_origem

    @property
    def eh_fragmento(self) -> bool:
        return self.tipo == "fragmento"

    @classmethod
    def from_dict(cls, dados: dict) -> "ItemUnico":
        """Cria uma instância a partir de um dicionário/JSON (aceita id_item ou id_fragmento)."""
        return cls(
            id_item=dados.get("id_item") or dados.get("id_fragmento", ""),
            nome=dados.get("nome", "Item Desconhecido"),
            descricao=dados.get("descricao", ""),
            tipo=dados.get("tipo", "fragmento"),
            bonus=dict(dados.get("bonus", {})),
            portador_original=dados.get("portador_original"),
            historia_origem=dados.get("historia_origem"),
        )

    def to_dict(self) -> dict:
        return {
            "id_item": self.id_item,
            "nome": self.nome,
            "descricao": self.descricao,
            "tipo": self.tipo,
            "bonus": dict(self.bonus),
            "portador_original": self.portador_original,
            "historia_origem": self.historia_origem,
        }

    def obter_dados_inspecao(self) -> dict:
        """Retorna os detalhes estruturados para o Terminal ou Flet exibirem ao inspecionar."""
        return {
            "nome": self.nome,
            "tipo": "Fragmento Divino" if self.eh_fragmento else "Item Único",
            "descricao": self.descricao,
            "portador_original": self.portador_original,
            "historia_origem": self.historia_origem,
            "bonus": dict(self.bonus),
        }
