
class HotelException(Exception):
    """Classe base para todas as exceções de domínio.
    """

    def __init__(self, mensagem: str = "Ocorreu um erro no sistema hoteleiro.") -> None:
        """Inicializa a exceção base com uma mensagem descritiva do erro."""

        self.mensagem: str = mensagem
        super().__init__(self.mensagem)

    def __str__(self) -> str:
        return f"[{self.__class__.__name__}] {self.mensagem}"

    def __repr__(self) -> str:
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
    """
   
    def __init__(
        self,
        mensagem: str = "O quarto solicitado não está disponível para o período informado.",
    ) -> None:
        
        super().__init__(mensagem)


class CapacidadeExcedidaException(HotelException):
    """Exceção lançada quando o número de hóspedes ultrapassa o limite do quarto.

    Disparada durante a criação ou alteração de uma ``Reserva`` quando o
    atributo ``num_hospedes`` é estritamente superior à ``capacidade`` máxima
    suportada pelo objeto ``Quarto`` selecionado.
    """

    def __init__(
        self,
        mensagem: str = "O número de hóspedes excede a capacidade máxima do quarto.",
    ) -> None:
        
        super().__init__(mensagem)


class TransicaoEstadoInvalidaException(HotelException):
    """Exceção lançada ao tentar realizar uma mudança de estado não permitida.

    Garante o cumprimento rigoroso das máquinas de estados de ``Reserva`` e
    ``Quarto``.
    """

    def __init__(
        self,
        mensagem: str = "A transição de estado solicitada não é permitida.",
    ) -> None:
        
        super().__init__(mensagem)

class PagamentoInsuficienteException(HotelException):
    """Exceção lançada quando há pendências financeiras no momento do check-out. """

    def __init__(
        self,
        mensagem: str = "O valor pago é insuficiente para concluir a operação.",
    ) -> None:
       
        super().__init__(mensagem)


class DadosInvalidosException(HotelException):
    """Exceção lançada quando atributos ou parâmetros violam validações básicas."""

    def __init__(
        self,
        mensagem: str = "Os dados fornecidos são inválidos ou inconsistentes.",
    ) -> None:
        
        super().__init__(mensagem)