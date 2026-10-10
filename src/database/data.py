
"""Operações de persistência do sistema."""

from datetime import date
from typing import Optional

from .connection import obter_conexao
from src.models.person import Hospede
from src.models.reservation import Reserva
from src.models.room import Quarto

def listar_quartos() -> list[Quarto]:
    """Retorna todos os quartos cadastrados."""
    ...


def buscar_quarto(numero: int) -> Optional[Quarto]:
    """Busca um quarto pelo número."""
    ...


def salvar_hospede(hospede: Hospede) -> int:
    """Insere um hóspede e retorna seu ID."""
    ...


def buscar_hospede(id_: int) -> Optional[Hospede]:
    """Busca um hóspede pelo ID."""
    ...


def listar_temporadas(data_referencia: date) -> list[dict]:
    """Retorna temporadas que abrangem uma data."""
    ...


def salvar_reserva(reserva: Reserva) -> int:
    """Insere uma reserva e retorna seu ID."""
    ...


def buscar_reserva(id_: int) -> Optional[Reserva]:
    """Busca uma reserva pelo ID."""
    ...