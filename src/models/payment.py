
from __future__ import annotations
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, Optional

from .enums import MetodoPagamento
from .exceptions import DadosInvalidosException
from .mixins import Serializavel

if TYPE_CHECKING:
    from .reservation import Reserva


class Pagamento(Serializavel):
    """Representa uma transação financeira de pagamento vinculada a uma reserva.

    Cada instância registra uma quantia monetária quitada pelo hóspede em uma
    modalidade permitida (`DINHEIRO`, `CREDITO`, `DEBITO` ou `PIX`), abatendo o
    saldo devedor da reserva correspondente.
    """

    def __init__(
        self,
        id_: int = 0,
        valor: float = 0.0,
        metodo: MetodoPagamento = MetodoPagamento.DINHEIRO,
        data_pagamento: Optional[datetime] = None,
    ) -> None:
    
        super().__init__()
        self._id: int = 0
        self._valor: float = 0.0
        self._metodo: MetodoPagamento = MetodoPagamento.DINHEIRO
        self._data_pagamento: datetime = data_pagamento or datetime.now()

        if id_ != 0:
            self.id = id_
        else:
            self._id = id_

        if valor != 0.0:
            self.valor = valor
        else:
            self._valor = valor

        if metodo is not None:
            self.metodo = metodo

    @classmethod
    def vazio(cls) -> Pagamento:
        """Construtor de fábrica que retorna um pagamento com valores padrão."""
        return cls()

# ----------------------------------------------------------------------- #
# Propriedades de Acesso (Getters e Setters)                               #
# ----------------------------------------------------------------------- #

    @property
    def id(self) -> int:
        """Retorna o identificador numérico único do pagamento."""
        return self._id

    @id.setter
    def id(self, valor: int) -> None:
        """Define o identificador numérico único do pagamento."""

        if not isinstance(valor, int) or valor < 0:
            raise DadosInvalidosException("O ID do pagamento deve ser um número inteiro maior ou igual a zero.")
        self._id = valor

    @property
    def valor(self) -> float:
        """Retorna o valor monetário registrado no pagamento."""
        return self._valor

    @valor.setter
    def valor(self, valor: float) -> None:
        """Define e valida o valor monetário do pagamento."""
        try:
            val_float = float(valor)
        except (ValueError, TypeError):
            raise DadosInvalidosException("O valor do pagamento deve ser um número real válido.")

        if val_float <= 0.0:
            raise DadosInvalidosException(f"O valor do pagamento deve ser estritamente positivo (> 0). Recebido: {val_float}")
        self._valor = round(val_float, 2)

    @property
    def metodo(self) -> MetodoPagamento:
        """Retorna a modalidade de pagamento utilizada."""
        return self._metodo

    @metodo.setter
    def metodo(self, valor: Any) -> None:
        """Define e valida o meio de pagamento utilizado."""
        if isinstance(valor, MetodoPagamento):
            self._metodo = valor
        elif isinstance(valor, str):
            try:
                self._metodo = MetodoPagamento(valor.upper())
            except ValueError:
                raise DadosInvalidosException(
                    f"Método de pagamento inválido: '{valor}'. Valores válidos: {[m.value for m in MetodoPagamento]}"
                )
        else:
            raise DadosInvalidosException("O método de pagamento deve ser uma instância válida de MetodoPagamento.")

    @property
    def data_pagamento(self) -> datetime:
        """Retorna a data e hora em que a transação foi efetuada."""
        return self._data_pagamento

    @data_pagamento.setter
    def data_pagamento(self, valor: datetime) -> None:
        """Define a data e hora do pagamento."""
        if not isinstance(valor, datetime):
            raise DadosInvalidosException("A data de pagamento deve ser um objeto datetime válido.")
        self._data_pagamento = valor

# ----------------------------------------------------------------------- #
# Serialização e Métodos Especiais                                        #
# ----------------------------------------------------------------------- #

    @classmethod
    def from_dict(cls, dados: Dict[str, Any]) -> Pagamento:
        """Reconstrói uma instância de `Pagamento` a partir de um dicionário."""
        if not isinstance(dados, dict):
            raise DadosInvalidosException("Os dados de entrada para Pagamento devem ser um dicionário.")

        data_str = dados.get("data_pagamento")
        data_dt: Optional[datetime] = None
        if data_str:
            if isinstance(data_str, datetime):
                data_dt = data_str
            else:
                try:
                    data_dt = datetime.fromisoformat(str(data_str))
                except ValueError:
                    data_dt = datetime.now()

        metodo_raw = dados.get("metodo", MetodoPagamento.DINHEIRO.value)
        metodo = MetodoPagamento(metodo_raw) if isinstance(metodo_raw, str) else metodo_raw

        return cls(
            id_=int(dados.get("id", 0)),
            valor=float(dados.get("valor", 0.0)),
            metodo=metodo,
            data_pagamento=data_dt,
        )

    def __str__(self) -> str:
        """Retorna uma representação legível do pagamento."""
        data_fmt = self._data_pagamento.strftime("%d/%m/%Y %H:%M")
        return f"Pagamento #{self._id}: R$ {self._valor:.2f} via {self._metodo.value} em {data_fmt}"

    def __repr__(self) -> str:
        """Retorna a representação técnica oficial para depuração."""
        return (
            f"Pagamento(id={self._id!r}, valor={self._valor!r}, "
            f"metodo={self._metodo!r}, data_pagamento={self._data_pagamento.isoformat()!r})"
        )



