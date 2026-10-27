
from datetime import date, datetime,timedelta, time
from typing import Optional
import json
from pathlib import Path

from src.models.payment import Pagamento, Adicional
from src.models.person import Hospede
from src.models.reservation import Reserva
from src.models.room import Quarto
from src.models.enums import (
    MetodoPagamento,
    OrigemReserva,
    StatusQuarto,
    StatusReserva,
    TipoQuarto,
)
from src.models.exceptions import (
    DadosInvalidosException,
    PagamentoInsuficienteException,
    QuartoIndisponivelException,
    TransicaoEstadoInvalidaException,
    CapacidadeExcedidaException
)
from src.services.rates import CalculadoraTarifa
from src.services.reports import ServicoRelatorios
from src.database import data

class Hotel:
    """Orquestrador central da camada de serviços do sistema hoteleiro.

    Coordena o cadastro de quartos e hóspedes, a busca de disponibilidade, a
    criação de reservas sem conflitos (prevenção de overbooking) e os fluxos
    de check-in, check-out, cancelamento, no-show e geração de relatórios.
    """

    def __init__(self, settings: dict | None = None) -> None:
        """Inicializa o hotel carregando as configurações do settings.json."""
        if settings is not None:
            self._settings = settings
        else:
            caminho_settings = Path(__file__).resolve().parent.parent.parent / "settings.json"
            if caminho_settings.exists():
                with open(caminho_settings, "r", encoding="utf-8") as f:
                    self._settings = json.load(f)
            else:
                self._settings = {}

    # =========================================================================
    #  Cadastros e Quartos
    # =========================================================================
    def cadastrar_quarto(self, quarto: Quarto) -> None:
        """Cadastra um novo quarto no hotel e salva no banco."""

        if not isinstance(quarto, Quarto):
            raise DadosInvalidosException("O objeto quarto fornecido é inválido.")
        data.salvar_quarto(quarto)

    def cadastrar_hospede(self, hospede: Hospede) -> int:
        """Cadastra um hóspede no hotel e retorna o ID gerado."""
        if not isinstance(hospede, Hospede):
            raise DadosInvalidosException("O objeto hóspede fornecido é inválido.")
        novo_id = data.salvar_hospede(hospede)
        hospede.id = novo_id
        return novo_id

    def bloquear_quarto(self, numero: int, motivo: str, inicio: date, fim: date) -> None:
        """Interdita um quarto para manutenção e atualiza o banco."""
        quarto = data.buscar_quarto(numero)
        if quarto is None:
            raise DadosInvalidosException(f"Quarto {numero} não encontrado.")
        quarto.bloquear_manutencao(motivo, inicio, fim)
        data.salvar_quarto(quarto)

    def desbloquear_quarto(self, numero: int) -> None:
        """Libera o quarto da manutenção para DISPONIVEL."""
        quarto = data.buscar_quarto(numero)
        if quarto is None:
            raise DadosInvalidosException(f"Quarto {numero} não encontrado.")
        
        quarto.liberar_manutencao()
        data.salvar_quarto(quarto)

    def buscar_quartos_disponiveis(self, inicio: date, fim: date, tipo: TipoQuarto | None = None) -> list[Quarto]:
        """Retorna quartos que não possuem reservas ativas nem manutenção no período."""

        if (
            not isinstance(inicio, date)
            or not isinstance(fim, date)
            or isinstance(inicio, datetime)
            or isinstance(fim, datetime)
        ):
            raise DadosInvalidosException("Início e fim devem ser datas do tipo date.")
        if inicio >= fim:
            raise DadosInvalidosException("A data de início deve ser anterior à data de saída.")
        quartos = data.listar_quartos()
        if tipo is not None:
            quartos = [q for q in quartos if q.tipo == tipo]
        quartos_ocupados = data.buscar_quartos_ocupados_no_periodo(inicio, fim)
        disponiveis = []
        for q in quartos:
            # Se tem reserva conflitante, não está disponível
            if q.numero in quartos_ocupados:
                continue
            # Se está bloqueado administrativamente, não está disponível
            if q.status == StatusQuarto.BLOQUEADO:
                continue
            # Se está em manutenção e colide com as datas solicitadas
            if q.status == StatusQuarto.MANUTENCAO:
                if q.inicio_manutencao and q.fim_manutencao:
                    if inicio < q.fim_manutencao and fim > q.inicio_manutencao:
                        continue
                else:
                    continue
            disponiveis.append(q)
        return disponiveis

    # =========================================================================
    # Ciclo de Vida da Reserva 
    # =========================================================================
    def criar_reserva(
        self,
        hospede_id: int,
        quarto_num: int,
        entrada: date,
        saida: date,
        num_hospedes: int,
        origem: OrigemReserva = OrigemReserva.BALCAO
    ) -> Reserva:
        """Cria reserva validando overbooking e calculando tarifas dinâmicas."""

        if (
            not isinstance(entrada, date)
            or not isinstance(saida, date)
            or isinstance(entrada, datetime)
            or isinstance(saida, datetime)
        ):
            raise DadosInvalidosException("Entrada e saída devem ser datas do tipo date.")
        if entrada >= saida:
            raise DadosInvalidosException("A data de entrada deve ser anterior à data de saída.")
        if not isinstance(num_hospedes, int) or num_hospedes < 1:
            raise DadosInvalidosException("O número de hóspedes deve ser pelo menos 1.")
        hospede = data.buscar_hospede(hospede_id)
        if hospede is None:
            raise DadosInvalidosException(f"Hóspede {hospede_id} não encontrado.")
        quarto = data.buscar_quarto(quarto_num)
        if quarto is None:
            raise DadosInvalidosException(f"Quarto {quarto_num} não encontrado.")
        if num_hospedes > quarto.capacidade:
            raise CapacidadeExcedidaException(
                f"O número de hóspedes ({num_hospedes}) excede a capacidade do quarto ({quarto.capacidade})."
            )
        # Prevenção de Overbooking
        disponiveis = self.buscar_quartos_disponiveis(entrada, saida)
        if not any(q.numero == quarto_num for q in disponiveis):
            raise QuartoIndisponivelException(
                f"O quarto {quarto_num} não está disponível entre {entrada} e {saida}."
            )
        # Cálculo dinâmico das diárias
        total_diarias = CalculadoraTarifa.calcular_total_reserva(
            quarto=quarto,
            inicio=entrada,
            fim=saida,
            settings=self._settings,
        )
        reserva = Reserva(
            id_=0,
            hospede=hospede,
            quarto=quarto,
            data_entrada=entrada,
            data_saida=saida,
            num_hospedes=num_hospedes,
            origem=origem,
            valor_total_diarias=total_diarias,
            status=StatusReserva.CONFIRMADA,
        )
        novo_id = data.salvar_reserva(reserva)
        reserva.id = novo_id
        return reserva

    def processar_checkin(self, reserva_id: int, momento: datetime) -> None:
        """Efetua check-in validando tolerância, status CONFIRMADA e quarto livre."""

        if not isinstance(reserva_id, int) or reserva_id <= 0:
            raise DadosInvalidosException("O ID da reserva deve ser um número inteiro positivo.")
        if not isinstance(momento, datetime):
            raise DadosInvalidosException("O momento de check-in deve ser uma instância de datetime.")
        reserva = data.buscar_reserva(reserva_id)
        if reserva is None:
            raise DadosInvalidosException(f"Reserva {reserva_id} não encontrada.")
        
        # Validação de janela e tolerância
        config_horarios = self._settings.get("entrada_e_saida", {})
        hora_str = config_horarios.get("checkIn_a_partir", "14:00")
        tolerancia_min = int(config_horarios.get("tolerancia_min", 30))
        h, m = map(int, hora_str.split(":"))
        horario_padrao = datetime.combine(reserva.data_entrada, time(h, m))
        horario_minimo = horario_padrao - timedelta(minutes=tolerancia_min)

        if momento < horario_minimo:
            raise DadosInvalidosException(
                f"Check-in antecipado não permitido. Horário mínimo: {horario_minimo}."
            )
        reserva.realizar_checkin(momento, tolerancia_min=tolerancia_min)
        data.salvar_reserva(reserva)
        if reserva.quarto:
            data.salvar_quarto(reserva.quarto)

    def processar_checkout(self, reserva_id: int, momento: datetime) -> float:
        """Efetua check-out calculando diárias extras e barrando se houver dívida."""

        if not isinstance(reserva_id, int) or reserva_id <= 0:
            raise DadosInvalidosException("O ID da reserva deve ser um número inteiro positivo.")
        if not isinstance(momento, datetime):
            raise DadosInvalidosException("O momento de check-out deve ser uma instância de datetime.")
        reserva = data.buscar_reserva(reserva_id)
        if reserva is None:
            raise DadosInvalidosException(f"Reserva {reserva_id} não encontrada.")
        
        # Validação de janela e atraso
        config_horarios = self._settings.get("entrada_e_saida", {})
        hora_str = config_horarios.get("checkOut_ate", "12:00")
        tolerancia_min = int(config_horarios.get("tolerancia_min", 30))
        h, m = map(int, hora_str.split(":"))
        horario_padrao = datetime.combine(reserva.data_saida, time(h, m))
        horario_limite = horario_padrao + timedelta(minutes=tolerancia_min)
        taxa_multa_atraso = 0.0

        if momento > horario_limite:
            # Cobrança de diária extra pelo atraso
            taxa_multa_atraso = reserva.quarto.calcular_diaria() if reserva.quarto else 0.0
        total_devido = reserva.realizar_checkout(momento, taxa_multa_atraso=taxa_multa_atraso)
        data.salvar_reserva(reserva)
        if reserva.quarto:
            data.salvar_quarto(reserva.quarto)
        return total_devido

    def processar_cancelamento(self, reserva_id: int, momento: datetime | None = None) -> float:
        """Cancela a reserva aplicando multa de 50% se for feito em < 48h."""

        if not isinstance(reserva_id, int) or reserva_id <= 0:
            raise DadosInvalidosException("O ID da reserva deve ser um número inteiro positivo.")
        if momento is not None and not isinstance(momento, datetime):
            raise DadosInvalidosException("O momento do cancelamento deve ser uma instância de datetime.")
        reserva = data.buscar_reserva(reserva_id)
        if reserva is None:
            raise DadosInvalidosException(f"Reserva {reserva_id} não encontrada.")
        
        momento_cancelamento = momento or datetime.now()
        config_multa = self._settings.get("multa_de_cancelamento", {})
        horas_antecedencia = float(config_multa.get("horas_antecedencia", 48))
        percentual_multa = float(config_multa.get("percentual", 0.5))
        config_horarios = self._settings.get("entrada_e_saida", {})
        hora_str = config_horarios.get("checkIn_a_partir", "14:00")
        h, m = map(int, hora_str.split(":"))
        horario_previsto_checkin = datetime.combine(reserva.data_entrada, time(h, m))
        limite_sem_multa = horario_previsto_checkin - timedelta(hours=horas_antecedencia)

        if momento_cancelamento > limite_sem_multa:
            multa = round(reserva.valor_total_diarias * percentual_multa, 2)
        else:
            multa = 0.0
        valor_multa = reserva.cancelar(taxa_multa=multa)
        data.salvar_reserva(reserva)
        if reserva.quarto:
            data.salvar_quarto(reserva.quarto)
        return valor_multa

    def processar_noshows(self, momento_atual: datetime) -> list[int]:
        """Varre reservas não comparecidas após a tolerância e libera os quartos."""

        if not isinstance(momento_atual, datetime):
            raise DadosInvalidosException("O momento atual deve ser uma instância de datetime.")
        
        cfg_noshow = self._settings.get("tolerancia_no_show", {})
        minutos_tolerancia = int(cfg_noshow.get("minutos", 120))
        cfg_horarios = self._settings.get("entrada_e_saida", {})
        hora_str = cfg_horarios.get("checkIn_a_partir", "14:00")
        h, m = map(int, hora_str.split(":"))
        reservas_confirmadas = data.listar_reservas(status="CONFIRMADA")
        noshows_processados: list[int] = []

        for reserva in reservas_confirmadas:
            horario_previsto = datetime.combine(reserva.data_entrada, time(h, m))
            horario_limite = horario_previsto + timedelta(minutes=minutos_tolerancia)
            if momento_atual > horario_limite:
                reserva.marcar_noshow()
                data.salvar_reserva(reserva)
                if reserva.quarto:
                    data.salvar_quarto(reserva.quarto)
                noshows_processados.append(reserva.id)
        return noshows_processados

    # =========================================================================
    # Pagamentos e Consumo Extra
    # =========================================================================
    def registrar_pagamento(self, reserva_id: int, valor: float, metodo: MetodoPagamento) -> Pagamento:
        """Registra um pagamento (PIX/Cartão/Dinheiro) na reserva e grava no banco."""
        pass

    def lancar_adicional(self, reserva_id: int, descricao: str, preco: float, quantidade: int = 1) -> Adicional:
        """Lança consumo (frigobar, refeição) na reserva em estadia ativa."""
        pass
