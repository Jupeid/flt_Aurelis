import copy
from core.npc import NPC


class Jogador:
    ATRIBUTOS_VALIDOS = ("forca", "destreza", "inteligencia", "sorte", "magia", "vitalidade")

    def __init__(self, nome: str = "Kael"):
        self.nome = nome
        self.nivel = 0
        self.experiencia = 0
        self.exp_proximo_nivel = 10
        self.pontos_disponiveis = 0
        self.pode_distribuir_pontos = False

        # --- ATRIBUTOS BASE ---
        self.forca = 0
        self.destreza = 1
        self.inteligencia = 1
        self.sorte = 1
        self.magia = 0       # 0 = sem magia (mp = magia * 5)
        self.vitalidade = 0  # 0 = hp base (20 + (vitalidade * 5))

        # Modificadores temporários: {"forca": 1}
        self.debuffs: dict[str, int] = {}
        self.buffs: dict[str, int] = {}

        # --- INVENTÁRIOS E EQUIPAMENTOS ---
        self.inventario: dict[str, int] = {}     # itens comuns acumulativos
        self.inventario_unico: set[str] = set()  # IDs de itens únicos/fragmentos
        self.catalogo_itens: dict = {}           # referência ao banco de ItemUnico
        self.equipamentos: dict[str, dict | None] = {
            "arma": None,
            "armadura": None,
            "acessorio": None,
        }
        self.dados_equipaveis: dict[str, dict] = {}  # dados de equipamentos carregados do banco de dados
        self.moedas = 0

        # --- MEMÓRIA E FLAGS DO MUNDO ---
        self.conhecimentos: set[str] = set()
        self.npcs: dict[str, NPC] = {}

        # --- FILA DE NOTIFICAÇÕES ENTRE CENAS ---
        self.notificacoes_pendentes: list[str] = []

        # --- STATUS DERIVADOS ---
        self.hp_base = 20
        self.hp_max = 20
        self.mp_max = 0
        self.hp_atual = self.hp_max
        self.mp_atual = self.mp_max
        self.recalcular_status_maximos(inicializacao=True)

    # ------ CATÁLOGO DE ITENS E ATRIBUTOS ------

    def vincular_catalogo_itens(self, catalogo: dict) -> None:
        """Vincula o dicionário de ItemUnico carregado pelo BancoDados e recalcula bônus."""
        self.catalogo_itens = catalogo or {}
        self.recalcular_status_maximos()

    def permitir_distribuicao(self, permitir: bool) -> None:
        self.pode_distribuir_pontos = permitir

    def obter_atributo_total(self, nome_atributo: str) -> int:
        nome = nome_atributo.lower().strip()
        valor_base = getattr(self, nome, 0)

        bonus_equipamentos = sum(
            item["bonus"].get(nome, 0)
            for item in self.equipamentos.values()
            if isinstance(item, dict) and "bonus" in item
        )

        bonus_fragmentos = 0
        for id_item in self.inventario_unico:
            item_obj = self.catalogo_itens.get(id_item)
            if item_obj is not None:
                bonus_dict = item_obj.bonus if hasattr(item_obj, "bonus") else item_obj.get("bonus", {})
                bonus_fragmentos += bonus_dict.get(nome, 0)

        bonus_buff = self.buffs.get(nome, 0)
        penalidade_debuff = self.debuffs.get(nome, 0)

        return max(0, valor_base + bonus_equipamentos + bonus_fragmentos + bonus_buff - penalidade_debuff)

    def recalcular_status_maximos(self, inicializacao: bool = False) -> None:
        self.hp_max = self.hp_base + (self.obter_atributo_total("vitalidade") * 5)
        self.mp_max = self.obter_atributo_total("magia") * 5

        if inicializacao:
            self.hp_atual = self.hp_max
            self.mp_atual = self.mp_max
        else:
            self.hp_atual = min(self.hp_atual, self.hp_max)
            self.mp_atual = min(self.mp_atual, self.mp_max)

    def alocar_pontos(self, nome_atributo: str) -> tuple[bool, str]:
        if not self.pode_distribuir_pontos:
            return False, "Você só pode distribuir pontos em áreas de descanso!"
        if self.pontos_disponiveis <= 0:
            return False, "Você não possui pontos disponíveis!"

        attr = nome_atributo.lower().strip()
        if attr not in self.ATRIBUTOS_VALIDOS:
            return False, "Atributo inválido."

        setattr(self, attr, getattr(self, attr) + 1)
        self.pontos_disponiveis -= 1

        if attr == "vitalidade":
            self.hp_atual += 5
        elif attr == "magia":
            self.mp_atual += 5

        self.recalcular_status_maximos()
        return True, f"+1 ponto aplicado em {attr.capitalize()}!"

    # ------ SERIALIZAÇÃO (SALVAR / CARREGAR) ------

    def para_dicionario(self, cena_atual: str) -> dict:
        """Serialização completa para salvar o estado total do jogo em JSON."""
        npcs_serializados = {}
        for id_npc, npc_obj in self.npcs.items():
            if hasattr(npc_obj, "to_dict"):
                npcs_serializados[id_npc] = npc_obj.to_dict()
            elif isinstance(npc_obj, dict):
                npcs_serializados[id_npc] = copy.deepcopy(npc_obj)

        return {
            "nome": self.nome,
            "nivel": self.nivel,
            "experiencia": self.experiencia,
            "exp_proximo_nivel": self.exp_proximo_nivel,
            "pontos_disponiveis": self.pontos_disponiveis,
            "pode_distribuir_pontos": self.pode_distribuir_pontos,
            "atributos": {attr: getattr(self, attr) for attr in self.ATRIBUTOS_VALIDOS},
            "buffs": dict(self.buffs),
            "debuffs": dict(self.debuffs),
            "inventario": dict(self.inventario),
            "inventario_unico": sorted(list(self.inventario_unico)),
            "equipamentos": copy.deepcopy(self.equipamentos),
            "moedas": self.moedas,
            "conhecimentos": sorted(list(self.conhecimentos)),
            "npcs": npcs_serializados,
            "hp_atual": self.hp_atual,
            "mp_atual": self.mp_atual,
            "notificacoes_pendentes": list(self.notificacoes_pendentes),
            "cena_atual": cena_atual,
            "dados_equipaveis": copy.deepcopy(self.dados_equipaveis),
        }

    @classmethod
    def do_dicionario(cls, dados: dict) -> tuple["Jogador", str]:
        """Desserialização completa a partir de um dicionário carregado do JSON."""
        p = cls(dados.get("nome", "Kael"))
        p.nivel = dados.get("nivel", 0)
        p.experiencia = dados.get("experiencia", 0)
        p.exp_proximo_nivel = dados.get("exp_proximo_nivel", 10)
        p.pontos_disponiveis = dados.get("pontos_disponiveis", 0)
        p.pode_distribuir_pontos = dados.get("pode_distribuir_pontos", False)

        for attr, val in dados.get("atributos", {}).items():
            if attr in cls.ATRIBUTOS_VALIDOS:
                setattr(p, attr, val)

        p.buffs = dict(dados.get("buffs", {}))
        p.debuffs = dict(dados.get("debuffs", {}))
        p.moedas = dados.get("moedas", 0)
        p.inventario = dict(dados.get("inventario", {}))
        p.inventario_unico = set(dados.get("inventario_unico", []))

        equip_salvos = dados.get("equipamentos", {})
        p.equipamentos = {
            "arma": equip_salvos.get("arma"),
            "armadura": equip_salvos.get("armadura"),
            "acessorio": equip_salvos.get("acessorio"),
        }
        p.dados_equipaveis = copy.deepcopy(dados.get("dados_equipaveis", {}))

        p.conhecimentos = set(dados.get("conhecimentos", []))

        npcs_salvos = dados.get("npcs") or dados.get("npc") or {}
        for id_npc, dados_npc in npcs_salvos.items():
            if isinstance(dados_npc, NPC):
                p.npcs[id_npc] = dados_npc
            elif isinstance(dados_npc, dict):
                if hasattr(NPC, "from_dict"):
                    p.npcs[id_npc] = NPC.from_dict(dados_npc)
                else:
                    p.npcs[id_npc] = NPC(
                        id_npc=dados_npc.get("id_npc", id_npc),
                        nome=dados_npc.get("nome", id_npc.capitalize()),
                        afeicao=dados_npc.get("afeicao", 50),
                        eh_campeao=dados_npc.get("eh_campeao", False),
                    )
                p.npcs[id_npc].conhecido = bool(dados_npc.get("conhecido", False))

        p.notificacoes_pendentes = list(dados.get("notificacoes_pendentes", []))

        p.recalcular_status_maximos()
        p.hp_atual = min(p.hp_max, dados.get("hp_atual", p.hp_max))
        p.mp_atual = min(p.mp_max, dados.get("mp_atual", p.mp_max))

        return p, dados.get("cena_atual", "prologo")

    # ------ TESTES DE ATRIBUTOS E CONDIÇÕES ------

    def tem_atributo(self, nome_atributo: str, valor_minimo: int) -> bool:
        return self.obter_atributo_total(nome_atributo) >= valor_minimo

    def tem_mp(self, custo_mp: int) -> bool:
        return self.mp_atual >= custo_mp

    def tem_moedas(self, custo: int) -> bool:
        return self.moedas >= custo

    def tem_item_unico(self, id_item: str) -> bool:
        return id_item in self.inventario_unico

    def tem_item(self, nome_item: str, quantidade: int = 1) -> bool:
        return self.inventario.get(nome_item, 0) >= quantidade

    def tem_conhecimento(self, id_conhecimento: str) -> bool:
        return id_conhecimento in self.conhecimentos

    def npc_esta_vivo(self, id_npc: str) -> bool:
        npc = self.npcs.get(id_npc)
        if npc is None:
            return False
        if isinstance(npc, dict):
            return npc.get("vivo", False)
        return getattr(npc, "vivo", False)

    # ------ ALTERAÇÕES DE STATUS (HP / MP) ------

    def consumir_mp(self, quantidade: int, notificar: bool = True) -> bool:
        if quantidade <= 0:
            return True
        if self.tem_mp(quantidade):
            self.mp_atual -= quantidade
            if notificar:
                self.adicionar_notificacao(f"[MAGIA] -{quantidade} MP (MP: {self.mp_atual}/{self.mp_max})")
            return True
        return False

    def receber_dano(self, dano: int, notificar: bool = True) -> bool:
        dano_real = max(0, dano)
        self.hp_atual = max(0, self.hp_atual - dano_real)
        if notificar:
            self.adicionar_notificacao(f"[DANO] Você sofreu {dano_real} de dano! (HP: {self.hp_atual}/{self.hp_max})")
        return self.hp_atual > 0

    def descansar(self, curar_debuffs: bool = False) -> None:
        """Restaura HP e MP ao máximo nas áreas de descanso."""
        self.hp_atual = self.hp_max
        self.mp_atual = self.mp_max
        self.limpar_todos_buffs()

        if curar_debuffs:
            self.curar_todos_debuffs()

        self.adicionar_notificacao(
            f"[DESCANSO] Energias restauradas! (HP: {self.hp_atual}/{self.hp_max} | MP: {self.mp_atual}/{self.mp_max})"
        )

    def receber_cura(self, quantidade: int, notificar: bool = True) -> tuple[int, str]:
        if quantidade <= 0:
            return 0, "A cura não teve efeito."
        if self.hp_atual >= self.hp_max:
            return 0, f"{self.nome} já está com a vida máxima!"

        hp_anterior = self.hp_atual
        self.hp_atual = min(self.hp_max, self.hp_atual + quantidade)
        cura_real = self.hp_atual - hp_anterior

        msg = f"[CURA] {self.nome} recuperou {cura_real} de vida! (HP: {self.hp_atual}/{self.hp_max})"
        if notificar:
            self.adicionar_notificacao(msg)
        return cura_real, msg

    # ------ SISTEMA DE BUFFS E DEBUFFS ------

    def aplicar_debuff(self, nome_atributo: str, quantidade: int) -> None:
        nome = nome_atributo.lower().strip()
        if nome not in self.ATRIBUTOS_VALIDOS or quantidade <= 0:
            return

        self.debuffs[nome] = self.debuffs.get(nome, 0) + quantidade
        self.recalcular_status_maximos()
        self.adicionar_notificacao(
            f"[CONDIÇÃO] Você sofreu uma penalidade! (-{quantidade} em {nome.upper()})"
        )

    def remover_debuff(self, nome_atributo: str, quantidade: int | None = None) -> None:
        nome = nome_atributo.lower().strip()
        if nome in self.debuffs:
            if quantidade is None or quantidade >= self.debuffs[nome]:
                del self.debuffs[nome]
            else:
                self.debuffs[nome] -= quantidade

            self.recalcular_status_maximos()
            self.adicionar_notificacao(
                f"[CURA] Sua condição melhorou! (Penalidade de {nome.upper()} removida/reduzida)"
            )

    def curar_todos_debuffs(self) -> None:
        if self.debuffs:
            self.debuffs.clear()
            self.recalcular_status_maximos()
            self.adicionar_notificacao("[CURA] Todos os seus ferimentos e debuffs foram totalmente curados!")

    def aplicar_buff(self, nome_atributo: str, quantidade: int) -> None:
        nome = nome_atributo.lower().strip()
        if nome not in self.ATRIBUTOS_VALIDOS or quantidade <= 0:
            return

        self.buffs[nome] = self.buffs.get(nome, 0) + quantidade
        self.recalcular_status_maximos()
        self.adicionar_notificacao(
            f"[BÊNÇÃO] Você recebeu um bônus! (+{quantidade} em {nome.upper()})"
        )

    def remover_buff(self, nome_atributo: str, quantidade: int | None = None) -> None:
        nome = nome_atributo.lower().strip()
        if nome in self.buffs:
            if quantidade is None or quantidade >= self.buffs[nome]:
                del self.buffs[nome]
            else:
                self.buffs[nome] -= quantidade
            self.recalcular_status_maximos()

    def limpar_todos_buffs(self) -> None:
        if self.buffs:
            self.buffs.clear()
            self.recalcular_status_maximos()

    # ------ MÉTODOS DE INVENTÁRIO E EQUIPAMENTOS ------

    def registrar_equipavel(self, item) -> dict | None:
        """Registra os dados de um item equipável no catálogo do jogador."""
        if hasattr(item, "to_dict"):
            item_dict = item.to_dict()
        elif isinstance(item, dict):
            item_dict = dict(item)
        else:
            return None

        nome = item_dict.get("nome")
        if nome and "slot" in item_dict:
            self.dados_equipaveis[nome] = item_dict
            return item_dict
        
    def equipar_item(self, item) -> bool:
        item_dict = self.registrar_equipavel(item)
        if not item_dict:
            return False

        nome_item = item_dict.get("nome", "Item Desconhecido")
        slot = item_dict.get("slot", "acessorio")

        if not self.tem_item(nome_item):
            self.adicionar_item(nome_item)

        # Se o exato mesmo item já está equipado neste slot, não desequipa nem notifica de novo
        atual_no_slot = self.equipamentos.get(slot)
        if isinstance(atual_no_slot, dict) and atual_no_slot.get("nome") == nome_item:
            return True

        if atual_no_slot is not None:
            self.desequipar_item(slot)

        self.equipamentos[slot] = item_dict
        self.recalcular_status_maximos()

        texto_bonus = ""
        if "bonus" in item_dict and isinstance(item_dict["bonus"], dict):
            lista_bonus = [
                f"+{val} {attr.upper()[:3]}"
                for attr, val in item_dict["bonus"].items()
                if val != 0
            ]
            if lista_bonus:
                texto_bonus = f" (Bônus: {', '.join(lista_bonus)})"

        self.adicionar_notificacao(
            f"[EQUIPAMENTO] Você equipou '{nome_item}' no slot [{slot.upper()}]{texto_bonus}!"
        )
        return True

    def desequipar_item(self, slot: str) -> dict | None:
        item_removido = self.equipamentos.get(slot)
        if item_removido is not None:
            self.registrar_equipavel(item_removido)  # Garante que o item ainda esteja registrado
            self.equipamentos[slot] = None
            nome_item = (
                item_removido.get("nome", "Item")
                if isinstance(item_removido, dict)
                else str(item_removido)
            )
            self.recalcular_status_maximos()
            self.adicionar_notificacao(
                f"[EQUIPAMENTO] '{nome_item}' foi desequipado do slot [{slot.upper()}]."
            )
            return item_removido
        return None

    def adicionar_item(self, nome_item: str, quantidade: int = 1) -> None:
        if quantidade <= 0:
            return
        self.inventario[nome_item] = self.inventario.get(nome_item, 0) + quantidade

    def remover_item(self, nome_item: str, quantidade: int = 1) -> bool:
        if self.inventario.get(nome_item, 0) >= quantidade:
            self.inventario[nome_item] -= quantidade
            if self.inventario[nome_item] <= 0:
                del self.inventario[nome_item]
            return True
        return False

    def adicionar_item_unico(self, id_reliquia: str) -> None:
        if id_reliquia not in self.inventario_unico:
            self.inventario_unico.add(id_reliquia)
            self.recalcular_status_maximos()
            item_obj = self.catalogo_itens.get(id_reliquia)
            nome_exibicao = item_obj.nome if item_obj and hasattr(item_obj, "nome") else id_reliquia
            self.adicionar_notificacao(f"[RELÍQUIA] Você obteve: {nome_exibicao}!")

    def remover_item_unico(self, id_reliquia: str) -> bool:
        if id_reliquia in self.inventario_unico:
            self.inventario_unico.discard(id_reliquia)
            self.recalcular_status_maximos()
            item_obj = self.catalogo_itens.get(id_reliquia)
            nome_exibicao = item_obj.nome if item_obj and hasattr(item_obj, "nome") else id_reliquia
            self.adicionar_notificacao(f"[PERDA] Você perdeu a relíquia: {nome_exibicao}!")
            return True
        return False

    # ------ MÉTODOS DE MOEDAS ------

    def adicionar_moedas(self, quantidade: int, multiplicador: float = 1.0) -> None:
        ganho_real = int(quantidade * multiplicador)
        if ganho_real <= 0:
            return
        self.moedas += ganho_real
        self.adicionar_notificacao(f"[MOEDAS] +{ganho_real}C (Total: {self.moedas}C).")

    def gastar_moedas(self, quantidade: int) -> bool:
        if quantidade <= 0:
            return True
        if self.tem_moedas(quantidade):
            self.moedas -= quantidade
            self.adicionar_notificacao(f"[MOEDAS] -{quantidade}C (Total: {self.moedas}C).")
            return True
        return False

    # ------ SISTEMA DE CONHECIMENTO INVISÍVEL ------

    def adicionar_conhecimento(self, chave_conhecimento: str) -> None:
        self.conhecimentos.add(chave_conhecimento)

    # ------ SISTEMA DE NÍVEL E EXPERIÊNCIA ------

    def ganhar_xp(self, quantidade_xp: int) -> bool:
        if quantidade_xp <= 0:
            return False

        self.experiencia += quantidade_xp
        self.adicionar_notificacao(f"[XP] Você ganhou {quantidade_xp} de experiência!")

        subiu_nivel = False
        while self.experiencia >= self.exp_proximo_nivel:
            self.experiencia -= self.exp_proximo_nivel
            self.nivel += 1
            self.pontos_disponiveis += 1
            self.exp_proximo_nivel = int(self.exp_proximo_nivel * 1.5)
            subiu_nivel = True
            self.adicionar_notificacao(
                f"[LEVEL UP!] Você alcançou o Nível {self.nivel}! "
                f"Você possui {self.pontos_disponiveis} ponto(s) de atributo disponível(is)!"
            )

        return subiu_nivel

    # ------ MÉTODOS DE NPCS ------

    def registrar_npc(
        self,
        id_npc: str | NPC,
        npc_objeto: NPC | None = None,
        nome: str | None = None,
        afeicao_inicial: int = 50,
        eh_campeao: bool = False,
    ) -> NPC:
        # Caso o motor.py passe o objeto NPC diretamente como primeiro argumento
        if isinstance(id_npc, NPC):
            npc_instancia = id_npc
            chave = npc_instancia.id_npc
            if chave not in self.npcs:
                self.npcs[chave] = npc_instancia
            return self.npcs[chave]

        if id_npc not in self.npcs:
            if isinstance(npc_objeto, NPC):
                self.npcs[id_npc] = npc_objeto
            else:
                self.npcs[id_npc] = NPC(
                    id_npc=id_npc,
                    nome=nome or id_npc.capitalize(),
                    afeicao=afeicao_inicial,
                    eh_campeao=eh_campeao,
                )
        return self.npcs[id_npc]

    def obter_npc(self, id_npc: str) -> NPC | None:
        return self.npcs.get(id_npc)

    def alterar_afeicao_npc(self, id_npc: str, delta: int, silenciar: bool = False) -> None:
        npc = self.obter_npc(id_npc)
        if not npc or not npc.vivo or delta == 0:
            return

        nova_afeicao, rel_antiga, rel_nova = npc.alterar_afeicao(delta)

        if not silenciar:
            sinal = "+" if delta > 0 else ""
            aviso = f"[RELAÇÃO] {npc.nome}: {sinal}{delta} de afeição ({nova_afeicao}/100 - {rel_nova.upper()})"
            if rel_antiga != rel_nova:
                aviso += f" | Status mudou de {rel_antiga.upper()} para {rel_nova.upper()}!"
            self.adicionar_notificacao(aviso)

    def aplicar_efeitos_npc(self, id_npc: str, acao: str, valor: int = 0) -> None:
        npc = self.obter_npc(id_npc)
        if not npc:
            return

        if acao == "imobilizar":
            npc.imobilizar()
            self.adicionar_notificacao(f"[NPC] {npc.nome} foi imobilizado.")
        elif acao == "abater":
            npc.abater()
            self.adicionar_notificacao(f"[NPC] {npc.nome} foi abatido.")
        elif acao == "afeicao":
            self.alterar_afeicao_npc(id_npc, valor)

    def verificar_relacao_npc(self, id_npc: str, relacao_esperada: str) -> bool:
        npc = self.obter_npc(id_npc)
        if not npc:
            return False
        return npc.relacao == relacao_esperada.lower()

    # ------ SISTEMA DE NOTIFICAÇÕES ------

    def adicionar_notificacao(self, mensagem: str) -> None:
        """Guarda uma notificação para ser exibida no próximo carregamento de cena."""
        self.notificacoes_pendentes.append(f"✨ {mensagem}")

    def consumir_notificacoes(self) -> list[str]:
        """Retorna todas as notificações acumuladas e limpa a fila."""
        notifs = list(self.notificacoes_pendentes)
        self.notificacoes_pendentes.clear()
        return notifs

    def obter_resumo_status(self) -> dict:
        """Retorna um pacote de dados limpos para qualquer UI montar seu HUD."""
        equipamentos_formatados = {}
        for slot, item in self.equipamentos.items():
            if isinstance(item, dict):
                equipamentos_formatados[slot] = item.get("nome", "Item")
            elif item is not None:
                equipamentos_formatados[slot] = str(item)
            else:
                equipamentos_formatados[slot] = "Vazio"

        return {
            "nome": self.nome,
            "nivel": self.nivel,
            "exp": f"{self.experiencia}/{self.exp_proximo_nivel}",
            "pontos": self.pontos_disponiveis,
            "hp": f"{self.hp_atual}/{self.hp_max}",
            "hp_atual": self.hp_atual,
            "hp_max": self.hp_max,
            "mp": f"{self.mp_atual}/{self.mp_max}",
            "mp_atual": self.mp_atual,
            "mp_max": self.mp_max,
            "moedas": self.moedas,
            "atributos": {
                attr: self.obter_atributo_total(attr)
                for attr in self.ATRIBUTOS_VALIDOS
            },
            "equipamentos": equipamentos_formatados,
            "inventario": dict(self.inventario),
            "inventario_unico": sorted(list(self.inventario_unico)),
            "buffs": dict(self.buffs),
            "debuffs": dict(self.debuffs),
        }