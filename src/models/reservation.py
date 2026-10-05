"""Módulo que define a entidade central de Reserva do sistema hoteleiro.

Este módulo contém a classe `Reserva`, responsável por associar um `Hospede`
a um `Quarto` num intervalo de datas, gerir o ciclo de vida da estadia,
compor listas de `Pagamento` e `Adicional`, e implementar herança múltipla
com `Auditoria` e `Serializavel`.

"""


from __future__ import annotations
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

try:
    from .enums import OrigemReserva, StatusQuarto, StatusReserva
    from .exceptions import (
        CapacidadeExcedidaException,
        DadosInvalidosException,
        PagamentoInsuficienteException,
        QuartoIndisponivelException,
        TransicaoEstadoInvalidaException,
    )
    from .mixins import Auditoria, Serializavel
    from .payment import Adicional, Pagamento
    from .person import Hospede
    from .room import Quarto
except (ImportError, ValueError):
    from enums import OrigemReserva, StatusQuarto, StatusReserva  # type: ignore
    from exceptions import (  # type: ignore
        CapacidadeExcedidaException,
        DadosInvalidosException,
        PagamentoInsuficienteException,
        QuartoIndisponivelException,
        TransicaoEstadoInvalidaException,
    )
    from mixins import Auditoria, Serializavel  # type: ignore
    from payment import Adicional, Pagamento  # type: ignore
    from person import Hospede  # type: ignore
    from room import Quarto  # type: ignore

class Reserva(Auditoria, Serializavel):
    """Entidade central que representa uma reserva de acomodação no hotel.

    Coordena as regras de validação de datas e capacidade, controla as
    transições de estado da hospedagem e consolida os valores financeiros
    de diárias, consumos adicionais, multas e pagamentos.

    Attributes:
        _id (int): Identificador único da reserva.
        _hospede (Hospede): Objeto `Hospede` titular da reserva (agregação).
        _quarto (Quarto): Objeto `Quarto` alocado na reserva (agregação).
        _data_entrada (date): Data prevista para o início da estadia (check-in).
        _data_saida (date): Data prevista para o término da estadia (check-out).
        _checkin_real (datetime | None): Data e hora exatas em que o check-in ocorreu.
        _checkout_real (datetime | None): Data e hora exatas em que o check-out ocorreu.
        _num_hospedes (int): Quantidade de ocupantes vinculada à reserva.
        _origem (OrigemReserva): Canal de origem da reserva (SITE, TELEFONE, BALCAO).
        _status (StatusReserva): Estado atual no ciclo de vida da reserva.
        _valor_total_diarias (float): Soma do valor das diárias calculadas para o período.
        _pagamentos (list[Pagamento]): Lista de pagamentos efetuados (composição).
        _adicionais (list[Adicional]): Lista de consumos extras lançados (composição).
    """

    def __init__(
        self,
        id_: int = 0,
        hospede: Optional[Hospede] = None,
        quarto: Optional[Quarto] = None,
        data_entrada: Optional[date] = None,
        data_saida: Optional[date] = None,
        num_hospedes: int = 1,
        origem: OrigemReserva = OrigemReserva.SITE,
        valor_total_diarias: float = 0.0,
        status: StatusReserva = StatusReserva.PENDENTE,
    ) -> None:
        """Inicializa uma reserva com validações de datas e capacidade.

        Permite a criação vazia (`Reserva()`) com valores padrão ou
        parametrizada com verificação das regras de negócio.

        Args:
            id_ (int, optional): Identificador único da reserva. Padrão é 0.
            hospede (Optional[Hospede], optional): Titular da reserva.
            quarto (Optional[Quarto], optional): Quarto alocado.
            data_entrada (Optional[date], optional): Início da hospedagem.
            data_saida (Optional[date], optional): Término da hospedagem.
            num_hospedes (int, optional): Quantidade de ocupantes. Padrão é 1.
            origem (OrigemReserva, optional): Canal da reserva. Padrão é SITE.
            valor_total_diarias (float, optional): Valor das diárias. Padrão é 0.0.
            status (StatusReserva, optional): Estado inicial. Padrão é PENDENTE.

        Raises:
            DadosInvalidosException: Se `data_entrada >= data_saida` ou `num_hospedes < 1`.
            CapacidadeExcedidaException: Se `num_hospedes > quarto.capacidade`.
        """
        super().__init__()  # Inicializa o mixin Auditoria

        self._id: int = int(id_)
        self._hospede: Optional[Hospede] = hospede
        self._quarto: Optional[Quarto] = quarto

        hoje = date.today()
        entrada_valida = data_entrada or hoje
        saida_valida = data_saida or (entrada_valida + timedelta(days=1))

        if entrada_valida >= saida_valida:
            raise DadosInvalidosException(
                f"A data de entrada ({entrada_valida}) deve ser anterior à data de saída ({saida_valida})."
            )

        self._data_entrada: date = entrada_valida
        self._data_saida: date = saida_valida

        if num_hospedes < 1:
            raise DadosInvalidosException("O número de hóspedes deve ser de no mínimo 1.")

        if quarto is not None and num_hospedes > quarto.capacidade:
            raise CapacidadeExcedidaException(
                f"O número de hóspedes ({num_hospedes}) excede a capacidade do quarto {quarto.numero} ({quarto.capacidade})."
            )

        self._num_hospedes: int = int(num_hospedes)
        self._origem: OrigemReserva = origem
        self._status: StatusReserva = status
        self._valor_total_diarias: float = float(valor_total_diarias)
        self._checkin_real: Optional[datetime] = None
        self._checkout_real: Optional[datetime] = None
        self._pagamentos: List[Pagamento] = []
        self._adicionais: List[Adicional] = []

    @classmethod
    def vazio(cls) -> Reserva:
        """Construtor de fábrica que retorna uma reserva com atributos padrão.

        Returns:
            Reserva: Nova instância vazia de Reserva.
        """
        return cls()

