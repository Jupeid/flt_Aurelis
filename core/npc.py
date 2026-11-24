class NPC:
    def __init__(
        self,
        id_npc: str,
        nome: str,
        afeicao: int = 50,
        eh_campeao: bool = False,
        conhecido: bool = False,
        vivo: bool = True,
        imobilizado: bool = False,
        id_fragmento: str | None = None,
    ):
        self.id_npc = id_npc
        self.nome = nome
        self.afeicao = max(0, min(100, afeicao))
        self.conhecido = conhecido
        self.eh_campeao = eh_campeao
        self.vivo = vivo
        self.imobilizado = imobilizado
        self.id_fragmento = id_fragmento  # ID no JSON de itens/fragmentos

    # ------ RELAÇÃO DINÂMICA (0 A 100) ------
    @property
    def relacao(self) -> str:
        """Calcula o status da relação com base na afeição atual."""
        if not self.vivo:
            return "morto"
        if self.afeicao < 30:
            return "inimigo"
        elif self.afeicao < 50:
            return "desfavoravel"
        elif self.afeicao < 60:
            return "neutro"
        elif self.afeicao < 80:
            return "favoravel"
        elif self.afeicao < 95 or not self.eh_campeao:
            return "aliado"
        else:
            return "partner"

    def alterar_afeicao(self, delta: int) -> tuple[int, str, str]:
        """Altera a afeição (0-100) e retorna (nova_afeicao, rel_anterior, rel_nova)."""
        relacao_anterior = self.relacao
        self.afeicao = max(0, min(100, self.afeicao + delta))
        return self.afeicao, relacao_anterior, self.relacao

    # ------ ESTADO FÍSICO E DISPONIBILIDADE ------
    def esta_disponivel(self) -> bool:
        """Verifica se o NPC está vivo e consciente para agir ou conversar."""
        return self.vivo and not self.imobilizado

    def abater(self) -> str:
        self.vivo = False
        self.imobilizado = False
        return f"[MUNDO] {self.nome} foi abatido!"

    def imobilizar(self) -> str:
        if self.vivo:
            self.imobilizado = True
            return f"[MUNDO] {self.nome} foi imobilizado!"
        return f"[MUNDO] {self.nome} já está morto."

    def desimobilizar(self) -> str:
        if self.vivo and self.imobilizado:
            self.imobilizado = False
            return f"[MUNDO] {self.nome} recuperou os sentidos!"
        return ""

    # ------ POSSE DE FRAGMENTO ------
    def possui_fragmento(self) -> bool:
        return self.id_fragmento is not None

    def entregar_fragmento(self) -> tuple[str | None, str]:
        """Remove o fragmento da posse do NPC e retorna (id_fragmento, mensagem)."""
        if self.id_fragmento:
            id_frag = self.id_fragmento
            self.id_fragmento = None
            return id_frag, f"Você obteve o fragmento de {self.nome}!"
        return None, f"{self.nome} não possui nenhum fragmento."

    # ------ SERIALIZAÇÃO (JSON / SAVE) ------
    def to_dict(self) -> dict:
        return {
            "id": self.id_npc,
            "nome": self.nome,
            "afeicao": self.afeicao,
            "eh_campeao": self.eh_campeao,
            "vivo": self.vivo,
            "imobilizado": self.imobilizado,
            "id_fragmento": self.id_fragmento,
            "conhecido": self.conhecido,
        }

    @classmethod
    def from_dict(cls, dados: dict) -> "NPC":
        # Aceita tanto "id" quanto "id_npc" para total compatibilidade com seus JSONs
        id_resolvido = dados.get("id") or dados.get("id_npc", "")

        # Se o JSON antigo ainda tiver "faccao" em vez de "afeicao", converte automaticamente
        afeicao_inicial = dados.get("afeicao")
        if afeicao_inicial is None:
            mapa_legado = {"inimigo": 20, "desfavoravel": 40, "neutro": 50, "favoravel": 70, "aliado": 85}
            afeicao_inicial = mapa_legado.get(dados.get("faccao", "neutro"), 50)

        return cls(
            id_npc=id_resolvido,
            nome=dados.get("nome", "Desconhecido"),
            afeicao=afeicao_inicial,
            eh_campeao=dados.get("eh_campeao", bool(dados.get("id_fragmento"))),
            vivo=dados.get("vivo", True),
            imobilizado=dados.get("imobilizado", False),
            id_fragmento=dados.get("id_fragmento"),
            conhecido=dados.get("conhecido", False),
        )
