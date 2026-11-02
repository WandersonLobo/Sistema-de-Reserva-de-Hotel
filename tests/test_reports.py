"""Testes da ocupação e contratos dos indicadores ainda pendentes."""

from copy import deepcopy
from datetime import date, datetime

import pytest

from src.models.enums import StatusQuarto, StatusReserva
from src.models.exceptions import DadosInvalidosException
from src.models.payment import Adicional, Pagamento
from src.models.reservation import Reserva
from src.models.room import QuartoSimples
from src.services.reports import ServicoRelatorios


@pytest.fixture
def quartos():
    return [QuartoSimples(numero=101), QuartoSimples(numero=102)]


def criar_reserva(quarto, entrada=10, saida=12, status=StatusReserva.CONFIRMADA, valor=300.0):
    return Reserva(
        quarto=quarto, data_entrada=date(2026, 11, entrada),
        data_saida=date(2026, 11, saida), status=status, valor_total_diarias=valor,
    )


def test_ocupacao_sem_quartos_ou_reservas_retorna_zero(quartos):
    assert ServicoRelatorios.taxa_ocupacao([], [], date(2026, 11, 10), date(2026, 11, 12)) == 0.0
    assert ServicoRelatorios.taxa_ocupacao(
        quartos, [], date(2026, 11, 10), date(2026, 11, 12)
    ) == 0.0


def test_ocupacao_parcial_e_total(quartos):
    reservas = [criar_reserva(quartos[0])]
    assert ServicoRelatorios.taxa_ocupacao(
        quartos, reservas, date(2026, 11, 10), date(2026, 11, 12)
    ) == 50.0
    reservas.append(criar_reserva(quartos[1]))
    assert ServicoRelatorios.taxa_ocupacao(
        quartos, reservas, date(2026, 11, 10), date(2026, 11, 12)
    ) == 100.0


@pytest.mark.parametrize("status, esperado", [
    (StatusReserva.PENDENTE, 0.0),
    (StatusReserva.CONFIRMADA, 50.0),
    (StatusReserva.CHECKIN, 50.0),
    (StatusReserva.CHECKOUT, 50.0),
    (StatusReserva.CANCELADA, 0.0),
    (StatusReserva.NO_SHOW, 0.0),
])
def test_ocupacao_considera_apenas_estados_ativos_e_finalizados(quartos, status, esperado):
    reservas = [criar_reserva(quartos[0], status=status)]
    assert ServicoRelatorios.taxa_ocupacao(
        quartos, reservas, date(2026, 11, 10), date(2026, 11, 12)
    ) == esperado


@pytest.mark.parametrize("entrada, saida, esperado", [
    (8, 11, 25.0),
    (11, 14, 25.0),
    (8, 14, 50.0),
    (8, 10, 0.0),
    (12, 14, 0.0),
])
def test_ocupacao_recorta_estadias_ao_intervalo_e_exclui_saida(quartos, entrada, saida, esperado):
    reservas = [criar_reserva(quartos[0], entrada, saida)]
    assert ServicoRelatorios.taxa_ocupacao(
        quartos, reservas, date(2026, 11, 10), date(2026, 11, 12)
    ) == esperado


def test_sobreposicoes_nao_contam_mesmo_quarto_duas_vezes(quartos):
    reservas = [criar_reserva(quartos[0]), criar_reserva(quartos[0], entrada=11, saida=13)]
    assert ServicoRelatorios.taxa_ocupacao(
        quartos, reservas, date(2026, 11, 10), date(2026, 11, 13)
    ) == 50.0


def test_inventario_duplicado_e_identificado_pelo_numero(quartos):
    inventario = quartos + [QuartoSimples(numero=101)]
    assert ServicoRelatorios.taxa_ocupacao(
        inventario, [criar_reserva(quartos[0])], date(2026, 11, 10), date(2026, 11, 12)
    ) == 50.0


def test_reservas_sem_quarto_ou_fora_do_inventario_sao_ignoradas(quartos):
    reservas = [criar_reserva(None), criar_reserva(QuartoSimples(numero=999))]
    assert ServicoRelatorios.taxa_ocupacao(
        quartos, reservas, date(2026, 11, 10), date(2026, 11, 12)
    ) == 0.0


def test_estado_atual_de_manutencao_nao_apaga_ocupacao_historica(quartos):
    reservas = [criar_reserva(quartos[0], status=StatusReserva.CHECKOUT)]
    quartos[0].bloquear_manutencao("Pintura", date(2026, 11, 20), date(2026, 11, 22))
    quartos[1].status = StatusQuarto.BLOQUEADO
    assert ServicoRelatorios.taxa_ocupacao(
        quartos, reservas, date(2026, 11, 10), date(2026, 11, 12)
    ) == 50.0


def test_ocupacao_arredonda_duas_casas(quartos):
    assert ServicoRelatorios.taxa_ocupacao(
        quartos[:1], [criar_reserva(quartos[0], saida=11)],
        date(2026, 11, 10), date(2026, 11, 13),
    ) == pytest.approx(33.33)


def test_relatorio_nao_modifica_entidades(quartos):
    reservas = [criar_reserva(quartos[0])]
    antes = deepcopy([reserva.to_dict() for reserva in reservas])
    inventario_antes = [quarto.to_dict() for quarto in quartos]
    ServicoRelatorios.taxa_ocupacao(quartos, reservas, date(2026, 11, 10), date(2026, 11, 12))
    assert [reserva.to_dict() for reserva in reservas] == antes
    assert [quarto.to_dict() for quarto in quartos] == inventario_antes


