"""Regras do serviço Hotel com persistência real em banco temporário."""

from datetime import date, datetime, timedelta

import pytest

from src.database import data
from src.database.connection import inicializar_banco, obter_conexao
from src.models.enums import MetodoPagamento, StatusQuarto, StatusReserva, TipoQuarto
from src.models.exceptions import (
    CapacidadeExcedidaException,
    DadosInvalidosException,
    PagamentoInsuficienteException,
    QuartoIndisponivelException,
    TransicaoEstadoInvalidaException,
)
from src.models.person import Hospede
from src.models.room import QuartoDuplo, QuartoSimples
from src.services.hotel import Hotel


@pytest.fixture
def hotel(tmp_path, monkeypatch):
    """Mantém os dados de cada teste separados do banco usado pelo servidor."""
    caminho = tmp_path / "regras_teste.db"
    inicializar_banco(caminho)
    monkeypatch.setattr(data, "obter_conexao", lambda: obter_conexao(caminho))
    servico = Hotel(settings={
        "entrada_e_saida": {
            "checkIn_a_partir": "14:00", "checkOut_ate": "12:00", "tolerancia_min": 30,
        },
        "temporadas": [{"inicio": "2026-07-01", "fim": "2026-08-31", "multiplicador": 1.3}],
        "fim_de_semana": {"sabado": 1.4, "domingo": 1.1},
        "multa_de_cancelamento": {"horas_antecedencia": 48, "percentual": 0.5},
        "tolerancia_no_show": {"horario_referencia": "23:59", "minutos": 120},
    })
    servico.cadastrar_quarto(QuartoSimples(numero=101, capacidade=2, tarifa_base=100.0))
    servico.cadastrar_quarto(QuartoDuplo(numero=202, capacidade=2, tarifa_base=200.0))
    return servico


@pytest.fixture
def hospede(hotel):
    pessoa = Hospede(nome="Maria Silva", documento="123456789",
                     email="maria@example.com", telefone="88999999999")
    hotel.cadastrar_hospede(pessoa)
    return pessoa


@pytest.fixture
def reserva(hotel, hospede):
    return hotel.criar_reserva(hospede.id, 101, date(2026, 11, 10), date(2026, 11, 12), 2)


def test_criacao_calcula_tarifas_e_persiste_vinculos(hotel, hospede):
    reserva = hotel.criar_reserva(hospede.id, 101, date(2026, 8, 1), date(2026, 8, 3), 2)
    salva = data.buscar_reserva(reserva.id)
    # Sábado: 100 * 1,3 * 1,4; domingo: 100 * 1,3 * 1,1.
    assert salva.valor_total_diarias == 325.0
    assert salva.hospede.id == hospede.id
    assert salva.quarto.numero == 101
    assert salva.status == StatusReserva.CONFIRMADA


@pytest.mark.parametrize("entrada, saida, conflito", [
    (10, 12, True), (9, 11, True), (11, 13, True), (9, 13, True),
    (8, 10, False), (12, 14, False),
])
def test_disponibilidade_respeita_sobreposicoes_e_limites(hotel, hospede, reserva, entrada, saida, conflito):
    if conflito:
        with pytest.raises(QuartoIndisponivelException):
            hotel.criar_reserva(hospede.id, 101, date(2026, 11, entrada), date(2026, 11, saida), 1)
        assert len(data.listar_reservas()) == 1
    else:
        nova = hotel.criar_reserva(hospede.id, 101, date(2026, 11, entrada), date(2026, 11, saida), 1)
        assert nova.id != reserva.id
        assert len(data.listar_reservas()) == 2


def test_capacidade_excedida_nao_cria_reserva(hotel, hospede):
    with pytest.raises(CapacidadeExcedidaException):
        hotel.criar_reserva(hospede.id, 101, date(2026, 11, 10), date(2026, 11, 12), 3)
    assert data.listar_reservas() == []


@pytest.mark.parametrize("campo, valor", [
    ("num_hospedes", 0), ("hospede_id", 999), ("quarto_num", 999),
    ("entrada", "2026-11-10"), ("saida", date(2026, 11, 10)),
])
def test_criacao_rejeita_dados_invalidos_sem_persistir(hotel, hospede, campo, valor):
    dados = {"hospede_id": hospede.id, "quarto_num": 101, "entrada": date(2026, 11, 10),
             "saida": date(2026, 11, 12), "num_hospedes": 1}
    dados[campo] = valor
    with pytest.raises(DadosInvalidosException):
        hotel.criar_reserva(**dados)
    assert data.listar_reservas() == []


