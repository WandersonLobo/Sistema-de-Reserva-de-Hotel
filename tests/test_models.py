
# Utilizando re-export #
from datetime import date, datetime, timedelta
import pytest
from src.models import (
    # Enums #
    MetodoPagamento,
    OrigemReserva,
    StatusQuarto,
    StatusReserva,
    TipoQuarto,
    # Exceções #
    CapacidadeExcedidaException,
    DadosInvalidosException,
    PagamentoInsuficienteException,
    QuartoIndisponivelException,
    TransicaoEstadoInvalidaException,
    # Entidades #
    Hospede,
    Quarto,
    QuartoSimples,
    QuartoDuplo,
    QuartoLuxo,
    Reserva,
    Pagamento,
    Adicional,
)

# =========================================================================== #
# Fixtures reutilizáveis (Objetos base para os testes)                        #
# =========================================================================== #

@pytest.fixture
def hospede_padrao() -> Hospede:
    """Fixture que fornece uma instância válida de Hospede."""
    return Hospede(
        id_=1,
        nome="Carlos Drummond",
        documento="123.456.789-00",
        email="carlos@email.com",
        telefone="(88) 98765-4321",
        preferencias="Andar alto, travesseiro extra",
    )


@pytest.fixture
def quarto_simples() -> QuartoSimples:
    """Fixture que fornece um QuartoSimples padrão."""
    return QuartoSimples(numero=101, capacidade=1, tarifa_base=150.0)


@pytest.fixture
def quarto_duplo() -> QuartoDuplo:
    """Fixture que fornece um QuartoDuplo padrão com varanda."""
    return QuartoDuplo(numero=102, capacidade=2, tarifa_base=250.0, tem_varanda=True)


@pytest.fixture
def quarto_luxo() -> QuartoLuxo:
    """Fixture que fornece um QuartoLuxo padrão."""
    return QuartoLuxo(
        numero=201,
        capacidade=4,
        tarifa_base=450.0,
        tem_hidromassagem=True,
        taxa_servico_adicional=50.0,
    )


# =========================================================================== #
# 1. Testes de Pessoa e Hospede                                               #
# =========================================================================== #

def test_criar_hospede_sucesso(hospede_padrao: Hospede) -> None:
    """Testa a criação válida de um hóspede com verificação de propriedades."""
    assert hospede_padrao.id == 1
    assert hospede_padrao.nome == "Carlos Drummond"
    assert hospede_padrao.documento == "123.456.789-00"
    assert hospede_padrao.email == "carlos@email.com"
    assert hospede_padrao.telefone == "(88) 98765-4321"
    assert "Andar alto" in hospede_padrao.preferencias
    assert hospede_padrao.historico_reservas == []


def test_hospede_email_invalido_lanca_excecao() -> None:
    """Garante que formatos inválidos de e-mail disparem DadosInvalidosException."""
    with pytest.raises(DadosInvalidosException):
        Hospede(nome="Ana", documento="111", email="email_sem_arroba.com", telefone="123")


def test_hospede_nome_e_documento_vazios_lancam_excecao(hospede_padrao: Hospede) -> None:
    """Garante que atribuir nome ou documento vazios dispare DadosInvalidosException."""
    with pytest.raises(DadosInvalidosException):
        hospede_padrao.nome = "   "

    with pytest.raises(DadosInvalidosException):
        hospede_padrao.documento = ""


def test_hospede_vincular_reserva_e_copia_defensiva(hospede_padrao: Hospede, quarto_simples: QuartoSimples) -> None:
    """Testa a vinculação de reservas e a proteção de encapsulamento da lista."""
    reserva = Reserva(id_=1, hospede=hospede_padrao, quarto=quarto_simples)
    hospede_padrao.vincular_reserva(reserva)

    assert len(hospede_padrao.historico_reservas) == 1
    assert hospede_padrao.historico_reservas[0] == reserva

    # Tentativa de vincular a mesma reserva novamente deve falhar
    with pytest.raises(DadosInvalidosException):
        hospede_padrao.vincular_reserva(reserva)

    # Cópia defensiva: alterar a lista retornada não altera o estado interno
    lista = hospede_padrao.historico_reservas
    lista.clear()
    assert len(hospede_padrao.historico_reservas) == 1


# =========================================================================== #
# 2. Testes de Quarto, Polimorfismo e Métodos Especiais                        #
# =========================================================================== #

