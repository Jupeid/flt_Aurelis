import sys
import flet as ft
from core.motor import MotorJogo
from ui.ui_flet import UIFlet
from utils.paths import obter_caminho_recurso


def main(page: ft.Page):
    page.title = "Aurelis"
    # Resolve o caminho absoluto (funciona no Python e no PyInstaller)
    page.window.icon = obter_caminho_recurso("assets/Aurelis.png")
    motor = MotorJogo(idioma="pt")
    UIFlet(page, motor)


if __name__ == "__main__":
    if "--cli" in sys.argv:
        from ui.ui_terminal import UITerminal
        motor = MotorJogo(idioma="pt")
        UITerminal(motor).iniciar()
    else:
        if hasattr(ft, "run"):
            ft.run(main, assets_dir= obter_caminho_recurso("assets"))
        else:
            ft.app(target=main)
