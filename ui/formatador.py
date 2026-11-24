import re
import textwrap


class FormatadorLivro:
    """Responsável por interpolar variáveis da história e aplicar tipografia literária."""

    @staticmethod
    def aplicar_tipografia(texto: str) -> str:
        """Converte '--' em travessão literário '—' e normaliza espaços iniciais."""
        if not texto:
            return ""

        linhas_tratadas = []
        for linha in texto.splitlines():
            linha_limpa = linha.strip()
            if not linha_limpa:
                linhas_tratadas.append("")
                continue

            # Preserva linhas puramente divisórias (ex: "---" ou "===")
            if set(linha_limpa) <= {"-", "="}:
                linhas_tratadas.append(linha_limpa)
                continue

            # Converte '--' em travessão '—' (ex: "-- Olá!" -> "— Olá!", "palavra--palavra" -> "palavra—palavra")
            linha_limpa = re.sub(r"(?<!-)-{2,3}(?!-)", "—", linha_limpa)
            # Garante um espaço elegante após travessão de início de fala (ex: "—Olá" -> "— Olá")
            linha_limpa = re.sub(r"^—\s*", "— ", linha_limpa)
            linhas_tratadas.append(linha_limpa)

        return "\n".join(linhas_tratadas).strip()

    @staticmethod
    def interpolar_variaveis(texto: str, jogador) -> str:
        """Substitui placeholders como {nome} e aplica a tipografia literária."""
        if not texto:
            return ""
        try:
            resultado = texto.format(nome=jogador.nome)
        except (KeyError, ValueError):
            resultado = texto
        return FormatadorLivro.aplicar_tipografia(resultado)

    @staticmethod
    def formatar_para_terminal(
        texto: str, largura: int = 80, recuo_paragrafo: str = "  "
    ) -> str:
        """Aplica quebras de linha e recuo de parágrafo para exibição limpa no console."""
        if not texto:
            return ""

        texto = FormatadorLivro.aplicar_tipografia(texto)
        linhas_formatadas = []
        novo_paragrafo = True

        for linha in texto.splitlines():
            linha_str = linha.strip()
            if not linha_str:
                linhas_formatadas.append("")
                novo_paragrafo = True
                continue

            if set(linha_str) == {"="} or set(linha_str) == {"-"}:
                linhas_formatadas.append(linha_str)
                novo_paragrafo = True
            elif linha_str.startswith("[") or linha_str.startswith("•") or linha_str.startswith("—"):
                linhas_formatadas.append(
                    textwrap.fill(
                        linha_str,
                        width=largura,
                        subsequent_indent="  ",
                    )
                )
                novo_paragrafo = True
            else:
                indent_inicial = recuo_paragrafo if novo_paragrafo else ""
                linhas_formatadas.append(
                    textwrap.fill(
                        linha_str,
                        width=largura,
                        initial_indent=indent_inicial,
                        subsequent_indent="",
                    )
                )
                novo_paragrafo = False

        return "\n".join(linhas_formatadas)