"""Módulo de comportamentos transversais (Mixins) do domínio do hotel.

Concentra as classes utilitárias de herança múltipla responsáveis pela
auditoria temporal e pela serialização de dados.
"""



class Auditoria:
    """Mixin que adiciona rastreabilidade temporal de criação e atualização.

    Attributes:
        _data_criacao (datetime): Data e hora exatas em que o objeto foi criado.
        _data_atualizacao (datetime): Data e hora da última modificação do objeto.
    """

    pass


class Serializavel:
    """Mixin que fornece capacidades de serialização para dicionário e JSON.

    Utilizado via herança múltipla pelas classes de domínio (Pessoa, Quarto,
    Reserva, Pagamento e Adicional) para padronizar a exportação de dados
    para o banco SQLite e para a API FastAPI.
    """

    pass