"""Fluxos HTTP completos do hotel, com serviços reais e SQLite temporário."""

import pytest
from fastapi.testclient import TestClient

from src.api import app as app_module
from src.api import routes
from src.database import data
from src.database.connection import inicializar_banco, obter_conexao
from src.database.seed import executar_seed
from src.services.hotel import Hotel


@pytest.fixture
def cliente(tmp_path, monkeypatch):
    """Executa o lifespan real sem acessar hotel.db, inclusive durante o seed."""
    caminho = tmp_path / "api_teste.db"
    monkeypatch.setattr(data, "obter_conexao", lambda: obter_conexao(caminho))
    monkeypatch.setattr(app_module, "inicializar_banco", lambda: inicializar_banco(caminho))
    monkeypatch.setattr(app_module, "executar_seed", lambda: executar_seed(caminho))
    # Configurações fixas tornam os resultados independentes do settings.json e do relógio.
    monkeypatch.setattr(routes, "_hotel", Hotel(settings={
        "entrada_e_saida": {
            "checkIn_a_partir": "14:00", "checkOut_ate": "12:00", "tolerancia_min": 30,
        },
        "multa_de_cancelamento": {"horas_antecedencia": 48, "percentual": 0.5},
        "tolerancia_no_show": {"horario_referencia": "23:59", "minutos": 120},
    }))

    with TestClient(app_module.app) as client:
        yield client


def enviar(cliente, metodo, caminho, status=200, **kwargs):
    """Exibe o corpo da resposta quando uma etapa do atendimento falha."""
    resposta = cliente.request(metodo, caminho, **kwargs)
    assert resposta.status_code == status, (
        f"{metodo} {caminho}: esperado {status}, recebido "
        f"{resposta.status_code}: {resposta.text}"
    )
    assert resposta.headers["content-type"].startswith("application/json")
    return resposta.json()


def cadastrar_hospede(cliente, **alteracoes):
    dados = {
        "nome": "Maria Silva", "documento": "123456789",
        "email": "maria@example.com", "telefone": "88999999999",
        "preferencias": "Quarto silencioso",
    }
    dados.update(alteracoes)
    return enviar(cliente, "POST", "/hospedes", status=201, json=dados)


def cadastrar_quarto(cliente, **alteracoes):
    dados = {"numero": 901, "tipo": "SIMPLES", "capacidade": 2, "tarifa_base": 200.0}
    dados.update(alteracoes)
    return enviar(cliente, "POST", "/quartos", status=201, json=dados)


def dados_reserva(hospede_id, **alteracoes):
    dados = {
        "hospede_id": hospede_id, "quarto_num": 901,
        "entrada": "2026-11-10", "saida": "2026-11-12",
        "num_hospedes": 2, "origem": "BALCAO",
    }
    dados.update(alteracoes)
    return dados


@pytest.fixture
def reserva(cliente):
    """Prepara o atendimento pela própria API, sem inserir reservas por SQL."""
    cadastrar_quarto(cliente)
    hospede = cadastrar_hospede(cliente)
    return enviar(cliente, "POST", "/reservas", status=201,
                  json=dados_reserva(hospede["id"]))


def numeros_disponiveis(cliente, **alteracoes):
    parametros = {"entrada": "2026-11-10", "saida": "2026-11-12"}
    parametros.update(alteracoes)
    quartos = enviar(cliente, "GET", "/quartos/disponiveis", params=parametros)
    return {quarto["numero"] for quarto in quartos}


# =========================================================================
# Percorre os 14 endpoints da aplicação
# =========================================================================

