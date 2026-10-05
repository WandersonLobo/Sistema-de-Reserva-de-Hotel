"""Módulo que define as entidades financeiras e de consumo extra da reserva."""

from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, Optional

try:
    from .enums import MetodoPagamento
    from .exceptions import DadosInvalidosException
    from .mixins import Serializavel
except (ImportError, ValueError):
    from enums import MetodoPagamento  # type: ignore
    from exceptions import DadosInvalidosException  # type: ignore
    from mixins import Serializavel  # type: ignore


class Pagamento(Serializavel):
    """Representa uma transação financeira de pagamento vinculada a uma reserva.

    Cada instância registra uma quantia monetária quitada pelo hóspede em uma
    modalidade permitida (`DINHEIRO`, `CREDITO`, `DEBITO` ou `PIX`), abatendo o
    saldo devedor da reserva correspondente.

    Attributes:
        _id (int): Identificador único do registro de pagamento.
        _valor (float): Quantia monetária paga na transação (> 0).
        _metodo (MetodoPagamento): Modalidade utilizada (DINHEIRO, CREDITO, DEBITO, PIX).
        _data_pagamento (datetime): Data e hora exatas em que o pagamento ocorreu.
    """

    def __init__(
        self,
        id_: int = 0,
        valor: float = 0.0,
        metodo: MetodoPagamento = MetodoPagamento.DINHEIRO,
        data_pagamento: Optional[datetime] = None,
    ) -> None:
        """Inicializa um novo registro de pagamento.

        Permite a criação vazia (`Pagamento()`) com valores padrão ou
        parametrizada com validação das regras financeiras.

        Args:
            id_ (int, optional): Identificador único do pagamento. Padrão é 0.
            valor (float, optional): Valor monetário pago (> 0 se especificado). Padrão é 0.0.
            metodo (MetodoPagamento, optional): Modalidade de pagamento. Padrão é DINHEIRO.
            data_pagamento (Optional[datetime], optional): Momento da transação.
                Se omitido, assume a data e hora atuais.

        Raises:
            DadosInvalidosException: Se `valor < 0` ou método inválido.
        """
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
        """Construtor de fábrica que retorna um pagamento com valores padrão.

        Returns:
            Pagamento: Nova instância vazia de Pagamento.
        """
        return cls()

# ----------------------------------------------------------------------- #
# Propriedades de Acesso (Getters e Setters)                               #
# ----------------------------------------------------------------------- #

    @property
    def id(self) -> int:
        """Retorna o identificador numérico único do pagamento.

        Returns:
            int: ID do pagamento.
        """
        return self._id

    @id.setter
    def id(self, valor: int) -> None:
        """Define o identificador numérico único do pagamento.

        Args:
            valor (int): Novo identificador (deve ser >= 0).

        Raises:
            DadosInvalidosException: Se o valor for negativo ou não for inteiro.
        """
        if not isinstance(valor, int) or valor < 0:
            raise DadosInvalidosException("O ID do pagamento deve ser um número inteiro maior ou igual a zero.")
        self._id = valor

    @property
    def valor(self) -> float:
        """Retorna o valor monetário registrado no pagamento.

        Returns:
            float: Quantia monetária da transação.
        """
        return self._valor

    @valor.setter
    def valor(self, valor: float) -> None:
        """Define e valida o valor monetário do pagamento.

        Args:
            valor (float): Quantia paga (deve ser estritamente positiva).

        Raises:
            DadosInvalidosException: Se o valor for menor ou igual a zero.
        """
        try:
            val_float = float(valor)
        except (ValueError, TypeError):
            raise DadosInvalidosException("O valor do pagamento deve ser um número real válido.")

        if val_float <= 0.0:
            raise DadosInvalidosException(f"O valor do pagamento deve ser estritamente positivo (> 0). Recebido: {val_float}")
        self._valor = round(val_float, 2)

    @property
    def metodo(self) -> MetodoPagamento:
        """Retorna a modalidade de pagamento utilizada.

        Returns:
            MetodoPagamento: Enumeração correspondente ao meio de pagamento.
        """
        return self._metodo

    @metodo.setter
    def metodo(self, valor: Any) -> None:
        """Define e valida o meio de pagamento utilizado.

        Args:
            valor (Any): Membro de `MetodoPagamento` ou string compatível.

        Raises:
            DadosInvalidosException: Se o valor não for reconhecido como MetodoPagamento.
        """
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
        """Retorna a data e hora em que a transação foi efetuada.

        Returns:
            datetime: Carimbo de tempo do pagamento.
        """
        return self._data_pagamento

    @data_pagamento.setter
    def data_pagamento(self, valor: datetime) -> None:
        """Define a data e hora do pagamento.

        Args:
            valor (datetime): Novo carimbo de tempo da transação.

        Raises:
            DadosInvalidosException: Se o valor não for uma instância de datetime.
        """
        if not isinstance(valor, datetime):
            raise DadosInvalidosException("A data de pagamento deve ser um objeto datetime válido.")
        self._data_pagamento = valor