def test_manutencao_persiste_periodo_e_desbloqueio_restaura_disponibilidade(hotel, hospede):
    hotel.bloquear_quarto(101, "Pintura", date(2026, 11, 10), date(2026, 11, 12))
    salvo = data.buscar_quarto(101)
    assert salvo.inicio_manutencao == date(2026, 11, 10)
    assert salvo.motivo_manutencao == "Pintura"
    with pytest.raises(QuartoIndisponivelException):
        hotel.criar_reserva(hospede.id, 101, date(2026, 11, 10), date(2026, 11, 12), 1)
    fora = hotel.buscar_quartos_disponiveis(date(2026, 11, 13), date(2026, 11, 14))
    assert 101 in {quarto.numero for quarto in fora}
    hotel.desbloquear_quarto(101)
    salvo = data.buscar_quarto(101)
    assert salvo.status == StatusQuarto.DISPONIVEL
    assert salvo.inicio_manutencao is salvo.fim_manutencao is None


def test_bloqueio_administrativo_e_filtro_por_tipo(hotel):
    quarto = data.buscar_quarto(101)
    quarto.status = StatusQuarto.BLOQUEADO
    data.salvar_quarto(quarto)
    disponiveis = hotel.buscar_quartos_disponiveis(date(2026, 11, 10), date(2026, 11, 12))
    assert [quarto.numero for quarto in disponiveis] == [202]
    assert hotel.buscar_quartos_disponiveis(
        date(2026, 11, 10), date(2026, 11, 12), TipoQuarto.SIMPLES
    ) == []


def test_atendimento_com_adicionais_pagamentos_parciais_e_checkout(hotel, reserva):
    hotel.processar_checkin(reserva.id, datetime(2026, 11, 10, 14))
    hotel.lancar_adicional(reserva.id, "Água", 10.0, 2)
    hotel.registrar_pagamento(reserva.id, 100.0, MetodoPagamento.PIX)
    with pytest.raises(PagamentoInsuficienteException):
        hotel.processar_checkout(reserva.id, datetime(2026, 11, 12, 12))
    assert data.buscar_reserva(reserva.id).status == StatusReserva.CHECKIN
    assert data.buscar_quarto(101).status == StatusQuarto.OCUPADO

    hotel.registrar_pagamento(reserva.id, 120.0, MetodoPagamento.CREDITO)
    assert hotel.processar_checkout(reserva.id, datetime(2026, 11, 12, 12)) == 220.0
    salva = data.buscar_reserva(reserva.id)
    assert salva.status == StatusReserva.CHECKOUT
    assert salva.saldo_devedor == 0.0
    assert len(salva.pagamentos) == 2
    assert salva.total_adicionais == 20.0
    assert data.buscar_quarto(101).status == StatusQuarto.DISPONIVEL


@pytest.mark.parametrize("momento, total", [
    (datetime(2026, 11, 12, 12, 30), 200.0),
    (datetime(2026, 11, 12, 12, 31), 300.0),
])
def test_checkout_respeita_tolerancia_e_persiste_diaria_extra(hotel, reserva, momento, total):
    hotel.processar_checkin(reserva.id, datetime(2026, 11, 10, 14))
    hotel.registrar_pagamento(reserva.id, total, MetodoPagamento.DINHEIRO)
    assert hotel.processar_checkout(reserva.id, momento) == total
    assert data.buscar_reserva(reserva.id).valor_total_devido == total


def test_operacoes_incompativeis_com_estado_nao_alteram_reserva(hotel, reserva):
    with pytest.raises(TransicaoEstadoInvalidaException):
        hotel.lancar_adicional(reserva.id, "Água", 10.0)
    with pytest.raises(TransicaoEstadoInvalidaException):
        hotel.processar_checkout(reserva.id, datetime(2026, 11, 12, 12))
    hotel.processar_checkin(reserva.id, datetime(2026, 11, 10, 14))
    with pytest.raises(TransicaoEstadoInvalidaException):
        hotel.processar_checkin(reserva.id, datetime(2026, 11, 10, 15))
    with pytest.raises(TransicaoEstadoInvalidaException):
        hotel.processar_cancelamento(reserva.id, datetime(2026, 11, 10, 15))
    with pytest.raises(QuartoIndisponivelException):
        hotel.bloquear_quarto(101, "Pintura", date(2026, 11, 10), date(2026, 11, 12))
    assert data.buscar_reserva(reserva.id).status == StatusReserva.CHECKIN


def test_checkin_antecipado_e_recusado_sem_ocupar_quarto(hotel, reserva):
    with pytest.raises(DadosInvalidosException):
        hotel.processar_checkin(reserva.id, datetime(2026, 11, 10, 13, 29))
    assert data.buscar_quarto(101).status == StatusQuarto.DISPONIVEL
    hotel.processar_checkin(reserva.id, datetime(2026, 11, 10, 13, 30))
    assert data.buscar_reserva(reserva.id).status == StatusReserva.CHECKIN


