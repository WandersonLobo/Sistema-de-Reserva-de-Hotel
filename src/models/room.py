
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
    """Classe base abstrata que representa uma acomodação genérica do hotel."""

    def __init__(
        self,
        numero: int = 0,
        capacidade: int = 1,
        tarifa_base: float = 0.0,
        status: StatusQuarto = StatusQuarto.DISPONIVEL,
    ) -> None:
        
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
        """Retorna o número identificador do quarto."""
        return self._numero

    @numero.setter
    def numero(self, valor: int) -> None:
        """Define e valida o número identificador do quarto."""

        if not isinstance(valor, int) or valor <= 0:
            raise DadosInvalidosException(f"O número do quarto deve ser um número inteiro positivo (> 0). Recebido: {valor}")
        self._numero = valor

    @property
    def capacidade(self) -> int:
        """Retorna a capacidade máxima de hóspedes do quarto."""
        return self._capacidade

    @capacidade.setter
    def capacidade(self, valor: int) -> None:
        """Define e valida a capacidade máxima do quarto."""
        if not isinstance(valor, int) or valor < 1:
            raise DadosInvalidosException(f"A capacidade do quarto deve ser de no mínimo 1 pessoa. Recebido: {valor}")
        self._capacidade = valor

    @property
    def tarifa_base(self) -> float:
        """Retorna o valor da tarifa base da diária do quarto."""
        return self._tarifa_base

    @tarifa_base.setter
    def tarifa_base(self, valor: float) -> None:
        """Define e valida a tarifa base por noite do quarto."""
        try:
            val_float = float(valor)
        except (ValueError, TypeError):
            raise DadosInvalidosException("A tarifa base deve ser um número real válido.")

        if val_float <= 0.0:
            raise DadosInvalidosException(f"A tarifa base deve ser estritamente positiva (> 0). Recebido: {val_float}")
        self._tarifa_base = round(val_float, 2)

    @property
    def status(self) -> StatusQuarto:
        """Retorna o estado operacional atual do quarto."""
        return self._status

    @status.setter
    def status(self, valor: Any) -> None:
        """Atualiza e valida o estado operacional do quarto."""

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
        """Retorna o motivo do bloqueio de manutenção ativo, se houver."""
        return self._motivo_manutencao

    @property
    def inicio_manutencao(self) -> Optional[date]:
        """Retorna a data de início da interdição de manutenção."""
        return self._inicio_manutencao

    @property
    def fim_manutencao(self) -> Optional[date]:
        """Retorna a data prevista de término da interdição de manutenção."""
        return self._fim_manutencao

    @property
    @abstractmethod
    def tipo(self) -> TipoQuarto:
        """Retorna a categoria do quarto definida pela subclasse concreta."""
        pass

