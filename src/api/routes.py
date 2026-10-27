"""Rotas da API — traduz requisições HTTP em chamadas ao serviço Hotel."""

from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.models.enums import MetodoPagamento, OrigemReserva, TipoQuarto
from src.models.exceptions import (
    CapacidadeExcedidaException,
    DadosInvalidosException,
    PagamentoInsuficienteException,
    QuartoIndisponivelException,
    TransicaoEstadoInvalidaException,
)
from src.models.person import Hospede
from src.models.room import QuartoDuplo, QuartoLuxo, QuartoSimples
from src.services.hotel import Hotel
from src.services.reports import ServicoRelatorios
from src.database import data

router = APIRouter()
_hotel = Hotel()


# =========================================================================
# Schemas de Entrada (Pydantic)
# =========================================================================

class HospedeIn(BaseModel):
    """Dados necessários para cadastrar um novo hóspede."""
    nome: str
    documento: str
    email: str
    telefone: str
    preferencias: str = ""


class QuartoIn(BaseModel):
    """Dados necessários para cadastrar um novo quarto."""
    numero: int
    tipo: TipoQuarto
    capacidade: int
    tarifa_base: float
    tem_varanda: bool = False
    tem_hidromassagem: bool = False
    taxa_servico_adicional: float = 0.0


class BloqueioIn(BaseModel):
    """Dados necessários para bloquear um quarto para manutenção."""
    motivo: str
    inicio: date
    fim: date


class ReservaIn(BaseModel):
    """Dados necessários para criar uma nova reserva."""
    hospede_id: int
    quarto_num: int
    entrada: date
    saida: date
    num_hospedes: int
    origem: OrigemReserva = OrigemReserva.BALCAO


class CheckinIn(BaseModel):
    """Momento em que o check-in está sendo realizado."""
    momento: datetime


class CheckoutIn(BaseModel):
    """Momento em que o check-out está sendo realizado."""
    momento: datetime


class CancelamentoIn(BaseModel):
    """Momento opcional do cancelamento (usa datetime.now() se omitido)."""
    momento: Optional[datetime] = None


class NoShowIn(BaseModel):
    """Momento atual para varredura de reservas em no-show."""
    momento_atual: datetime


class PagamentoIn(BaseModel):
    """Dados necessários para registrar um pagamento na reserva."""
    valor: float
    metodo: MetodoPagamento


class AdicionalIn(BaseModel):
    """Dados necessários para lançar um consumo extra na reserva."""
    descricao: str
    preco: float
    quantidade: int = 1


# =========================================================================
# Utilitário de Tratamento de Exceções de Domínio
# =========================================================================

def _tratar_excecao(exc: Exception) -> None:
    """Converte exceções de domínio em respostas HTTP semanticamente corretas."""
    if isinstance(exc, (
        QuartoIndisponivelException,
        CapacidadeExcedidaException,
        TransicaoEstadoInvalidaException,
        DadosInvalidosException,
    )):
        raise HTTPException(status_code=400, detail=str(exc))
    if isinstance(exc, PagamentoInsuficienteException):
        raise HTTPException(status_code=402, detail=str(exc))
    raise HTTPException(status_code=500, detail=str(exc))


# =========================================================================
# Quartos
# =========================================================================

@router.post("/quartos", status_code=201, tags=["Quartos"])
def cadastrar_quarto(payload: QuartoIn) -> dict:
    """Cadastra um novo quarto no hotel e persiste no banco."""
    pass


@router.get("/quartos/disponiveis", tags=["Quartos"])
def buscar_quartos_disponiveis(
    entrada: date,
    saida: date,
    tipo: Optional[TipoQuarto] = None,
) -> list[dict]:
    """Retorna quartos disponíveis no período, com filtro opcional por tipo."""
    pass


@router.patch("/quartos/{numero}/bloquear", tags=["Quartos"])
def bloquear_quarto(numero: int, payload: BloqueioIn) -> dict:
    """Interdita um quarto para manutenção em um período com motivo definido."""
    pass


@router.patch("/quartos/{numero}/desbloquear", tags=["Quartos"])
def desbloquear_quarto(numero: int) -> dict:
    """Libera um quarto da manutenção, tornando-o disponível novamente."""
    pass


# =========================================================================
# Hóspedes
# =========================================================================

@router.post("/hospedes", status_code=201, tags=["Hóspedes"])
def cadastrar_hospede(payload: HospedeIn) -> dict:
    """Cadastra um novo hóspede e retorna o ID gerado pelo banco."""
    pass


# =========================================================================
# Ciclo de Vida da Reserva
# =========================================================================

@router.post("/reservas", status_code=201, tags=["Reservas"])
def criar_reserva(payload: ReservaIn) -> dict:
    """Cria reserva validando overbooking, capacidade e calcula tarifas dinâmicas."""
    pass


@router.post("/reservas/{reserva_id}/checkin", tags=["Reservas"])
def processar_checkin(reserva_id: int, payload: CheckinIn) -> dict:
    """Realiza o check-in validando tolerância de horário e status da reserva."""
    pass


@router.post("/reservas/{reserva_id}/checkout", tags=["Reservas"])
def processar_checkout(reserva_id: int, payload: CheckoutIn) -> dict:
    """Realiza o check-out calculando atrasos e exigindo quitação financeira."""
    pass


@router.post("/reservas/{reserva_id}/cancelar", tags=["Reservas"])
def processar_cancelamento(reserva_id: int, payload: CancelamentoIn) -> dict:
    """Cancela a reserva aplicando multa de 50% se feito com menos de 48h de antecedência."""
    pass


@router.post("/reservas/noshows", tags=["Reservas"])
def processar_noshows(payload: NoShowIn) -> dict:
    """Varre reservas confirmadas com tolerância expirada e as marca como NO_SHOW."""
    pass


# =========================================================================
# Pagamentos e Consumo Extra
# =========================================================================

@router.post("/reservas/{reserva_id}/pagamentos", status_code=201, tags=["Financeiro"])
def registrar_pagamento(reserva_id: int, payload: PagamentoIn) -> dict:
    """Registra um pagamento (PIX, Cartão, Dinheiro) na conta da reserva."""
    pass


@router.post("/reservas/{reserva_id}/adicionais", status_code=201, tags=["Financeiro"])
def lancar_adicional(reserva_id: int, payload: AdicionalIn) -> dict:
    """Lança um consumo extra (frigobar, refeição) durante a estadia ativa."""
    pass


# =========================================================================
# Relatórios
# =========================================================================

@router.get("/relatorios/ocupacao", tags=["Relatórios"])
def relatorio_ocupacao(inicio: date, fim: date) -> dict:
    """Retorna a taxa de ocupação percentual do hotel no período informado."""
    pass


@router.get("/relatorios/financeiro", tags=["Relatórios"])
def relatorio_financeiro(inicio: date, fim: date) -> dict:
    """Retorna a receita total gerada pelas reservas finalizadas no período."""
    pass
