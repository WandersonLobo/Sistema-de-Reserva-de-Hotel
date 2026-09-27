"""Módulo de exceções customizadas de domínio do Sistema de Reservas de Hotel."""


class HotelException(Exception):
    """Classe base para todas as exceções de domínio do sistema hoteleiro.

    Attributes:
        mensagem (str): Descrição detalhada e amigável do erro ocorrido.
    """

    pass


class QuartoIndisponivelException(HotelException):
    """Exceção lançada quando um quarto não pode ser alocado no período solicitado.

    Utilizada para impedir situações de overbooking ou tentativas de reserva e
    check-in em quartos nos estados `OCUPADO`, `MANUTENCAO` ou `BLOQUEADO`.
    """

    pass


class CapacidadeExcedidaException(HotelException):
    """Exceção lançada quando o número de hóspedes ultrapassa o limite do quarto."""

    pass


class TransicaoEstadoInvalidaException(HotelException):
    """Exceção lançada ao tentar realizar uma mudança de estado não permitida."""

    pass


class PagamentoInsuficienteException(HotelException):
    """Exceção lançada quando há pendências financeiras no momento do check-out."""

    pass


class DadosInvalidosException(HotelException):
    """Exceção lançada quando atributos ou parâmetros violam validações básicas."""

    pass