@pytest.mark.parametrize("inicio, fim", [
    (date(2026, 11, 10), date(2026, 11, 10)),
    (date(2026, 11, 12), date(2026, 11, 10)),
    ("2026-11-10", date(2026, 11, 12)),
    (date(2026, 11, 10), datetime(2026, 11, 12)),
])
def test_ocupacao_rejeita_periodos_invalidos_mesmo_sem_inventario(inicio, fim):
    with pytest.raises(DadosInvalidosException):
        ServicoRelatorios.taxa_ocupacao([], [], inicio, fim)


def test_adr_divide_receita_de_hospedagem_por_diarias_vendidas(quartos):
    reservas = [
        criar_reserva(quartos[0], status=StatusReserva.CHECKOUT, valor=200.0),
        criar_reserva(quartos[1], saida=11, status=StatusReserva.CHECKOUT, valor=150.0),
    ]
    assert ServicoRelatorios.calcular_adr(
        reservas, date(2026, 11, 10), date(2026, 11, 12)
    ) == pytest.approx(116.67, abs=0.01)


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="calcular_revpar ainda não foi implementado")
def test_revpar_considera_quartos_sem_venda(quartos):
    reservas = [criar_reserva(quartos[0], saida=11, status=StatusReserva.CHECKOUT, valor=150.0)]
    assert ServicoRelatorios.calcular_revpar(
        quartos, reservas, date(2026, 11, 10), date(2026, 11, 11)
    ) == 75.0


def test_adr_sem_vendas_retorna_zero():
    assert ServicoRelatorios.calcular_adr([], date(2026, 11, 10), date(2026, 11, 12)) == 0.0


@pytest.mark.parametrize("status", list(StatusReserva))
def test_adr_considera_somente_hospedagens_finalizadas(quartos, status):
    reserva = criar_reserva(quartos[0], status=status)
    esperado = 150.0 if status == StatusReserva.CHECKOUT else 0.0
    assert ServicoRelatorios.calcular_adr(
        [reserva], date(2026, 11, 10), date(2026, 11, 12)
    ) == esperado


def test_adr_rateia_receita_e_pondera_noites_no_recorte(quartos):
    reservas = [
        criar_reserva(quartos[0], entrada=8, saida=12, status=StatusReserva.CHECKOUT, valor=400.0),
        criar_reserva(quartos[1], entrada=11, saida=12, status=StatusReserva.CHECKOUT, valor=200.0),
    ]
    # No recorte: duas noites de R$ 100 e uma de R$ 200; receita de R$ 400 / 3.
    assert ServicoRelatorios.calcular_adr(
        reservas, date(2026, 11, 10), date(2026, 11, 12)
    ) == 133.33


def test_adr_exclui_estadias_que_apenas_tocam_os_limites(quartos):
    reservas = [
        criar_reserva(quartos[0], entrada=8, saida=10, status=StatusReserva.CHECKOUT),
        criar_reserva(quartos[1], entrada=12, saida=14, status=StatusReserva.CHECKOUT),
    ]
    assert ServicoRelatorios.calcular_adr(
        reservas, date(2026, 11, 10), date(2026, 11, 12)
    ) == 0.0


def test_adr_ignora_reserva_sem_quarto(quartos):
    reservas = [
        criar_reserva(None, status=StatusReserva.CHECKOUT, valor=900.0),
        criar_reserva(quartos[0], status=StatusReserva.CHECKOUT, valor=200.0),
    ]
    assert ServicoRelatorios.calcular_adr(
        reservas, date(2026, 11, 10), date(2026, 11, 12)
    ) == 100.0


def test_adr_exclui_adicionais_e_nao_modifica_reserva(quartos):
    reserva = criar_reserva(quartos[0])
    reserva.realizar_checkin(datetime(2026, 11, 10, 14))
    reserva.adicionar_adicional(Adicional(descricao="Frigobar", preco_unitario=50.0))
    reserva.adicionar_pagamento(Pagamento(valor=350.0))
    reserva.realizar_checkout(datetime(2026, 11, 12, 12))
    antes = deepcopy(reserva.to_dict())

    assert reserva.valor_total_devido == 350.0
    assert ServicoRelatorios.calcular_adr(
        [reserva], date(2026, 11, 10), date(2026, 11, 12)
    ) == 150.0
    assert reserva.to_dict() == antes


@pytest.mark.parametrize("inicio, fim", [
    (date(2026, 11, 10), date(2026, 11, 10)),
    (date(2026, 11, 12), date(2026, 11, 10)),
    ("2026-11-10", date(2026, 11, 12)),
    (datetime(2026, 11, 10), date(2026, 11, 12)),
    (date(2026, 11, 10), datetime(2026, 11, 12)),
])
def test_adr_rejeita_periodos_invalidos_mesmo_sem_vendas(inicio, fim):
    with pytest.raises(DadosInvalidosException):
        ServicoRelatorios.calcular_adr([], inicio, fim)


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="calcular_revpar ainda não foi implementado")
def test_revpar_sem_inventario_retorna_zero():
    assert ServicoRelatorios.calcular_revpar([], [], date(2026, 11, 10), date(2026, 11, 12)) == 0.0
