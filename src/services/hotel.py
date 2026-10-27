
from datetime import date, datetime
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
        pass

    def processar_checkin(self, reserva_id: int, momento: datetime) -> None:
        """Efetua check-in validando tolerância, status CONFIRMADA e quarto livre."""
        pass

    def processar_checkout(self, reserva_id: int, momento: datetime) -> float:
        """Efetua check-out calculando diárias extras e barrando se houver dívida."""
        pass

    def processar_cancelamento(self, reserva_id: int, momento: datetime | None = None) -> float:
        """Cancela a reserva aplicando multa de 50% se for feito em < 48h."""
        pass

    def processar_noshows(self, momento_atual: datetime) -> list[int]:
        """Varre reservas não comparecidas após a tolerância e libera os quartos."""
        pass

    # =========================================================================
    # Pagamentos e Consumo Extra
    # =========================================================================
    def registrar_pagamento(self, reserva_id: int, valor: float, metodo: MetodoPagamento) -> Pagamento:
        """Registra um pagamento (PIX/Cartão/Dinheiro) na reserva e grava no banco."""
        pass

    def lancar_adicional(self, reserva_id: int, descricao: str, preco: float, quantidade: int = 1) -> Adicional:
        """Lança consumo (frigobar, refeição) na reserva em estadia ativa."""
        pass