# ----------------------------------------------------------------------- #
# Métodos de Comportamento Operacional                                     #
# ----------------------------------------------------------------------- #

    def bloquear_manutencao(self, motivo: str, inicio: date, fim: date) -> None:
        """Interdita o quarto para manutenção durante um período determinado.

        Altera o status do quarto para `StatusQuarto.MANUTENCAO` e registra
        o motivo e o intervalo de datas do bloqueio.
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
        """Encerra o bloqueio de manutenção e restaura o quarto para `DISPONIVEL`."""

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
        """Calcula o valor de uma diária aplicando as regras da categoria do quarto."""
        pass

# ----------------------------------------------------------------------- #
# Serialização e Métodos Especiais                                        #
# ----------------------------------------------------------------------- #

    def to_dict(self) -> Dict[str, Any]:
        """Converte os atributos do quarto em dicionário, incluindo o tipo."""
        dados = super().to_dict()
        dados["tipo"] = self.tipo.value
        return dados

    @classmethod
    def from_dict(cls, dados: Dict[str, Any]) -> Quarto:
        """Fábrica de desserialização polimórfica de quartos a partir de dicionário."""

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
        """Retorna uma representação textual amigável do quarto."""
        return (
            f"Quarto {self._numero} [{self.tipo.value}] - Cap: {self._capacidade} pess. | "
            f"Base: R$ {self._tarifa_base:.2f} | Status: {self._status.value}"
        )

    def __repr__(self) -> str:
        """Retorna a representação técnica do objeto Quarto."""
        return (
            f"{self.__class__.__name__}(numero={self._numero!r}, capacidade={self._capacidade!r}, "
            f"tarifa_base={self._tarifa_base!r}, status={self._status.value!r})"
        )

    def __lt__(self, outro: Quarto) -> bool:
        """Compara dois quartos para ordenação natural (menor que)."""
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
    
        super().__init__(numero=numero, capacidade=capacidade, tarifa_base=tarifa_base, status=status)

    @property
    def tipo(self) -> TipoQuarto:
        """Retorna a categoria fixa do Quarto Simples."""
        return TipoQuarto.SIMPLES

    def calcular_diaria(self, fator_temporada: float = 1.0) -> float:
        """Calcula a diária do Quarto Simples (`tarifa_base * fator_temporada`)."""
        return round(self._tarifa_base * float(fator_temporada), 2)

    @classmethod
    def from_dict(cls, dados: Dict[str, Any]) -> QuartoSimples:
        """Reconstrói um QuartoSimples a partir de um dicionário."""
        status_raw = dados.get("status", StatusQuarto.DISPONIVEL.value)
        status = StatusQuarto(status_raw) if isinstance(status_raw, str) else status_raw
        return cls(
            numero=int(dados.get("numero", 0)),
            capacidade=int(dados.get("capacidade", 1)),
            tarifa_base=float(dados.get("tarifa_base", 150.0)),
            status=status,
        )


class QuartoDuplo(Quarto):
    """Subclasse concreta que representa uma acomodação da categoria Duplo."""

    def __init__(
        self,
        numero: int = 0,
        capacidade: int = 2,
        tarifa_base: float = 250.0,
        tem_varanda: bool = False,
        status: StatusQuarto = StatusQuarto.DISPONIVEL,
    ) -> None:
       
        super().__init__(numero=numero, capacidade=capacidade, tarifa_base=tarifa_base, status=status)
        self._tem_varanda: bool = bool(tem_varanda)

    @property
    def tipo(self) -> TipoQuarto:
        """Retorna a categoria fixa do Quarto Duplo."""
        return TipoQuarto.DUPLO

    @property
    def tem_varanda(self) -> bool:
        """Indica se o quarto duplo possui varanda."""
        return self._tem_varanda

    @tem_varanda.setter
    def tem_varanda(self, valor: bool) -> None:
        """Define a presença de varanda privativa no quarto."""
        self._tem_varanda = bool(valor)

    def calcular_diaria(self, fator_temporada: float = 1.0) -> float:
        """Calcula a diária do Quarto Duplo considerando acréscimo de varanda."""
        multiplicador_varanda = 1.15 if self._tem_varanda else 1.0
        return round(self._tarifa_base * multiplicador_varanda * float(fator_temporada), 2)

    @classmethod
    def from_dict(cls, dados: Dict[str, Any]) -> QuartoDuplo:
        """Reconstrói um QuartoDuplo a partir de um dicionário."""
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
    """Subclasse concreta que representa uma acomodação da categoria Luxo."""

    def __init__(
        self,
        numero: int = 0,
        capacidade: int = 4,
        tarifa_base: float = 450.0,
        tem_hidromassagem: bool = True,
        taxa_servico_adicional: float = 50.0,
        status: StatusQuarto = StatusQuarto.DISPONIVEL,
    ) -> None:

        super().__init__(numero=numero, capacidade=capacidade, tarifa_base=tarifa_base, status=status)
        self._tem_hidromassagem: bool = bool(tem_hidromassagem)
        self._taxa_servico_adicional: float = 0.0

        if taxa_servico_adicional != 0.0:
            self.taxa_servico_adicional = taxa_servico_adicional
        else:
            self._taxa_servico_adicional = taxa_servico_adicional

    @property
    def tipo(self) -> TipoQuarto:
        """Retorna a categoria fixa do Quarto Luxo."""
        return TipoQuarto.LUXO

    @property
    def tem_hidromassagem(self) -> bool:
        """Indica se a acomodação de luxo possui hidromassagem."""
        return self._tem_hidromassagem

    @tem_hidromassagem.setter
    def tem_hidromassagem(self, valor: bool) -> None:
        """Define a presença de hidromassagem na suíte."""
        self._tem_hidromassagem = bool(valor)

    @property
    def taxa_servico_adicional(self) -> float:
        """Retorna o valor da taxa de serviço adicional do quarto de luxo."""
        return self._taxa_servico_adicional

    @taxa_servico_adicional.setter
    def taxa_servico_adicional(self, valor: float) -> None:
        """Define e valida a taxa de serviço adicional."""

        try:
            val_float = float(valor)
        except (ValueError, TypeError):
            raise DadosInvalidosException("A taxa de serviço adicional deve ser um número real válido.")

        if val_float < 0.0:
            raise DadosInvalidosException(f"A taxa de serviço adicional não pode ser negativa. Recebido: {val_float}")
        self._taxa_servico_adicional = round(val_float, 2)

    def calcular_diaria(self, fator_temporada: float = 1.0) -> float:
        """Calcula a diária do Quarto Luxo somando a taxa de serviço adicional."""
        return round((self._tarifa_base * float(fator_temporada)) + self._taxa_servico_adicional, 2)

    @classmethod
    def from_dict(cls, dados: Dict[str, Any]) -> QuartoLuxo:
        """Reconstrói um QuartoLuxo a partir de um dicionário."""
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