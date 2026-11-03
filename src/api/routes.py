"""Rotas da API — traduz requisições HTTP em chamadas ao serviço Hotel."""

from datetime import date, datetime
import logging
from sqlite3 import IntegrityError
from typing import NoReturn, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.models.enums import MetodoPagamento, OrigemReserva, StatusReserva, TipoQuarto
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
logger = logging.getLogger(__name__)


# =========================================================================
# Schemas de Entrada (Pydantic)
# =========================================================================

class HospedeIn(BaseModel):
    """Dados necessários para cadastrar um novo hóspede."""
    nome: str = Field(min_length=1)
    documento: str = Field(min_length=1)
    email: str = Field(min_length=1)
    telefone: str = Field(min_length=1)
    preferencias: str = ""


class QuartoIn(BaseModel):
    """Dados necessários para cadastrar um novo quarto."""
    numero: int = Field(gt=0)
    tipo: TipoQuarto
    capacidade: int = Field(ge=1)
    tarifa_base: float = Field(gt=0, allow_inf_nan=False)
    tem_varanda: bool = False
    tem_hidromassagem: bool = False
    taxa_servico_adicional: float = Field(default=0.0, ge=0, allow_inf_nan=False)


class BloqueioIn(BaseModel):
    """Dados necessários para bloquear um quarto para manutenção."""
    motivo: str
    inicio: date
    fim: date


class ReservaIn(BaseModel):
    """Dados necessários para criar uma nova reserva."""
    hospede_id: int = Field(gt=0)
    quarto_num: int = Field(gt=0)
    entrada: date
    saida: date
    num_hospedes: int = Field(ge=1)
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
    valor: float = Field(gt=0, allow_inf_nan=False)
    metodo: MetodoPagamento


class AdicionalIn(BaseModel):
    """Dados necessários para lançar um consumo extra na reserva."""
    descricao: str = Field(min_length=1)
    preco: float = Field(gt=0, allow_inf_nan=False)
    quantidade: int = Field(default=1, ge=1)


# =========================================================================
# Utilitário de Tratamento de Exceções de Domínio
# =========================================================================

def _tratar_excecao(exc: Exception) -> NoReturn:
    """Converte exceções de domínio em respostas HTTP semanticamente corretas."""
    # Preserva erros HTTP já definidos pela rota, como 404 e 409.
    if isinstance(exc, HTTPException):
        raise exc
    if isinstance(exc, (
        QuartoIndisponivelException,
        CapacidadeExcedidaException,
        TransicaoEstadoInvalidaException,
        DadosInvalidosException,
    )):
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if isinstance(exc, PagamentoInsuficienteException):
        raise HTTPException(status_code=402, detail=str(exc)) from exc
    if isinstance(exc, IntegrityError):
        raise HTTPException(
            status_code=409,
            detail="A operação conflita com os dados já cadastrados.",
        ) from exc

    # Detalhes técnicos ficam no servidor, sem expor informações do banco ao cliente.
    logger.error("Erro inesperado na API.", exc_info=(type(exc), exc, exc.__traceback__))
    raise HTTPException(status_code=500, detail="Erro interno do servidor.") from exc


# =========================================================================
# Quartos
# =========================================================================

@router.post("/quartos", status_code=201, tags=["Quartos"])
def cadastrar_quarto(payload: QuartoIn) -> dict:
    """Cadastra um novo quarto no hotel e persiste no banco."""
    try:
        # O salvamento também atualiza quartos; o cadastro não deve sobrescrever um existente.
        if data.buscar_quarto(payload.numero) is not None:
            raise HTTPException(status_code=409, detail="Quarto já cadastrado.")

        dados = {
            "numero": payload.numero,
            "capacidade": payload.capacidade,
            "tarifa_base": payload.tarifa_base,
        }
        # Cada categoria recebe apenas os atributos aceitos pelo seu construtor.
        if payload.tipo == TipoQuarto.SIMPLES:
            quarto = QuartoSimples(**dados)
        elif payload.tipo == TipoQuarto.DUPLO:
            quarto = QuartoDuplo(**dados, tem_varanda=payload.tem_varanda)
        else:
            quarto = QuartoLuxo(
                **dados,
                tem_hidromassagem=payload.tem_hidromassagem,
                taxa_servico_adicional=payload.taxa_servico_adicional,
            )

        _hotel.cadastrar_quarto(quarto)
        return quarto.to_dict()
    except Exception as exc:
        _tratar_excecao(exc)


@router.get("/quartos/disponiveis", tags=["Quartos"])
def buscar_quartos_disponiveis(
    entrada: date,
    saida: date,
    tipo: Optional[TipoQuarto] = None,
) -> list[dict]:
    """Retorna quartos disponíveis no período, com filtro opcional por tipo."""
    try:
        quartos = _hotel.buscar_quartos_disponiveis(entrada, saida, tipo)
        return [quarto.to_dict() for quarto in quartos]
    except Exception as exc:
        _tratar_excecao(exc)