@pytest.mark.parametrize("momento, multa", [
    (datetime(2026, 11, 8, 13, 59), 0.0),
    (datetime(2026, 11, 8, 14), 0.0),
    (datetime(2026, 11, 8, 14, 1), 100.0),
])
def test_cancelamento_respeita_janela_e_libera_periodo(hotel, reserva, momento, multa):
    assert hotel.processar_cancelamento(reserva.id, momento) == multa
    assert data.buscar_reserva(reserva.id).status == StatusReserva.CANCELADA
    assert 101 in {q.numero for q in hotel.buscar_quartos_disponiveis(
        date(2026, 11, 10), date(2026, 11, 12)
    )}
    with pytest.raises(TransicaoEstadoInvalidaException):
        hotel.registrar_pagamento(reserva.id, 100.0, MetodoPagamento.PIX)


def test_politica_de_cancelamento_pode_ser_configurada(hotel, reserva):
    configurado = Hotel(settings={
        "multa_de_cancelamento": {"horas_antecedencia": 24, "percentual": 0.25},
        "entrada_e_saida": {"checkIn_a_partir": "14:00"},
    })
    assert configurado.processar_cancelamento(reserva.id, datetime(2026, 11, 9, 15)) == 50.0


def test_noshow_persiste_libera_periodo_e_nao_e_reprocessado(hotel, reserva):
    momento = datetime(2026, 11, 11, 3)
    assert hotel.processar_noshows(momento) == [reserva.id]
    assert data.buscar_reserva(reserva.id).status == StatusReserva.NO_SHOW
    assert data.buscar_quarto(101).status == StatusQuarto.DISPONIVEL
    assert hotel.processar_noshows(momento + timedelta(minutes=1)) == []
    assert 101 in {q.numero for q in hotel.buscar_quartos_disponiveis(
        date(2026, 11, 10), date(2026, 11, 12)
    )}


def test_noshow_nao_afeta_reserva_com_checkin_realizado(hotel, reserva):
    hotel.processar_checkin(reserva.id, datetime(2026, 11, 10, 14))
    assert hotel.processar_noshows(datetime(2026, 11, 11, 3)) == []
    assert data.buscar_quarto(101).status == StatusQuarto.OCUPADO


def test_checkin_em_dia_posterior_deve_ser_rejeitado(hotel, reserva):
    with pytest.raises(DadosInvalidosException):
        hotel.processar_checkin(reserva.id, datetime(2026, 11, 11, 14))
    assert data.buscar_reserva(reserva.id).status == StatusReserva.CONFIRMADA


@pytest.mark.parametrize("momento, deve_processar", [
    (datetime(2026, 11, 10, 16, 1), False),
    (datetime(2026, 11, 11, 1, 58, 59), False),
    (datetime(2026, 11, 11, 1, 59), False),
    (datetime(2026, 11, 11, 1, 59, 1), True),
])
def test_noshow_respeita_tolerancia_apos_2359_do_dia_da_entrada(
    hotel, reserva, momento, deve_processar
):
    """O limite é 01h59 do dia seguinte; só depois disso a reserva pode mudar."""
    esperado = [reserva.id] if deve_processar else []
    assert hotel.processar_noshows(momento) == esperado
    status = StatusReserva.NO_SHOW if deve_processar else StatusReserva.CONFIRMADA
    assert data.buscar_reserva(reserva.id).status == status
    disponiveis = {q.numero for q in hotel.buscar_quartos_disponiveis(
        date(2026, 11, 10), date(2026, 11, 12)
    )}
    assert (101 in disponiveis) == deve_processar


@pytest.mark.parametrize("referencia, minutos, limite", [
    ("18:30", 30, datetime(2026, 11, 10, 19)),
    ("23:59", 0, datetime(2026, 11, 10, 23, 59)),
    ("22:00", 180, datetime(2026, 11, 11, 1)),
])
def test_noshow_usa_referencia_e_tolerancia_configuradas(hotel, reserva, referencia, minutos, limite):
    configurado = Hotel(settings={
        "entrada_e_saida": {"checkIn_a_partir": "09:00"},
        "tolerancia_no_show": {"horario_referencia": referencia, "minutos": minutos},
    })
    # Os limites esperados são explícitos para detectar cálculos incorretos do serviço.
    assert configurado.processar_noshows(limite - timedelta(seconds=1)) == []
    assert configurado.processar_noshows(limite) == []
    assert data.buscar_reserva(reserva.id).status == StatusReserva.CONFIRMADA
    assert configurado.processar_noshows(limite + timedelta(seconds=1)) == [reserva.id]
    assert data.buscar_reserva(reserva.id).status == StatusReserva.NO_SHOW
    assert configurado.processar_noshows(limite + timedelta(minutes=1)) == []


def test_noshow_carrega_politica_do_settings_do_projeto(hotel, reserva):
    """Também confere a configuração real, além das configurações isoladas dos testes."""
    configurado = Hotel()
    assert configurado.processar_noshows(datetime(2026, 11, 10, 16, 1)) == []
    assert configurado.processar_noshows(datetime(2026, 11, 11, 1, 59)) == []
    assert configurado.processar_noshows(datetime(2026, 11, 11, 2)) == [reserva.id]
