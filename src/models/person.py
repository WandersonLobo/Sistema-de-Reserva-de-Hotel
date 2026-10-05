"""Módulo que define a hierarquia de pessoas e hóspedes do hotel.

Este módulo contém a classe base abstrata `Pessoa` e a sua especialização
concreta `Hospede`, aplicando herança simples, herança múltipla via
`Serializavel` e encapsulamento através de `@property`.
"""

from __future__ import annotations
from abc import ABC
import re
from typing import TYPE_CHECKING, Any, Dict, List, Optional

try:
    from .exceptions import DadosInvalidosException
    from .mixins import Serializavel
except (ImportError, ValueError):
    from exceptions import DadosInvalidosException  # type: ignore
    from mixins import Serializavel  # type: ignore

if TYPE_CHECKING:
    from .reservation import Reserva

class Pessoa(Serializavel, ABC):
    """Classe base abstrata que encapsula os dados cadastrais de uma pessoa.

    superclasse para `Hospede` e eventuais outros perfis do sistema,
    garantindo validação de dados de identificação e contato, além de fornecer
    capacidade de serialização em dicionários e JSON.
    
    Attributes:
        _id (int): Identificador único da pessoa no sistema.
        _nome (str): Nome completo da pessoa.
        _documento (str): Documento de identificação oficial (CPF ou Passaporte).
        _email (str): Endereço de correio eletrónico para contacto.
        _telefone (str): Número de telefone de contacto.
    """

    def __init__(
        self,
        id_: int = 0,
        nome: str = "",
        documento: str = "",
        email: str = "",
        telefone: str = "",
    ) -> None:
        """Inicializa os atributos cadastrais básicos de uma pessoa.

        Permite tanto a instanciação vazia com valores padrão quanto a
        instanciação parametrizada completa.

        Args:
            id_ (int, optional): Identificador numérico do registro. Padrão é 0.
            nome (str, optional): Nome completo da pessoa. Padrão é "".
            documento (str, optional): CPF ou Passaporte válido. Padrão é "".
            email (str, optional): Endereço de e-mail de contato. Padrão é "".
            telefone (str, optional): Número de telefone com DDD. Padrão é "".

        Raises:
            DadosInvalidosException: Se qualquer um dos campos fornecidos for inválido.
        """
        super().__init__()
        self._id: int = 0
        self._nome: str = ""
        self._documento: str = ""
        self._email: str = ""
        self._telefone: str = ""

        if id_ != 0:
            self.id = id_
        else:
            self._id = id_

        if nome:
            self.nome = nome
        if documento:
            self.documento = documento
        if email:
            self.email = email
        if telefone:
            self.telefone = telefone

    @classmethod
    def vazio(cls) -> Pessoa:
        """Construtor de fábrica que retorna uma instância vazia.

        Returns:
            Pessoa: Objeto pessoa com valores iniciais padrão.
        """
        return cls()

    # ----------------------------------------------------------------------- #
    # Propriedades de Acesso (Getters e Setters)                               #
    # ----------------------------------------------------------------------- #

    @property
    def id(self) -> int:
        """Identificador numérico único da pessoa.

        Returns:
            int: ID do registro.
        """
        return self._id

    @id.setter
    def id(self, valor: int) -> None:
        """Define o identificador numérico único da pessoa.

        Args:
            valor (int): Novo identificador numérico (deve ser >= 0).

        Raises:
            DadosInvalidosException: Se o valor for negativo.
        """
        if not isinstance(valor, int) or valor < 0:
            raise DadosInvalidosException("O ID da pessoa deve ser um número inteiro maior ou igual a zero.")
        self._id = valor

    @property
    def nome(self) -> str:
        """Nome completo da pessoa.

        Returns:
            str: Nome da pessoa.
        """
        return self._nome

    @nome.setter
    def nome(self, valor: str) -> None:
        """Define e valida o nome completo da pessoa.

        Args:
            valor (str): Nome completo da pessoa (não pode ser vazio ou conter apenas espaços).

        Raises:
            DadosInvalidosException: Se o nome for vazio ou não for string.
        """
        if not isinstance(valor, str) or not valor.strip():
            raise DadosInvalidosException("O nome da pessoa não pode ser vazio.")
        self._nome = valor.strip()

    @property
    def documento(self) -> str:
        """Número do documento de identificação (CPF ou Passaporte).

        Returns:
            str: Documento de identificação cadastrado.
        """
        return self._documento

    @documento.setter
    def documento(self, valor: str) -> None:
        """Define e valida o documento de identificação da pessoa.

        Args:
            valor (str): Número do documento (não pode ser vazio).

        Raises:
            DadosInvalidosException: Se o documento for vazio ou não for string.
        """
        if not isinstance(valor, str) or not valor.strip():
            raise DadosInvalidosException("O documento da pessoa não pode ser vazio.")
        self._documento = valor.strip()

    @property
    def email(self) -> str:
        """Endereço de correio eletrônico cadastrado.

        Returns:
            str: E-mail da pessoa.
        """
        return self._email

    @email.setter
    def email(self, valor: str) -> None:
        """Define e valida o endereço de e-mail da pessoa.

        Args:
            valor (str): Endereço de e-mail (deve conter '@' e ponto).

        Raises:
            DadosInvalidosException: Se o formato do e-mail for inválido.
        """
        if not isinstance(valor, str) or not valor.strip():
            raise DadosInvalidosException("O e-mail da pessoa não pode ser vazio.")
        padrao = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        if not re.match(padrao, valor.strip()):
            raise DadosInvalidosException(f"O e-mail '{valor}' possui formato inválido.")
        self._email = valor.strip()

    @property
    def telefone(self) -> str:
        """Número de telefone com código de área.

        Returns:
            str: Telefone cadastrado.
        """
        return self._telefone

    @telefone.setter
    def telefone(self, valor: str) -> None:
        """Define e valida o telefone de contato da pessoa.

        Args:
            valor (str): Número de telefone com DDD (não pode ser vazio).

        Raises:
            DadosInvalidosException: Se o telefone for vazio ou não for string.
        """
        if not isinstance(valor, str) or not valor.strip():
            raise DadosInvalidosException("O telefone da pessoa não pode ser vazio.")
        self._telefone = valor.strip()