@router.patch("/quartos/{numero}/bloquear", tags=["Quartos"])
def bloquear_quarto(numero: int, payload: BloqueioIn) -> dict:
    """Interdita um quarto para manutenção em um período com motivo definido."""
    try:
        if data.buscar_quarto(numero) is None:
            raise HTTPException(status_code=404, detail="Quarto não encontrado.")

        _hotel.bloquear_quarto(numero, payload.motivo, payload.inicio, payload.fim)
        # O serviço persiste a alteração; a consulta retorna o estado atualizado.
        return data.buscar_quarto(numero).to_dict()
    except Exception as exc:
        _tratar_excecao(exc)


@router.patch("/quartos/{numero}/desbloquear", tags=["Quartos"])
def desbloquear_quarto(numero: int) -> dict:
    """Libera um quarto da manutenção, tornando-o disponível novamente."""
    try:
        if data.buscar_quarto(numero) is None:
            raise HTTPException(status_code=404, detail="Quarto não encontrado.")

        _hotel.desbloquear_quarto(numero)
        return data.buscar_quarto(numero).to_dict()
    except Exception as exc:
        _tratar_excecao(exc)


# =========================================================================
# Hóspedes
# =========================================================================

@router.post("/hospedes", status_code=201, tags=["Hóspedes"])
def cadastrar_hospede(payload: HospedeIn) -> dict:
    """Cadastra um novo hóspede e retorna o ID gerado pelo banco."""
    try:
        hospede = Hospede(
            nome=payload.nome,
            documento=payload.documento,
            email=payload.email,
            telefone=payload.telefone,
            preferencias=payload.preferencias,
        )
        # O serviço salva o cadastro e atribui ao objeto o ID gerado pelo banco.
        _hotel.cadastrar_hospede(hospede)
        return hospede.to_dict()
    except Exception as exc:
        _tratar_excecao(exc)


# =========================================================================
# Ciclo de Vida da Reserva
# =========================================================================

@router.post("/reservas", status_code=201, tags=["Reservas"])
def criar_reserva(payload: ReservaIn) -> dict:
    """Cria reserva validando overbooking, capacidade e calcula tarifas dinâmicas."""
    try:
        if data.buscar_hospede(payload.hospede_id) is None:
            raise HTTPException(status_code=404, detail="Hóspede não encontrado.")
        if data.buscar_quarto(payload.quarto_num) is None:
            raise HTTPException(status_code=404, detail="Quarto não encontrado.")

        # O serviço valida as regras, calcula as diárias e já persiste a reserva.
        reserva = _hotel.criar_reserva(
            hospede_id=payload.hospede_id,
            quarto_num=payload.quarto_num,
            entrada=payload.entrada,
            saida=payload.saida,
            num_hospedes=payload.num_hospedes,
            origem=payload.origem,
        )
        return reserva.to_dict()
    except Exception as exc:
        _tratar_excecao(exc)


@router.post("/reservas/{reserva_id}/checkin", tags=["Reservas"])
def processar_checkin(reserva_id: int, payload: CheckinIn) -> dict:
    """Realiza o check-in validando tolerância de horário e status da reserva."""
    try:
        if data.buscar_reserva(reserva_id) is None:
            raise HTTPException(status_code=404, detail="Reserva não encontrada.")

        _hotel.processar_checkin(reserva_id, payload.momento)
        return data.buscar_reserva(reserva_id).to_dict()
    except Exception as exc:
        _tratar_excecao(exc)


@router.post("/reservas/{reserva_id}/checkout", tags=["Reservas"])
def processar_checkout(reserva_id: int, payload: CheckoutIn) -> dict:
    """Realiza o check-out calculando atrasos e exigindo quitação financeira."""
    try:
        if data.buscar_reserva(reserva_id) is None:
            raise HTTPException(status_code=404, detail="Reserva não encontrada.")

        total_devido = _hotel.processar_checkout(reserva_id, payload.momento)
        resposta = data.buscar_reserva(reserva_id).to_dict()
        resposta["total_devido"] = total_devido
        return resposta
    except Exception as exc:
        _tratar_excecao(exc)


@router.post("/reservas/{reserva_id}/cancelar", tags=["Reservas"])
def processar_cancelamento(reserva_id: int, payload: CancelamentoIn) -> dict:
    """Cancela a reserva aplicando multa de 50% se feito com menos de 48h de antecedência."""
    try:
        if data.buscar_reserva(reserva_id) is None:
            raise HTTPException(status_code=404, detail="Reserva não encontrada.")

        multa = _hotel.processar_cancelamento(reserva_id, payload.momento)
        resposta = data.buscar_reserva(reserva_id).to_dict()
        resposta["multa"] = multa
        return resposta
    except Exception as exc:
        _tratar_excecao(exc)


