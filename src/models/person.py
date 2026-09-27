"""Módulo que define a hierarquia de pessoas e hóspedes do hotel."""

from abc import ABC
from src.models.mixins import Serializavel



class Pessoa(Serializavel, ABC):
    """Classe base abstrata que encapsula os dados cadastrais de uma pessoa.

    Attributes:
        _id (int): Identificador único da pessoa no sistema.
        _nome (str): Nome completo da pessoa.
        _documento (str): Documento de identificação oficial (CPF ou Passaporte).
        _email (str): Endereço de correio eletrónico para contacto.
        _telefone (str): Número de telefone de contacto.
    """

    pass


class Hospede(Pessoa):
    """Subclasse concreta que representa um cliente (hóspede) do hotel.

    Especializa a classe `Pessoa`, adicionando preferências de estadia
    e mantendo a associação com o histórico de reservas do cliente.

    Attributes:
        _preferencias (str): Observações ou preferências de estadia do hóspede.
        _historico_reservas (list[Reserva]): Lista de reservas associadas ao hóspede.
    """

    pass