# ----------------------------------------------------------------------- #
# Propriedades de Acesso (Getters e Setters)                               #
# ----------------------------------------------------------------------- #

    @property
    def id(self) -> int:
        """Retorna o identificador numérico único da reserva.

        Returns:
            int: ID da reserva.
        """
        return self._id

    @id.setter
    def id(self, valor: int) -> None:
        """Define o identificador numérico da reserva.

        Args:
            valor (int): Novo ID (deve ser >= 0).

        Raises:
            DadosInvalidosException: Se o valor for negativo.
        """
        if not isinstance(valor, int) or valor < 0:
            raise DadosInvalidosException("O ID da reserva deve ser um número inteiro maior ou igual a zero.")
        self._id = valor

    @property
    def hospede(self) -> Optional[Hospede]:
        """Retorna o hóspede titular associado à reserva.

        Returns:
            Optional[Hospede]: Objeto Hospede ou None.
        """
        return self._hospede

    @hospede.setter
    def hospede(self, valor: Optional[Hospede]) -> None:
        """Define o hóspede titular da reserva.

        Args:
            valor (Optional[Hospede]): Instância de Hospede.
        """
        self._hospede = valor

    @property
    def quarto(self) -> Optional[Quarto]:
        """Retorna o quarto alocado para a reserva.

        Returns:
            Optional[Quarto]: Objeto Quarto ou None.
        """
        return self._quarto

    @quarto.setter
    def quarto(self, valor: Optional[Quarto]) -> None:
        """Aloca um quarto para a reserva, validando capacidade.

        Args:
            valor (Optional[Quarto]): Instância de Quarto.

        Raises:
            CapacidadeExcedidaException: Se a quantidade de hóspedes exceder a capacidade do novo quarto.
        """
        if valor is not None and self._num_hospedes > valor.capacidade:
            raise CapacidadeExcedidaException(
                f"O número de hóspedes ({self._num_hospedes}) excede a capacidade do novo quarto ({valor.capacidade})."
            )
        self._quarto = valor

    @property
    def data_entrada(self) -> date:
        """Retorna a data prevista de entrada (check-in).

        Returns:
            date: Data inicial da estadia.
        """
        return self._data_entrada

    @data_entrada.setter
    def data_entrada(self, valor: date) -> None:
        """Define e valida a nova data de entrada da reserva.

        Args:
            valor (date): Nova data de início.

        Raises:
            DadosInvalidosException: Se `valor >= self._data_saida`.
        """
        if not isinstance(valor, date):
            raise DadosInvalidosException("A data de entrada deve ser uma instância válida de date.")
        if valor >= self._data_saida:
            raise DadosInvalidosException(
                f"A data de entrada ({valor}) não pode ser posterior ou igual à data de saída ({self._data_saida})."
            )
        self._data_entrada = valor

    @property
    def data_saida(self) -> date:
        """Retorna a data prevista de saída (check-out).

        Returns:
            date: Data final da estadia.
        """
        return self._data_saida

    @data_saida.setter
    def data_saida(self, valor: date) -> None:
        """Define e valida a nova data de saída da reserva.

        Args:
            valor (date): Nova data de término.

        Raises:
            DadosInvalidosException: Se `valor <= self._data_entrada`.
        """
        if not isinstance(valor, date):
            raise DadosInvalidosException("A data de saída deve ser uma instância válida de date.")
        if valor <= self._data_entrada:
            raise DadosInvalidosException(
                f"A data de saída ({valor}) deve ser posterior à data de entrada ({self._data_entrada})."
            )
        self._data_saida = valor

    @property
    def checkin_real(self) -> Optional[datetime]:
        """Retorna a data e hora em que o check-in efetivo ocorreu.

        Returns:
            Optional[datetime]: Momento do check-in ou None.
        """
        return self._checkin_real

    @property
    def checkout_real(self) -> Optional[datetime]:
        """Retorna a data e hora em que o check-out efetivo ocorreu.

        Returns:
            Optional[datetime]: Momento do check-out ou None.
        """
        return self._checkout_real

    @property
    def num_hospedes(self) -> int:
        """Retorna o número de hóspedes registrados na reserva.

        Returns:
            int: Quantidade de hóspedes.
        """
        return self._num_hospedes

    @num_hospedes.setter
    def num_hospedes(self, valor: int) -> None:
        """Define e valida a quantidade de hóspedes.

        Args:
            valor (int): Novo número de hóspedes.

        Raises:
            DadosInvalidosException: Se `valor < 1`.
            CapacidadeExcedidaException: Se `valor > quarto.capacidade`.
        """
        if not isinstance(valor, int) or valor < 1:
            raise DadosInvalidosException("O número de hóspedes deve ser de no mínimo 1.")
        if self._quarto is not None and valor > self._quarto.capacidade:
            raise CapacidadeExcedidaException(
                f"O número de hóspedes ({valor}) excede a capacidade do quarto ({self._quarto.capacidade})."
            )
        self._num_hospedes = valor

    @property
    def origem(self) -> OrigemReserva:
        """Retorna o canal de origem da reserva.

        Returns:
            OrigemReserva: Constante de OrigemReserva.
        """
        return self._origem

    @origem.setter
    def origem(self, valor: Any) -> None:
        """Define o canal de atendimento da reserva.

        Args:
            valor (Any): Membro de `OrigemReserva` ou string compatível.

        Raises:
            DadosInvalidosException: Se o valor for inválido.
        """
        if isinstance(valor, OrigemReserva):
            self._origem = valor
        elif isinstance(valor, str):
            try:
                self._origem = OrigemReserva(valor.upper())
            except ValueError:
                raise DadosInvalidosException(f"Origem de reserva inválida: '{valor}'.")
        else:
            raise DadosInvalidosException("Origem deve ser uma instância válida de OrigemReserva.")

    @property
    def status(self) -> StatusReserva:
        """Retorna o estado operacional atual no ciclo de vida da reserva.

        Returns:
            StatusReserva: Estado da reserva.
        """
        return self._status

    @property
    def valor_total_diarias(self) -> float:
        """Retorna o valor total cobrado pelas diárias.

        Returns:
            float: Valor financeiro das diárias.
        """
        return self._valor_total_diarias

    @valor_total_diarias.setter
    def valor_total_diarias(self, valor: float) -> None:
        """Define o valor total das diárias contratadas.

        Args:
            valor (float): Montante financeiro (deve ser >= 0).

        Raises:
            DadosInvalidosException: Se o valor for negativo.
        """
        try:
            val_float = float(valor)
        except (ValueError, TypeError):
            raise DadosInvalidosException("O valor das diárias deve ser um número real válido.")
        if val_float < 0.0:
            raise DadosInvalidosException("O valor das diárias não pode ser negativo.")
        self._valor_total_diarias = round(val_float, 2)

    @property
    def pagamentos(self) -> List[Pagamento]:
        """Retorna uma cópia da lista de pagamentos lançados.

        Returns:
            List[Pagamento]: Cópia da lista de pagamentos.
        """
        return list(self._pagamentos)

    @property
    def adicionais(self) -> List[Adicional]:
        """Retorna uma cópia da lista de itens adicionais consumidos.

        Returns:
            List[Adicional]: Cópia da lista de adicionais.
        """
        return list(self._adicionais)