def test_fluxo_completo_de_atendimento_percorre_todos_os_endpoints(cliente):
    quarto = cadastrar_quarto(cliente)
    assert quarto["status"] == "DISPONIVEL"

    bloqueado = enviar(cliente, "PATCH", "/quartos/901/bloquear", json={
        "motivo": "Pintura", "inicio": "2026-11-10", "fim": "2026-11-12",
    })
    assert bloqueado["status"] == "MANUTENCAO"
    assert bloqueado["inicio_manutencao"] == "2026-11-10"
    assert 901 not in numeros_disponiveis(cliente)
    assert 901 in numeros_disponiveis(cliente, entrada="2026-11-13", saida="2026-11-14")

    liberado = enviar(cliente, "PATCH", "/quartos/901/desbloquear")
    assert liberado["status"] == "DISPONIVEL"
    assert liberado["motivo_manutencao"] is None
    assert liberado["fim_manutencao"] is None

    hospede = cadastrar_hospede(cliente)
    assert hospede["id"] > 0
    criada = enviar(cliente, "POST", "/reservas", status=201,
                    json=dados_reserva(hospede["id"]))
    reserva_id = criada["id"]
    assert criada["status"] == "CONFIRMADA"
    assert criada["valor_total_diarias"] == 400.0
    assert criada["hospede"]["id"] == hospede["id"]
    assert criada["quarto"]["numero"] == 901
    assert 901 not in numeros_disponiveis(cliente)

    checkin = enviar(cliente, "POST", f"/reservas/{reserva_id}/checkin",
                     json={"momento": "2026-11-10T14:00:00"})
    assert checkin["status"] == "CHECKIN"
    assert checkin["quarto"]["status"] == "OCUPADO"
    assert checkin["checkin_real"] == "2026-11-10T14:00:00"

    adicional = enviar(cliente, "POST", f"/reservas/{reserva_id}/adicionais", status=201,
                       json={"descricao": "Água do frigobar", "preco": 10.0, "quantidade": 2})
    assert adicional["total"] == 20.0
    pagamento = enviar(cliente, "POST", f"/reservas/{reserva_id}/pagamentos", status=201,
                       json={"valor": 420.0, "metodo": "PIX"})
    assert pagamento["valor"] == 420.0
    assert pagamento["metodo"] == "PIX"

    checkout = enviar(cliente, "POST", f"/reservas/{reserva_id}/checkout",
                      json={"momento": "2026-11-12T12:00:00"})
    assert checkout["status"] == "CHECKOUT"
    assert checkout["total_devido"] == 420.0
    assert checkout["quarto"]["status"] == "DISPONIVEL"
    assert len(checkout["adicionais"]) == len(checkout["pagamentos"]) == 1
    assert checkout["checkout_real"] == "2026-11-12T12:00:00"
    assert data.buscar_reserva(reserva_id).saldo_devedor == 0.0
    assert data.buscar_quarto(901).status.value == "DISPONIVEL"
    assert 901 in numeros_disponiveis(cliente, entrada="2026-11-12", saida="2026-11-14")

    ocupacao = enviar(cliente, "GET", "/relatorios/ocupacao",
                      params={"inicio": "2026-11-10", "fim": "2026-11-12"})
    # O seed cria oito quartos; com o novo quarto, duas noites em 18 possíveis.
    assert ocupacao["taxa_ocupacao"] == pytest.approx(11.11)
    financeiro = enviar(cliente, "GET", "/relatorios/financeiro",
                        params={"inicio": "2026-11-12", "fim": "2026-11-13"})
    assert financeiro["receita_total"] == 420.0
    assert financeiro["quantidade_reservas"] == 1

    # O mesmo quarto volta a ser usado em atendimentos posteriores.
    cancelavel = enviar(cliente, "POST", "/reservas", status=201, json=dados_reserva(
        hospede["id"], entrada="2026-11-14", saida="2026-11-16"
    ))
    cancelada = enviar(cliente, "POST", f"/reservas/{cancelavel['id']}/cancelar",
                      json={"momento": "2026-11-13T14:00:00"})
    assert cancelada["status"] == "CANCELADA"
    assert cancelada["multa"] == 200.0

    ausente = enviar(cliente, "POST", "/reservas", status=201, json=dados_reserva(
        hospede["id"], entrada="2026-11-20", saida="2026-11-22"
    ))
    noshows = enviar(cliente, "POST", "/reservas/noshows",
                     json={"momento_atual": "2026-11-21T02:00:00"})
    assert noshows == {"reservas_processadas": [ausente["id"]], "quantidade": 1}
    assert data.buscar_reserva(ausente["id"]).status.value == "NO_SHOW"
    assert 901 in numeros_disponiveis(cliente, entrada="2026-11-20", saida="2026-11-22")
    # Cancelamentos e no-shows não entram na receita de estadias finalizadas.
    financeiro = enviar(cliente, "GET", "/relatorios/financeiro",
                        params={"inicio": "2026-11-01", "fim": "2026-12-01"})
    assert financeiro["receita_total"] == 420.0
    assert financeiro["quantidade_reservas"] == 1


