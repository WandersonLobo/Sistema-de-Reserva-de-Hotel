"""Testes das tarifas por categoria, temporada e fim de semana."""

from copy import deepcopy
from datetime import date, datetime

import pytest

from src.models.exceptions import DadosInvalidosException
from src.models.room import QuartoDuplo, QuartoLuxo, QuartoSimples
from src.services.rates import CalculadoraTarifa


@pytest.fixture
def quarto():
    return QuartoSimples(numero=101, tarifa_base=100.0)


@pytest.fixture
def settings():
    """Usa valores fixos para não depender das configurações de demonstração."""
    return {
        "temporadas": [{
            "inicio": "2026-07-01", "fim": "2026-08-31", "multiplicador": 1.3,
        }],
        "fim_de_semana": {"sexta": 1.5, "sabado": 1.4, "domingo": 1.1},
    }


def test_dia_util_sem_ajuste_preserva_tarifa(quarto):
    assert CalculadoraTarifa.calcular_diaria_com_ajustes(quarto, date(2026, 11, 10), {}) == 100.0


@pytest.mark.parametrize("dia, esperado", [
    (date(2026, 11, 13), 150.0),
    (date(2026, 11, 14), 140.0),
    (date(2026, 11, 15), 110.0),
    (date(2026, 11, 16), 100.0),
])
def test_ajustes_de_fim_de_semana(quarto, settings, dia, esperado):
    assert CalculadoraTarifa.calcular_diaria_com_ajustes(quarto, dia, settings) == esperado


@pytest.mark.parametrize("dia, esperado", [
    (date(2026, 6, 30), 100.0),
    (date(2026, 7, 1), 130.0),
    (date(2026, 8, 31), 130.0),
    (date(2026, 9, 1), 100.0),
])
def test_temporada_inclui_os_dois_limites(quarto, settings, dia, esperado):
    assert CalculadoraTarifa.calcular_diaria_com_ajustes(quarto, dia, settings) == esperado


def test_temporada_e_fim_de_semana_sao_cumulativos(quarto, settings):
    # Sábado na alta temporada: 100 * 1,3 * 1,4.
    assert CalculadoraTarifa.calcular_diaria_com_ajustes(
        quarto, date(2026, 8, 1), settings
    ) == 182.0


@pytest.mark.parametrize("dia, esperado", [
    (date(2026, 11, 13), 100.0),
    (date(2026, 11, 14), 120.0),
    (date(2026, 11, 15), 120.0),
])
def test_multiplicador_unico_aplica_apenas_sabado_e_domingo(quarto, dia, esperado):
    assert CalculadoraTarifa.calcular_diaria_com_ajustes(
        quarto, dia, {"fim_de_semana": 1.2}
    ) == esperado


@pytest.mark.parametrize("temporada", [
    {"inicio": "2026-07-01", "fim": "2026-08-31", "multiplicador": 1.3},
    {"data_inicio": "2026-07-01", "data_fim": "2026-08-31", "multiplicador": 1.3},
    {"inicio": date(2026, 7, 1), "fim": date(2026, 8, 31), "multiplicador": 1.3},
])
def test_temporada_aceita_formatos_do_json_e_do_banco(quarto, temporada):
    assert CalculadoraTarifa.calcular_diaria_com_ajustes(
        quarto, date(2026, 7, 1), {"temporadas": [temporada]}
    ) == 130.0


def test_temporadas_sobrepostas_usam_primeira_correspondente(quarto, settings):
    settings["temporadas"].append({
        "inicio": "2026-07-01", "fim": "2026-07-31", "multiplicador": 2.0,
    })
    assert CalculadoraTarifa.calcular_diaria_com_ajustes(
        quarto, date(2026, 7, 1), settings
    ) == 130.0


