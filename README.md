# Aurelis — O Caminho da Alvorada

RPG textual interativo e *visual novel* de fantasia sombria desenvolvido em **Python** com interface gráfica responsiva em **Flet**.

## Recursos

- **Narrativa Ramificada:** Sistema de cenas orientadas a dados em JSON com testes de atributos, condições dinâmicas, consequências narrativas e múltiplos desfechos.
- **Sistema de RPG Completo:** Atributos base (`Vitalidade`, `Força`, `Destreza`, `Inteligência`, `Magia`, `Sorte`), pontos distribuíveis em áreas de descanso, *buffs*, *debuffs*, inventário, relíquias únicas e equipamentos vinculados às escolhas da história.
- **Relações com NPCs:** Sistema de afeição e estados de personagens que reagem às decisões do jogador.
- **Interface Visual Customizável:**
  - Suporte a retratos de personagens, ilustrações integradas ao texto e planos de fundo persistentes por capítulo.
  - Alternância instantânea entre **modo ilustrado** e **modo puramente textual** (no início da jornada ou pelo botão superior).
  - Tema claro/escuro e suporte multilíngue (**PT / EN**).
- **Salvamento Local:** Persistência completa do progresso, atributos, inventário e relações em JSON.

## Estrutura do Projeto

```text
Aurelis/
├── assets/          # Ícones, retratos de personagens e cenários
├── core/            # Motor do jogo, regras de jogador, NPCs, banco de dados e salvamento
├── data/            # Cenas, itens, NPCs e textos da interface em JSON (PT/EN)
├── ui/              # Interface Flet responsiva e formatador de texto
├── utils/           # Resolução de caminhos (desenvolvimento e executável)
└── main.py          # Ponto de entrada da aplicação

##Como Executar:
**Pré-requisitos**
- Python 3.10 ou superior
- Flet (pip install flet)

**Executando localmente:**
git clone https://github.com/Jupeid/flt_Aurelis.git
cd flt_Aurelis
pip install flet
python main.py

**Licença**
© 2026 Jupeid. Todos os direitos reservados.