# =========================================================================
# Regras que devem impedir operações ou cobrar os valores corretos
# =========================================================================

def test_checkout_com_divida_nao_libera_quarto_e_aceita_quitacao(cliente, reserva):
    caminho = f"/reservas/{reserva['id']}"
    enviar(cliente, "POST", caminho + "/checkin", json={"momento": "2026-11-10T14:00:00"})
    enviar(cliente, "POST", caminho + "/pagamentos", status=201,
           json={"valor": 100.0, "metodo": "DINHEIRO"})
    enviar(cliente, "POST", caminho + "/checkout", status=402,
           json={"momento": "2026-11-12T12:00:00"})

    persistida = data.buscar_reserva(reserva["id"])
    assert persistida.status.value == "CHECKIN"
    assert persistida.checkout_real is None
    assert persistida.saldo_devedor == 300.0
    assert data.buscar_quarto(901).status.value == "OCUPADO"
    enviar(cliente, "POST", caminho + "/pagamentos", status=201,
           json={"valor": 300.0, "metodo": "CREDITO"})
    resposta = enviar(cliente, "POST", caminho + "/checkout",
                      json={"momento": "2026-11-12T12:00:00"})
    assert resposta["status"] == "CHECKOUT"
    assert resposta["total_devido"] == 400.0


@pytest.mark.parametrize("momento, total", [
    ("2026-11-12T12:30:00", 400.0),
    ("2026-11-12T12:31:00", 600.0),
])
def test_checkout_respeita_tolerancia_e_persiste_multa(cliente, reserva, momento, total):
    caminho = f"/reservas/{reserva['id']}"
    enviar(cliente, "POST", caminho + "/checkin", json={"momento": "2026-11-10T14:00:00"})
    enviar(cliente, "POST", caminho + "/pagamentos", status=201,
           json={"valor": total, "metodo": "PIX"})
    resposta = enviar(cliente, "POST", caminho + "/checkout", json={"momento": momento})
    assert resposta["total_devido"] == total
    assert data.buscar_reserva(reserva["id"]).valor_total_devido == total


@pytest.mark.parametrize("momento, multa", [
    ("2026-11-08T14:00:00", 0.0),
    ("2026-11-08T14:01:00", 200.0),
])
def test_cancelamento_respeita_limite_de_48h_e_libera_periodo(cliente, reserva, momento, multa):
    resposta = enviar(cliente, "POST", f"/reservas/{reserva['id']}/cancelar",
                      json={"momento": momento})
    assert resposta["multa"] == multa
    assert data.buscar_reserva(reserva["id"]).status.value == "CANCELADA"
    assert 901 in numeros_disponiveis(cliente)
    for relatorio, campo in [("ocupacao", "taxa_ocupacao"), ("financeiro", "receita_total")]:
        resultado = enviar(cliente, "GET", f"/relatorios/{relatorio}",
                           params={"inicio": "2026-11-10", "fim": "2026-11-13"})
        assert resultado[campo] == 0.0


