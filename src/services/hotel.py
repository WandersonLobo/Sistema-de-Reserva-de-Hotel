
from typing import Any, Dict, List

from src.models.person import Hospede
from src.models.reservation import Reserva
from src.models.room import Quarto


class Hotel:
    """Orquestrador central da camada de serviços do sistema hoteleiro.

    Coordena o cadastro de quartos e hóspedes, a busca de disponibilidade, a
    criação de reservas sem conflitos (prevenção de overbooking) e os fluxos
    de check-in, check-out, cancelamento, no-show e geração de relatórios.
    """

    pass