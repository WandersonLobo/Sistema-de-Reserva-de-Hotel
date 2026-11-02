# 📐 Registro de Decisões de Arquitetura e Engenharia (Decisions)

Este documento registra as principais decisões técnicas, escolhas de design orientado a objetos, ferramentas de automação e metodologia de desenvolvimento adotadas no **Sistema de Reservas de Hotel**.

---

## 1. Uso de Inteligência Artificial (IA)

### Por que foi usado?
O uso de Inteligência Artificial (IA) foi integrado ao fluxo de trabalho com foco em **revisão contínua e apoio na estruturação do projeto**. O objetivo principal não foi a geração indiscriminada de código, mas sim atuar como um parceiro técnico consultivo para:
1. Validar a coerência da arquitetura em camadas frente aos requisitos do professor.
2. Identificar contradições entre a modelagem conceitual (UML) e o código em evolução.
3. Desenhar cenários de testes de borda (*edge cases*) para assegurar que as regras de negócio fossem cumpridas à risca.

### De que forma foi usado?
A ferramenta de IA atuou de forma iterativa em sessões de *pair programming*:
* **Revisão Contínua:** Verificação de contratos de API HTTP, validação de transições válidas na máquina de estados de `Reserva` e auditoria de consultas SQL no módulo `data.py`.
* **Apoio na Estruturação:** Auxílio na divisão modular do repositório (`models`, `services`, `database`, `api`), garantindo que o acoplamento se mantivesse unidirecional (API $\rightarrow$ Services $\rightarrow$ Database/Models).

### Exemplo Prático
Durante a implementação das rotas em `src/api/routes.py`, a IA foi utilizada para analisar se os 14 endpoints estavam em excesso em relação aos 9 subcomandos de exemplo da CLI do documento. A análise comprovou que rotas como `POST /hospedes`, `PATCH /quartos/{numero}/desbloquear`, cancelamento com multa e varredura de `no-show` eram indispensáveis para atender aos Requisitos Funcionais (RF 1, 2 e 6) da especificação oficial. Além disso, a IA identificou e corrigiu divergências entre o `docs/uml_diagram.md` e a persistência real no SQLite em `src/services/hotel.py`.

---

## 2. Decisões de Design (Arquitetura e POO)

### Por que foi usado?
Para satisfazer rigorosamente os pilares de **Programação Orientada a Objetos** (Abstração, Encapsulamento, Herança e Polimorfismo), garantindo baixo acoplamento, alta coesão e facilidade de manutenção.

### De que forma foi usado?
* **Arquitetura em Camadas:** As entidades de negócio (`src/models/`) desconhecem detalhes de persistência e de transporte HTTP. A camada de serviços (`src/services/`) orquestra as operações e cálculos dinâmicos, enquanto a persistência (`src/database/`) opera via SQLite nativo e a interface (`src/api/`) expõe endpoints FastAPI.
* **Herança e Polimorfismo:** A classe abstrata `Quarto` define o contrato comum. Suas subclasses (`QuartoSimples`, `QuartoDuplo` e `QuartoLuxo`) sobrescrevem polimorficamente o método `calcular_diaria()`, adicionando regras específicas (como varanda, hidromassagem e taxa de serviço adicional).
* **Herança Múltipla via Mixins:** Uso de `Auditoria` (para carimbos temporais automáticos) e `Serializavel` (para conversão padronizada em dicionários e JSON), evitando repetição de código sem ferir a hierarquia de domínio.
* **Composição e Agregação:** A classe `Reserva` agrega instâncias de `Hospede` e `Quarto`, e compõe listas de objetos `Pagamento` e `Adicional`.
* **Encapsulamento Rigoroso com `@property`:** Todos os atributos críticos são privados/protegidos, com validações explícitas que impedem estados inconsistentes (ex.: capacidade $< 1$, tarifa base $\le 0$, data de saída anterior à entrada).

### Exemplo Prático: Polimorfismo e Encapsulamento
```python
# Polimorfismo na especialização de Quarto (src/models/room.py)
class QuartoLuxo(Quarto):
    def calcular_diaria(self, fator_temporada: float = 1.0) -> float:
        """Aplica multiplicador de temporada sobre a tarifa base e soma taxa extra."""
        tarifa_ajustada = self.tarifa_base * fator_temporada
        return round(tarifa_ajustada + self.taxa_servico_adicional, 2)

# Encapsulamento com @property em Reserva (src/models/reservation.py)
@property
def data_saida(self) -> date:
    return self._data_saida

@data_saida.setter
def data_saida(self, valor: date) -> None:
    if valor <= self._data_entrada:
        raise DadosInvalidosException("A data de saída deve ser posterior à data de entrada.")
    self._data_saida = valor
```

---

## 3. Padronização Técnica: Docstrings Estilo Google, Type Hints e CI/CD

### Por que foi usado?
Para assegurar legibilidade imediata do código, reduzir bugs por incompatibilidade de tipos em tempo de edição e garantir que nenhuma regressão seja introduzida durante a evolução do projeto.

### De que forma foi usado?
* **Docstrings no Padrão Google:** Todas as classes, métodos e funções contam com documentação padronizada dividida em descrição sucinta, argumentos (`Args:`), valores retornados (`Returns:`) e exceções disparadas (`Raises:`).
* **Type Hints (Tipagem Estática):** Uso consistente de anotações de tipo modernas (`int`, `str`, `date`, `datetime`, `Optional`, `list[dict]`), integrando-se nativamente com a validação do Pydantic na API e com o analisador de código (Pylance).
* **Integração Contínua (CI/CD com GitHub Actions):** Configuração de um pipeline automatizado em `.github/workflows/ci.yml` que executa automaticamente a cada `push` e `pull_request` no repositório.

### Exemplos Práticos

#### A. Docstrings Estilo Google e Type Hints
```python
def calcular_total_reserva(
    quarto: Quarto,
    inicio: date,
    fim: date,
    settings: dict,
) -> float:
    """Calcula o valor total acumulado das diárias de uma reserva.

    Itera dia a dia aplicando cumulativamente os multiplicadores de alta
    temporada e os adicionais de fim de semana configurados.

    Args:
        quarto: Instância do quarto reservado para cálculo polimórfico.
        inicio: Data inicial da estadia (inclusiva).
        fim: Data final da estadia (exclusiva).
        settings: Dicionário contendo as regras de temporadas e finais de semana.

    Returns:
        float: Valor financeiro total consolidado das diárias, arredondado a 2 casas.

    Raises:
        DadosInvalidosException: Se as datas forem inválidas ou início >= fim.
    """
```

#### B. Pipeline de CI/CD (`.github/workflows/ci.yml`)
O workflow executa em ambiente limpo Ubuntu com Python 3.14, instalando as dependências e rodando a suíte com mais de 200 testes automatizados:
```yaml
name: CI - Testes

on:
  push:
  pull_request:

jobs:
  testes:
    name: Testes Python
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - name: Baixar o código do repositório
        uses: actions/checkout@v7

      - name: Configurar o Python
        uses: actions/setup-python@v7
        with:
          python-version: '3.14'
          cache: pip

      - name: Instalar as dependências
        run: python -m pip install -r requirements.txt

      - name: Executar os testes
        run: python -m pytest tests -v --tb=short
```

