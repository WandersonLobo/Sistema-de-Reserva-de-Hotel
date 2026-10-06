"""Módulo que define a hierarquia de quartos e acomodações do hotel.

Este módulo contém a classe base abstrata `Quarto` e as subclasses concretas
`QuartoSimples`, `QuartoDuplo` e `QuartoLuxo`, implementando herança simples,
herança múltipla via `Serializavel`, polimorfismo no cálculo de diárias,
encapsulamento com `@property` e métodos especiais (`__str__`, `__repr__`, `__lt__`).
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import date
from typing import Any, Dict, Optional


from .enums import StatusQuarto, TipoQuarto
from .exceptions import (
        DadosInvalidosException,
        QuartoIndisponivelException,
        TransicaoEstadoInvalidaException,
    )
from .mixins import Serializavel

class Quarto(Serializavel, ABC):
    """Classe base abstrata que representa uma acomodação genérica do hotel.

    Attributes:
        _numero (int): Número identificador único do quarto no hotel.
        _capacidade (int): Quantidade máxima de hóspedes suportada (>= 1).
        _tarifa_base (float): Valor base da diária antes de ajustes (> 0).
        _status (StatusQuarto): Estado atual do quarto (DISPONIVEL, OCUPADO, etc.).
        _motivo_manutencao (str | None): Descrição do motivo de manutenção ativa.
        _inicio_manutencao (date | None): Data de início do bloqueio de manutenção.
        _fim_manutencao (date | None): Data de término do bloqueio de manutenção.
    """

    def __init__(
        self,
        numero: int = 0,
        capacidade: int = 1,
        tarifa_base: float = 0.0,
        status: StatusQuarto = StatusQuarto.DISPONIVEL,
    ) -> None:
        """Inicializa os dados base de um quarto do hotel.

        Permite a criação vazia com valores padrão ou parametrizada com
        validação das regras de capacidade e tarifa.

        Args:
            numero (int, optional): Número físico do quarto (> 0 se especificado). Padrão é 0.
            capacidade (int, optional): Limite de ocupantes (>= 1). Padrão é 1.
            tarifa_base (float, optional): Preço base por noite (> 0 se especificado). Padrão é 0.0.
            status (StatusQuarto, optional): Estado operacional inicial. Padrão é DISPONIVEL.

        Raises:
            DadosInvalidosException: Se a capacidade for < 1 ou tarifa_base < 0.
        """
        super().__init__()  # Inicializa o mixin Serializavel
        self._numero: int = 0
        self._capacidade: int = 1
        self._tarifa_base: float = 0.0
        self._status: StatusQuarto = StatusQuarto.DISPONIVEL
        self._motivo_manutencao: Optional[str] = None
        self._inicio_manutencao: Optional[date] = None
        self._fim_manutencao: Optional[date] = None

        if numero != 0:
            self.numero = numero
        else:
            self._numero = numero

        if capacidade != 1:
            self.capacidade = capacidade
        else:
            self._capacidade = capacidade

        if tarifa_base != 0.0:
            self.tarifa_base = tarifa_base
        else:
            self._tarifa_base = tarifa_base

        if status is not None:
            self.status = status

# ----------------------------------------------------------------------- #
# (Getters e Setters)                               #
# ----------------------------------------------------------------------- #

    @property
    def numero(self) -> int:
        """Retorna o número identificador do quarto.

        Returns:
            int: Número do quarto.
        """
        return self._numero

    @numero.setter
    def numero(self, valor: int) -> None:
        """Define e valida o número identificador do quarto.

        Args:
            valor (int): Número físico do quarto (deve ser > 0).

        Raises:
            DadosInvalidosException: Se o número for menor ou igual a zero.
        """
        if not isinstance(valor, int) or valor <= 0:
            raise DadosInvalidosException(f"O número do quarto deve ser um número inteiro positivo (> 0). Recebido: {valor}")
        self._numero = valor

    @property
    def capacidade(self) -> int:
        """Retorna a capacidade máxima de hóspedes do quarto.

        Returns:
            int: Limite máximo de pessoas (>= 1).
        """
        return self._capacidade

    @capacidade.setter
    def capacidade(self, valor: int) -> None:
        """Define e valida a capacidade máxima do quarto.

        Args:
            valor (int): Nova capacidade máxima (deve ser >= 1).

        Raises:
            DadosInvalidosException: Se o valor for menor que 1.
        """
        if not isinstance(valor, int) or valor < 1:
            raise DadosInvalidosException(f"A capacidade do quarto deve ser de no mínimo 1 pessoa. Recebido: {valor}")
        self._capacidade = valor

    @property
    def tarifa_base(self) -> float:
        """Retorna o valor da tarifa base da diária do quarto.

        Returns:
            float: Valor monetário base da diária.
        """
        return self._tarifa_base

    @tarifa_base.setter
    def tarifa_base(self, valor: float) -> None:
        """Define e valida a tarifa base por noite do quarto.

        Args:
            valor (float): Novo valor monetário da diária (deve ser > 0).

        Raises:
            DadosInvalidosException: Se o valor for menor ou igual a zero.
        """
        try:
            val_float = float(valor)
        except (ValueError, TypeError):
            raise DadosInvalidosException("A tarifa base deve ser um número real válido.")

        if val_float <= 0.0:
            raise DadosInvalidosException(f"A tarifa base deve ser estritamente positiva (> 0). Recebido: {val_float}")
        self._tarifa_base = round(val_float, 2)

    @property
    def status(self) -> StatusQuarto:
        """Retorna o estado operacional atual do quarto.

        Returns:
            StatusQuarto: Estado atual (DISPONIVEL, OCUPADO, etc.).
        """
        return self._status

    @status.setter
    def status(self, valor: Any) -> None:
        """Atualiza e valida o estado operacional do quarto.

        Args:
            valor (Any): Membro de `StatusQuarto` ou string correspondente.

        Raises:
            DadosInvalidosException: Se o valor não pertencer a `StatusQuarto`.
        """
        if isinstance(valor, StatusQuarto):
            self._status = valor
        elif isinstance(valor, str):
            try:
                self._status = StatusQuarto(valor.upper())
            except ValueError:
                raise DadosInvalidosException(
                    f"Status inválido: '{valor}'. Valores válidos: {[s.value for s in StatusQuarto]}"
                )
        else:
            raise DadosInvalidosException("O status deve ser uma instância válida de StatusQuarto.")

    @property
    def motivo_manutencao(self) -> Optional[str]:
        """Retorna o motivo do bloqueio de manutenção ativo, se houver.

        Returns:
            Optional[str]: Justificativa cadastrada ou None.
        """
        return self._motivo_manutencao

    @property
    def inicio_manutencao(self) -> Optional[date]:
        """Retorna a data de início da interdição de manutenção.

        Returns:
            Optional[date]: Data de início ou None.
        """
        return self._inicio_manutencao

    @property
    def fim_manutencao(self) -> Optional[date]:
        """Retorna a data prevista de término da interdição de manutenção.

        Returns:
            Optional[date]: Data de término ou None.
        """
        return self._fim_manutencao

    @property
    @abstractmethod
    def tipo(self) -> TipoQuarto:
        """Retorna a categoria do quarto definida pela subclasse concreta.

        Returns:
            TipoQuarto: Categoria (`SIMPLES`, `DUPLO` ou `LUXO`).
        """
        pass

# ----------------------------------------------------------------------- #
# Métodos de Comportamento Operacional                                     #
# ----------------------------------------------------------------------- #

    def bloquear_manutencao(self, motivo: str, inicio: date, fim: date) -> None:
        """Interdita o quarto para manutenção durante um período determinado.

        Altera o status do quarto para `StatusQuarto.MANUTENCAO` e registra
        o motivo e o intervalo de datas do bloqueio.

        Args:
            motivo (str): Justificativa técnica para o bloqueio (não vazia).
            inicio (date): Data inicial da interdição.
            fim (date): Data prevista de conclusão (deve ser >= inicio).

        Raises:
            QuartoIndisponivelException: Se o quarto estiver atualmente `OCUPADO`.
            DadosInvalidosException: Se o motivo for vazio ou se `inicio > fim`.
        """
        if self._status == StatusQuarto.OCUPADO:
            raise QuartoIndisponivelException(
                f"Quarto {self._numero} não pode entrar em manutenção enquanto estiver OCUPADO."
            )

        if not isinstance(motivo, str) or not motivo.strip():
            raise DadosInvalidosException("O motivo da manutenção não pode ser vazio.")

        if not isinstance(inicio, date) or not isinstance(fim, date):
            raise DadosInvalidosException("As datas de início e fim da manutenção devem ser instâncias de date.")

        if inicio > fim:
            raise DadosInvalidosException(
                f"Data de início ({inicio}) não pode ser posterior à data de término ({fim})."
            )

        self._motivo_manutencao = motivo.strip()
        self._inicio_manutencao = inicio
        self._fim_manutencao = fim
        self._status = StatusQuarto.MANUTENCAO

    def liberar_manutencao(self) -> None:
        """Encerra o bloqueio de manutenção e restaura o quarto para `DISPONIVEL`.

        Limpa os registros de motivo e período de manutenção e restabelece
        o quarto no inventário operacional do hotel.

        Raises:
            TransicaoEstadoInvalidaException: Se o quarto não estiver em estado
                de `MANUTENCAO` ou `BLOQUEADO`.
        """
        if self._status not in (StatusQuarto.MANUTENCAO, StatusQuarto.BLOQUEADO):
            raise TransicaoEstadoInvalidaException(
                f"Não é possível liberar o quarto {self._numero}: ele está com status '{self._status.value}', "
                f"não em MANUTENCAO ou BLOQUEADO."
            )

        self._motivo_manutencao = None
        self._inicio_manutencao = None
        self._fim_manutencao = None
        self._status = StatusQuarto.DISPONIVEL

    @abstractmethod
    def calcular_diaria(self, fator_temporada: float = 1.0) -> float:
        """Calcula o valor de uma diária aplicando as regras da categoria do quarto.

        Método abstrato que deve ser implementado polimorficamente por cada
        subclasse (`QuartoSimples`, `QuartoDuplo` e `QuartoLuxo`).

        Args:
            fator_temporada (float, optional): Multiplicador de temporada ou
                fim de semana. Padrão é 1.0.

        Returns:
            float: Valor final calculado para a diária.
        """
        pass

# ----------------------------------------------------------------------- #
# Serialização e Métodos Especiais                                        #
# ----------------------------------------------------------------------- #

    def to_dict(self) -> Dict[str, Any]:
        """Converte os atributos do quarto em dicionário, incluindo o tipo.

        Returns:
            Dict[str, Any]: Dicionário com atributos e o tipo de quarto.
        """
        dados = super().to_dict()
        dados["tipo"] = self.tipo.value
        return dados

    @classmethod
    def from_dict(cls, dados: Dict[str, Any]) -> Quarto:
        """Fábrica de desserialização polimórfica de quartos a partir de dicionário.

        Instancia a subclasse correta com base no campo `tipo`.

        Args:
            dados (Dict[str, Any]): Dicionário com os dados cadastrais do quarto.

        Returns:
            Quarto: Instância da subclasse apropriada (`QuartoSimples`, `QuartoDuplo` ou `QuartoLuxo`).

        Raises:
            DadosInvalidosException: Se o tipo for desconhecido ou faltarem dados.
        """
        if not isinstance(dados, dict):
            raise DadosInvalidosException("Os dados de entrada para Quarto devem ser um dicionário.")

        tipo_raw = str(dados.get("tipo", TipoQuarto.SIMPLES.value)).upper()
        if tipo_raw == TipoQuarto.SIMPLES.value:
            return QuartoSimples.from_dict(dados)
        elif tipo_raw == TipoQuarto.DUPLO.value:
            return QuartoDuplo.from_dict(dados)
        elif tipo_raw == TipoQuarto.LUXO.value:
            return QuartoLuxo.from_dict(dados)
        else:
            raise DadosInvalidosException(f"Tipo de quarto desconhecido: '{tipo_raw}'.")

    def __str__(self) -> str:
        """Retorna uma representação textual amigável do quarto.

        Returns:
            str: Resumo com número, tipo, capacidade, diária base e status.
        """
        return (
            f"Quarto {self._numero} [{self.tipo.value}] - Cap: {self._capacidade} pess. | "
            f"Base: R$ {self._tarifa_base:.2f} | Status: {self._status.value}"
        )

    def __repr__(self) -> str:
        """Retorna a representação técnica do objeto Quarto.

        Returns:
            str: Representação técnica para depuração.
        """
        return (
            f"{self.__class__.__name__}(numero={self._numero!r}, capacidade={self._capacidade!r}, "
            f"tarifa_base={self._tarifa_base!r}, status={self._status.value!r})"
        )

    def __lt__(self, outro: Quarto) -> bool:
        """Compara dois quartos para ordenação natural (menor que).

        Ordena primeiramente pela hierarquia de tipo de quarto
        (`SIMPLES` < `DUPLO` < `LUXO`) e, em caso de empate, pelo número
        do quarto em ordem crescente.

        Args:
            outro (Quarto): Outro quarto a ser comparado.

        Returns:
            bool: True se o quarto atual preceder o outro na ordenação.
        """
        if not isinstance(outro, Quarto):
            return NotImplemented

        ordem_tipos = {
            TipoQuarto.SIMPLES: 1,
            TipoQuarto.DUPLO: 2,
            TipoQuarto.LUXO: 3,
        }

        peso_self = ordem_tipos.get(self.tipo, 0)
        peso_outro = ordem_tipos.get(outro.tipo, 0)

        if peso_self != peso_outro:
            return peso_self < peso_outro
        return self._numero < outro._numero


class QuartoSimples(Quarto):
    """Subclasse concreta que representa uma acomodação da categoria Simples.

    Aplica o cálculo padrão de diária diretamente sobre a tarifa base e o
    fator de temporada.
    """

    def __init__(
        self,
        numero: int = 0,
        capacidade: int = 1,
        tarifa_base: float = 150.0,
        status: StatusQuarto = StatusQuarto.DISPONIVEL,
    ) -> None:
        """Inicializa um Quarto Simples com valores padrão sugeridos.

        Args:
            numero (int, optional): Número identificador do quarto. Padrão é 0.
            capacidade (int, optional): Capacidade máxima. Padrão é 1.
            tarifa_base (float, optional): Valor base da diária. Padrão é 150.0.
            status (StatusQuarto, optional): Estado inicial. Padrão é DISPONIVEL.
        """
        super().__init__(numero=numero, capacidade=capacidade, tarifa_base=tarifa_base, status=status)

    @property
    def tipo(self) -> TipoQuarto:
        """Retorna a categoria fixa do Quarto Simples.

        Returns:
            TipoQuarto: Constante `TipoQuarto.SIMPLES`.
        """
        return TipoQuarto.SIMPLES

    def calcular_diaria(self, fator_temporada: float = 1.0) -> float:
        """Calcula a diária do Quarto Simples (`tarifa_base * fator_temporada`).

        Args:
            fator_temporada (float, optional): Multiplicador de temporada/fim de semana.

        Returns:
            float: Valor final calculado da diária.
        """
        return round(self._tarifa_base * float(fator_temporada), 2)

    @classmethod
    def from_dict(cls, dados: Dict[str, Any]) -> QuartoSimples:
        """Reconstrói um QuartoSimples a partir de um dicionário.

        Args:
            dados (Dict[str, Any]): Dicionário com chaves do quarto.

        Returns:
            QuartoSimples: Instância reconstruída.
        """
        status_raw = dados.get("status", StatusQuarto.DISPONIVEL.value)
        status = StatusQuarto(status_raw) if isinstance(status_raw, str) else status_raw
        return cls(
            numero=int(dados.get("numero", 0)),
            capacidade=int(dados.get("capacidade", 1)),
            tarifa_base=float(dados.get("tarifa_base", 150.0)),
            status=status,
        )


class QuartoDuplo(Quarto):
    """Subclasse concreta que representa uma acomodação da categoria Duplo.

    Attributes:
        _tem_varanda (bool): Indica se o quarto duplo dispõe de varanda privativa.
    """

    def __init__(
        self,
        numero: int = 0,
        capacidade: int = 2,
        tarifa_base: float = 250.0,
        tem_varanda: bool = False,
        status: StatusQuarto = StatusQuarto.DISPONIVEL,
    ) -> None:
        """Inicializa um Quarto Duplo com opção de varanda.

        Args:
            numero (int, optional): Número identificador do quarto. Padrão é 0.
            capacidade (int, optional): Capacidade máxima. Padrão é 2.
            tarifa_base (float, optional): Preço base por diária. Padrão é 250.0.
            tem_varanda (bool, optional): Indica se há varanda privativa. Padrão é False.
            status (StatusQuarto, optional): Estado inicial. Padrão é DISPONIVEL.
        """
        super().__init__(numero=numero, capacidade=capacidade, tarifa_base=tarifa_base, status=status)
        self._tem_varanda: bool = bool(tem_varanda)

    @property
    def tipo(self) -> TipoQuarto:
        """Retorna a categoria fixa do Quarto Duplo.

        Returns:
            TipoQuarto: Constante `TipoQuarto.DUPLO`.
        """
        return TipoQuarto.DUPLO

    @property
    def tem_varanda(self) -> bool:
        """Indica se o quarto duplo possui varanda.

        Returns:
            bool: True se possuir varanda; False caso contrário.
        """
        return self._tem_varanda

    @tem_varanda.setter
    def tem_varanda(self, valor: bool) -> None:
        """Define a presença de varanda privativa no quarto.

        Args:
            valor (bool): Novo valor booleano para varanda.
        """
        self._tem_varanda = bool(valor)

    def calcular_diaria(self, fator_temporada: float = 1.0) -> float:
        """Calcula a diária do Quarto Duplo considerando acréscimo de varanda.

        Aplica multiplicador de 1.15x caso disponha de varanda privativa.

        Args:
            fator_temporada (float, optional): Multiplicador de temporada/fim de semana.

        Returns:
            float: Valor final calculado da diária.
        """
        multiplicador_varanda = 1.15 if self._tem_varanda else 1.0
        return round(self._tarifa_base * multiplicador_varanda * float(fator_temporada), 2)

    @classmethod
    def from_dict(cls, dados: Dict[str, Any]) -> QuartoDuplo:
        """Reconstrói um QuartoDuplo a partir de um dicionário.

        Args:
            dados (Dict[str, Any]): Dicionário com chaves do quarto duplo.

        Returns:
            QuartoDuplo: Instância reconstruída.
        """
        status_raw = dados.get("status", StatusQuarto.DISPONIVEL.value)
        status = StatusQuarto(status_raw) if isinstance(status_raw, str) else status_raw
        return cls(
            numero=int(dados.get("numero", 0)),
            capacidade=int(dados.get("capacidade", 2)),
            tarifa_base=float(dados.get("tarifa_base", 250.0)),
            tem_varanda=bool(dados.get("tem_varanda", False)),
            status=status,
        )


class QuartoLuxo(Quarto):
    """Subclasse concreta que representa uma acomodação da categoria Luxo.

    Attributes:
        _tem_hidromassagem (bool): Indica se a suíte possui banheira de hidromassagem.
        _taxa_servico_adicional (float): Valor adicional de serviço VIP na diária.
    """

    def __init__(
        self,
        numero: int = 0,
        capacidade: int = 4,
        tarifa_base: float = 450.0,
        tem_hidromassagem: bool = True,
        taxa_servico_adicional: float = 50.0,
        status: StatusQuarto = StatusQuarto.DISPONIVEL,
    ) -> None:
        """Inicializa um Quarto de Luxo com comodidades de alto padrão.

        Args:
            numero (int, optional): Número identificador do quarto. Padrão é 0.
            capacidade (int, optional): Capacidade máxima. Padrão é 4.
            tarifa_base (float, optional): Tarifa base por noite. Padrão é 450.0.
            tem_hidromassagem (bool, optional): Presença de hidromassagem. Padrão é True.
            taxa_servico_adicional (float, optional): Taxa adicional por diária. Padrão é 50.0.
            status (StatusQuarto, optional): Estado inicial. Padrão é DISPONIVEL.

        Raises:
            DadosInvalidosException: Se a taxa de serviço adicional for negativa.
        """
        super().__init__(numero=numero, capacidade=capacidade, tarifa_base=tarifa_base, status=status)
        self._tem_hidromassagem: bool = bool(tem_hidromassagem)
        self._taxa_servico_adicional: float = 0.0

        if taxa_servico_adicional != 0.0:
            self.taxa_servico_adicional = taxa_servico_adicional
        else:
            self._taxa_servico_adicional = taxa_servico_adicional

    @property
    def tipo(self) -> TipoQuarto:
        """Retorna a categoria fixa do Quarto Luxo.

        Returns:
            TipoQuarto: Constante `TipoQuarto.LUXO`.
        """
        return TipoQuarto.LUXO

    @property
    def tem_hidromassagem(self) -> bool:
        """Indica se a acomodação de luxo possui hidromassagem.

        Returns:
            bool: True se possuir hidromassagem; False caso contrário.
        """
        return self._tem_hidromassagem

    @tem_hidromassagem.setter
    def tem_hidromassagem(self, valor: bool) -> None:
        """Define a presença de hidromassagem na suíte.

        Args:
            valor (bool): Novo valor booleano.
        """
        self._tem_hidromassagem = bool(valor)

    @property
    def taxa_servico_adicional(self) -> float:
        """Retorna o valor da taxa de serviço adicional do quarto de luxo.

        Returns:
            float: Valor da taxa adicional por diária.
        """
        return self._taxa_servico_adicional

    @taxa_servico_adicional.setter
    def taxa_servico_adicional(self, valor: float) -> None:
        """Define e valida a taxa de serviço adicional.

        Args:
            valor (float): Nova quantia da taxa (deve ser >= 0).

        Raises:
            DadosInvalidosException: Se o valor for negativo.
        """
        try:
            val_float = float(valor)
        except (ValueError, TypeError):
            raise DadosInvalidosException("A taxa de serviço adicional deve ser um número real válido.")

        if val_float < 0.0:
            raise DadosInvalidosException(f"A taxa de serviço adicional não pode ser negativa. Recebido: {val_float}")
        self._taxa_servico_adicional = round(val_float, 2)

    def calcular_diaria(self, fator_temporada: float = 1.0) -> float:
        """Calcula a diária do Quarto Luxo somando a taxa de serviço adicional.

        Fórmula: `(tarifa_base * fator_temporada) + taxa_servico_adicional`.

        Args:
            fator_temporada (float, optional): Multiplicador de temporada/fim de semana.

        Returns:
            float: Valor final calculado da diária de luxo.
        """
        return round((self._tarifa_base * float(fator_temporada)) + self._taxa_servico_adicional, 2)

    @classmethod
    def from_dict(cls, dados: Dict[str, Any]) -> QuartoLuxo:
        """Reconstrói um QuartoLuxo a partir de um dicionário.

        Args:
            dados (Dict[str, Any]): Dicionário com chaves do quarto de luxo.

        Returns:
            QuartoLuxo: Instância reconstruída.
        """
        status_raw = dados.get("status", StatusQuarto.DISPONIVEL.value)
        status = StatusQuarto(status_raw) if isinstance(status_raw, str) else status_raw
        return cls(
            numero=int(dados.get("numero", 0)),
            capacidade=int(dados.get("capacidade", 4)),
            tarifa_base=float(dados.get("tarifa_base", 450.0)),
            tem_hidromassagem=bool(dados.get("tem_hidromassagem", True)),
            taxa_servico_adicional=float(dados.get("taxa_servico_adicional", 50.0)),
            status=status,
        )