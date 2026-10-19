
from __future__ import annotations
from abc import ABC
import re
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from .exceptions import DadosInvalidosException
from .mixins import Serializavel

if TYPE_CHECKING:
    from .reservation import Reserva

class Pessoa(Serializavel, ABC):
    """Classe base abstrata que encapsula os dados cadastrais de uma pessoa.

    superclasse para `Hospede` e eventuais outros perfis do sistema,
    garantindo validação de dados de identificação e contato, além de fornecer
    capacidade de serialização em dicionários e JSON.
    """

    def __init__(
        self,
        id_: int = 0,
        nome: str = "",
        documento: str = "",
        email: str = "",
        telefone: str = "",
    ) -> None:
        
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
        """Construtor de fábrica que retorna uma instância vazia."""
        return cls()

    # ----------------------------------------------------------------------- #
    # Propriedades de Acesso (Getters e Setters)                               #
    # ----------------------------------------------------------------------- #

    @property
    def id(self) -> int:
        """Identificador numérico único da pessoa."""
        return self._id

    @id.setter
    def id(self, valor: int) -> None:
        """Define o identificador numérico único da pessoa."""
        if not isinstance(valor, int) or valor < 0:
            raise DadosInvalidosException("O ID da pessoa deve ser um número inteiro maior ou igual a zero.")
        self._id = valor

    @property
    def nome(self) -> str:
        """Nome completo da pessoa."""
        return self._nome

    @nome.setter
    def nome(self, valor: str) -> None:
        """Define e valida o nome completo da pessoa."""
        if not isinstance(valor, str) or not valor.strip():
            raise DadosInvalidosException("O nome da pessoa não pode ser vazio.")
        self._nome = valor.strip()

    @property
    def documento(self) -> str:
        """Número do documento de identificação (CPF ou Passaporte)."""
        return self._documento

    @documento.setter
    def documento(self, valor: str) -> None:
        """Define e valida o documento de identificação da pessoa."""
        if not isinstance(valor, str) or not valor.strip():
            raise DadosInvalidosException("O documento da pessoa não pode ser vazio.")
        self._documento = valor.strip()

    @property
    def email(self) -> str:
        """Endereço de correio eletrônico cadastrado."""
        return self._email

    @email.setter
    def email(self, valor: str) -> None:
        """Define e valida o endereço de e-mail da pessoa."""
        if not isinstance(valor, str) or not valor.strip():
            raise DadosInvalidosException("O e-mail da pessoa não pode ser vazio.")
        padrao = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        if not re.match(padrao, valor.strip()):
            raise DadosInvalidosException(f"O e-mail '{valor}' possui formato inválido.")
        self._email = valor.strip()

    @property
    def telefone(self) -> str:
        """Número de telefone com código de área."""
        return self._telefone

    @telefone.setter
    def telefone(self, valor: str) -> None:
        """Define e valida o telefone de contato da pessoa."""
        if not isinstance(valor, str) or not valor.strip():
            raise DadosInvalidosException("O telefone da pessoa não pode ser vazio.")
        self._telefone = valor.strip()


class Hospede(Pessoa):
    """Subclasse concreta que representa um cliente (hóspede) do hotel.

    Especializa a classe `Pessoa`, adicionando preferências de estadia
    e mantendo a associação com o histórico de reservas do cliente.
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
       
        super().__init__(id_=id_, nome=nome, documento=documento, email=email, telefone=telefone)
        self._preferencias: str = preferencias or ""
        self._historico_reservas: List[Reserva] = []

    @classmethod
    def vazio(cls) -> Hospede:
        """Construtor de fábrica que retorna um hóspede com atributos padrão vazios."""
        return cls()

    # ----------------------------------------------------------------------- #
    # Propriedades de Acesso                                #
    # ----------------------------------------------------------------------- #

    @property
    def preferencias(self) -> str:
        """Texto descritivo das preferências de estadia do hóspede."""
        return self._preferencias

    @preferencias.setter
    def preferencias(self, valor: str) -> None:
        """Define as preferências de acomodação do hóspede."""
        self._preferencias = str(valor) if valor is not None else ""

    @property
    def historico_reservas(self) -> List[Reserva]:
        """Lista de reservas associadas ao histórico do hóspede."""
        return list(self._historico_reservas)

    # ----------------------------------------------------------------------- #
    # Métodos de Comportamento                                                #
    # ----------------------------------------------------------------------- #

    def vincular_reserva(self, reserva: Reserva) -> None:
        """Adiciona uma reserva ao histórico pessoal do hóspede."""
        if reserva is None:
            raise DadosInvalidosException("A reserva fornecida para vinculação não pode ser nula.")
        if reserva in self._historico_reservas:
            raise DadosInvalidosException(f"A reserva com ID {getattr(reserva, 'id', 'desconhecido')} já consta no histórico do hóspede.")
        self._historico_reservas.append(reserva)

    # ----------------------------------------------------------------------- #
    # Serialização e Métodos Especiais                                        #
    # ----------------------------------------------------------------------- #

    def to_dict(self) -> Dict[str, Any]:
        """Converte o hóspede em dicionário sem expandir reservas recursivamente."""
        dados = {
            "id": self._id,
            "nome": self._nome,
            "documento": self._documento,
            "email": self._email,
            "telefone": self._telefone,
            "preferencias": self._preferencias,
        }
        dados["historico_reservas"] = [
            {"id": reserva.id} for reserva in self._historico_reservas
        ]
        return dados

    @classmethod
    def from_dict(cls, dados: Dict[str, Any]) -> Hospede:
        """Reconstrói uma instância de Hospede a partir de um dicionário."""
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
        """Retorna uma representação amigável do hóspede."""
        return f"Hóspede #{self._id}: {self._nome} (Doc: {self._documento}, Contato: {self._telefone})"

    def __repr__(self) -> str:
        """Retorna a representação técnica do objeto Hospede."""
        return (
            f"Hospede(id={self._id!r}, nome={self._nome!r}, documento={self._documento!r}, "
            f"email={self._email!r}, telefone={self._telefone!r}, preferencias={self._preferencias!r})"
        )