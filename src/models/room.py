"""Módulo que define a hierarquia de quartos e acomodações do hotel."""

from abc import ABC
from src.models.mixins import Serializavel


class Quarto(Serializavel, ABC):
    """Classe base abstrata que representa uma acomodação genérica do hotel.

    Attributes:
        _numero (int): Número identificador único do quarto no hotel.
        _capacidade (int): Quantidade máxima de hóspedes suportada (>= 1).
        _tarifa_base (float): Valor base da diária antes de ajustes (> 0).
        _status (StatusQuarto): Estado atual do quarto (DISPONIVEL, OCUPADO, etc.).
        _motivo_manutencao (str | None): Descrição do motivo de manutenção ativa.
        _inicio_manutencao (date | None): Data de início do bloqueio de manutenção.
        _fim_manutencao (date | None): Data de término do bloqueio de manutenção.
    """

    pass


class QuartoSimples(Quarto):
    """Subclasse concreta que representa uma acomodação da categoria Simples.

    Aplica o cálculo padrão de diária diretamente sobre a tarifa base e o
    fator de temporada.
    """

    pass


class QuartoDuplo(Quarto):
    """Subclasse concreta que representa uma acomodação da categoria Duplo.

    Attributes:
        _tem_varanda (bool): Indica se o quarto duplo dispõe de varanda privativa.
    """

    pass


class QuartoLuxo(Quarto):
    """Subclasse concreta que representa uma acomodação da categoria Luxo.

    Attributes:
        _tem_hidromassagem (bool): Indica se a suíte possui banheira de hidromassagem.
        _taxa_servico_adicional (float): Valor adicional de serviço VIP na diária.
    """

    pass