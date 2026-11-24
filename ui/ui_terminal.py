import os
from core.motor import MotorJogo
from core.salvamento import salvar_progresso, carregar_progresso
from ui.formatador import FormatadorLivro


class UITerminal:
    """Interface de linha de comando (CLI) conectada ao MotorJogo."""

    def __init__(self, motor: MotorJogo):
        self.motor = motor

    def limpar_console(self) -> None:
        os.system("cls" if os.name == "nt" else "clear")

    def pausar(self, msg: str = "\nPressione ENTER para continuar...") -> None:
        input(msg)

    def iniciar(self) -> None:
        """Loop principal do menu inicial no terminal."""
        while True:
            self.limpar_console()
            print("=" * 60)
            print("        AURELIS: O CAMINHO DA ALVORADA")
            print("=" * 60)
            print("[1] ⚔️  Iniciar Novo Jogo")
            print("[2] 📜 Carregar Jogo")
            print(f"[3] 🌐 Idioma atual: {self.motor.banco.idioma.upper()}")
            print("[4] ℹ️  Sobre o Jogo")
            print("[0] 🚪 Sair")
            print("=" * 60)

            escolha = input("Escolha uma opção: ").strip()

            if escolha == "1":
                self.limpar_console()
                nome = "Kael"
                self.motor.iniciar_novo_jogo(nome_jogador=nome, cena_inicial="prologo")
                self.loop_jogo()

            elif escolha == "2":
                jogador, cena_salva, msg = carregar_progresso()
                print(f"\n{msg}")
                if jogador and cena_salva:
                    self.motor.carregar_sessao(jogador, cena_salva)
                    self.pausar()
                    self.loop_jogo()
                else:
                    self.pausar()

            elif escolha == "3":
                novo_idioma = "en" if self.motor.banco.idioma == "pt" else "pt"
                self.motor.mudar_idioma(novo_idioma)
                print(f"\nIdioma alterado para: {novo_idioma.upper()}")
                self.pausar()

            elif escolha == "4":
                self.limpar_console()
                print("=== SOBRE O JOGO ===")
                print("Aurelis: O Caminho da Alvorada")
                print("RPG textual interativo em arquitetura modular.\n")
                self.pausar()

            elif escolha == "0":
                print("\nEncerrando jornada...")
                break

    def loop_jogo(self) -> None:
        """Loop principal de leitura de cenas, escolhas e menus de personagem."""
        primeira_cena = True

        while True:
            id_cena = self.motor.cena_atual_id

            if id_cena == "MENU_INICIAL":
                break

            if id_cena not in self.motor.banco.cenas:
                self.limpar_console()
                print("[CAPÍTULO EM CONSTRUÇÃO]")
                print("Esta parte da história ainda não foi escrita.")
                self.pausar("\nPressione ENTER para voltar ao Menu Inicial...")
                break

            estado = self.motor.obter_estado_cena_atual()

            # Se houve desvio automático por check oculto
            if estado.get("proxima_cena_dinamica"):
                self.motor.cena_atual_id = estado["proxima_cena_dinamica"]
                continue

            if estado.get("limpar_tela") or primeira_cena:
                self.limpar_console()
                primeira_cena = False
            else:
                print("\n" + "─" * 80 + "\n")

            # 1. HUD
            if estado.get("exibir_hud") and self.motor.jogador:
                print(self.motor.jogador.obter_hud())
                print("-" * 80)

            # 2. Título e Notificações
            if estado.get("titulo"):
                print(f"\n=== {estado['titulo'].upper()} ===\n")

            if estado.get("notificacoes"):
                for notif in estado["notificacoes"]:
                    print(notif)
                print("-" * 45)

            # 3. Narrativa formatada
            for paragrafo in estado.get("paragrafos", []):
                texto_interp = FormatadorLivro.interpolar_variaveis(paragrafo, self.motor.jogador)
                print(FormatadorLivro.formatar_para_terminal(texto_interp))
                print()

            # Verifica morte durante eventos automáticos da cena
            if self.motor.jogador.hp_atual <= 0:
                print("\n💀 GAME OVER: Você sucumbiu aos ferimentos na jornada...")
                self.pausar()
                break

            # 4. Opções da cena + Atalhos de Ficha/Inventário
            opcoes = estado.get("opcoes", [])
            mapa_opcoes = {}

            print("-" * 80)
            if opcoes:
                for op in opcoes:
                    rotulo = op.get("_rotulo", "?").upper()
                    texto_op = FormatadorLivro.interpolar_variaveis(op["texto"], self.motor.jogador)
                    if op.get("_bloqueada"):
                        print(f"[{rotulo}] 🔒 {texto_op} (Requisitos não atendidos)")
                    else:
                        print(f"[{rotulo}] {texto_op}")
                        mapa_opcoes[rotulo] = op
            elif estado.get("proxima_cena_direta"):
                print("[C] ➡️  Continuar")
                mapa_opcoes["C"] = {"proxima_cena": estado["proxima_cena_direta"]}

            # Barra de atalhos rápidos do jogador
            atalhos = ["[F] Ficha/Atributos", "[I] Inventário/Fragmentos", "[N] Relações (NPCs)"]
            if estado.get("permite_descanso"):
                atalhos.append("[S] 💾 Salvar")
            atalhos.append("[M] Menu")
            print("\n" + " | ".join(atalhos))

            comando = input("\nSua escolha: ").strip().upper()

            if comando == "F":
                self.exibir_ficha(pode_distribuir=estado.get("permite_descanso", False))
                primeira_cena = True
            elif comando == "I":
                self.exibir_inventario()
                primeira_cena = True
            elif comando == "N":
                self.exibir_relacoes()
                primeira_cena = True
            elif comando == "S" and estado.get("permite_descanso"):
                _, msg_save = salvar_progresso(self.motor.jogador, self.motor.cena_atual_id)
                print(f"\n{msg_save}")
                self.pausar()
                primeira_cena = True
            elif comando == "M":
                confirma = input("Voltar ao menu inicial? Progresso não salvo será perdido (S/N): ").strip().upper()
                if confirma == "S":
                    break
                primeira_cena = True
            elif comando in mapa_opcoes:
                opcao_escolhida = mapa_opcoes[comando]
                resultado = self.motor.escolher_opcao(opcao_escolhida)

                if self.motor.jogador.hp_atual <= 0:
                    print("\n💀 GAME OVER: Você sucumbiu aos ferimentos na jornada...")
                    self.pausar()
                    break

                if resultado.get("narrativa_consequencia"):
                    print("\n" + "─" * 45)
                    texto_cons = FormatadorLivro.interpolar_variaveis(
                        resultado["narrativa_consequencia"], self.motor.jogador
                    )
                    print(FormatadorLivro.formatar_para_terminal(texto_cons))
                    self.pausar()
            else:
                print("\n[!] Opção inválida ou bloqueada.")
                self.pausar()
                primeira_cena = True

    # ------ TELAS AUXILIARES DO JOGADOR ------

    def exibir_ficha(self, pode_distribuir: bool = False) -> None:
        while True:
            self.limpar_console()
            j = self.motor.jogador
            print(f"=== FICHA DE {j.nome.upper()} (Nível {j.nivel}) ===")
            print(f"HP: {j.hp_atual}/{j.hp_max} | MP: {j.mp_atual}/{j.mp_max} | XP: {j.xp}/{j.xp_proximo_nivel} | Moedas: {j.moedas}")
            print(f"Pontos disponíveis: {j.pontos_disponiveis} {'(Área de Descanso ativa!)' if pode_distribuir else '(Bloqueado fora de descanso)'}\n")

            atributos = ["vitalidade", "forca", "destreza", "inteligencia", "magia", "sorte"]
            for idx, attr in enumerate(atributos, 1):
                base = getattr(j, attr)
                total = j.obter_atributo_total(attr)
                extra = f" (Total: {total})" if total != base else ""
                print(f"[{idx}] {attr.capitalize():<14}: {base}{extra}")

            if j.debuffs:
                print(f"\n⚠️ Debuffs ativos: {j.debuffs}")

            if pode_distribuir and j.pontos_disponiveis > 0:
                print("\nDigite o número (1-6) para gastar 1 ponto ou [0] para voltar:")
                op = input("> ").strip()
                if op == "0":
                    break
                if op.isdigit() and 1 <= int(op) <= 6:
                    attr_escolhido = atributos[int(op) - 1]
                    _, msg = j.alocar_ponto(attr_escolhido)
                    print(f"\n{msg}")
                    self.pausar()
            else:
                self.pausar("\nPressione ENTER para voltar à cena...")
                break

    def exibir_inventario(self) -> None:
        self.limpar_console()
        j = self.motor.jogador
        print("=== INVENTÁRIO ===\n")

        print("📦 Itens Comuns:")
        if not j.inventario:
            print("  (Vazio)")
        else:
            for nome, qtd in j.inventario.items():
                print(f"  • {nome} x{qtd}")

        print("\n✨ Relíquias & Itens Únicos:")
        if not j.inventario_unico:
            print("  (Nenhum item obtido ainda)")
        else:
            for id_item in sorted(j.inventario_unico):
                item_obj = self.motor.banco.itens.get(id_item)
                if item_obj:
                    bonus_txt = ", ".join(f"+{v} {k.upper()[:3]}" for k, v in item_obj.bonus.items())
                    print(f"  ★ {item_obj.nome} [{bonus_txt}]")
                    print(f"    {item_obj.descricao}")
                    if item_obj.portador_original:
                        print(f"    Portador Original: {item_obj.portador_original}")
                    if item_obj.historia_origem:
                        print(f"    Origem: {item_obj.historia_origem}")
                else:
                    print(f"  ★ {id_item}")

        self.pausar("\nPressione ENTER para voltar à cena...")

    def exibir_relacoes(self) -> None:
        self.limpar_console()
        j = self.motor.jogador
        print("=== RELAÇÕES ===\n")

        conhecidos = [npc for npc in j.npcs.values() if getattr(npc, "conhecido", False)]

        if not conhecidos:
            print("Você ainda não conheceu ninguém nesta jornada.")
        else:
            for npc in conhecidos:
                status_vida = (
                    "💀 Morto"
                    if not npc.vivo
                    else ("⛓️ Imobilizado" if npc.imobilizado else "🟢 Ativo")
                )
                print(
                    f"• {npc.nome:<14} | Relação: {npc.relacao.upper():<12} ({npc.afeicao}/100) | {status_vida}"
                )

        self.pausar("\nPressione ENTER para voltar à cena...")
