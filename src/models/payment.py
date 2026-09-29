"""Módulo que define as entidades financeiras e de consumo extra da reserva."""

from src.models.mixins import Serializavel


class Pagamento(Serializavel):
    """Representa uma transação financeira de pagamento vinculada a uma reserva.

    Attributes:
        _id (int): Identificador único do registro de pagamento.
        _valor (float): Quantia monetária paga na transação (> 0).
        _metodo (MetodoPagamento): Modalidade utilizada (DINHEIRO, CREDITO, DEBITO, PIX).
        _data_pagamento (datetime): Data e hora exatas em que o pagamento ocorreu.
    """

    pass



class Adicional(Serializavel):
    """Representa um item de consumo ou serviço extra lançado na reserva.

    Attributes:
        _id (int): Identificador único do consumo adicional.
        _descricao (str): Nome ou descrição do produto/serviço consumido.
        _preco_unitario (float): Valor unitário do item (> 0).
        _quantidade (int): Quantidade consumida do item (>= 1).
    """

    pass