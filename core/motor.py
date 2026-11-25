import random
from core.jogador import Jogador
from core.banco_dados import BancoDeDados


class MotorJogo:
    """Coração lógico do jogo: executa cenas, testes, escolhas e regras sem depender de UI."""

    def __init__(self, idioma: str = "pt"):
        self.banco = BancoDeDados(idioma=idioma)
        self.banco.carregar_tudo()
        self.jogador: Jogador | None = None
        self.cena_atual_id: str = "boas_vindas"
        self.exibir_imagens: bool = True
        self.background_atual: str | None = None

    def t(self, chave: str, padrao: str | None = None) -> str:
        """Atalho rápido para buscar textos traduzidos da interface."""
        return self.banco.obter_texto_ui(chave, padrao)

    def mudar_idioma(self, novo_idioma: str) -> None:
        """Recarrega os bancos de dados no novo idioma preservando o estado do jogador."""
        self.banco.definir_idioma(novo_idioma)
        if self.jogador:
            self.jogador.vincular_catalogo_itens(self.banco.itens)
            for id_npc, npc_traduzido in self.banco.npcs.items():
                if id_npc in self.jogador.npcs:
                    self.jogador.npcs[id_npc].nome = npc_traduzido.nome

    def iniciar_novo_jogo(self, nome_jogador: str, cena_inicial: str = "boas_vindas") -> None:
        """Cria um jogador zerado, vincula o catálogo de itens e registra os 8 Campeões."""
        self.jogador = Jogador(nome=nome_jogador)
        self.jogador.vincular_catalogo_itens(self.banco.itens)
        self._ultima_cena_entrada_processada = None
        self.background_atual: str | None = None

        from core.npc import NPC
        for id_npc, npc_base in self.banco.npcs.items():
            npc_novo = NPC.from_dict(npc_base.to_dict())
            npc_novo.conhecido = False
            self.jogador.registrar_npc(npc_novo)

        self.cena_atual_id = cena_inicial

    def carregar_sessao(self, jogador: Jogador, cena_atual_id: str) -> None:
        """Restaura uma sessão carregada do savegame."""
        self.jogador = jogador
        self.jogador.vincular_catalogo_itens(self.banco.itens)
        self._ultima_cena_entrada_processada = None
        self.background_atual: str | None = None

        from core.npc import NPC
        for id_npc, npc_base in self.banco.npcs.items():
            if id_npc not in self.jogador.npcs:
                npc_novo = NPC.from_dict(npc_base.to_dict())
                npc_novo.conhecido = False
                self.jogador.registrar_npc(npc_novo)

        self.cena_atual_id = cena_atual_id

    # ------ AVALIAÇÃO DE REQUISITOS E TESTES OCULTOS ------

    def _avaliar_requisito_unico(self, req: dict) -> bool:
        """Avalia um único dicionário de requisito antes da eventual inversão por 'negado'."""
        if not self.jogador:
            return True

        tipo = req.get("tipo")

        if tipo == "atributo":
            return self.jogador.tem_atributo(req["nome"], req["valor"])
        elif tipo == "magia":
            nome_attr = req.get("nome", "magia")
            val_min = req.get("valor", 1)
            custo = req.get("custo_mp", 0)
            return self.jogador.tem_atributo(nome_attr, val_min) and self.jogador.tem_mp(custo)
        elif tipo == "item":
            return self.jogador.tem_item(req["nome"], req.get("quantidade", 1))
        elif tipo == "item_unico":
            chave_item = req.get("nome") or req.get("id_item", "")
            return self.jogador.tem_item_unico(chave_item)
        elif tipo == "moedas":
            return self.jogador.tem_moedas(req["valor"])
        elif tipo in ("conhecimento", "flag"):
            return self.jogador.tem_conhecimento(req["nome"])
        elif tipo == "relacao_npc":
            return self.jogador.verificar_relacao_npc(req["id_npc"], req["relacao"])
        elif tipo == "npc_vivo":
            npc = self.jogador.npcs.get(req["id_npc"])
            return bool(npc and npc.vivo == req.get("valor", True))
        elif tipo == "hp_minimo":
            return self.jogador.hp_atual >= req["valor"]
        elif tipo == "mp_minimo":
            return self.jogador.mp_atual >= req["valor"]

        return True

    def testar_requisitos(self, lista_requisitos: list[dict]) -> bool:
        """Valida se o jogador cumpre todos os requisitos de uma opção ou bloco (com suporte a 'negado')."""
        if not self.jogador or not lista_requisitos:
            return True

        for req in lista_requisitos:
            resultado = self._avaliar_requisito_unico(req)
            if req.get("negado", False):
                resultado = not resultado
            if not resultado:
                return False

        return True

    def avaliar_condicao_oculta(self, condicao: dict) -> bool:
        """Avalia rolagem de sorte ou requisito silencioso durante a narrativa."""
        if not self.jogador: return False
        tipo = condicao.get("tipo")     

        if tipo in ["sorte", "chance_sorte"]:
            base = condicao.get("requisito_base", 90)
            bonus = condicao.get("bonus_por_ponto", 10)
            sorte_total = self.jogador.obter_atributo_total("sorte")
            limite = max(0, base - ((sorte_total - 1) * bonus))
            dado = random.randint(0, 100)

            sucesso = dado >= limite
            status = "SUCESSO!" if sucesso else "FALHA!"
            self.jogador.adicionar_notificacao(
                f"[SORTE] Rolou {dado}/100 (Meta: {limite}+ | SOR: {sorte_total}) - {status}"
            )
            return sucesso

        return self.testar_requisitos([condicao])

    # ------ PROCESSAMENTO DE EFEITOS ------

    def aplicar_efeitos(self, origem: dict) -> None:
        """Executa todos os impactos de uma cena, bloco ou opção escolhida."""
        if not self.jogador or not origem:
            return

        if "exibir_imagem" in origem:
            self.exibir_imagens = bool(origem["exibir_imagem"])
        elif "exibir_imagens" in origem:
            self.exibir_imagens = bool(origem["exibir_imagens"])

        if "equipar_item" in origem:
            dados_eq = origem["equipar_item"]
            lista_eq = dados_eq if isinstance(dados_eq, list) else [dados_eq]
            for item_eq in lista_eq:
                self.jogador.equipar_item(item_eq)

        if "ganho_equipavel" in origem:
            dados_eq = origem["ganho_equipavel"]
            lista_eq = dados_eq if isinstance(dados_eq, list) else [dados_eq]
            for item_eq in lista_eq:
                item_dict = self.jogador.registrar_equipavel(item_eq)
                if item_dict:
                    nome_eq = item_dict.get("nome", "Equipamento")
                    self.jogador.adicionar_item(nome_eq, 1)
                    self.jogador.adicionar_notificacao(f"[ITEM] Você obteve o equipamento: {nome_eq}!")

        if "custo_mp" in origem:
            self.jogador.consumir_mp(origem["custo_mp"])

        if "dano_recebido" in origem:
            self.jogador.receber_dano(origem["dano_recebido"])

        if "curar_hp" in origem:
            self.jogador.receber_cura(origem["curar_hp"])

        if "curar_mp" in origem:
            qtd = origem["curar_mp"]
            if qtd > 0:
                mp_anterior = self.jogador.mp_atual
                self.jogador.mp_atual = min(self.jogador.mp_max, self.jogador.mp_atual + qtd)
                mp_recuperado = self.jogador.mp_atual - mp_anterior
                if mp_recuperado > 0:
                    self.jogador.adicionar_notificacao(
                        f"[MAGIA] +{mp_recuperado} MP (MP: {self.jogador.mp_atual}/{self.jogador.mp_max})"
                    )

        if "ganho_xp" in origem:
            self.jogador.ganhar_xp(origem["ganho_xp"])

        if "ganho_moedas" in origem:
            self.jogador.adicionar_moedas(origem["ganho_moedas"])

        if "gasto_moedas" in origem:
            self.jogador.gastar_moedas(origem["gasto_moedas"])

        if "ganho_item" in origem:
            item = origem["ganho_item"]
            self.jogador.adicionar_item(item["nome"], item.get("quantidade", 1))

        for chave_rem in ("remover_item", "perda_item"):
         if chave_rem in origem:
             item = origem[chave_rem]
             self.jogador.remover_item(item["nome"], item.get("quantidade", 1))

        if "ganho_item_unico" in origem:
         self.jogador.adicionar_item_unico(origem["ganho_item_unico"])

        for chave_rem_u in ("remover_item_unico", "perda_item_unico"):
         if chave_rem_u in origem:
             self.jogador.remover_item_unico(origem[chave_rem_u])

        if "conhecimento" in origem:
            self.jogador.adicionar_conhecimento(origem["conhecimento"])

        if "novos_npcs" in origem:
            for dados_novo in origem["novos_npcs"]:
                id_novo = dados_novo["id_npc"]
                nome_novo = dados_novo.get("nome") or id_novo.split("_")[-1].capitalize()
                faccao = str(dados_novo.get("faccao", "neutro")).lower()
                afeicao_ini = 75 if faccao == "aliado" else (20 if faccao == "inimigo" else 50)

                npc = self.jogador.registrar_npc(
                    id_npc=id_novo,
                    nome=nome_novo,
                    afeicao_inicial=afeicao_ini,
                    eh_campeao=False,
                )
                if not getattr(npc, "conhecido", False):
                    npc.conhecido = True
                    self.jogador.adicionar_notificacao(f"[NPC] Você conheceu {npc.nome}!")

        if "conhecer_npc" in origem:
            dados_npc = origem["conhecer_npc"]
            lista_itens = dados_npc if isinstance(dados_npc, list) else [dados_npc]
            for item_npc in lista_itens:
                if isinstance(item_npc, dict):
                    id_npc = item_npc["id_npc"]
                    nome_custom = item_npc.get("nome")
                    faccao = str(item_npc.get("faccao", "neutro")).lower()
                    afeicao_ini = item_npc.get(
                        "afeicao",
                        75 if faccao == "aliado" else (20 if faccao == "inimigo" else 50),
                    )
                else:
                    id_npc = str(item_npc)
                    nome_custom = None
                    afeicao_ini = 50

                npc = self.jogador.npcs.get(id_npc)
                if npc is None:
                    # Tenta localizar Campeão no npcs.json caso tenha sido passado sem prefixo
                    chave_curta = id_npc.replace("campeao_", "").lower()
                    for candidato in self.jogador.npcs.values():
                        if candidato.id_npc.lower() in (id_npc.lower(), chave_curta):
                            npc = candidato
                            break

                # Se não é um Campeão do JSON, registra dinamicamente como NPC comum!
                if npc is None:
                    # Extrai um nome limpo a partir do ID (ex: "father_eskil" -> "Eskil")
                    nome_inferido = nome_custom or id_npc.split("_")[-1].capitalize()
                    npc = self.jogador.registrar_npc(
                        id_npc=id_npc,
                        nome=nome_inferido,
                        afeicao_inicial=afeicao_ini,
                        eh_campeao=False,
                    )

                if not getattr(npc, "conhecido", False):
                    npc.conhecido = True
                    self.jogador.adicionar_notificacao(f"[NPC] Você conheceu {npc.nome}!")

        if "afeicao_npc" in origem:
            dados_af = origem["afeicao_npc"]
            lista_af = dados_af if isinstance(dados_af, list) else [dados_af]
            for af in lista_af:
                self.jogador.alterar_afeicao_npc(af["id_npc"], af["delta"])

        if "entregar_fragmento_npc" in origem:
            id_npc = origem["entregar_fragmento_npc"]
            npc = self.jogador.npcs.get(id_npc)
            if npc and npc.possui_fragmento():
                id_frag, msg = npc.entregar_fragmento()
                if id_frag:
                    self.jogador.adicionar_item_unico(id_frag)
                    self.jogador.adicionar_notificacao(f"✨ {msg}")

        if "abater_npc" in origem:
            npc = self.jogador.npcs.get(origem["abater_npc"])
            if npc:
                self.jogador.adicionar_notificacao(npc.abater())

        if "imobilizar_npc" in origem:
            npc = self.jogador.npcs.get(origem["imobilizar_npc"])
            if npc:
                self.jogador.adicionar_notificacao(npc.imobilizar())

        if "aplicar_debuff" in origem:
            dados = origem["aplicar_debuff"]
            lista = dados if isinstance(dados, list) else [dados]
            for item in lista:
                self.jogador.aplicar_debuff(item["atributo"], item.get("valor", 1))

        if "remover_debuff" in origem:
            dados = origem["remover_debuff"]
            if dados == "todos":
                self.jogador.curar_todos_debuffs()
            elif isinstance(dados, dict):
                self.jogador.remover_debuff(dados["atributo"], dados.get("valor"))

    # ------ EXECUÇÃO DA CENA ATUAL ------

    def obter_estado_cena_atual(self) -> dict:
        """Processa a cena atual e retorna um pacote estruturado pronto para qualquer UI."""
        if not self.jogador: return {"erro": "Nenhum jogador ativo.", "titulo": "Erro", "paragrafos": [], "opcoes": []}
        cena = self.banco.cenas.get(self.cena_atual_id)
        if not cena:
            return {
                "erro": f"Cena '{self.cena_atual_id}' não encontrada.",
                "titulo": "Erro",
                "paragrafos": [],
                "opcoes_disponiveis": [],
            }

        self.jogador.pode_distribuir_pontos = bool(cena.get("area_descanso", False))

        if cena.get("descansar", False):
            self.jogador.descansar(curar_debuffs=cena.get("curar_debuffs", False))

        if cena.get("limpar_background"):
            self.background_atual = None
        elif "background" in cena:
            # Se no JSON você escrever "background": "assets/...", ele troca;
            # se escrever "background": "" ou null, ele limpa o fundo.
            self.background_atual = cena["background"] or None

        # Evita disparar efeitos de entrada duas vezes se a UI apenas re-renderizar a mesma cena
        if getattr(self, "_ultima_cena_entrada_processada", None) != self.cena_atual_id:
            self._ultima_cena_entrada_processada = self.cena_atual_id
            self.aplicar_efeitos(cena)
            if "efeitos_entrada" in cena:
                self.aplicar_efeitos(cena["efeitos_entrada"])

        notificacoes = self.jogador.consumir_notificacoes()
        if "notificacao" in cena:
            notif_est = cena["notificacao"]
            if isinstance(notif_est, list):
                notificacoes.extend([f"✨ {m}" for m in notif_est])
            else:
                notificacoes.append(f"✨ {notif_est}")

        paragrafos, proxima_dinamica = self._construir_blocos_narrativos(cena)

        opcoes_brutas = cena.get("opcoes", {})
        if isinstance(opcoes_brutas, dict):
            iterador_opcoes = [(letra, dados) for letra, dados in opcoes_brutas.items()]
        else:
            letras = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            iterador_opcoes = [(letras[i], dados) for i, dados in enumerate(opcoes_brutas)]

        opcoes_validas = []
        for rotulo_chave, op in iterador_opcoes:
            op_resolvida = dict(op)

            # Resolve variantes condicionais da mesma opção (ex: estados diferentes de NPCs)
            if "variantes" in op_resolvida:
                variante_escolhida = None
                for var in op_resolvida["variantes"]:
                    conds_var = var.get("condicoes") or var.get("requisitos", [])
                    if self.testar_requisitos(conds_var):
                        variante_escolhida = var
                        break
                if variante_escolhida is None:
                    continue
                op_resolvida.update(variante_escolhida)

            rotulo_exibicao = op_resolvida.get("rotulo", rotulo_chave)
            requisitos = op_resolvida.get("requisitos", [])
            if self.testar_requisitos(requisitos):
                opcoes_validas.append({**op_resolvida, "_rotulo": rotulo_exibicao})
            elif op_resolvida.get("mostrar_bloqueada", True):
                opcoes_validas.append({**op_resolvida, "_rotulo": rotulo_exibicao, "_bloqueada": True})
        
        return {
            "id_cena": self.cena_atual_id,
            "titulo": cena.get("titulo", ""),
            "limpar_tela": cena.get("limpar_tela", False),
            "imagem": cena.get("imagem"),
            "background": self.background_atual,
            "exibir_hud": cena.get("HUD", True),
            "permite_descanso": bool(cena.get("permite_descanso", False)),
            "area_descanso": bool(cena.get("area_descanso", False)),
            "notificacoes": notificacoes,
            "paragrafos": paragrafos,
            "proxima_cena_direta": cena.get("proxima_cena"),
            "proxima_cena_dinamica": proxima_dinamica,
            "opcoes": opcoes_validas,
            "combate": cena.get("combate"),
            "pode_equipar": bool(cena.get("pode_equipar", not bool(cena.get("combate")))),
        }

    def _construir_blocos_narrativos(self, cena: dict) -> tuple[list[str], str | None]:
        if not self.jogador: return [], None
        paragrafos = []
        proxima_cena_dinamica = None

        if cena.get("narrativa"):
            paragrafos.append(cena["narrativa"])

        for bloco in cena.get("blocos_sequenciais", []):
            if "check_oculto" in bloco:
                passou = self.avaliar_condicao_oculta(bloco["check_oculto"])
                notifs = self.jogador.consumir_notificacoes()
                if notifs:
                    paragrafos.append("\n".join(notifs))

                if passou:
                    ramo = bloco.get("sucesso", {})
                    if ramo.get("texto"):
                        paragrafos.append(ramo["texto"])
                    if ramo.get("imagem"): paragrafos.append(f"[IMG: {ramo['imagem']}]")
                    self.aplicar_efeitos(ramo.get("efeitos", {}))

                    sub_passou = False
                    for sub in ramo.get("sub_checks", []):
                        if self.avaliar_condicao_oculta(sub["check"]):
                            sub_passou = True
                            self.aplicar_efeitos(sub.get("efeitos", {}))
                            notifs_sub = self.jogador.consumir_notificacoes()
                            if notifs_sub:
                                paragrafos.append("\n".join(notifs_sub))
                            if sub.get("texto"):
                                paragrafos.append(sub["texto"])
                            proxima_cena_dinamica = sub.get("proxima_cena")
                            break

                    if not sub_passou:
                        if ramo.get("texto_falha_sub_checks"):
                            paragrafos.append(ramo["texto_falha_sub_checks"])
                        if ramo.get("proxima_cena"):
                            proxima_cena_dinamica = ramo["proxima_cena"]
                else:
                    ramo = bloco.get("falha", {})
                    if ramo.get("texto"):
                        paragrafos.append(ramo["texto"])
                    if ramo.get("imagem"): paragrafos.append(f"[IMG: {ramo['imagem']}]")
                    self.aplicar_efeitos(ramo)
                    self.aplicar_efeitos(ramo.get("efeitos", {}))

                    notifs_falha = self.jogador.consumir_notificacoes()
                    if notifs_falha:
                        paragrafos.append("\n".join(notifs_falha))

                    dados_resgate = ramo.get("check_resgate") or ramo.get("cheque_resgate")
                    if dados_resgate:
                        passou_resg = self.avaliar_condicao_oculta(dados_resgate)
                        notifs_resg = self.jogador.consumir_notificacoes()
                        if notifs_resg:
                            paragrafos.append("\n".join(notifs_resg))
                        resg = ramo.get("sucesso_resgate", {}) if passou_resg else ramo.get("falha_resgate", {})
                        if resg.get("texto"):
                            paragrafos.append(resg["texto"])
                        if resg.get("imagem"):
                            paragrafos.append(f"[IMG: {resg['imagem']}]")
                        proxima_cena_dinamica = resg.get("proxima_cena")
                    elif ramo.get("proxima_cena"):
                        proxima_cena_dinamica = ramo["proxima_cena"]

            elif "texto" in bloco:
                reqs = list(bloco.get("requisitos", []))
                if "condicao" in bloco:
                    cond = bloco["condicao"]
                    reqs.extend(cond if isinstance(cond, list) else [cond])

                if self.testar_requisitos(reqs):
                    paragrafos.append(bloco["texto"])
                    if bloco.get("imagem"):
                        paragrafos.append(f"[IMG: {bloco['imagem']}]")
                    self.aplicar_efeitos(bloco)
                    self.aplicar_efeitos(bloco.get("efeitos", {}))
                    destino = bloco.get("proxima_cena") or bloco.get("redirecionar_cena")
                    if destino:
                        proxima_cena_dinamica = destino
                elif bloco.get("texto_alternativo"):
                    paragrafos.append(bloco["texto_alternativo"])
                    if bloco.get("imagem_alternativa"):
                        paragrafos.append(f"[IMG: {bloco['imagem_alternativa']}]")

        return paragrafos, proxima_cena_dinamica

    def escolher_opcao(self, opcao: dict) -> dict:
        """Executa uma opção selecionada pelo jogador e avança para a próxima cena."""
        if opcao.get("_bloqueada"):
            return {"sucesso": False, "mensagem": "Requisitos insuficientes."}

        self.aplicar_efeitos(opcao)
        self.aplicar_efeitos(opcao.get("efeitos", {}))

        proxima = opcao.get("proxima_cena")
        if proxima:
            self.cena_atual_id = proxima

        return {
            "sucesso": True,
            "proxima_cena": proxima,
            "narrativa_consequencia": opcao.get("narrativa_consequencia", ""),
        }