# ----------------------------------------------------------------------- #
# Serialização e Métodos Especiais                                        #
# ----------------------------------------------------------------------- #

    @classmethod
    def from_dict(cls, dados: Dict[str, Any]) -> Pagamento:
        """Reconstrói uma instância de `Pagamento` a partir de um dicionário.

        Args:
            dados (Dict[str, Any]): Dicionário com chaves `id`, `valor`, `metodo` e `data_pagamento`.

        Returns:
            Pagamento: Nova instância reconstruída com os tipos corretos.

        Raises:
            DadosInvalidosException: Se os dados forem inconsistentes ou faltarem chaves obrigatórias.
        """
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
        """Retorna uma representação legível do pagamento.

        Returns:
            str: Resumo com ID, valor formatado, método e data.
        """
        data_fmt = self._data_pagamento.strftime("%d/%m/%Y %H:%M")
        return f"Pagamento #{self._id}: R$ {self._valor:.2f} via {self._metodo.value} em {data_fmt}"

    def __repr__(self) -> str:
        """Retorna a representação técnica oficial para depuração.

        Returns:
            str: Representação técnica do objeto Pagamento.
        """
        return (
            f"Pagamento(id={self._id!r}, valor={self._valor!r}, "
            f"metodo={self._metodo!r}, data_pagamento={self._data_pagamento.isoformat()!r})"
        )



class Adicional(Serializavel):
    """Representa um item de consumo ou serviço extra lançado na reserva.

    Utilizada para registrar consumos durante a estadia (ex.: frigobar,
    estacionamento, refeições, lavanderia), compondo o montante global devido
    no momento do encerramento da conta (check-out).
    
    Attributes:
        _id (int): Identificador único do consumo adicional.
        _descricao (str): Nome ou descrição do produto/serviço consumido.
        _preco_unitario (float): Valor unitário do item (> 0).
        _quantidade (int): Quantidade consumida do item (>= 1).
    """

    def __init__(
        self,
        id_: int = 0,
        descricao: str = "",
        preco_unitario: float = 0.0,
        quantidade: int = 1,
    ) -> None:
        """Inicializa um novo lançamento de consumo adicional.

        Permite a criação vazia (`Adicional()`) com valores padrão ou
        parametrizada com validação dos dados de produto e quantidade.

        Args:
            id_ (int, optional): Identificador único do adicional. Padrão é 0.
            descricao (str, optional): Nome ou descrição do produto/serviço. Padrão é "".
            preco_unitario (float, optional): Preço unitário (> 0 se especificado). Padrão é 0.0.
            quantidade (int, optional): Quantidade consumida (>= 1). Padrão é 1.

        Raises:
            DadosInvalidosException: Se a descrição for vazia, `preco_unitario < 0`
                ou `quantidade < 1`.
        """
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
        """Construtor de fábrica que retorna um adicional com atributos padrão vazios.

        Returns:
            Adicional: Nova instância vazia de Adicional.
        """
        return cls()

