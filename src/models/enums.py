"""Módulo de enumerações e constantes de estado do Sistema de Reservas de Hotel.

Este módulo define os tipos enumerados (Enums) que restringem os valores
válidos para categorias de quartos, estados operacionais de acomodações,
ciclo de vida das reservas, canais de origem e modalidades de pagamento.
"""

from enum import Enum


class TipoQuarto(str, Enum):
    """Categorias de acomodação disponíveis no hotel.

    Utilizada para diferenciar polimorficamente as subclasses de `Quarto`
    e identificar o tipo de acomodação na coluna `tipo` da tabela relacional
    no banco de dados SQLite.

    Attributes:
        SIMPLES (str): Acomodação padrão individual ou económica.
        DUPLO (str): Acomodação com capacidade ampliada e opção de varanda.
        LUXO (str): Acomodação de alto padrão com serviços adicionais.
    """

    SIMPLES = "SIMPLES"
    DUPLO = "DUPLO"
    LUXO = "LUXO"


class StatusQuarto(str, Enum):
    """Estados operacionais e de disponibilidade física de um quarto.

    Controla se um quarto pode receber novas alocações ou check-in num
    determinado momento.

    Attributes:
        DISPONIVEL (str): Quarto livre e apto para reservas e check-in.
        OCUPADO (str): Quarto atualmente com hóspede em estadia ativa (check-in).
        MANUTENCAO (str): Quarto temporariamente interditado para reparos.
        BLOQUEADO (str): Quarto bloqueado administrativamente pela gerência.
    """

    DISPONIVEL = "DISPONIVEL"
    OCUPADO = "OCUPADO"
    MANUTENCAO = "MANUTENCAO"
    BLOQUEADO = "BLOQUEADO"


class StatusReserva(str, Enum):
    """Estados válidos do ciclo de vida de uma reserva no hotel.

    Governa a máquina de estados da classe `Reserva`, impedindo transições
    ilegais (como realizar check-out sem check-in prévio).

    Attributes:
        PENDENTE (str): Reserva criada, aguardando confirmação ou sinal.
        CONFIRMADA (str): Reserva garantida e pronta para o check-in na data.
        CHECKIN (str): Hóspede presente no hotel; estadia em andamento.
        CHECKOUT (str): Estadia encerrada e conta totalmente quitada.
        CANCELADA (str): Reserva cancelada antes do início da hospedagem.
        NO_SHOW (str): Hóspede não compareceu dentro do prazo de tolerância.
    """

    PENDENTE = "PENDENTE"
    CONFIRMADA = "CONFIRMADA"
    CHECKIN = "CHECKIN"
    CHECKOUT = "CHECKOUT"
    CANCELADA = "CANCELADA"
    NO_SHOW = "NO_SHOW"


class OrigemReserva(str, Enum):
    """Canais de atendimento pelos quais uma reserva pode ser originada.

    Attributes:
        SITE (str): Reserva efetuada online através do portal ou aplicação.
        TELEFONE (str): Reserva solicitada remotamente via central telefónica.
        BALCAO (str): Reserva presencial realizada diretamente na receção (walk-in).
    """

    SITE = "SITE"
    TELEFONE = "TELEFONE"
    BALCAO = "BALCAO"


class MetodoPagamento(str, Enum):
    """Modalidades financeiras aceites para quitação de reservas e consumos.

    Attributes:
        DINHEIRO (str): Pagamento em espécie na receção.
        CREDITO (str): Pagamento via cartão de crédito.
        DEBITO (str): Pagamento via cartão de débito.
        PIX (str): Transferência instantânea via PIX.
    """

    DINHEIRO = "DINHEIRO"
    CREDITO = "CREDITO"
    DEBITO = "DEBITO"
    PIX = "PIX"