@pytest.mark.parametrize("categoria, esperado", [
    ("simples", 182.0),
    ("duplo", 209.3),
    ("luxo", 252.0),
])
def test_ajustes_preservam_regras_polimorficas(settings, categoria, esperado):
    quartos = {
        "simples": QuartoSimples(numero=101, tarifa_base=100.0),
        "duplo": QuartoDuplo(numero=201, tarifa_base=100.0, tem_varanda=True),
        "luxo": QuartoLuxo(numero=301, tarifa_base=100.0, taxa_servico_adicional=50.0),
    }
    assert CalculadoraTarifa.calcular_diaria_com_ajustes(
        quartos[categoria], date(2026, 8, 1), settings
    ) == esperado


def test_total_recalcula_noites_ao_atravessar_temporada_e_fim_de_semana(quarto, settings):
    # 30/06 a 06/07: 100 + 130 + 130 + 195 + 182 + 143; a saída não é cobrada.
    assert CalculadoraTarifa.calcular_total_reserva(
        quarto, date(2026, 6, 30), date(2026, 7, 6), settings
    ) == 880.0


def test_uma_noite_nao_cobra_o_dia_da_saida(quarto):
    assert CalculadoraTarifa.calcular_total_reserva(
        quarto, date(2026, 11, 10), date(2026, 11, 11), {}
    ) == 100.0


def test_arredonda_cada_diaria_antes_de_somar():
    quarto = QuartoSimples(numero=101, tarifa_base=99.99)
    settings = {"fim_de_semana": 1.333}
    assert CalculadoraTarifa.calcular_total_reserva(
        quarto, date(2026, 11, 14), date(2026, 11, 16), settings
    ) == 266.58


def test_calculo_nao_modifica_quarto_nem_configuracoes(quarto, settings):
    configuracoes_antes = deepcopy(settings)
    quarto_antes = quarto.to_dict()
    CalculadoraTarifa.calcular_total_reserva(
        quarto, date(2026, 7, 1), date(2026, 7, 6), settings
    )
    assert settings == configuracoes_antes
    assert quarto.to_dict() == quarto_antes


@pytest.mark.parametrize("fator", [0, -1, True, "1.3", float("nan"), float("inf")])
@pytest.mark.parametrize("origem", ["temporada", "fim_de_semana"])
def test_rejeita_multiplicadores_invalidos(quarto, fator, origem):
    settings = {"fim_de_semana": {"sabado": fator}} if origem == "fim_de_semana" else {
        "temporadas": [{"inicio": "2026-01-01", "fim": "2026-12-31", "multiplicador": fator}]
    }
    with pytest.raises(DadosInvalidosException):
        CalculadoraTarifa.calcular_diaria_com_ajustes(quarto, date(2026, 8, 1), settings)


@pytest.mark.parametrize("inicio, fim", [
    ("data-invalida", "2026-08-31"),
    ("2026-08-31", "2026-07-01"),
])
def test_rejeita_periodo_de_temporada_invalido(quarto, inicio, fim):
    settings = {"temporadas": [{"inicio": inicio, "fim": fim, "multiplicador": 1.3}]}
    with pytest.raises(DadosInvalidosException):
        CalculadoraTarifa.calcular_diaria_com_ajustes(quarto, date(2026, 8, 1), settings)


@pytest.mark.parametrize("inicio, fim", [
    (date(2026, 11, 10), date(2026, 11, 10)),
    (date(2026, 11, 12), date(2026, 11, 10)),
    ("2026-11-10", date(2026, 11, 12)),
    (date(2026, 11, 10), datetime(2026, 11, 12)),
])
def test_rejeita_periodo_de_reserva_invalido(quarto, inicio, fim):
    with pytest.raises(DadosInvalidosException):
        CalculadoraTarifa.calcular_total_reserva(quarto, inicio, fim, {})


def test_diaria_rejeita_datetime_em_vez_de_date(quarto):
    with pytest.raises(DadosInvalidosException):
        CalculadoraTarifa.calcular_diaria_com_ajustes(quarto, datetime(2026, 11, 10), {})
