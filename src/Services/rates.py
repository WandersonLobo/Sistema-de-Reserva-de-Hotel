"""Módulo de serviço para cálculo de tarifas e diárias do hotel."""


class CalculadoraTarifa:
    """Serviço utilitário responsável pelo cálculo de diárias e tarifas dinâmicas.

    Opera por meio de métodos estáticos e funções puras que consultam as regras
    de sazonalidade e fins de semana parametrizadas no arquivo settings.json,
    invocando o comportamento polimórfico de cálculo de cada subclasse de Quarto.
    """

    pass