# ----------------------------------------------------------------------- #
# Propriedades (Cálculos Financeiros e Temporais)               #
# ----------------------------------------------------------------------- #

    @property
    def total_diarias(self) -> int:
        """Retorna o número de diárias (noites) contratadas na reserva.

        Returns:
            int: Quantidade de noites entre data_entrada e data_saida.
        """
        return (self._data_saida - self._data_entrada).days

    @property
    def total_adicionais(self) -> float:
        """Calcula o valor monetário total de todos os itens adicionais lançados.

        Returns:
            float: Soma dos consumos extras.
        """
        return round(sum(a.total for a in self._adicionais), 2)

    @property
    def valor_total_devido(self) -> float:
        """Calcula a conta global da reserva (diárias + adicionais).

        Returns:
            float: Total devido pelo hóspede.
        """
        return round(self._valor_total_diarias + self.total_adicionais, 2)

    @property
    def total_pago(self) -> float:
        """Calcula a soma de todas as transações financeiras de pagamento registradas.

        Returns:
            float: Montante já quitado na reserva.
        """
        return round(sum(p.valor for p in self._pagamentos), 2)

    @property
    def saldo_devedor(self) -> float:
        """Calcula o saldo devedor restante (`valor_total_devido - total_pago`).

        Returns:
            float: Valor pendente de quitação (mínimo 0.0).
        """
        pendente = self.valor_total_devido - self.total_pago
        return round(max(0.0, pendente), 2)