# ----------------------------------------------------------------------- #
# Propriedades de Acesso (Getters e Setters)                               #
# ----------------------------------------------------------------------- #

    @property
    def id(self) -> int:
        """Retorna o identificador único do consumo adicional.

        Returns:
            int: ID do adicional.
        """
        return self._id

    @id.setter
    def id(self, valor: int) -> None:
        """Define o identificador numérico único do adicional.

        Args:
            valor (int): Novo identificador (deve ser >= 0).

        Raises:
            DadosInvalidosException: Se o valor for negativo ou não for inteiro.
        """
        if not isinstance(valor, int) or valor < 0:
            raise DadosInvalidosException("O ID do adicional deve ser um número inteiro maior ou igual a zero.")
        self._id = valor

    @property
    def descricao(self) -> str:
        """Retorna a descrição do produto ou serviço adicional.

        Returns:
            str: Descrição do item consumido.
        """
        return self._descricao

    @descricao.setter
    def descricao(self, valor: str) -> None:
        """Define e valida a descrição do item adicional.

        Args:
            valor (str): Descrição do produto ou serviço (não vazia).

        Raises:
            DadosInvalidosException: Se o valor for vazio ou não for string.
        """
        if not isinstance(valor, str) or not valor.strip():
            raise DadosInvalidosException("A descrição do adicional não pode ser vazia.")
        self._descricao = valor.strip()

    @property
    def preco_unitario(self) -> float:
        """Retorna o preço unitário do item consumido.

        Returns:
            float: Valor de uma unidade.
        """
        return self._preco_unitario

    @preco_unitario.setter
    def preco_unitario(self, valor: float) -> None:
        """Define e valida o preço unitário do item.

        Args:
            valor (float): Preço unitário (deve ser estritamente positivo).

        Raises:
            DadosInvalidosException: Se o preço for menor ou igual a zero.
        """
        try:
            val_float = float(valor)
        except (ValueError, TypeError):
            raise DadosInvalidosException("O preço unitário deve ser um número real válido.")

        if val_float <= 0.0:
            raise DadosInvalidosException(f"O preço unitário deve ser estritamente positivo (> 0). Recebido: {val_float}")
        self._preco_unitario = round(val_float, 2)

    @property
    def quantidade(self) -> int:
        """Retorna o número de unidades consumidas do item.

        Returns:
            int: Quantidade consumida.
        """
        return self._quantidade

    @quantidade.setter
    def quantidade(self, valor: int) -> None:
        """Define e valida a quantidade consumida do item.

        Args:
            valor (int): Quantidade consumida (deve ser maior ou igual a 1).

        Raises:
            DadosInvalidosException: Se a quantidade for menor que 1.
        """
        if not isinstance(valor, int) or valor < 1:
            raise DadosInvalidosException(f"A quantidade de itens adicionais deve ser de no mínimo 1. Recebido: {valor}")
        self._quantidade = valor

    @property
    def total(self) -> float:
        """Calcula e retorna o subtotal do item (`preco_unitario * quantidade`).

        Returns:
            float: Valor total acumulado deste item adicional.
        """
        return round(self._preco_unitario * self._quantidade, 2)

# ----------------------------------------------------------------------- #
# Serialização e Métodos Especiais                                        #
# ----------------------------------------------------------------------- #

    @classmethod
    def from_dict(cls, dados: Dict[str, Any]) -> Adicional:
        """Reconstrói uma instância de `Adicional` a partir de um dicionário.

        Args:
            dados (Dict[str, Any]): Dicionário com chaves `id`, `descricao`, `preco_unitario` e `quantidade`.

        Returns:
            Adicional: Objeto reconstruído com os dados fornecidos.

        Raises:
            DadosInvalidosException: Se os dados forem inconsistentes.
        """
        if not isinstance(dados, dict):
            raise DadosInvalidosException("Os dados de entrada para Adicional devem ser um dicionário.")
        return cls(
            id_=int(dados.get("id", 0)),
            descricao=str(dados.get("descricao", "")),
            preco_unitario=float(dados.get("preco_unitario", 0.0)),
            quantidade=int(dados.get("quantidade", 1)),
        )

    def __str__(self) -> str:
        """Retorna uma representação textual amigável do item adicional.

        Returns:
            str: Resumo com descrição, quantidade, preço unitário e total.
        """
        return (
            f"Adicional #{self._id}: {self._descricao} - {self._quantidade}x "
            f"R$ {self._preco_unitario:.2f} (Total: R$ {self.total:.2f})"
        )

    def __repr__(self) -> str:
        """Retorna a representação técnica oficial para depuração.

        Returns:
            str: Representação técnica do objeto Adicional.
        """
        return (
            f"Adicional(id={self._id!r}, descricao={self._descricao!r}, "
            f"preco_unitario={self._preco_unitario!r}, quantidade={self._quantidade!r})"
        )