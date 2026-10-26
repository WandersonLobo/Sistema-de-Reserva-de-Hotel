"""Módulo de serviço para cálculo de tarifas e diárias do hotel."""

from datetime import date, datetime, timedelta
from math import isfinite

from src.models.exceptions import DadosInvalidosException
from src.models.room import Quarto


class CalculadoraTarifa:
    """Serviço utilitário responsável pelo cálculo de diárias e tarifas dinâmicas.

    Os métodos recebem configurações já carregadas: não leem arquivos, não
    consultam o banco e não modificam o quarto nem o dicionário recebido.

    Para preservar as assinaturas do UML, as temporadas chegam dentro de
    settings["temporadas"]. O serviço Hotel pode preencher essa lista com os
    registros do SQLite que abrangem a estadia inteira.

    Temporada e fim de semana são cumulativos. Quando temporadas se sobrepõem,
    usamos a primeira correspondente na ordem da lista recebida.
    """
    @staticmethod
    def calcular_diaria_com_ajustes(
        quarto: Quarto,
        data: date,
        settings: dict,
    ) -> float:
        """Calcula uma diária com ajustes de temporada e fim de semana."""
        if not isinstance(data, date) or isinstance(data, datetime):
            raise DadosInvalidosException("A data da diária deve ser do tipo date.")

        # weekday() retorna 0 para segunda-feira e 6 para domingo.
        dia_semana = data.weekday()

        # Multiplicar por 1.0 mantém o preço original nos dias úteis.
        fator_fim_de_semana = 1.0
        fds = settings.get("fim_de_semana", {})
        if isinstance(fds, dict):
            if dia_semana == 4:
                fator_fim_de_semana = fds.get("sexta", 1.0)
            elif dia_semana == 5:
                fator_fim_de_semana = fds.get("sabado", 1.0)
            elif dia_semana == 6:
                fator_fim_de_semana = fds.get("domingo", 1.0)
        elif isinstance(fds, (int, float)):
            if dia_semana in (5, 6):
                fator_fim_de_semana = float(fds)

        # Sem temporada correspondente, o preço não recebe ajuste sazonal.
        fator_temporada = 1.0

        for temporada in settings.get("temporadas", []):
            # O JSON usa inicio/fim; os registros do banco usam
            # data_inicio/data_fim. Aceitamos ambos sem modificar a entrada.
            inicio_texto = temporada.get("data_inicio", temporada.get("inicio"))
            fim_texto = temporada.get("data_fim", temporada.get("fim"))

            # JSON e SQLite armazenam as datas como texto ISO: AAAA-MM-DD.
            try:
                if isinstance(inicio_texto, date) and not isinstance(inicio_texto, datetime):
                    inicio_temporada = inicio_texto
                else:
                    inicio_temporada = date.fromisoformat(str(inicio_texto))

                if isinstance(fim_texto, date) and not isinstance(fim_texto, datetime):
                    fim_temporada = fim_texto
                else:
                    fim_temporada = date.fromisoformat(str(fim_texto))
            except (TypeError, ValueError) as erro:
                raise DadosInvalidosException(
                    "As datas da temporada devem estar no formato AAAA-MM-DD."
                ) from erro

            if inicio_temporada > fim_temporada:
                raise DadosInvalidosException(
                    "O fim da temporada não pode ser anterior ao início."
                )

            # Os dois limites da temporada estão incluídos.
            if inicio_temporada <= data <= fim_temporada:
                fator_temporada = temporada["multiplicador"]
                # Evita acumular várias temporadas sobre a mesma diária.
                break

        # Um multiplicador deve ser positivo e finito para gerar um preço válido.
        for fator in (fator_temporada, fator_fim_de_semana):
            if (
                isinstance(fator, bool)
                or not isinstance(fator, (int, float))
                or not isfinite(fator)
                or fator <= 0
            ):
                raise DadosInvalidosException(
                    "Os multiplicadores devem ser números positivos e finitos."
                )

        # Polimorfismo: cada categoria aplica sua própria regra, inclusive
        # varanda ou taxa de serviço. A temporada já será aplicada aqui.
        valor_diaria = quarto.calcular_diaria(fator_temporada)

        # O fim de semana incide sobre a diária inteira, incluindo a taxa de
        # serviço do quarto de luxo. Não multiplicamos a temporada novamente.
        return round(valor_diaria * fator_fim_de_semana, 2)

    @staticmethod
    def calcular_total_reserva(
        quarto: Quarto,
        inicio: date,
        fim: date,
        settings: dict,
    ) -> float:
        """Soma as noites da estadia, incluindo inicio e excluindo fim."""
        if (
            not isinstance(inicio, date)
            or not isinstance(fim, date)
            or isinstance(inicio, datetime)
            or isinstance(fim, datetime)
        ):
            raise DadosInvalidosException("Início e fim devem ser datas do tipo date.")

        if fim <= inicio:
            raise DadosInvalidosException("A data de saída deve ser posterior à data de entrada.")

        valor_total_diarias = 0.0
        data_atual = inicio

        # A saída não gera uma nova noite: de dia 10 a dia 12 são duas diárias.
        while data_atual < fim:
            # Recalcular a cada data permite atravessar fins de semana e
            # mudanças de temporada dentro da mesma reserva.
            valor_total_diarias += CalculadoraTarifa.calcular_diaria_com_ajustes(
                quarto, data_atual, settings
            )
            data_atual += timedelta(days=1)

        # Cada diária já foi arredondada; arredondamos a soma para remover
        # pequenas diferenças de representação dos números float.
        return round(valor_total_diarias, 2)