def test_noshow_respeita_tolerancia_e_nao_processa_duas_vezes(cliente, reserva):
    ainda_no_dia = enviar(cliente, "POST", "/reservas/noshows",
                          json={"momento_atual": "2026-11-10T16:01:00"})
    assert ainda_no_dia == {"reservas_processadas": [], "quantidade": 0}
    antes = enviar(cliente, "POST", "/reservas/noshows",
                   json={"momento_atual": "2026-11-11T01:59:00"})
    assert antes == {"reservas_processadas": [], "quantidade": 0}
    assert data.buscar_reserva(reserva["id"]).status.value == "CONFIRMADA"
    assert 901 not in numeros_disponiveis(cliente)
    depois = enviar(cliente, "POST", "/reservas/noshows",
                    json={"momento_atual": "2026-11-11T01:59:01"})
    assert depois == {"reservas_processadas": [reserva["id"]], "quantidade": 1}
    assert data.buscar_reserva(reserva["id"]).status.value == "NO_SHOW"
    assert 901 in numeros_disponiveis(cliente)
    repetida = enviar(cliente, "POST", "/reservas/noshows",
                      json={"momento_atual": "2026-11-11T02:00:00"})
    assert repetida == {"reservas_processadas": [], "quantidade": 0}


def test_noshow_processa_somente_confirmadas_e_preserva_quarto_ocupado(cliente, reserva):
    em_estadia = enviar(cliente, "POST", "/reservas", status=201,
                        json=dados_reserva(reserva["hospede"]["id"], quarto_num=101, num_hospedes=1))
    enviar(cliente, "POST", f"/reservas/{em_estadia['id']}/checkin",
           json={"momento": "2026-11-10T14:00:00"})
    cancelavel = enviar(cliente, "POST", "/reservas", status=201,
                        json=dados_reserva(reserva["hospede"]["id"], quarto_num=102, num_hospedes=1))
    enviar(cliente, "POST", f"/reservas/{cancelavel['id']}/cancelar",
           json={"momento": "2026-11-08T14:00:00"})

    resposta = enviar(cliente, "POST", "/reservas/noshows",
                      json={"momento_atual": "2026-11-11T02:00:00"})
    assert resposta == {"reservas_processadas": [reserva["id"]], "quantidade": 1}
    assert data.buscar_reserva(reserva["id"]).status.value == "NO_SHOW"
    assert data.buscar_reserva(em_estadia["id"]).status.value == "CHECKIN"
    assert data.buscar_reserva(cancelavel["id"]).status.value == "CANCELADA"
    assert data.buscar_quarto(101).status.value == "OCUPADO"
    assert data.buscar_quarto(901).status.value == "DISPONIVEL"


def test_reserva_conflitante_e_capacidade_excedida_nao_gravam_dados(cliente, reserva):
    enviar(cliente, "POST", "/reservas", status=400,
           json=dados_reserva(reserva["hospede"]["id"]))
    enviar(cliente, "POST", "/reservas", status=400,
           json=dados_reserva(reserva["hospede"]["id"], num_hospedes=3))
    assert len(data.listar_reservas()) == 1


def test_checkin_antecipado_e_operacoes_fora_da_estadia_sao_recusados(cliente, reserva):
    caminho = f"/reservas/{reserva['id']}"
    enviar(cliente, "POST", caminho + "/checkin", status=400,
           json={"momento": "2026-11-10T13:29:00"})
    enviar(cliente, "POST", caminho + "/checkout", status=400,
           json={"momento": "2026-11-12T12:00:00"})
    enviar(cliente, "POST", caminho + "/adicionais", status=400,
           json={"descricao": "Água", "preco": 10.0, "quantidade": 1})
    assert data.buscar_reserva(reserva["id"]).status.value == "CONFIRMADA"
    assert data.buscar_reserva(reserva["id"]).adicionais == []
    # O minuto exato do início da tolerância já deve permitir o check-in.
    enviar(cliente, "POST", caminho + "/checkin", json={"momento": "2026-11-10T13:30:00"})
    enviar(cliente, "POST", caminho + "/checkin", status=400,
           json={"momento": "2026-11-10T14:00:00"})
    enviar(cliente, "POST", caminho + "/cancelar", status=400,
           json={"momento": "2026-11-10T14:00:00"})
    enviar(cliente, "PATCH", "/quartos/901/bloquear", status=400,
           json={"motivo": "Pintura", "inicio": "2026-11-10", "fim": "2026-11-12"})
    noshows = enviar(cliente, "POST", "/reservas/noshows",
                     json={"momento_atual": "2026-11-10T18:00:00"})
    assert noshows["quantidade"] == 0
    assert data.buscar_quarto(901).status.value == "OCUPADO"


