"""Módulo de comportamentos transversais (Mixins) do domínio do hotel.

Concentra as classes utilitárias de herança múltipla responsáveis pela
auditoria temporal e pela serialização de dados.
"""

import json
from datetime import datetime
from typing import Any, Dict

# =========================================================================== #
# Mixin de Auditoria                                                          #
# =========================================================================== #

class Auditoria:
    """Mixin que adiciona rastreabilidade temporal de criação e atualização.

    Attributes:
        _data_criacao (datetime): Data e hora exatas em que o objeto foi criado.
        _data_atualizacao (datetime): Data e hora da última modificação do objeto.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Inicializa os carimbos de tempo e propaga a cadeia de herança."""
        super().__init__(*args, **kwargs)  # <-- Garante a continuidade do MRO
        self._data_criacao: datetime = datetime.now()
        self._data_atualizacao: datetime = datetime.now()

# ----------------------------------------------------------------------- #
# Getters                                   #
# ----------------------------------------------------------------------- #

    @property
    def data_criacao(self) -> datetime:
        """Retorna a data e hora de criação do registro.

        Returns:
            datetime: Instante em que o objeto foi instanciado pela primeira vez.
                Valor imutável — não possui setter correspondente.
        """
        return self._data_criacao

    @property
    def data_atualizacao(self) -> datetime:
        """Retorna a data e hora da última atualização do registro.

        Returns:
            datetime: Instante da última chamada a :meth:`registrar_alteracao`.
                Inicialmente igual a :attr:`data_criacao`.
        """
        return self._data_atualizacao

# ----------------------------------------------------------------------- #
# Métodos de comportamento                                                 #
# ----------------------------------------------------------------------- #

    def registrar_alteracao(self) -> None:
        """Atualiza o carimbo ``__data_atualizacao`` para o instante atual.

        Deve ser chamado internamente pelas subclasses sempre que o objeto
        sofrer uma mudança de estado relevante — por exemplo, ao confirmar
        uma reserva, realizar check-in ou check-out, ou adicionar pagamentos.

        Example::

            reserva.confirmar()
            reserva.registrar_alteracao()
            print(reserva.data_atualizacao)  # novo datetime
        """
        self._data_atualizacao = datetime.now()


# =========================================================================== #
# Mixin de Serialização                                                       #
# =========================================================================== #        

class Serializavel:
    """Mixin que fornece capacidades de serialização para dicionário e JSON.

    Utilizado via herança múltipla pelas classes de domínio (Pessoa, Quarto,
    Reserva, Pagamento e Adicional) para padronizar a exportação de dados
    para o banco SQLite e para a API FastAPI.
    """

# ----------------------------------------------------------------------- #
# Método auxiliar privado de conversão                                    #
# ----------------------------------------------------------------------- #

    @staticmethod
    def __serializar_valor(valor: Any) -> Any:
        """Converte um valor individual para um tipo primitivo serializável em JSON.

        Aplica a seguinte lógica de conversão em ordem de prioridade:

        1. ``datetime`` ou ``date`` → string ISO-8601 via ``.isoformat()``.
        2. Objetos Enum (possuem atributo ``value``) → valor primitivo (``.value``).
        3. Objetos do domínio com ``to_dict()`` → chamada recursiva ao método.
        4. Listas → cada item é convertido individualmente via recursão.
        5. Demais tipos (``int``, ``float``, ``str``, ``bool``, ``None``) →
           retornados sem modificação.

        Args:
            valor (Any): Valor a ser convertido para um tipo primitivo serializável.

        Returns:
            Any: Representação primitiva (JSON-compatível) do valor fornecido.
        """
        from datetime import date as date_type

        if isinstance(valor, (datetime, date_type)):
            return valor.isoformat()
        if hasattr(valor, "value"):  # Enum
            return valor.value
        if hasattr(valor, "to_dict"):  # Objeto do domínio com Serializavel
            return valor.to_dict()
        if isinstance(valor, list):
            return [Serializavel.__serializar_valor(item) for item in valor]
        return valor

# ----------------------------------------------------------------------- #
# Métodos públicos de serialização                                         #
# ----------------------------------------------------------------------- #

    def to_dict(self) -> Dict[str, Any]:
        """Converte os atributos da instância em um dicionário Python.

        Itera sobre ``self.__dict__``, remove prefixos de encapsulamento
        (name-mangling ``_ClassName__attr`` → ``attr`` e underscores
        simples ``_attr`` → ``attr``) e serializa cada valor via
        :meth:`__serializar_valor`.

        Returns:
            Dict[str, Any]: Dicionário com os pares chave-valor representando
                o estado atual da instância, com chaves limpas (sem underscores).

        Example::

            reserva = Reserva(id=1, status=StatusReserva.PENDENTE)
            d = reserva.to_dict()
            # {'id': 1, 'status': 'PENDENTE', ...}
        """
        resultado: Dict[str, Any] = {}

        for chave_raw, valor in self.__dict__.items():
            chave = chave_raw
            # Remove name-mangling: '_ClassName__attr' → 'attr'
            if "__" in chave_raw:
                chave = chave_raw.split("__", 1)[-1]
            # Remove underscores de proteção restantes: '_attr' → 'attr'
            chave = chave.lstrip("_")

            resultado[chave] = self.__serializar_valor(valor)

        return resultado

    def to_json(self) -> str:
        """Serializa o estado atual do objeto para uma string JSON formatada.

        Utiliza :meth:`to_dict` internamente para produzir a representação
        intermediária e, em seguida, aplica ``json.dumps`` com indentação de
        2 espaços e suporte a caracteres Unicode.

        Returns:
            str: String formatada em JSON representando o estado do objeto.

        Example::

            print(reserva.to_json())
            # {
            #   "id": 1,
            #   "status": "PENDENTE"
            # }
        """
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_dict(cls, dados: Dict[str, Any]) -> Any:
        """Reconstrói uma instância da classe a partir de um dicionário de dados.

        Método de fábrica (factory method) utilizado pela camada de persistência
        ao carregar registros do banco de dados SQLite ou de arquivos JSON.

        **Cada subclasse concreta deve obrigatoriamente sobrescrever este método**
        para realizar a conversão correta de tipos — por exemplo, parsear strings
        ISO-8601 de volta em objetos ``datetime`` e recriar Enums a partir de
        seus valores primitivos.

        A implementação base levanta ``NotImplementedError`` para garantir que
        subclasses não herdem silenciosamente um comportamento indefinido.

        Args:
            dados (Dict[str, Any]): Dicionário com os dados brutos necessários
                para instanciar o objeto. As chaves devem corresponder aos nomes
                dos atributos sem underscores (conforme gerado por :meth:`to_dict`).

        Returns:
            Any: Nova instância da subclasse populada com os dados fornecidos.

        Raises:
            NotImplementedError: Sempre, pois a subclasse deve sobrescrever
                este método com sua lógica específica de reconstrução.
            DadosInvalidosException: Se o dicionário não contiver as chaves
                obrigatórias ou apresentar valores incompatíveis com o domínio.

        Example::

            dados = {'id': 1, 'status': 'PENDENTE', ...}
            reserva = Reserva.from_dict(dados)
        """
        raise NotImplementedError(
            f"A classe '{cls.__name__}' deve implementar o método 'from_dict'."
        )