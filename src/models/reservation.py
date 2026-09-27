"""Módulo que define a entidade central de Reserva do sistema hoteleiro."""

from src.models.mixins import Auditoria, Serializavel

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

    pass