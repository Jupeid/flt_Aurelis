from abc import ABC, abstractmethod

class InterfaceJogo(ABC):
  @abstractmethod
  def atualizar_status(self, jogador):
    """Atualiza barra HP, MP, Inventario"""
    pass

  @abstractmethod
  def exibir_cena(self, texto: str, caminho_imagem: str | None = None, limpar_tela: bool = True):
    """Mostra a narrativa e a imagem da cena se habilitado"""
    pass

  @abstractmethod
  def notificar(self, mensagem: str):
    """Mostra uma notificação na tela"""
    pass

  @abstractmethod
  def apresentar_escolhas(self, opcoes: list[dict], callback_escolha):
    """Envia uma lista de opções para escolha"""
    pass
