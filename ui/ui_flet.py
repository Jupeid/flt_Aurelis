import os
import flet as ft
import re
from core.motor import MotorJogo
from core.salvamento import salvar_progresso, carregar_progresso
from ui.formatador import FormatadorLivro
from ui.config import TEMA_ESCURO, TEMA_CLARO
from utils.paths import obter_caminho_recurso


class UIFlet:
    """Interface gráfica responsiva em Flet 1.0+ (Desktop e Android) conectada ao MotorJogo."""

    def __init__(self, page: ft.Page, motor: MotorJogo):
        self.page = page
        self.motor = motor
        self.modo_escuro = True
        self.cores = TEMA_ESCURO
        self.primeira_cena = True

        self.page.title = "Aurelis"
        self.page.padding = 12

        # Ajustes de janela e ícone apenas para Desktop
        if self.page.platform in (ft.PagePlatform.WINDOWS, ft.PagePlatform.LINUX, ft.PagePlatform.MACOS):
            self.page.window.width = 920
            self.page.window.height = 720
            self.page.window.min_width = 360
            self.page.window.min_height = 550

            caminho_icone = obter_caminho_recurso("assets/Aurelis.png")
            if os.path.exists(caminho_icone):
                self.page.window.icon = caminho_icone

        # Controles persistentes (Flet 1.0+ usa content=ft.Text(...))
        self.txt_idioma = ft.Text(f"🌐 {self.motor.banco.idioma.upper()}")
        self.btn_idioma = ft.OutlinedButton(
            content=self.txt_idioma,
            on_click=self._alternar_idioma,
        )
        self.btn_tema = ft.IconButton(
            icon=ft.Icons.LIGHT_MODE,
            tooltip="Alternar Tema",
            on_click=self._alternar_tema,
        )
        self.btn_imagens = ft.IconButton(
            icon=ft.Icons.IMAGE,
            tooltip="Ativar/Desativar Imagens",
            on_click=self._alternar_imagens,
        )

        self.container_principal = ft.Container(expand=True)
        self.coluna_narrativa = ft.ListView(
            expand=True,
            spacing=12,
        )
        self.coluna_escolhas = ft.Column(spacing=8)
        self.barra_hud = ft.Row(wrap=True, spacing=8, run_spacing=6)
        self.barra_atalhos = ft.Row(wrap=True, spacing=6, run_spacing=6)

        self._aplicar_tema_pagina()

        layout_raiz = ft.SafeArea(
            expand=True,
            content=ft.Column(
                expand=True,
                spacing=8,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.END,
                        controls=[self.btn_idioma, self.btn_tema, self.btn_imagens],
                    ),
                    self.container_principal,
                ],
            ),
        )
        self.page.add(layout_raiz)
        self.exibir_menu_inicial()

    # ------ AUXILIARES DE COMPATIBILIDADE FLET 1.0+ ------

    def _abrir_dialogo(self, dlg: ft.AlertDialog) -> None:
        if hasattr(self.page, "show_dialog"):
            self.page.show_dialog(dlg)
        elif hasattr(self.page, "open"):
            self.page.open(dlg)
        else:
            self.page.dialog = dlg
            dlg.open = True
            self.page.update()

    def _mostrar_snackbar(self, mensagem: str) -> None:
        sb = ft.SnackBar(content=ft.Text(mensagem))
        if hasattr(self.page, "show_dialog"):
            self.page.show_dialog(sb)
        elif hasattr(self.page, "open"):
            self.page.open(sb)
        else:
            self.page.overlay.append(sb)
            sb.open = True
            self.page.update()

    # ------ TEMA, IMAGENS E IDIOMA ------

    def _aplicar_tema_pagina(self) -> None:
        self.cores = TEMA_ESCURO if self.modo_escuro else TEMA_CLARO
        self.page.bgcolor = self.cores["cor_fundo"]
        self.page.theme_mode = ft.ThemeMode.DARK if self.modo_escuro else ft.ThemeMode.LIGHT
        self.btn_tema.icon = ft.Icons.LIGHT_MODE if self.modo_escuro else ft.Icons.DARK_MODE

    def _alternar_tema(self, e) -> None:
        self.modo_escuro = not self.modo_escuro
        self._aplicar_tema_pagina()
        if self.motor.jogador:
            self.renderizar_cena_atual(preservar_historico=True)
        else:
            self.exibir_menu_inicial()

    def _alternar_idioma(self, e) -> None:
        novo = "en" if self.motor.banco.idioma == "pt" else "pt"
        self.motor.mudar_idioma(novo)
        self.txt_idioma.value = f"🌐 {novo.upper()}"
        if self.motor.jogador:
            self.renderizar_cena_atual(preservar_historico=True)
        else:
            self.exibir_menu_inicial()

    def _alternar_imagens(self, e) -> None:
        self.motor.exibir_imagens = not self.motor.exibir_imagens
        self.btn_imagens.icon = (
            ft.Icons.IMAGE if self.motor.exibir_imagens else ft.Icons.HIDE_IMAGE
        )
        self._mostrar_snackbar(
            "🖼️ Imagens ativadas." if self.motor.exibir_imagens else "🚫 Imagens desativadas."
        )
        if self.motor.jogador:
            # Se ligou as imagens no meio de uma cena que tinha imagens ocultadas,
            # re-renderiza a cena atual do zero para exibir tanto o fundo quanto os retratos.
            self.primeira_cena = True
            self.renderizar_cena_atual(preservar_historico=False)
        else:
            self.page.update()

    # ------ MENU INICIAL ------

    def exibir_menu_inicial(self) -> None:
        self.motor.jogador = None

        def iniciar_novo(e):
            self.motor.iniciar_novo_jogo(nome_jogador="Kael", cena_inicial="boas_vindas")
            self.primeira_cena = True
            self.montar_layout_jogo()
            self.renderizar_cena_atual()

        def carregar(e):
            jogador, cena_salva, msg = carregar_progresso()
            if jogador and cena_salva:
                self.motor.carregar_sessao(jogador, cena_salva)
                self.primeira_cena = True
                self.montar_layout_jogo()
                self._mostrar_snackbar(msg)
                self.renderizar_cena_atual()
            else:
                self._mostrar_snackbar(msg)

        def sobre(e):
            dlg = ft.AlertDialog(
                title=ft.Text("Sobre o Jogo"),
                content=ft.Text(
                    "Aurelis\n"
                    "Versão 1.0\n"
                    "RPG textual interativo desenvolvido em Python e Flet.\n"
                    "Criado por Jupeid (2026)©"
                ),
            )
            self._abrir_dialogo(dlg)

        self.container_principal.content = ft.Column(
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
            spacing=16,
            controls=[
                ft.Text(
                    "Aurelis",
                    size=38,
                    weight=ft.FontWeight.BOLD,
                    color=self.cores["cor_destaque"],
                    font_family="Georgia",
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(
                    "O Caminho da Alvorada",
                    size=15,
                    italic=True,
                    color=self.cores["cor_texto"],
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(height=12),
                ft.Button(
                    content=ft.Text("⚔️ Iniciar Novo Jogo"),
                    width=280,
                    height=46,
                    on_click=iniciar_novo,
                ),
                ft.Button(
                    content=ft.Text("📜 Carregar Jogo"),
                    width=280,
                    height=46,
                    on_click=carregar,
                ),
                ft.OutlinedButton(
                    content=ft.Text("ℹ️ Sobre o Jogo"),
                    width=280,
                    height=42,
                    on_click=sobre,
                ),
            ],
        )
        self.page.update()

    # ------ TELA PRINCIPAL DE JOGO ------

    def montar_layout_jogo(self) -> None:
        self.img_background = ft.Image(
            src="",
            fit=ft.BoxFit.COVER,
            opacity=0.45,
        )

        self.camada_background = ft.Container(
            content=self.img_background,
            left=0,
            top=0,
            right=0,
            bottom=0,
            visible=False,
        )

        camada_leitura = ft.Container(
            content=self.coluna_narrativa,
            bgcolor=ft.Colors.with_opacity(0.84, self.cores["cor_painel"]),
            border_radius=10,
            padding=16,
            expand=True,
        )

        painel_leitura = ft.Container(
            bgcolor=self.cores["cor_painel"],
            border_radius=10,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            expand=True,
            content=ft.Stack(
                expand=True,
                controls=[
                    self.camada_background,
                    camada_leitura,
                ],
            ),
        )

        self.container_principal.content = ft.Column(
            expand=True,
            spacing=10,
            controls=[
                self.barra_hud,
                painel_leitura,
                self.coluna_escolhas,
                ft.Divider(height=1),
                self.barra_atalhos,
            ],
        )

    def _atualizar_hud(self, exibir: bool) -> None:
        self.barra_hud.controls.clear()
        j = self.motor.jogador
        if not exibir or not j:
            return

        itens_hud = [
            f"👤 {j.nome} (Nv. {j.nivel})",
            f"❤️ HP: {j.hp_atual}/{j.hp_max}",
            f"🔷 MP: {j.mp_atual}/{j.mp_max}",
            f"⭐ XP: {j.experiencia}/{j.exp_proximo_nivel}",
            f"🪙 {j.moedas}C",
        ]
        for texto in itens_hud:
            self.barra_hud.controls.append(
                ft.Container(
                    content=ft.Text(texto, size=12, weight=ft.FontWeight.W_600),
                    bgcolor=self.cores["cor_painel"],
                    padding=ft.Padding.symmetric(horizontal=10, vertical=5),
                    border_radius=6,
                )
            )

    def renderizar_cena_atual(self, preservar_historico: bool = False) -> None:
        j = self.motor.jogador
        if not j:
            self.exibir_menu_inicial()
            return

        id_cena = self.motor.cena_atual_id

        if id_cena == "MENU_INICIAL":
            self.exibir_menu_inicial()
            return

        if id_cena not in self.motor.banco.cenas:
            self.coluna_narrativa.controls.clear()
            self.coluna_narrativa.controls.append(
                ft.Text("[CAPÍTULO EM CONSTRUÇÃO]\nEsta parte ainda não foi escrita.", size=16)
            )
            self.coluna_escolhas.controls = [
                ft.Button(
                    content=ft.Text("Voltar ao Menu Inicial"),
                    on_click=lambda e: self.exibir_menu_inicial(),
                )
            ]
            self.page.update()
            return

        estado = self.motor.obter_estado_cena_atual()
        paragrafos = estado.get("paragrafos", [])
        notificacoes = estado.get("notificacoes", [])
        prox_dinamica = estado.get("proxima_cena_dinamica")

        if prox_dinamica and not paragrafos and not notificacoes and not estado.get("titulo"):
            self.motor.cena_atual_id = prox_dinamica
            self.renderizar_cena_atual(preservar_historico=preservar_historico)
            return

        self._atualizar_hud(estado.get("exibir_hud", True))

        # Atualiza ícone e background SEMPRE (mesmo se preservar_historico=True)
        self.btn_imagens.icon = (
            ft.Icons.IMAGE if self.motor.exibir_imagens else ft.Icons.HIDE_IMAGE
        )

        caminho_bg = estado.get("background")
        if hasattr(self, "img_background"):
            if self.motor.exibir_imagens and caminho_bg:
                bg_resolvido = obter_caminho_recurso(caminho_bg)
                if os.path.exists(bg_resolvido):
                    self.img_background.src = bg_resolvido
                    self.camada_background.visible = True
                else:
                    self.camada_background.visible = False
            else:
                self.camada_background.visible = False

        if not preservar_historico:
            if estado.get("limpar_tela") or self.primeira_cena:
                self.coluna_narrativa.controls.clear()
                self.primeira_cena = False
            elif self.coluna_narrativa.controls:
                self.coluna_narrativa.controls.append(ft.Divider())

            if estado.get("titulo"):
                self.coluna_narrativa.controls.append(
                    ft.Text(
                        estado["titulo"],
                        size=19,
                        weight=ft.FontWeight.BOLD,
                        color=self.cores["cor_destaque"],
                    )
                )

            imagens_topo = estado.get("imagem")
            if imagens_topo:
                lista_imgs = imagens_topo if isinstance(imagens_topo, list) else [imagens_topo]
                for caminho_img in lista_imgs:
                    widget_img = self._criar_widget_imagem(caminho_img)
                    if widget_img:
                        self.coluna_narrativa.controls.append(widget_img)

            for notif in notificacoes:
                self.coluna_narrativa.controls.append(
                    ft.Container(
                        content=ft.Text(notif, size=13, italic=True),
                        bgcolor=ft.Colors.with_opacity(0.15, self.cores["cor_destaque"]),
                        padding=8,
                        border_radius=6,
                    )
                )

            for paragrafo in paragrafos:
                self._adicionar_texto_ou_imagens(paragrafo, j)

        # Verifica Game Over
        if j.hp_atual <= 0:
            self.coluna_escolhas.controls = [
                ft.Button(
                    content=ft.Text("💀 Fim de Jornada — Voltar ao Menu"),
                    width=float("inf"),
                    on_click=lambda e: self.exibir_menu_inicial(),
                )
            ]
            self.page.update()
            return

        # Botões de Escolha ou Continuação
        self.coluna_escolhas.controls.clear()
        opcoes = estado.get("opcoes", [])
        proxima_final = prox_dinamica or estado.get("proxima_cena_direta")

        if opcoes:
            for op in opcoes:
                rotulo = op.get("_rotulo", "•")
                texto_op = FormatadorLivro.interpolar_variaveis(op["texto"], j)
                bloqueada = op.get("_bloqueada", False)

                btn = ft.Button(
                    content=ft.Text(
                        f"[{rotulo}] {'🔒 ' + texto_op + ' (Requisitos não atendidos)' if bloqueada else texto_op}",
                        size=14,
                    ),
                    disabled=bloqueada,
                    width=float("inf"),
                    on_click=lambda e, opcao=op: self._ao_clicar_opcao(opcao),
                )
                self.coluna_escolhas.controls.append(btn)
        elif proxima_final:
            self.coluna_escolhas.controls.append(
                ft.Button(
                    content=ft.Text("➡️ Continuar"),
                    width=float("inf"),
                    height=44,
                    on_click=lambda e, p=proxima_final: self._avancar_para(p),
                )
            )

        # Barra de Atalhos
        permite_descanso = estado.get("permite_descanso", False)
        pode_distribuir = estado.get("area_descanso", False)
        pode_equipar = estado.get("pode_equipar", True)
        self.barra_atalhos.controls = [
            ft.OutlinedButton(content=ft.Text("📊 Ficha"), on_click=lambda e: self._abrir_ficha(pode_distribuir)),
            ft.OutlinedButton(content=ft.Text("🎒 Inventário"), on_click=lambda e: self._abrir_inventario(pode_equipar)),
            ft.OutlinedButton(content=ft.Text("🤝 Relações"), on_click=lambda e: self._abrir_relacoes()),
        ]
        if permite_descanso:
            self.barra_atalhos.controls.append(
                ft.OutlinedButton(content=ft.Text("💾 Salvar"), on_click=self._salvar_jogo)
            )
        self.barra_atalhos.controls.append(
            ft.TextButton(content=ft.Text("🚪 Menu"), on_click=lambda e: self.exibir_menu_inicial())
        )

        self.page.update()

    def _executar_avanco(self, proxima_cena: str) -> None:
        self.motor.cena_atual_id = proxima_cena
        self.renderizar_cena_atual()

    def _avancar_para(self, proxima_cena: str) -> None:
        j = self.motor.jogador
        if not j:
            return
        if j.pode_distribuir_pontos and j.pontos_disponiveis > 0:
            def fechar_aviso(dlg_alvo: ft.AlertDialog):
                dlg_alvo.open = False
                self.page.update()

            def confirmar_saida(e):
                fechar_aviso(dlg_aviso)
                self._mostrar_snackbar(
                    f"{j.pontos_disponiveis} ponto(s) guardado(s) para a próxima área de descanso."
                )
                self._executar_avanco(proxima_cena)

            dlg_aviso = ft.AlertDialog(
                title=ft.Text("Pontos Disponíveis"),
                content=ft.Text(
                    f"Você possui {j.pontos_disponiveis} ponto(s) disponível(is) para distribuir. "
                    "Se não distribuir agora, só poderá novamente na próxima área de descanso.\n\n"
                    "Tem certeza que quer prosseguir?"
                ),
                actions=[
                    ft.TextButton(
                        content=ft.Text("Não"),
                        on_click=lambda e: fechar_aviso(dlg_aviso),
                    ),
                    ft.Button(
                        content=ft.Text("Sim"),
                        on_click=confirmar_saida,
                    ),
                ],
            )
            self._abrir_dialogo(dlg_aviso)
            return

        self._executar_avanco(proxima_cena)

    def _ao_clicar_opcao(self, opcao: dict) -> None:
        j = self.motor.jogador
        if not j:
            return

        resultado = self.motor.escolher_opcao(opcao)

        if j.hp_atual <= 0:
            self.coluna_narrativa.controls.append(
                ft.Text(
                    "\n💀 Você sucumbiu aos ferimentos na jornada...",
                    color=ft.Colors.RED_400,
                    weight=ft.FontWeight.BOLD,
                )
            )
            self.coluna_escolhas.controls = [
                ft.Button(
                    content=ft.Text("Voltar ao Menu"),
                    width=float("inf"),
                    on_click=lambda e: self.exibir_menu_inicial(),
                )
            ]
            self.page.update()
            return

        consequencia = resultado.get("narrativa_consequencia")
        proxima = resultado.get("proxima_cena")

        if consequencia:
            texto_cons = FormatadorLivro.interpolar_variaveis(consequencia, j)
            self.coluna_narrativa.controls.append(ft.Divider())
            self.coluna_narrativa.controls.append(
                ft.Text(texto_cons, size=15, italic=True, color=self.cores["cor_texto"])
            )
            if proxima:
                self.coluna_escolhas.controls = [
                    ft.Button(
                        content=ft.Text("➡️ Continuar"),
                        width=float("inf"),
                        height=44,
                        on_click=lambda e, p=proxima: self._avancar_para(p),
                    )
                ]
            self.page.update()
        elif proxima:
            self._avancar_para(proxima)

    def _salvar_jogo(self, e) -> None:
        j = self.motor.jogador
        if not j:
            return
        _, msg = salvar_progresso(j, self.motor.cena_atual_id)
        self._mostrar_snackbar(msg)

    # ------ JANELAS MODAIS (FICHA, INVENTÁRIO, RELAÇÕES) ------

    def _largura_modal(self, max_w: int = 420) -> float:
        largura_tela = self.page.width or max_w
        return min(max_w, max(280, largura_tela - 48))

    def _abrir_ficha(self, pode_distribuir: bool) -> None:
        j = self.motor.jogador
        if not j:
            return
        atributos = ["vitalidade", "forca", "destreza", "inteligencia", "magia", "sorte"]
        pendentes = {attr: 0 for attr in atributos}
        lista_controles = ft.Column(tight=True, spacing=8)

        def fechar_dialogo(dlg_alvo: ft.AlertDialog):
            dlg_alvo.open = False
            self.page.update()

        def confirmar_distribuicao(e):
            total_alocado = sum(pendentes.values())
            if total_alocado <= 0:
                return

            resumo = "\n".join(
                f"• {attr.capitalize()}: +{qtd}"
                for attr, qtd in pendentes.items()
                if qtd > 0
            )

            def executar_confirmacao(ev):
                j.permitir_distribuicao(True)
                for attr, qtd in pendentes.items():
                    for _ in range(qtd):
                        j.alocar_pontos(attr)
                fechar_dialogo(dlg_confirm)
                fechar_dialogo(dlg)
                self._atualizar_hud(True)
                self._mostrar_snackbar("Atributos atualizados permanentemente!")
                self.page.update()

            dlg_confirm = ft.AlertDialog(
                title=ft.Text("Confirmar Distribuição?"),
                content=ft.Text(
                    f"Você está prestes a aplicar:\n\n{resumo}\n\n"
                    "⚠️ Esta ação não pode ser desfeita."
                ),
                actions=[
                    ft.TextButton(
                        content=ft.Text("Cancelar"),
                        on_click=lambda ev: fechar_dialogo(dlg_confirm),
                    ),
                    ft.Button(
                        content=ft.Text("Confirmar"),
                        on_click=executar_confirmacao,
                    ),
                ],
            )
            self._abrir_dialogo(dlg_confirm)

        def confirmar_guardar_pontos(e):
            restantes = j.pontos_disponiveis - sum(pendentes.values())

            def executar_guardar(ev):
                fechar_dialogo(dlg_guardar)
                fechar_dialogo(dlg)
                self._mostrar_snackbar(
                    f"{restantes} ponto(s) guardado(s) para a próxima área de descanso."
                )

            dlg_guardar = ft.AlertDialog(
                title=ft.Text("Guardar Pontos?"),
                content=ft.Text(
                    f"Você manterá {restantes} ponto(s) sem distribuir até a próxima área de descanso.\n\n"
                    "⚠️ Você não poderá distribuí-los fora de uma área de descanso. Deseja continuar?"
                ),
                actions=[
                    ft.TextButton(
                        content=ft.Text("Voltar"),
                        on_click=lambda ev: fechar_dialogo(dlg_guardar),
                    ),
                    ft.Button(
                        content=ft.Text("Guardar Pontos"),
                        on_click=executar_guardar,
                    ),
                ],
            )
            self._abrir_dialogo(dlg_guardar)

        def atualizar_lista():
            lista_controles.controls.clear()
            total_alocado = sum(pendentes.values())
            pontos_restantes = j.pontos_disponiveis - total_alocado

            lista_controles.controls.append(
                ft.Text(
                    f"Pontos disponíveis: {pontos_restantes} "
                    f"{'(Área de Descanso)' if pode_distribuir else '(Disponível apenas em descanso)'}",
                    weight=ft.FontWeight.BOLD,
                )
            )

            for attr in atributos:
                base = getattr(j, attr)
                pend = pendentes[attr]
                total = j.obter_atributo_total(attr) + pend
                bonus_equip = total - (base + pend)

                texto_valor = f"{base + pend}"
                if pend > 0:
                    texto_valor += f" (+{pend})"
                if bonus_equip != 0:
                    texto_valor += f" [Total: {total}]"

                def adicionar_temp(e, a=attr):
                    if j.pontos_disponiveis - sum(pendentes.values()) > 0:
                        pendentes[a] += 1
                        atualizar_lista()
                        self.page.update()

                def remover_temp(e, a=attr):
                    if pendentes[a] > 0:
                        pendentes[a] -= 1
                        atualizar_lista()
                        self.page.update()

                controles_linha = [ft.Text(f"{attr.capitalize()}: {texto_valor}", size=14)]
                if pode_distribuir and j.pontos_disponiveis > 0:
                    controles_linha.append(
                        ft.Row(
                            spacing=0,
                            controls=[
                                ft.IconButton(
                                    icon=ft.Icons.REMOVE_CIRCLE_OUTLINE,
                                    disabled=pend <= 0,
                                    on_click=remover_temp,
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.ADD_CIRCLE_OUTLINE,
                                    disabled=pontos_restantes <= 0,
                                    on_click=adicionar_temp,
                                ),
                            ],
                        )
                    )

                lista_controles.controls.append(
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=controles_linha,
                    )
                )

            if pode_distribuir and j.pontos_disponiveis > 0:
                lista_controles.controls.append(ft.Divider())
                lista_controles.controls.append(
                    ft.Row(
                        alignment=ft.MainAxisAlignment.END,
                        wrap=True,
                        spacing=8,
                        controls=[
                            ft.OutlinedButton(
                                content=ft.Text("💾 Guardar Pontos"),
                                disabled=pontos_restantes <= 0,
                                on_click=confirmar_guardar_pontos,
                            ),
                            ft.Button(
                                content=ft.Text("✅ Confirmar"),
                                disabled=total_alocado <= 0,
                                on_click=confirmar_distribuicao,
                            ),
                        ],
                    )
                )

        atualizar_lista()
        dlg = ft.AlertDialog(
            title=ft.Text(f"Ficha de {j.nome} — Nível {j.nivel}"),
            content=ft.Container(content=lista_controles, width=self._largura_modal(400)),
        )
        self._abrir_dialogo(dlg)

    def _abrir_inventario(self, pode_equipar: bool = True) -> None:
        j = self.motor.jogador
        if not j:
            return
        conteudo = ft.Column(scroll=ft.ScrollMode.AUTO, tight=True, spacing=10)

        def renderizar_conteudo():
            conteudo.controls.clear()

            if not pode_equipar:
                conteudo.controls.append(
                    ft.Container(
                        padding=8,
                        border_radius=6,
                        bgcolor=ft.Colors.with_opacity(0.15, ft.Colors.AMBER_400),
                        content=ft.Text(
                            "⚠️ Não é possível trocar equipamentos durante esta cena.",
                            size=12,
                            italic=True,
                        ),
                    )
                )

            conteudo.controls.append(ft.Text("🛡️ Equipamentos em Uso", weight=ft.FontWeight.BOLD))
            for slot, item in j.equipamentos.items():
                if isinstance(item, dict):
                    nome_eq = item.get("nome", "Item")
                    bonus = item.get("bonus", {})
                    bonus_txt = ", ".join(f"+{v} {k.upper()[:3]}" for k, v in bonus.items() if v != 0)
                    rotulo_eq = f"  • {slot.capitalize()}: {nome_eq}" + (f" ({bonus_txt})" if bonus_txt else "")

                    def ao_desequipar(e, s=slot):
                        j.desequipar_item(s)
                        j.consumir_notificacoes()
                        renderizar_conteudo()
                        self._atualizar_hud(True)
                        self.page.update()

                    conteudo.controls.append(
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Text(rotulo_eq, size=13, expand=True),
                                ft.TextButton(
                                    content=ft.Text("Desequipar"),
                                    disabled=not pode_equipar,
                                    on_click=ao_desequipar,
                                ),
                            ],
                        )
                    )
                else:
                    conteudo.controls.append(ft.Text(f"  • {slot.capitalize()}: Vazio", size=13))

            conteudo.controls.append(ft.Divider())
            conteudo.controls.append(ft.Text("📦 Mochila", weight=ft.FontWeight.BOLD))
            if not j.inventario:
                conteudo.controls.append(ft.Text("  (Bolsa vazia)", italic=True))
            else:
                nomes_equipados = {
                    eq.get("nome")
                    for eq in j.equipamentos.values()
                    if isinstance(eq, dict)
                }
                for nome, qtd in j.inventario.items():
                    meta_eq = j.dados_equipaveis.get(nome)
                    if not meta_eq and nome in self.motor.banco.itens:
                        item_cat = self.motor.banco.itens[nome]
                        if getattr(item_cat, "slot", None):
                            meta_eq = item_cat.to_dict()

                    if meta_eq:
                        bonus = meta_eq.get("bonus", {})
                        bonus_txt = ", ".join(f"+{v} {k.upper()[:3]}" for k, v in bonus.items() if v != 0)
                        ja_equipado = nome in nomes_equipados
                        desc_item = f"  • {nome} x{qtd} [{meta_eq.get('slot', '').capitalize()}]"
                        if bonus_txt:
                            desc_item += f" ({bonus_txt})"

                        def ao_equipar(e, dados=meta_eq):
                            j.equipar_item(dados)
                            j.consumir_notificacoes()
                            renderizar_conteudo()
                            self._atualizar_hud(True)
                            self.page.update()

                        conteudo.controls.append(
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Text(desc_item, size=13, expand=True),
                                    ft.OutlinedButton(
                                        content=ft.Text("Equipado" if ja_equipado else "Equipar"),
                                        disabled=(not pode_equipar) or ja_equipado,
                                        on_click=ao_equipar,
                                    ),
                                ],
                            )
                        )
                    else:
                        conteudo.controls.append(ft.Text(f"  • {nome} x{qtd}", size=13))

            conteudo.controls.append(ft.Divider())
            conteudo.controls.append(ft.Text("✨ Relíquias & Itens Únicos", weight=ft.FontWeight.BOLD))
            if not j.inventario_unico:
                conteudo.controls.append(ft.Text("  (Nenhum item único obtido)", italic=True))
            else:
                for id_item in sorted(j.inventario_unico):
                    item_obj = self.motor.banco.itens.get(id_item)
                    if item_obj:
                        bonus_txt = ", ".join(f"+{v} {k.upper()[:3]}" for k, v in item_obj.bonus.items())
                        conteudo.controls.append(
                            ft.Container(
                                padding=10,
                                border_radius=6,
                                bgcolor=ft.Colors.with_opacity(0.08, self.cores["cor_destaque"]),
                                content=ft.Column(
                                    tight=True,
                                    spacing=4,
                                    controls=[
                                        ft.Text(f"★ {item_obj.nome} [{bonus_txt}]", weight=ft.FontWeight.BOLD),
                                        ft.Text(item_obj.descricao, size=13),
                                        *(
                                            [ft.Text(f"Origem: {item_obj.historia_origem}", size=12, italic=True)]
                                            if item_obj.historia_origem
                                            else []
                                        ),
                                    ],
                                ),
                            )
                        )
                    else:
                        conteudo.controls.append(ft.Text(f"  ★ {id_item}", weight=ft.FontWeight.BOLD))

        renderizar_conteudo()
        dlg = ft.AlertDialog(
            title=ft.Text("Inventário"),
            content=ft.Container(content=conteudo, width=self._largura_modal(460), height=400),
        )
        self._abrir_dialogo(dlg)

    def _abrir_relacoes(self) -> None:
        j = self.motor.jogador
        if not j:
            return
        conhecidos = [npc for npc in j.npcs.values() if getattr(npc, "conhecido", False)]
        conteudo = ft.Column(scroll=ft.ScrollMode.AUTO, tight=True, spacing=10)

        if not conhecidos:
            conteudo.controls.append(ft.Text("Você ainda não conheceu ninguém nesta jornada.", italic=True))
        else:
            for npc in conhecidos:
                status_vida = (
                    "💀 Morto"
                    if not npc.vivo
                    else ("⛓️ Imobilizado" if npc.imobilizado else "🟢 Ativo")
                )
                conteudo.controls.append(
                    ft.Column(
                        tight=True,
                        spacing=4,
                        controls=[
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Text(f"{npc.nome} ({npc.relacao.capitalize()})", weight=ft.FontWeight.BOLD),
                                    ft.Text(f"{npc.afeicao}/100 | {status_vida}", size=12),
                                ],
                            ),
                            ft.ProgressBar(value=npc.afeicao / 100),
                        ],
                    )
                )

        dlg = ft.AlertDialog(
            title=ft.Text("Relações"),
            content=ft.Container(content=conteudo, width=self._largura_modal(420), height=340),
        )
        self._abrir_dialogo(dlg)

    #---IMAGENS TOP/IN/BETWEEN---
    def _criar_widget_imagem(self, caminho_relativo: str) -> ft.Control | None:
        if not self.motor.exibir_imagens or not caminho_relativo:
            return None
        caminho_resolvido = obter_caminho_recurso(caminho_relativo.strip())
        if not os.path.exists(caminho_resolvido):
            return None
        return ft.Container(
            alignment=ft.Alignment(0, 0),
            padding=ft.Padding.symmetric(vertical=8),
            content=ft.Image(
                src=caminho_resolvido,
                width=680,
                height=340,
                fit=ft.BoxFit.CONTAIN,
                border_radius=8,
            ),
        )

    def _adicionar_texto_ou_imagens(self, texto_bruto: str, jogador) -> None:
        """Divide o texto caso contenha tags [IMG: caminho] e intercala texto e imagens."""
        partes = re.split(r"(\[IMG:\s*[^\]]+\])", texto_bruto)
        for parte in partes:
            if not parte.strip():
                continue
            match_img = re.match(r"^\[IMG:\s*([^\]]+)\]$", parte.strip(), re.IGNORECASE)
            if match_img:
                widget_img = self._criar_widget_imagem(match_img.group(1))
                if widget_img:
                    self.coluna_narrativa.controls.append(widget_img)
            else:
                texto_interp = FormatadorLivro.interpolar_variaveis(parte, jogador)
                self.coluna_narrativa.controls.append(
                    ft.Text(
                        texto_interp,
                        size=15,
                        color=self.cores["cor_texto"],
                        selectable=True,
                    )
                )