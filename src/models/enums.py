
from enum import Enum


class TipoQuarto(str, Enum):
    """Categorias de acomodação disponíveis no hotel.

    Utilizada para diferenciar polimorficamente as subclasses de `Quarto`
    e identificar o tipo de acomodação na coluna `tipo` da tabela relacional
    no banco de dados SQLite.
    """

    SIMPLES = "SIMPLES"
    DUPLO = "DUPLO"
    LUXO = "LUXO"


class StatusQuarto(str, Enum):
    """Estados operacionais e de disponibilidade física de um quarto.

    Controla se um quarto pode receber novas alocações ou check-in num
    determinado momento.
    """

    DISPONIVEL = "DISPONIVEL"
    OCUPADO = "OCUPADO"
    MANUTENCAO = "MANUTENCAO"
    BLOQUEADO = "BLOQUEADO"


class StatusReserva(str, Enum):
    """Estados válidos do ciclo de vida de uma reserva no hotel.

    Governa a máquina de estados da classe `Reserva`, impedindo transições
    ilegais (como realizar check-out sem check-in prévio).
    """

    PENDENTE = "PENDENTE"
    CONFIRMADA = "CONFIRMADA"
    CHECKIN = "CHECKIN"
    CHECKOUT = "CHECKOUT"
    CANCELADA = "CANCELADA"
    NO_SHOW = "NO_SHOW"


class OrigemReserva(str, Enum):
    """Canais de atendimento pelos quais uma reserva pode ser originada"""

    SITE = "SITE"
    TELEFONE = "TELEFONE"
    BALCAO = "BALCAO"


class MetodoPagamento(str, Enum):
    """Modalidades financeiras aceites para quitação de reservas e consumos."""

    DINHEIRO = "DINHEIRO"
    CREDITO = "CREDITO"
    DEBITO = "DEBITO"
    PIX = "PIX"