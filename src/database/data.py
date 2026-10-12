
"""Operações de persistência do sistema."""

from datetime import date
from typing import Optional

from .connection import obter_conexao
from src.models.person import Hospede
from src.models.reservation import Reserva
from src.models.room import Quarto

# Função auxiliar para transformar uma linha do banco em um objeto Quarto
def _quarto_da_linha(linha) -> Quarto:
    return Quarto.from_dict(dict(linha)) # O from_dict é um método da classe Quarto que cria um objeto a partir de um dicionário


def listar_quartos() -> list[Quarto]:
    """Retorna todos os quartos cadastrados."""
    conexao = obter_conexao()
    try: 
        linhas = conexao.execute(
            "SELECT * FROM quartos ORDER BY numero"
        ).fetchall()
        return [_quarto_da_linha(linha) for linha in linhas] # Chama a função auxiliar (_quarto_da_linha) e transforma cada linha em um objeto Quarto
    finally:
        conexao.close()


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