def test_criar_subclasses_quarto_e_tipos(
    quarto_simples: QuartoSimples,
    quarto_duplo: QuartoDuplo,
    quarto_luxo: QuartoLuxo,
) -> None:
    """Testa as subclasses de quarto e a atribuição correta dos Enums de TipoQuarto."""
    assert quarto_simples.tipo == TipoQuarto.SIMPLES
    assert quarto_duplo.tipo == TipoQuarto.DUPLO
    assert quarto_luxo.tipo == TipoQuarto.LUXO

    assert quarto_simples.status == StatusQuarto.DISPONIVEL
    assert quarto_duplo.tem_varanda is True
    assert quarto_luxo.tem_hidromassagem is True


def test_quarto_validacao_capacidade_e_tarifa(quarto_simples: QuartoSimples) -> None:
    """Valida que capacidade < 1 e tarifa_base <= 0 disparam DadosInvalidosException."""
    with pytest.raises(DadosInvalidosException):
        QuartoSimples(numero=101, capacidade=0, tarifa_base=150.0)

    with pytest.raises(DadosInvalidosException):
        quarto_simples.tarifa_base = -50.0

    with pytest.raises(DadosInvalidosException):
        quarto_simples.tarifa_base = 0.0

    with pytest.raises(DadosInvalidosException):
        quarto_simples.capacidade = 0


def test_calculo_polimorfico_diaria(
    quarto_simples: QuartoSimples,
    quarto_duplo: QuartoDuplo,
    quarto_luxo: QuartoLuxo,
) -> None:
    """Valida o cálculo polimórfico da diária para cada subclasse de quarto."""
    #  Simples: tarifa_base * fator
    assert quarto_simples.calcular_diaria(fator_temporada=1.0) == 150.0
    assert quarto_simples.calcular_diaria(fator_temporada=1.2) == 180.0

    #  Duplo com varanda: tarifa_base * 1.15 * fator (250 * 1.15 = 287.50)
    assert quarto_duplo.calcular_diaria(fator_temporada=1.0) == 287.50
    quarto_duplo.tem_varanda = False
    assert quarto_duplo.calcular_diaria(fator_temporada=1.0) == 250.0

    #  Luxo: (tarifa_base * fator) + taxa_servico (450 * 1.0 + 50 = 500.0)
    assert quarto_luxo.calcular_diaria(fator_temporada=1.0) == 500.0
    assert quarto_luxo.calcular_diaria(fator_temporada=1.1) == 545.0  # 450*1.1 + 50 = 495 + 50 = 545


def test_ordenacao_natural_quartos_metodo_lt() -> None:
    """Testa a ordenação natural (__lt__): prioriza TipoQuarto, desempata por número."""
    q_luxo_1 = QuartoLuxo(numero=101)
    q_simples_1 = QuartoSimples(numero=205)
    q_simples_2 = QuartoSimples(numero=102)
    q_duplo_1 = QuartoDuplo(numero=150)

    quartos_desordenados = [q_luxo_1, q_simples_1, q_simples_2, q_duplo_1]
    quartos_ordenados = sorted(quartos_desordenados)

    # Esperado: Simples (102, 205), depois Duplo (150), depois Luxo (101)
    assert quartos_ordenados == [q_simples_2, q_simples_1, q_duplo_1, q_luxo_1]


def test_quarto_bloqueio_e_liberacao_manutencao(quarto_simples: QuartoSimples) -> None:
    """Testa a máquina de estados operacional de manutenção do quarto."""
    hoje = date.today()
    amanha = hoje + timedelta(days=1)

    quarto_simples.bloquear_manutencao(motivo="Pintura", inicio=hoje, fim=amanha)
    assert quarto_simples.status == StatusQuarto.MANUTENCAO
    assert quarto_simples.motivo_manutencao == "Pintura"

    quarto_simples.liberar_manutencao()
    assert quarto_simples.status == StatusQuarto.DISPONIVEL
    assert quarto_simples.motivo_manutencao is None

    # Tentar liberar um quarto que já está DISPONIVEL deve falhar
    with pytest.raises(TransicaoEstadoInvalidaException):
        quarto_simples.liberar_manutencao()


# =========================================================================== #
# 3. Testes de Pagamento e Adicional                                          #
# =========================================================================== #