class Adicional(Serializavel):
    """Representa um item de consumo ou serviço extra lançado na reserva.

    Utilizada para registrar consumos durante a estadia (ex.: frigobar,
    estacionamento, refeições, lavanderia), compondo o montante global devido
    no momento do encerramento da conta (check-out).
    """

    def __init__(
        self,
        id_: int = 0,
        descricao: str = "",
        preco_unitario: float = 0.0,
        quantidade: int = 1,
    ) -> None:
       
        super().__init__()
        self._id: int = 0
        self._descricao: str = ""
        self._preco_unitario: float = 0.0
        self._quantidade: int = 1

        if id_ != 0:
            self.id = id_
        else:
            self._id = id_

        if descricao:
            self.descricao = descricao
        if preco_unitario != 0.0:
            self.preco_unitario = preco_unitario
        if quantidade != 1:
            self.quantidade = quantidade

    @classmethod
    def vazio(cls) -> Adicional:
        """Construtor de fábrica que retorna um adicional com atributos padrão vazios."""
        return cls()

# ----------------------------------------------------------------------- #
# Propriedades de Acesso (Getters e Setters)                               #
# ----------------------------------------------------------------------- #

    @property
    def id(self) -> int:
        """Retorna o identificador único do consumo adicional."""
        return self._id

    @id.setter
    def id(self, valor: int) -> None:
        """Define o identificador numérico único do adicional."""
        if not isinstance(valor, int) or valor < 0:
            raise DadosInvalidosException("O ID do adicional deve ser um número inteiro maior ou igual a zero.")
        self._id = valor

    @property
    def descricao(self) -> str:
        """Retorna a descrição do produto ou serviço adicional."""
        return self._descricao

    @descricao.setter
    def descricao(self, valor: str) -> None:
        """Define e valida a descrição do item adicional."""
        if not isinstance(valor, str) or not valor.strip():
            raise DadosInvalidosException("A descrição do adicional não pode ser vazia.")
        self._descricao = valor.strip()

    @property
    def preco_unitario(self) -> float:
        """Retorna o preço unitário do item consumido."""
        return self._preco_unitario

    @preco_unitario.setter
    def preco_unitario(self, valor: float) -> None:
        """Define e valida o preço unitário do item."""
        try:
            val_float = float(valor)
        except (ValueError, TypeError):
            raise DadosInvalidosException("O preço unitário deve ser um número real válido.")

        if val_float <= 0.0:
            raise DadosInvalidosException(f"O preço unitário deve ser estritamente positivo (> 0). Recebido: {val_float}")
        self._preco_unitario = round(val_float, 2)

    @property
    def quantidade(self) -> int:
        """Retorna o número de unidades consumidas do item."""
        return self._quantidade

    @quantidade.setter
    def quantidade(self, valor: int) -> None:
        """Define e valida a quantidade consumida do item."""
        if not isinstance(valor, int) or valor < 1:
            raise DadosInvalidosException(f"A quantidade de itens adicionais deve ser de no mínimo 1. Recebido: {valor}")
        self._quantidade = valor

    @property
    def total(self) -> float:
        """Calcula e retorna o subtotal do item (`preco_unitario * quantidade`)."""
        return round(self._preco_unitario * self._quantidade, 2)

# ----------------------------------------------------------------------- #
# Serialização e Métodos Especiais                                        #
# ----------------------------------------------------------------------- #

    @classmethod
    def from_dict(cls, dados: Dict[str, Any]) -> Adicional:
        """Reconstrói uma instância de `Adicional` a partir de um dicionário."""
        if not isinstance(dados, dict):
            raise DadosInvalidosException("Os dados de entrada para Adicional devem ser um dicionário.")
        return cls(
            id_=int(dados.get("id", 0)),
            descricao=str(dados.get("descricao", "")),
            preco_unitario=float(dados.get("preco_unitario", 0.0)),
            quantidade=int(dados.get("quantidade", 1)),
        )

    def __str__(self) -> str:
        """Retorna uma representação textual amigável do item adicional."""
        return (
            f"Adicional #{self._id}: {self._descricao} - {self._quantidade}x "
            f"R$ {self._preco_unitario:.2f} (Total: R$ {self.total:.2f})"
        )

    def __repr__(self) -> str:
        """Retorna a representação técnica oficial para depuração."""
        return (
            f"Adicional(id={self._id!r}, descricao={self._descricao!r}, "
            f"preco_unitario={self._preco_unitario!r}, quantidade={self._quantidade!r})"
        )