"""Módulo de exceções customizadas de domínio do Sistema de Reservas de Hotel.

Este módulo define a hierarquia de erros específicos de regras de negócio,
permitindo que a camada de domínio (``models``) e a camada de serviços
(``services``) sinalizem violações de invariantes de forma semântica e
padronizada.

"""


class HotelException(Exception):
    """Classe base para todas as exceções de domínio do sistema hoteleiro.

    Attributes:
        mensagem (str): Descrição detalhada e amigável do erro ocorrido.

    Example::

        try:
            hotel.criar_reserva(...)
        except HotelException as e:
            print(e.mensagem)
    """

    def __init__(self, mensagem: str = "Ocorreu um erro no sistema hoteleiro.") -> None:
        """Inicializa a exceção base com uma mensagem descritiva do erro.

        Args:
            mensagem (str): Explicação clara do motivo pelo qual a regra de
                negócio foi violada. Valor padrão genérico para uso emergencial
                sem mensagem personalizada.
        """
        self.mensagem: str = mensagem
        super().__init__(self.mensagem)

    def __str__(self) -> str:
        """Retorna a representação em string da exceção.

        Returns:
            str: Mensagem descritiva do erro formatada para exibição.
        """
        return f"[{self.__class__.__name__}] {self.mensagem}"

    def __repr__(self) -> str:
        """Retorna a representação técnica da exceção para depuração.

        Returns:
            str: String no formato ``ClassName(mensagem='...')``.
        """
        return f"{self.__class__.__name__}(mensagem={self.mensagem!r})"

# =========================================================================== #
# Subclasses Especializadas                                                   #
# =========================================================================== #

class QuartoIndisponivelException(HotelException):
    """Exceção lançada quando um quarto não pode ser alocado no período solicitado.

   Cobre dois cenários distintos:

    1. **Overbooking**: o quarto já possui uma reserva ativa com datas
       conflitantes com o período solicitado.
    2. **Estado inválido**: o quarto está nos estados ``OCUPADO``,
       ``MANUTENCAO`` ou ``BLOQUEADO`` no momento da operação.

    Attributes:
        mensagem (str): Herdado de :class:`HotelException`. Deve incluir o
            número do quarto e, se aplicável, o período de conflito.

    Example::

        raise QuartoIndisponivelException(
            "Quarto 101 está OCUPADO de 10/10/2025 a 15/10/2025."
        )
    """
   
    def __init__(
        self,
        mensagem: str = "O quarto solicitado não está disponível para o período informado.",
    ) -> None:
        """Inicializa a exceção de quarto indisponível.

        Args:
            mensagem (str): Descrição do motivo da indisponibilidade, incluindo
                idealmente o número do quarto e o período de conflito.
        """
        super().__init__(mensagem)


class CapacidadeExcedidaException(HotelException):
    """Exceção lançada quando o número de hóspedes ultrapassa o limite do quarto.

    Disparada durante a criação ou alteração de uma ``Reserva`` quando o
    atributo ``num_hospedes`` é estritamente superior à ``capacidade`` máxima
    suportada pelo objeto ``Quarto`` selecionado.

    Attributes:
        mensagem (str): Herdado de :class:`HotelException`. Deve informar a
            capacidade máxima do quarto e o número de hóspedes solicitado.

    Example::

        raise CapacidadeExcedidaException(
            "Quarto 205 suporta no máximo 2 hóspedes; solicitado: 4."
        )
    """

    def __init__(
        self,
        mensagem: str = "O número de hóspedes excede a capacidade máxima do quarto.",
    ) -> None:
        """Inicializa a exceção de capacidade excedida.

        Args:
            mensagem (str): Descrição detalhada indicando a capacidade máxima
                do quarto e o valor solicitado que a ultrapassou.
        """
        super().__init__(mensagem)


class TransicaoEstadoInvalidaException(HotelException):
    """Exceção lançada ao tentar realizar uma mudança de estado não permitida.

    Garante o cumprimento rigoroso das máquinas de estados de ``Reserva`` e
    ``Quarto``. Exemplos de transições inválidas:

    - Realizar check-in em uma reserva ``CANCELADA`` ou ``PENDENTE``.
    - Realizar check-out sem que o check-in tenha sido efetuado.
    - Liberar da manutenção um quarto que não está em ``MANUTENCAO``.

    Attributes:
        mensagem (str): Herdado de :class:`HotelException`. Deve especificar
            o estado atual e o estado-alvo rejeitado.

    Example::

        raise TransicaoEstadoInvalidaException(
            "Não é possível fazer check-in: reserva está CANCELADA."
        )
    """

    def __init__(
        self,
        mensagem: str = "A transição de estado solicitada não é permitida.",
    ) -> None:
        """Inicializa a exceção de transição de estado inválida.

        Args:
            mensagem (str): Descrição da transição rejeitada, indicando
                o estado atual da entidade e o estado-alvo solicitado.
        """
        super().__init__(mensagem)

class PagamentoInsuficienteException(HotelException):
    """Exceção lançada quando há pendências financeiras no momento do check-out.

    Utilizada principalmente no fluxo de check-out de ``Reserva`` quando o
    valor acumulado em ``total_pago`` é inferior ao ``valor_total_devido``
    (soma das diárias, tarifas de temporada, consumos adicionais e multas).

    Attributes:
        mensagem (str): Herdado de :class:`HotelException`. Deve indicar o
            saldo devedor restante para orientar o operador.

    Example::

        raise PagamentoInsuficienteException(
            "Saldo devedor de R$ 350,00 impede a conclusão do check-out."
        )
    """

    def __init__(
        self,
        mensagem: str = "O valor pago é insuficiente para concluir a operação.",
    ) -> None:
        """Inicializa a exceção de pagamento insuficiente.

        Args:
            mensagem (str): Descrição da pendência financeira, incluindo
                idealmente o valor em aberto (saldo devedor).
        """
        super().__init__(mensagem)


class DadosInvalidosException(HotelException):
    """Exceção lançada quando atributos ou parâmetros violam validações básicas.

    Disparada pelos setters com ``@property`` ou por métodos de desserialização
    (``from_dict``) ao receberem valores inconsistentes. Exemplos de violações:

    - Tarifa base negativa ou igual a zero.
    - Capacidade do quarto menor que 1.
    - Documento ou nome de hóspede vazio.
    - ``data_saida`` anterior ou igual à ``data_entrada``.
    - Dicionário sem chaves obrigatórias em ``from_dict``.

    Attributes:
        mensagem (str): Herdado de :class:`HotelException`. Deve identificar
            o campo problemático e o valor rejeitado.

    Example::

        raise DadosInvalidosException(
            "tarifa_base deve ser um valor positivo; recebido: -50.0."
        )
    """

    def __init__(
        self,
        mensagem: str = "Os dados fornecidos são inválidos ou inconsistentes.",
    ) -> None:
        """Inicializa a exceção de dados inválidos.

        Args:
            mensagem (str): Descrição da violação de validação, identificando
                o campo problemático e o valor que foi rejeitado.
        """
        super().__init__(mensagem)