class Hospede(Pessoa):
    """Subclasse concreta que representa um cliente (hóspede) do hotel.

    Especializa a classe `Pessoa`, adicionando preferências de estadia
    e mantendo a associação com o histórico de reservas do cliente.

    Attributes:
        _preferencias (str): Observações ou preferências de estadia do hóspede.
        _historico_reservas (list[Reserva]): Lista de reservas associadas ao hóspede.
    """

    def __init__(
        self,
        id_: int = 0,
        nome: str = "",
        documento: str = "",
        email: str = "",
        telefone: str = "",
        preferencias: Optional[str] = "",
    ) -> None:
        """Inicializa um novo hóspede com seus dados pessoais e preferências.

        Permite tanto a criação vazia (`Hospede()`) quanto parametrizada.

        Args:
            id_ (int, optional): Identificador único do hóspede. Padrão é 0.
            nome (str, optional): Nome completo do hóspede. Padrão é "".
            documento (str, optional): Documento de identificação (CPF/Passaporte). Padrão é "".
            email (str, optional): Endereço de e-mail do hóspede. Padrão é "".
            telefone (str, optional): Telefone de contato com DDD. Padrão é "".
            preferencias (Optional[str], optional): Preferências de hospedagem. Padrão é "".

        Raises:
            DadosInvalidosException: Se algum dado cadastral fornecido for inválido.
        """
        super().__init__(id_=id_, nome=nome, documento=documento, email=email, telefone=telefone)
        self._preferencias: str = preferencias or ""
        self._historico_reservas: List[Reserva] = []

    @classmethod
    def vazio(cls) -> Hospede:
        """Construtor de fábrica que retorna um hóspede com atributos padrão vazios.

        Returns:
            Hospede: Instância vazia de Hospede.
        """
        return cls()

    # ----------------------------------------------------------------------- #
    # Propriedades de Acesso (Getters e Setters)                               #
    # ----------------------------------------------------------------------- #

    @property
    def preferencias(self) -> str:
        """Texto descritivo das preferências de estadia do hóspede.

        Returns:
            str: Preferências de acomodação ou serviços.
        """
        return self._preferencias

    @preferencias.setter
    def preferencias(self, valor: str) -> None:
        """Define as preferências de acomodação do hóspede.

        Args:
            valor (str): Texto descritivo das preferências.
        """
        self._preferencias = str(valor) if valor is not None else ""

    @property
    def historico_reservas(self) -> List[Reserva]:
        """Lista de reservas associadas ao histórico do hóspede.

        Retorna uma cópia da lista interna para proteger o encapsulamento.

        Returns:
            List[Reserva]: Cópia da lista de reservas do hóspede.
        """
        return list(self._historico_reservas)

    # ----------------------------------------------------------------------- #
    # Métodos de Comportamento                                                #
    # ----------------------------------------------------------------------- #

    def vincular_reserva(self, reserva: Reserva) -> None:
        """Adiciona uma reserva ao histórico pessoal do hóspede.

        Args:
            reserva (Reserva): Instância válida de `Reserva` pertencente a este hóspede.

        Raises:
            DadosInvalidosException: Se o objeto fornecido for nulo ou se já
                estiver presente no histórico.
        """
        if reserva is None:
            raise DadosInvalidosException("A reserva fornecida para vinculação não pode ser nula.")
        if reserva in self._historico_reservas:
            raise DadosInvalidosException(f"A reserva com ID {getattr(reserva, 'id', 'desconhecido')} já consta no histórico do hóspede.")
        self._historico_reservas.append(reserva)

    # ----------------------------------------------------------------------- #
    # Serialização e Métodos Especiais                                        #
    # ----------------------------------------------------------------------- #

    @classmethod
    def from_dict(cls, dados: Dict[str, Any]) -> Hospede:
        """Reconstrói uma instância de Hospede a partir de um dicionário.

        Args:
            dados (Dict[str, Any]): Dicionário com chaves cadastrais do hóspede.

        Returns:
            Hospede: Objeto reconstruído com os dados fornecidos.

        Raises:
            DadosInvalidosException: Se faltarem campos obrigatórios.
        """
        if not isinstance(dados, dict):
            raise DadosInvalidosException("Os dados para desserialização do hóspede devem ser um dicionário.")
        return cls(
            id_=int(dados.get("id", 0)),
            nome=str(dados.get("nome", "")),
            documento=str(dados.get("documento", "")),
            email=str(dados.get("email", "")),
            telefone=str(dados.get("telefone", "")),
            preferencias=str(dados.get("preferencias", "")),
        )

    def __str__(self) -> str:
        """Retorna uma representação amigável do hóspede.

        Returns:
            str: Resumo com ID, nome e documento do hóspede.
        """
        return f"Hóspede #{self._id}: {self._nome} (Doc: {self._documento}, Contato: {self._telefone})"

    def __repr__(self) -> str:
        """Retorna a representação técnica do objeto Hospede.

        Returns:
            str: Representação técnica para depuração.
        """
        return (
            f"Hospede(id={self._id!r}, nome={self._nome!r}, documento={self._documento!r}, "
            f"email={self._email!r}, telefone={self._telefone!r}, preferencias={self._preferencias!r})"
        )