@pytest.mark.parametrize("tipo, extras, total", [
    ("SIMPLES", {}, 400.0),
    ("DUPLO", {"tem_varanda": True}, 460.0),
    ("LUXO", {"tem_hidromassagem": True, "taxa_servico_adicional": 50.0}, 500.0),
])
def test_categorias_atributos_e_tarifas_pela_api(cliente, tipo, extras, total):
    quarto = cadastrar_quarto(cliente, tipo=tipo, **extras)
    for campo, valor in extras.items():
        assert quarto[campo] == valor
    assert 901 in numeros_disponiveis(cliente, tipo=tipo)
    outro_tipo = "LUXO" if tipo != "LUXO" else "SIMPLES"
    assert 901 not in numeros_disponiveis(cliente, tipo=outro_tipo)
    hospede = cadastrar_hospede(cliente)
    reserva = enviar(cliente, "POST", "/reservas", status=201,
                     json=dados_reserva(hospede["id"]))
    assert reserva["valor_total_diarias"] == total


def test_cadastros_duplicados_preservam_dados_originais(cliente):
    cadastrar_quarto(cliente)
    enviar(cliente, "POST", "/quartos", status=409, json={
        "numero": 901, "tipo": "LUXO", "capacidade": 4, "tarifa_base": 900.0,
    })
    hospede = cadastrar_hospede(cliente)
    enviar(cliente, "POST", "/hospedes", status=409, json={
        "nome": "Outra pessoa", "documento": hospede["documento"],
        "email": "outra@example.com", "telefone": "88999999999",
    })
    assert data.buscar_quarto(901).tipo.value == "SIMPLES"
    assert data.buscar_hospede(hospede["id"]).nome == "Maria Silva"


def test_relatorio_financeiro_respeita_data_real_e_limites(cliente, reserva):
    caminho = f"/reservas/{reserva['id']}"
    enviar(cliente, "POST", caminho + "/checkin", json={"momento": "2026-11-10T14:00:00"})
    # A saída real é um dia após a prevista e gera uma diária extra.
    enviar(cliente, "POST", caminho + "/pagamentos", status=201,
           json={"valor": 600.0, "metodo": "PIX"})
    enviar(cliente, "POST", caminho + "/checkout", json={"momento": "2026-11-13T10:00:00"})
    excluido = enviar(cliente, "GET", "/relatorios/financeiro",
                      params={"inicio": "2026-11-12", "fim": "2026-11-13"})
    incluido = enviar(cliente, "GET", "/relatorios/financeiro",
                      params={"inicio": "2026-11-13", "fim": "2026-11-14"})
    assert excluido["receita_total"] == 0.0
    assert excluido["quantidade_reservas"] == 0
    assert incluido["receita_total"] == 600.0
    assert incluido["quantidade_reservas"] == 1


# =========================================================================
# Recursos inexistentes e validação das entradas
# =========================================================================

@pytest.mark.parametrize("operacao, payload", [
    ("checkin", {"momento": "2026-11-10T14:00:00"}),
    ("checkout", {"momento": "2026-11-12T12:00:00"}),
    ("cancelar", {}),
    ("pagamentos", {"valor": 100.0, "metodo": "PIX"}),
    ("adicionais", {"descricao": "Água", "preco": 10.0, "quantidade": 1}),
])
def test_reserva_inexistente_retorna_404(cliente, operacao, payload):
    enviar(cliente, "POST", f"/reservas/99999/{operacao}", status=404, json=payload)