def test_pagamento_criacao_e_validacao() -> None:
    """Testa a criação de transação de pagamento e validação de valores monetários."""
    pag = Pagamento(id_=1, valor=150.0, metodo=MetodoPagamento.PIX)
    assert pag.valor == 150.0
    assert pag.metodo == MetodoPagamento.PIX

    with pytest.raises(DadosInvalidosException):
        pag.valor = -10.0

    with pytest.raises(DadosInvalidosException):
        pag.valor = 0.0


def test_adicional_calculo_total_e_validacao() -> None:
    """Testa o cálculo do total de adicional (preco_unitario * quantidade)."""
    adc = Adicional(id_=1, descricao="Frigobar - Água", preco_unitario=6.50, quantidade=3)
    assert adc.total == 19.50

    with pytest.raises(DadosInvalidosException):
        Adicional(descricao="Café", preco_unitario=10.0, quantidade=0)

    with pytest.raises(DadosInvalidosException):
        Adicional(descricao="Café", preco_unitario=-5.0, quantidade=1)


# =========================================================================== #
# 4. Testes Centrais de Reserva                                               #
# =========================================================================== #

def test_criar_reserva_sucesso_e_metodo_len(hospede_padrao: Hospede, quarto_duplo: QuartoDuplo) -> None:
    """Testa a criação da reserva, cálculo de diárias e o método especial __len__."""
    entrada = date(2026, 11, 1)
    saida = date(2026, 11, 6)  # 5 diárias

    reserva = Reserva(
        id_=10,
        hospede=hospede_padrao,
        quarto=quarto_duplo,
        data_entrada=entrada,
        data_saida=saida,
        num_hospedes=2,
        valor_total_diarias=1250.0,
    )

    assert reserva.id == 10
    assert reserva.status == StatusReserva.PENDENTE
    assert reserva.total_diarias == 5
    assert len(reserva) == 5  # Dunder method __len__
    assert reserva.valor_total_devido == 1250.0
    assert reserva.saldo_devedor == 1250.0


def test_reserva_validacao_datas_invalidas(hospede_padrao: Hospede, quarto_simples: QuartoSimples) -> None:
    """Garante que data_saida <= data_entrada dispare DadosInvalidosException."""
    hoje = date.today()
    ontem = hoje - timedelta(days=1)

    # Data de saída anterior à entrada
    with pytest.raises(DadosInvalidosException):
        Reserva(hospede=hospede_padrao, quarto=quarto_simples, data_entrada=hoje, data_saida=ontem)

    # Datas iguais (estadia mínima de 1 noite)
    with pytest.raises(DadosInvalidosException):
        Reserva(hospede=hospede_padrao, quarto=quarto_simples, data_entrada=hoje, data_saida=hoje)


def test_reserva_capacidade_excedida(hospede_padrao: Hospede, quarto_simples: QuartoSimples) -> None:
    """Garante que num_hospedes > quarto.capacidade dispare CapacidadeExcedidaException."""
    assert quarto_simples.capacidade == 1

    with pytest.raises(CapacidadeExcedidaException):
        Reserva(
            hospede=hospede_padrao,
            quarto=quarto_simples,
            num_hospedes=2,  # Excede capacidade de 1
        )


def test_reserva_igualdade_metodo_eq(hospede_padrao: Hospede, quarto_duplo: QuartoDuplo) -> None:
    """Valida o método __eq__: duas reservas são iguais se dividem quarto e datas."""
    d1 = date(2026, 12, 1)
    d2 = date(2026, 12, 5)

    r1 = Reserva(id_=1, hospede=hospede_padrao, quarto=quarto_duplo, data_entrada=d1, data_saida=d2)
    r2 = Reserva(id_=2, hospede=hospede_padrao, quarto=quarto_duplo, data_entrada=d1, data_saida=d2)
    r3 = Reserva(id_=3, hospede=hospede_padrao, quarto=quarto_duplo, data_entrada=d1, data_saida=date(2026, 12, 6))

    assert r1 == r2  # Mesmo quarto e mesmo período
    assert r1 != r3  # Período diferente


