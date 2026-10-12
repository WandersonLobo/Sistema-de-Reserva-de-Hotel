from datetime import date

import pytest

from src.database import data as data_module
from src.database.connection import inicializar_banco, obter_conexao
from src.models.enums import OrigemReserva
from src.models.person import Hospede
from src.models.reservation import Reserva
from src.models.room import QuartoSimples


@pytest.fixture
def banco_teste(tmp_path, monkeypatch):
    """Inicializa um banco temporário e o injeta nas funções de data.py."""
    caminho = tmp_path / "hotel_teste.db"
    inicializar_banco(caminho)

    monkeypatch.setattr(
        data_module,
        "obter_conexao",
        lambda: obter_conexao(caminho),
    )

    return caminho


def inserir_quarto_teste(caminho, numero=101):
    conexao = obter_conexao(caminho)
    try:
        with conexao:
            conexao.execute(
                """
                INSERT INTO quartos (
                    numero, tipo, capacidade, tarifa_base, status,
                    tem_varanda, tem_hidromassagem, taxa_servico_adicional
                )
                VALUES (?, 'SIMPLES', 1, 150.0, 'DISPONIVEL', 0, 0, 0.0)
                """,
                (numero,),
            )
    finally:
        conexao.close()


def inserir_temporada_teste(caminho):
    conexao = obter_conexao(caminho)
    try:
        with conexao:
            conexao.execute(
                """
                INSERT INTO temporadas (
                    nome, data_inicio, data_fim, multiplicador
                )
                VALUES (?, ?, ?, ?)
                """,
                ("Alta temporada", "2026-07-01", "2026-08-31", 1.3),
            )
    finally:
        conexao.close()


def criar_hospede_teste():
    return Hospede(
        nome="Maria Silva",
        documento="123456789",
        email="maria@example.com",
        telefone="11999999999",
        preferencias="Quarto silencioso",
    )


def test_inicializar_banco_cria_tabelas_e_ativa_chaves_estrangeiras(
    tmp_path,
):
    caminho = tmp_path / "estrutura.db"
    inicializar_banco(caminho)

    conexao = obter_conexao(caminho)
    try:
        tabelas = conexao.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            ORDER BY name
            """
        ).fetchall()
        foreign_keys = conexao.execute("PRAGMA foreign_keys").fetchone()[0]
    finally:
        conexao.close()

    assert {linha["name"] for linha in tabelas} >= {
        "hospedes",
        "quartos",
        "temporadas",
        "reservas",
    }
    assert foreign_keys == 1


def test_quartos_sao_listados_e_buscados(banco_teste):
    inserir_quarto_teste(banco_teste, numero=102)
    inserir_quarto_teste(banco_teste, numero=101)

    quartos = data_module.listar_quartos()
    encontrado = data_module.buscar_quarto(101)

    assert [quarto.numero for quarto in quartos] == [101, 102]
    assert isinstance(encontrado, QuartoSimples)
    assert encontrado.numero == 101
    assert data_module.buscar_quarto(999) is None


def test_hospede_e_reserva_sao_salvos_e_buscados(banco_teste):
    inserir_quarto_teste(banco_teste)
    hospede = criar_hospede_teste()
    hospede_id = data_module.salvar_hospede(hospede)

    salvo = data_module.buscar_hospede(hospede_id)
    reserva = Reserva(
        hospede=salvo,
        quarto=data_module.buscar_quarto(101),
        data_entrada=date(2026, 7, 10),
        data_saida=date(2026, 7, 12),
        num_hospedes=1,
        origem=OrigemReserva.SITE,
        valor_total_diarias=300.0,
    )
    reserva_id = data_module.salvar_reserva(reserva)
    recuperada = data_module.buscar_reserva(reserva_id)

    assert salvo is not None
    assert salvo.id == hospede_id
    assert salvo.nome == "Maria Silva"
    assert recuperada is not None
    assert recuperada.id == reserva_id
    assert recuperada.hospede is not None
    assert recuperada.hospede.id == hospede_id
    assert recuperada.quarto is not None
    assert recuperada.quarto.numero == 101
    assert data_module.buscar_hospede(999) is None
    assert data_module.buscar_reserva(999) is None


def test_temporada_eh_filtrada_pela_data_de_referencia(banco_teste):
    inserir_temporada_teste(banco_teste)

    dentro_do_periodo = data_module.listar_temporadas(date(2026, 7, 15))
    fora_do_periodo = data_module.listar_temporadas(date(2026, 9, 1))

    assert len(dentro_do_periodo) == 1
    assert dentro_do_periodo[0]["nome"] == "Alta temporada"
    assert fora_do_periodo == []