# ----------------------------------------------------------------------- #
# Métodos de Comportamento e Máquina de Estados                            #
# ----------------------------------------------------------------------- #

    def adicionar_pagamento(self, pagamento: Pagamento) -> None:
        """Registra um novo pagamento na reserva e atualiza a auditoria.

        Args:
            pagamento (Pagamento): Transação de pagamento a ser incorporada.

        Raises:
            DadosInvalidosException: Se o objeto fornecido for inválido.
            TransicaoEstadoInvalidaException: Se a reserva estiver em estado cancelado ou no-show.
        """
        if pagamento is None:
            raise DadosInvalidosException("O pagamento a ser adicionado não pode ser nulo.")

        if self._status in (StatusReserva.CANCELADA, StatusReserva.NO_SHOW):
            raise TransicaoEstadoInvalidaException(
                f"Não é permitido lançar pagamentos em reserva com status '{self._status.value}'."
            )

        self._pagamentos.append(pagamento)
        self.registrar_alteracao()

    def adicionar_adicional(self, adicional: Adicional) -> None:
        """Lança um novo consumo adicional na conta da reserva.

        Conforme regras do negócio, despesas extras só são permitidas durante
        a hospedagem ativa (`CHECKIN`).

        Args:
            adicional (Adicional): Item de consumo extra ou serviço.

        Raises:
            DadosInvalidosException: Se o item for nulo.
            TransicaoEstadoInvalidaException: Se a reserva não estiver em CHECKIN.
        """
        if adicional is None:
            raise DadosInvalidosException("O item adicional não pode ser nulo.")

        if self._status != StatusReserva.CHECKIN:
            raise TransicaoEstadoInvalidaException(
                f"Lançamento de adicionais só é permitido quando a reserva estiver em CHECKIN. "
                f"Status atual: '{self._status.value}'."
            )

        self._adicionais.append(adicional)
        self.registrar_alteracao()

    def confirmar(self) -> None:
        """Transiciona o estado da reserva de `PENDENTE` para `CONFIRMADA`.

        Raises:
            TransicaoEstadoInvalidaException: Se a reserva não estiver em `PENDENTE`.
        """
        if self._status != StatusReserva.PENDENTE:
            raise TransicaoEstadoInvalidaException(
                f"Apenas reservas PENDENTES podem ser confirmadas. Status atual: '{self._status.value}'."
            )

        self._status = StatusReserva.CONFIRMADA
        self.registrar_alteracao()

    def realizar_checkin(self, horario: datetime, tolerancia_min: int = 0) -> None:
        """Efetua a entrada do hóspede, transicionando o status para `CHECKIN`.

        Valida se a reserva está `CONFIRMADA` e se o quarto está `DISPONIVEL`.
        Altera o quarto para `OCUPADO` e registra o horário efetivo de entrada.

        Args:
            horario (datetime): Instante exato do check-in.
            tolerancia_min (int, optional): Tolerância em minutos. Padrão é 0.

        Raises:
            TransicaoEstadoInvalidaException: Se a reserva não estiver CONFIRMADA.
            QuartoIndisponivelException: Se o quarto não estiver DISPONIVEL.
        """
        if self._status != StatusReserva.CONFIRMADA:
            raise TransicaoEstadoInvalidaException(
                f"Check-in permitido apenas para reservas CONFIRMADAS. Status atual: '{self._status.value}'."
            )

        if self._quarto is not None:
            if self._quarto.status != StatusQuarto.DISPONIVEL:
                raise QuartoIndisponivelException(
                    f"Não é possível realizar check-in: o quarto {self._quarto.numero} "
                    f"está com status '{self._quarto.status.value}'."
                )
            self._quarto.status = StatusQuarto.OCUPADO

        self._checkin_real = horario
        self._status = StatusReserva.CHECKIN
        self.registrar_alteracao()

    def realizar_checkout(
        self,
        horario: datetime,
        taxa_multa_atraso: float = 0.0,
    ) -> float:
        """Finaliza a estadia, garantindo quitação financeira e liberando o quarto.

        Conforme os requisitos essenciais, o check-out só é permitido se
        `total_pago >= total_devido`.

        Args:
            horario (datetime): Instante exato do check-out.
            taxa_multa_atraso (float, optional): Multa por atraso no horário. Padrão é 0.0.

        Returns:
            float: Valor total financeiro da conta encerrada.

        Raises:
            TransicaoEstadoInvalidaException: Se a reserva não estiver em CHECKIN.
            PagamentoInsuficienteException: Se houver saldo devedor pendente.
        """
        if self._status != StatusReserva.CHECKIN:
            raise TransicaoEstadoInvalidaException(
                f"Check-out permitido apenas para reservas em CHECKIN. Status atual: '{self._status.value}'."
            )

        if taxa_multa_atraso > 0.0:
            item_multa = Adicional(
                id_=len(self._adicionais) + 1,
                descricao="Multa por atraso de check-out",
                preco_unitario=taxa_multa_atraso,
                quantidade=1,
            )
            self._adicionais.append(item_multa)

        if self.saldo_devedor > 0.0:
            raise PagamentoInsuficienteException(
                f"Não é possível concluir o check-out: há um saldo devedor de R$ {self.saldo_devedor:.2f} pendente. "
                f"(Total devido: R$ {self.valor_total_devido:.2f}, Total pago: R$ {self.total_pago:.2f})."
            )

        self._checkout_real = horario
        self._status = StatusReserva.CHECKOUT

        if self._quarto is not None:
            self._quarto.status = StatusQuarto.DISPONIVEL

        self.registrar_alteracao()
        return self.valor_total_devido

    def cancelar(self, taxa_multa: float = 0.0) -> float:
        """Cancela a reserva antes da entrada do hóspede, aplicando multa se cabível.

        Args:
            taxa_multa (float, optional): Valor da multa calculada conforme as
                políticas de cancelamento. Padrão é 0.0.

        Returns:
            float: Valor final da multa aplicada.

        Raises:
            TransicaoEstadoInvalidaException: Se a reserva não estiver em PENDENTE ou CONFIRMADA.
        """
        if self._status not in (StatusReserva.PENDENTE, StatusReserva.CONFIRMADA):
            raise TransicaoEstadoInvalidaException(
                f"Cancelamento permitido apenas para reservas PENDENTES ou CONFIRMADAS. "
                f"Status atual: '{self._status.value}'."
            )

        self._status = StatusReserva.CANCELADA
        if self._quarto is not None and self._quarto.status == StatusQuarto.OCUPADO:
            self._quarto.status = StatusQuarto.DISPONIVEL

        self.registrar_alteracao()
        return round(float(taxa_multa), 2)

    def marcar_noshow(self) -> None:
        """Registra o não comparecimento do hóspede (`NO_SHOW`) e libera o quarto.

        Raises:
            TransicaoEstadoInvalidaException: Se o estado atual não for CONFIRMADA.
        """
        if self._status != StatusReserva.CONFIRMADA:
            raise TransicaoEstadoInvalidaException(
                f"Marcação de NO_SHOW permitida apenas para reservas CONFIRMADAS. "
                f"Status atual: '{self._status.value}'."
            )

        self._status = StatusReserva.NO_SHOW
        if self._quarto is not None:
            self._quarto.status = StatusQuarto.DISPONIVEL

        self.registrar_alteracao()