@router.post("/reservas/noshows", tags=["Reservas"])
def processar_noshows(payload: NoShowIn) -> dict:
    """Varre reservas confirmadas com tolerância expirada e as marca como NO_SHOW."""
    try:
        reservas_processadas = _hotel.processar_noshows(payload.momento_atual)
        return {
            "reservas_processadas": reservas_processadas,
            "quantidade": len(reservas_processadas),
        }
    except Exception as exc:
        _tratar_excecao(exc)


# =========================================================================
# Pagamentos e Consumo Extra
# =========================================================================

@router.post("/reservas/{reserva_id}/pagamentos", status_code=201, tags=["Financeiro"])
def registrar_pagamento(reserva_id: int, payload: PagamentoIn) -> dict:
    """Registra um pagamento (PIX, Cartão, Dinheiro) na conta da reserva."""
    try:
        if data.buscar_reserva(reserva_id) is None:
            raise HTTPException(status_code=404, detail="Reserva não encontrada.")

        pagamento = _hotel.registrar_pagamento(reserva_id, payload.valor, payload.metodo)
        return pagamento.to_dict()
    except Exception as exc:
        _tratar_excecao(exc)


@router.post("/reservas/{reserva_id}/adicionais", status_code=201, tags=["Financeiro"])
def lancar_adicional(reserva_id: int, payload: AdicionalIn) -> dict:
    """Lança um consumo extra (frigobar, refeição) durante a estadia ativa."""
    try:
        if data.buscar_reserva(reserva_id) is None:
            raise HTTPException(status_code=404, detail="Reserva não encontrada.")

        adicional = _hotel.lancar_adicional(
            reserva_id, payload.descricao, payload.preco, payload.quantidade
        )
        resposta = adicional.to_dict()
        resposta["total"] = adicional.total
        return resposta
    except Exception as exc:
        _tratar_excecao(exc)


# =========================================================================
# Relatórios
# =========================================================================

@router.get("/relatorios/ocupacao", tags=["Relatórios"])
def relatorio_ocupacao(inicio: date, fim: date) -> dict:
    """Retorna a taxa de ocupação percentual do hotel no período informado."""
    try:
        quartos = data.listar_quartos()
        reservas = data.listar_reservas()
        taxa = ServicoRelatorios.taxa_ocupacao(quartos, reservas, inicio, fim)
        return {
            "inicio": inicio.isoformat(),
            "fim": fim.isoformat(),
            "taxa_ocupacao": taxa,
        }
    except Exception as exc:
        _tratar_excecao(exc)


@router.get("/relatorios/adr", tags=["Relatórios"])
def relatorio_adr(inicio: date, fim: date) -> dict:
    """Retorna a diária média (Average Daily Rate) das hospedagens finalizadas no período."""
    try:
        reservas = data.listar_reservas()
        adr = ServicoRelatorios.calcular_adr(reservas, inicio, fim)
        return {
            "inicio": inicio.isoformat(),
            "fim": fim.isoformat(),
            "adr": adr,
        }
    except Exception as exc:
        _tratar_excecao(exc)


@router.get("/relatorios/revpar", tags=["Relatórios"])
def relatorio_revpar(inicio: date, fim: date) -> dict:
    """Retorna a receita por quarto disponível (Revenue per Available Room) no período."""
    try:
        quartos = data.listar_quartos()
        reservas = data.listar_reservas()
        revpar = ServicoRelatorios.calcular_revpar(quartos, reservas, inicio, fim)
        return {
            "inicio": inicio.isoformat(),
            "fim": fim.isoformat(),
            "revpar": revpar,
        }
    except Exception as exc:
        _tratar_excecao(exc)


@router.get("/relatorios/financeiro", tags=["Relatórios"])
def relatorio_financeiro(inicio: date, fim: date) -> dict:
    """Soma o total devido das reservas com check-out real no intervalo [inicio, fim)."""
    try:
        if inicio >= fim:
            raise DadosInvalidosException("O início deve ser anterior ao fim do período.")

        reservas = data.listar_reservas(status=StatusReserva.CHECKOUT.value)
        # Usa a data real de encerramento; a data final não faz parte do intervalo.
        finalizadas = [
            reserva for reserva in reservas
            if reserva.checkout_real is not None
            and inicio <= reserva.checkout_real.date() < fim
        ]
        receita_total = round(sum(reserva.valor_total_devido for reserva in finalizadas), 2)
        return {
            "inicio": inicio.isoformat(),
            "fim": fim.isoformat(),
            "receita_total": receita_total,
            "quantidade_reservas": len(finalizadas),
        }
    except Exception as exc:
        _tratar_excecao(exc)
