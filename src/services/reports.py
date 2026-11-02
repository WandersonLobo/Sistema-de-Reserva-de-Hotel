"""Módulo de serviço para geração de relatórios e indicadores hoteleiros."""

from datetime import date, datetime, timedelta

from src.models.enums import StatusReserva
from src.models.exceptions import DadosInvalidosException
from src.models.reservation import Reserva
from src.models.room import Quarto


class ServicoRelatorios:
    """Serviço especializado na extração de métricas gerenciais e desempenho hoteleiro.

    Fornece operações de análise sobre o acervo de quartos e histórico de reservas
    para consolidar indicadores como Taxa de Ocupação, ADR (Average Daily Rate),
    RevPAR (Revenue per Available Room), estatísticas de cancelamento e receita
    segmentada por categoria de quarto.
    """
# Método especializado para calcular a taxa de ocupação de quartos em um período específico.
    @staticmethod
    def taxa_ocupacao(
        quartos: list[Quarto], reservas: list[Reserva], inicio: date, fim: date
    ) -> float:
        """Retorna a ocupação percentual no intervalo [inicio, fim).

        Calcula diárias ocupadas / (total de quartos * dias do período) * 100.
        Considera as datas previstas de reservas CONFIRMADA, CHECKIN e CHECKOUT,
        recortadas ao período, sem contar o dia da saída. Cada quarto conta
        apenas uma vez por noite, mesmo se houver reservas sobrepostas.

        O inventário informado é identificado pelo número do quarto e inclui
        quartos em manutenção ou bloqueados: o estado atual não representa
        todo o histórico de disponibilidade. Reservas sem quarto ou de quartos
        fora desse inventário são ignoradas. Inventário vazio retorna 0.0.
        """
        if ( # Verifica se as datas de início e fim são do tipo date e não datetime
            not isinstance(inicio, date)
            or not isinstance(fim, date)
            or isinstance(inicio, datetime)
            or isinstance(fim, datetime)
        ):
            raise DadosInvalidosException("Início e fim devem ser datas do tipo date.") # Se as datas não forem do tipo date, lança uma exceção de dados inválidos.
        if inicio >= fim:
            raise DadosInvalidosException("O início deve ser anterior ao fim do período.") # Se a data de início for maior ou igual à data de fim, lança outra exceção.

        # Cria um conjunto de números de quartos a partir da lista de quartos fornecida e retorna 0.0 se não houver quartos no inventário.
        numeros_quartos = {quarto.numero for quarto in quartos}
        if not numeros_quartos: 
            return 0.0

        # Define os status de reserva que indicam ocupação e inicializa um conjunto para armazenar as diárias ocupadas.
        status_ocupacao = {
            StatusReserva.CONFIRMADA,
            StatusReserva.CHECKIN,
            StatusReserva.CHECKOUT,
        }
        diarias_ocupadas: set[tuple[int, date]] = set()
        for reserva in reservas:
            if ( # Verifica se a reserva não está em um status de ocupação, se não possui quarto ou se o número do quarto não está no inventário. Se qualquer uma dessas condições for verdadeira, a reserva é ignorada.
                reserva.status not in status_ocupacao
                or reserva.quarto is None
                or reserva.quarto.numero not in numeros_quartos
            ):
                continue

            entrada = max(inicio, reserva.data_entrada)
            saida = min(fim, reserva.data_saida)
            for dia in range((saida - entrada).days): # 
                diarias_ocupadas.add(
                    (reserva.quarto.numero, entrada + timedelta(days=dia)) # Adiciona a combinação do número do quarto e a data da diária ocupada ao conjunto.
                )

        diarias_totais = len(numeros_quartos) * (fim - inicio).days
        return round(len(diarias_ocupadas) / diarias_totais * 100, 2) # Retorna a taxa de ocupação como uma porcentagem, arredondada para duas casas decimais.
    
# Diária média das hospedagens finalizadas no período informado.
    @staticmethod
    def calcular_adr(reservas: list[Reserva], inicio: date, fim: date) -> float:
        """Calcula receita de diárias / noites vendidas no intervalo [inicio, fim).

        Considera reservas CHECKOUT com quarto associado e exclui adicionais.
        Como a reserva armazena somente o total das diárias, distribui a receita
        proporcionalmente pelas noites contratadas. Em recortes de estadias
        com preços variáveis, esse rateio é uma aproximação da receita histórica.
        """
        if (
            not isinstance(inicio, date)
            or not isinstance(fim, date)
            or isinstance(inicio, datetime)
            or isinstance(fim, datetime)
        ):
            raise DadosInvalidosException("Início e fim devem ser datas do tipo date.")
        if inicio >= fim:
            raise DadosInvalidosException("O início deve ser anterior ao fim do período.")

        receita_hospedagem = 0.0
        diarias_vendidas = 0
        for reserva in reservas:
            if reserva.status != StatusReserva.CHECKOUT or reserva.quarto is None:
                continue

            entrada = max(inicio, reserva.data_entrada)
            saida = min(fim, reserva.data_saida)
            noites_no_periodo = (saida - entrada).days
            if noites_no_periodo <= 0:
                continue

            # O recorte recebe apenas a parcela da receita referente às suas noites.
            media_por_noite = reserva.valor_total_diarias / reserva.total_diarias
            receita_hospedagem += media_por_noite * noites_no_periodo
            diarias_vendidas += noites_no_periodo

        if diarias_vendidas == 0:
            return 0.0
        return round(receita_hospedagem / diarias_vendidas, 2)

# Método à ser incrementado posteriormente para calcular a RevPAR (Revenue per Available Room) com base nos quartos, reservas e período especificado.
    @staticmethod
    def calcular_revpar(
        quartos: list[Quarto], reservas: list[Reserva], inicio: date, fim: date
    ) -> float:
        """Base da receita por quarto disponível (RevPAR)."""
        ...
