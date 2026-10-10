"""Carga de dados iniciais para desenvolvimento e demonstração."""

from pathlib import Path
from typing import Union

from .connection import obter_conexao, inicializar_banco

# Dados iniciais para popular o banco de dados do hotel.
QUARTOS = (
    (101, "SIMPLES", 1, 150.0, 0, 0, 0.0),
    (102, "SIMPLES", 1, 150.0, 0, 0, 0.0),
    (103, "SIMPLES", 1, 170.0, 0, 0, 0.0),
    (201, "DUPLO", 2, 250.0, 1, 0, 0.0),
    (202, "DUPLO", 2, 250.0, 0, 0, 0.0),
    (203, "DUPLO", 2, 280.0, 1, 0, 0.0),
    (301, "LUXO", 4, 450.0, 0, 1, 50.0),
    (302, "LUXO", 4, 500.0, 0, 1, 50.0),
)
# A lista de temporadas é definida como uma tupla de tuplas, onde cada tupla representa uma temporada com seu nome,
#  data de início, data de fim e multiplicador de tarifa.
TEMPORADAS = (
    ("Baixa temporada", "2026-01-01", "2026-06-30", 1.0),
    ("Alta temporada", "2026-07-01", "2026-08-31", 1.3),
    ("Festas de fim de ano", "2026-12-01", "2026-12-31", 1.5),
)

# Função para executar a seed, que inicializa o banco de dados e insere os dados iniciais.
def executar_seed(caminho: Union[Path, str, None] = None) -> None:
    """Cria as tabelas e insere os dados básicos do hotel."""
    if caminho is None: # Se nenhum caminho for fornecido, inicializa o banco de dados padrão e obtém a conexão.
        inicializar_banco()
        conexao = obter_conexao()
    else:
        inicializar_banco(caminho)
        conexao = obter_conexao(caminho)
    try:
        with conexao:
            conexao.executemany(
                """
                INSERT OR IGNORE INTO quartos (
                    numero, tipo, capacidade, tarifa_base,
                    status, tem_varanda, tem_hidromassagem,
                    taxa_servico_adicional
                ) VALUES (?, ?, ?, ?, 'DISPONIVEL', ?, ?, ?)
                """,
                QUARTOS,
            )
            conexao.executemany(
                """
                INSERT OR IGNORE INTO temporadas (
                    nome, data_inicio, data_fim, multiplicador
                ) VALUES (?, ?, ?, ?)
                """,
                TEMPORADAS,
            )
            #A interrogação é usada para indicar que o valor será fornecido posteriormente, evitando a necessidade 
              #de concatenar strings e prevenindo ataques de injeção de SQL.
    finally:
        conexao.close()


if __name__ == "__main__":
    executar_seed()
    print("Seed executado com sucesso.")