@pytest.mark.parametrize("operacao, payload", [
    ("bloquear", {"motivo": "Pintura", "inicio": "2026-11-10", "fim": "2026-11-12"}),
    ("desbloquear", None),
])
def test_quarto_inexistente_retorna_404(cliente, operacao, payload):
    enviar(cliente, "PATCH", f"/quartos/99999/{operacao}", status=404, json=payload)


@pytest.mark.parametrize("campo", ["hospede_id", "quarto_num"])
def test_criacao_com_referencia_inexistente_retorna_404(cliente, reserva, campo):
    payload = dados_reserva(reserva["hospede"]["id"])
    payload[campo] = 99999
    enviar(cliente, "POST", "/reservas", status=404, json=payload)
    assert len(data.listar_reservas()) == 1


@pytest.mark.parametrize("operacao, payload", [
    ("pagamentos", {"valor": 0, "metodo": "PIX"}),
    ("pagamentos", {"valor": 100.0, "metodo": "BOLETO"}),
    ("adicionais", {"descricao": "Água", "preco": 0, "quantidade": 1}),
    ("adicionais", {"descricao": "Água", "preco": 10, "quantidade": 0}),
    ("checkin", {"momento": "horario-invalido"}),
])
def test_entradas_invalidas_retornam_422_sem_alterar_reserva(cliente, reserva, operacao, payload):
    resposta = enviar(cliente, "POST", f"/reservas/{reserva['id']}/{operacao}",
                      status=422, json=payload)
    assert isinstance(resposta["detail"], list)
    persistida = data.buscar_reserva(reserva["id"])
    assert persistida.status.value == "CONFIRMADA"
    assert persistida.pagamentos == persistida.adicionais == []


@pytest.mark.parametrize("relatorio", ["ocupacao", "financeiro"])
def test_relatorios_rejeitam_periodos_invalidos(cliente, relatorio):
    enviar(cliente, "GET", f"/relatorios/{relatorio}", status=400,
           params={"inicio": "2026-11-12", "fim": "2026-11-10"})
    enviar(cliente, "GET", f"/relatorios/{relatorio}", status=422,
           params={"inicio": "data-invalida", "fim": "2026-11-12"})


@pytest.mark.parametrize("alteracoes, status", [
    ({"entrada": "data-invalida"}, 422),
    ({"num_hospedes": 0}, 422),
    ({"saida": "2026-11-10"}, 400),
    ({"saida": "2026-11-09"}, 400),
])
def test_reserva_com_dados_invalidos_nao_e_criada(cliente, reserva, alteracoes, status):
    enviar(cliente, "POST", "/reservas", status=status,
           json=dados_reserva(reserva["hospede"]["id"], **alteracoes))
    assert len(data.listar_reservas()) == 1


def test_manutencao_impede_nova_reserva_e_periodo_invalido_nao_altera_bloqueio(cliente):
    cadastrar_quarto(cliente)
    hospede = cadastrar_hospede(cliente)
    enviar(cliente, "PATCH", "/quartos/901/bloquear", json={
        "motivo": "Pintura", "inicio": "2026-11-10", "fim": "2026-11-12",
    })
    enviar(cliente, "POST", "/reservas", status=400,
           json=dados_reserva(hospede["id"]))
    enviar(cliente, "PATCH", "/quartos/901/bloquear", status=400, json={
        "motivo": "Outro bloqueio", "inicio": "2026-11-12", "fim": "2026-11-10",
    })
    assert data.listar_reservas() == []
    assert data.buscar_quarto(901).motivo_manutencao == "Pintura"


@pytest.mark.parametrize("campo", ["numero", "capacidade", "tarifa_base"])
def test_cadastro_de_quarto_com_valor_zero_retorna_422(cliente, campo):
    dados = {"numero": 901, "tipo": "SIMPLES", "capacidade": 2, "tarifa_base": 200.0}
    dados[campo] = 0
    enviar(cliente, "POST", "/quartos", status=422, json=dados)
    assert data.buscar_quarto(901) is None
