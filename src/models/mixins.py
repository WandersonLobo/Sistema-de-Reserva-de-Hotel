
import json
from datetime import datetime
from typing import Any, Dict

# =========================================================================== #
# Mixin de Auditoria                                                          #
# =========================================================================== #

class Auditoria:
    """Mixin que adiciona rastreabilidade temporal de criação e atualização."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
       
        super().__init__(*args, **kwargs)  # <-- Garante a continuidade do MRO
        self._data_criacao: datetime = datetime.now()
        self._data_atualizacao: datetime = datetime.now()

# ----------------------------------------------------------------------- #
# Getters                                   #
# ----------------------------------------------------------------------- #

    @property
    def data_criacao(self) -> datetime:
        """Retorna a data e hora de criação do registro."""
        return self._data_criacao

    @property
    def data_atualizacao(self) -> datetime:
        """Retorna a data e hora da última atualização do registro."""
        return self._data_atualizacao

# ----------------------------------------------------------------------- #
# Métodos de comportamento                                                 #
# ----------------------------------------------------------------------- #

    def registrar_alteracao(self) -> None:
        """Atualiza o carimbo ``__data_atualizacao`` para o instante atual."""
        self._data_atualizacao = datetime.now()


# =========================================================================== #
# Mixin de Serialização                                                       #
# =========================================================================== #        

class Serializavel:
    """Mixin que fornece capacidades de serialização para dicionário e JSON."""

# ----------------------------------------------------------------------- #
# Método auxiliar privado de conversão                                    #
# ----------------------------------------------------------------------- #

    @staticmethod
    def __serializar_valor(valor: Any) -> Any:
        """Converte um valor individual para um tipo primitivo serializável em JSON. """
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
        """Converte os atributos da instância em um dicionário Python."""
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
        """Serializa o estado atual do objeto para uma string JSON formatada."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_dict(cls, dados: Dict[str, Any]) -> Any:
        """Reconstrói uma instância da classe a partir de um dicionário de dados."""
        raise NotImplementedError(
            f"A classe '{cls.__name__}' deve implementar o método 'from_dict'."
        )