# ----------------------------------------------------------------------- #
# Métodos Especiais                                   #
# ----------------------------------------------------------------------- #

    def __len__(self) -> int:
        """Retorna a quantidade exata de diárias contratadas na reserva.

        Returns:
            int: Quantidade de noites (`(data_saida - data_entrada).days`).
        """
        return self.total_diarias

    def __eq__(self, outra: object) -> bool:
        """Compara duas reservas para verificar igualdade estrita de alocação.

        Duas reservas são consideradas iguais se alocarem o mesmo quarto e
        possuírem exatamente o mesmo intervalo de datas de entrada e saída.

        Args:
            outra (object): Objeto a ser comparado.

        Returns:
            bool: True se houver coincidência de quarto e período; False caso contrário.
        """
        if not isinstance(outra, Reserva):
            return False

        quarto_igual = (
            (self._quarto is None and outra._quarto is None)
            or (
                self._quarto is not None
                and outra._quarto is not None
                and self._quarto.numero == outra._quarto.numero
            )
        )
        return (
            quarto_igual
            and self._data_entrada == outra._data_entrada
            and self._data_saida == outra._data_saida
        )

    def __str__(self) -> str:
        """Retorna uma representação amigável da reserva.

        Returns:
            str: Resumo com ID, hóspede, quarto, período, noites e status.
        """
        nome_hospede = self._hospede.nome if self._hospede else "Sem hóspede"
        num_quarto = self._quarto.numero if self._quarto else "Sem quarto"
        entrada_fmt = self._data_entrada.strftime("%d/%m/%Y")
        saida_fmt = self._data_saida.strftime("%d/%m/%Y")
        return (
            f"Reserva #{self._id} [{self._status.value}]: Hóspede '{nome_hospede}', "
            f"Quarto {num_quarto} ({entrada_fmt} até {saida_fmt}, {len(self)} diárias) - "
            f"Total: R$ {self.valor_total_devido:.2f}"
        )

    def __repr__(self) -> str:
        """Retorna a representação técnica do objeto Reserva.

        Returns:
            str: Representação técnica para depuração.
        """
        id_hospede = self._hospede.id if self._hospede else None
        num_quarto = self._quarto.numero if self._quarto else None
        return (
            f"Reserva(id={self._id!r}, hospede_id={id_hospede!r}, quarto_num={num_quarto!r}, "
            f"entrada={self._data_entrada.isoformat()!r}, saida={self._data_saida.isoformat()!r}, "
            f"num_hospedes={self._num_hospedes!r}, status={self._status.value!r})"
        )

    @classmethod
    def from_dict(cls, dados: Dict[str, Any]) -> Reserva:
        """Reconstrói uma instância de Reserva a partir de um dicionário.

        Args:
            dados (Dict[str, Any]): Dicionário com os atributos da reserva.

        Returns:
            Reserva: Instância reconstruída.

        Raises:
            DadosInvalidosException: Se os dados forem inválidos.
        """
        if not isinstance(dados, dict):
            raise DadosInvalidosException("Os dados de entrada para Reserva devem ser um dicionário.")

        data_entrada = (
            date.fromisoformat(dados["data_entrada"])
            if "data_entrada" in dados and dados["data_entrada"]
            else date.today()
        )
        data_saida = (
            date.fromisoformat(dados["data_saida"])
            if "data_saida" in dados and dados["data_saida"]
            else (data_entrada + timedelta(days=1))
        )

        origem_raw = dados.get("origem", OrigemReserva.SITE.value)
        origem = OrigemReserva(origem_raw) if isinstance(origem_raw, str) else origem_raw

        status_raw = dados.get("status", StatusReserva.PENDENTE.value)
        status = StatusReserva(status_raw) if isinstance(status_raw, str) else status_raw

        hospede_obj: Optional[Hospede] = None
        if "hospede" in dados and isinstance(dados["hospede"], dict):
            hospede_obj = Hospede.from_dict(dados["hospede"])

        quarto_obj: Optional[Quarto] = None
        if "quarto" in dados and isinstance(dados["quarto"], dict):
            quarto_obj = Quarto.from_dict(dados["quarto"])

        instancia = cls(
            id_=int(dados.get("id", 0)),
            hospede=hospede_obj,
            quarto=quarto_obj,
            data_entrada=data_entrada,
            data_saida=data_saida,
            num_hospedes=int(dados.get("num_hospedes", 1)),
            origem=origem,
            valor_total_diarias=float(dados.get("valor_total_diarias", 0.0)),
            status=status,
        )

        if "checkin_real" in dados and dados["checkin_real"]:
            instancia._checkin_real = datetime.fromisoformat(str(dados["checkin_real"]))
        if "checkout_real" in dados and dados["checkout_real"]:
            instancia._checkout_real = datetime.fromisoformat(str(dados["checkout_real"]))

        if "pagamentos" in dados and isinstance(dados["pagamentos"], list):
            for p_dict in dados["pagamentos"]:
                if isinstance(p_dict, dict):
                    instancia._pagamentos.append(Pagamento.from_dict(p_dict))

        if "adicionais" in dados and isinstance(dados["adicionais"], list):
            for a_dict in dados["adicionais"]:
                if isinstance(a_dict, dict):
                    instancia._adicionais.append(Adicional.from_dict(a_dict))

        return instancia