def test_reserva_calculos_financeiros_e_saldo_devedor(hospede_padrao: Hospede, quarto_luxo: QuartoLuxo) -> None:
    """Testa a agregação de pagamentos, consumos adicionais e cálculo de saldo devedor."""
    reserva = Reserva(
        id_=1,
        hospede=hospede_padrao,
        quarto=quarto_luxo,
        valor_total_diarias=1000.0,
    )

    # Inicia com 1000 de saldo devedor
    assert reserva.valor_total_devido == 1000.0
    assert reserva.saldo_devedor == 1000.0

    # Lança pagamento de sinal (R$ 300)
    reserva.adicionar_pagamento(Pagamento(id_=1, valor=300.0, metodo=MetodoPagamento.PIX))
    assert reserva.total_pago == 300.0
    assert reserva.saldo_devedor == 700.0

    # Avança para CHECKIN para permitir consumo
    reserva.confirmar()
    reserva.realizar_checkin(horario=datetime.now())

    # Adiciona consumos extras
    reserva.adicionar_adicional(Adicional(id_=1, descricao="Restaurante", preco_unitario=150.0, quantidade=1))
    assert reserva.total_adicionais == 150.0
    assert reserva.valor_total_devido == 1150.0
    assert reserva.saldo_devedor == 850.0


def test_reserva_fluxo_checkout_e_bloqueio_saldo_devedor(hospede_padrao: Hospede, quarto_simples: QuartoSimples) -> None:
    """Testa o check-out e valida que pendências financeiras barram o encerramento."""
    reserva = Reserva(id_=1, hospede=hospede_padrao, quarto=quarto_simples, valor_total_diarias=200.0)
    reserva.confirmar()
    reserva.realizar_checkin(horario=datetime.now())

    # Tentar check-out sem quitar a dívida deve lançar PagamentoInsuficienteException
    with pytest.raises(PagamentoInsuficienteException):
        reserva.realizar_checkout(horario=datetime.now())

    # Quita o saldo devedor restante
    reserva.adicionar_pagamento(Pagamento(valor=200.0, metodo=MetodoPagamento.DEBITO))
    assert reserva.saldo_devedor == 0.0

    # Agora o check-out deve concluir com sucesso e liberar o quarto
    total_encerrado = reserva.realizar_checkout(horario=datetime.now())
    assert total_encerrado == 200.0
    assert reserva.status == StatusReserva.CHECKOUT
    assert quarto_simples.status == StatusQuarto.DISPONIVEL


# =========================================================================== #
# 5. Testes de Serialização (Mixin Serializavel)                              #
# =========================================================================== #

def test_serializacao_quarto_e_reserva(hospede_padrao: Hospede, quarto_luxo: QuartoLuxo) -> None:
    """Testa a exportação para dicionário (to_dict) e reconstrução (from_dict)."""
    #  Quarto
    dados_quarto = quarto_luxo.to_dict()
    assert dados_quarto["numero"] == 201
    assert dados_quarto["tipo"] == "LUXO"

    quarto_recriado = Quarto.from_dict(dados_quarto)
    assert isinstance(quarto_recriado, QuartoLuxo)
    assert quarto_recriado.numero == 201

    #  Reserva
    reserva = Reserva(
        id_=5,
        hospede=hospede_padrao,
        quarto=quarto_luxo,
        data_entrada=date(2026, 12, 20),
        data_saida=date(2026, 12, 25),
        num_hospedes=3,
        valor_total_diarias=2500.0,
    )
    dados_reserva = reserva.to_dict()
    assert dados_reserva["id"] == 5
    assert dados_reserva["num_hospedes"] == 3
    assert dados_reserva["status"] == "PENDENTE"

    reserva_recriada = Reserva.from_dict(dados_reserva)
    assert reserva_recriada.id == 5
    assert len(reserva_recriada) == 5
    assert reserva_recriada.quarto is not None
    assert reserva_recriada.quarto.numero == 201


def test_serializacao_reserva_com_historico_do_hospede_nao_recursa(hospede_padrao: Hospede, quarto_luxo: QuartoLuxo) -> None:
    """Serializa o relacionamento Reserva-Hospede sem expandir o ciclo."""
    reserva = Reserva(
        id_=7,
        hospede=hospede_padrao,
        quarto=quarto_luxo,
        data_entrada=date(2026, 12, 20),
        data_saida=date(2026, 12, 25),
    )
    hospede_padrao.vincular_reserva(reserva)

    dados = reserva.to_dict()

    assert dados["hospede"]["id"] == hospede_padrao.id
    assert dados["hospede"]["historico_reservas"] == [{"id": reserva.id}]
