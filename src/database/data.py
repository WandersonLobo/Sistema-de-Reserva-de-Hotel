
"""Operações de persistência do sistema."""

import json
from datetime import date, datetime

from typing import Optional

from .connection import obter_conexao
from src.models.person import Hospede
from src.models.reservation import Reserva
from src.models.room import Quarto

# --- Funçôes auxiliares para transformar uma linha do banco em um objeto Quarto --- #
def _quarto_da_linha(linha) -> Quarto:
    return Quarto.from_dict(dict(linha)) # O from_dict é um método da classe Quarto que cria um objeto a partir de um dicionário

def _hospede_da_linha(linha) -> Hospede:
    """Converte uma linha da tabela hospedes em um objeto Hospede."""
    return Hospede.from_dict(dict(linha)) # O from_dict é um método da classe Hospede que cria um objeto a partir de um dicionário

# Função para listar todos os quartos cadastrados no banco de dados
def listar_quartos() -> list[Quarto]:
    """Retorna todos os quartos cadastrados."""
    conexao = obter_conexao()
    try: 
        linhas = conexao.execute(
            "SELECT * FROM quartos ORDER BY numero"
        ).fetchall()
        return [_quarto_da_linha(linha) for linha in linhas] # Método de compreensão de listas que transforma cada linha em um objeto Quarto
    finally:
        conexao.close()

# Função para buscar um quarto pelo seu número, retornando None se não encontrado
def buscar_quarto(numero: int) -> Optional[Quarto]:
    """Busca um quarto pelo número."""
    conexao = obter_conexao()
    try:
        linha = conexao.execute(
            "SELECT * FROM quartos WHERE numero = ?",
            (numero,), # O número do quarto é passado como parâmetro para evitar SQL injection
        ).fetchone()

        if linha is None: # Testa se a linha retornada é None, ou seja, se não encontrou o quarto
            return None

        return _quarto_da_linha(linha) # Se encontrou, transforma a linha em um objeto Quarto e retorna
    finally:
        conexao.close()

# Função para salvar um hóspede no banco de dados, retornando o ID gerado
def salvar_hospede(hospede: Hospede) -> int:
    """Insere um hóspede e retorna seu ID."""
    conexao = obter_conexao()
    try:
        with conexao:
            cursor = conexao.execute(
                """
                INSERT INTO hospedes (
                    nome, documento, email, telefone, preferencias
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    hospede.nome,
                    hospede.documento,
                    hospede.email,
                    hospede.telefone,
                    hospede.preferencias,
                ),
            )

            if cursor.lastrowid is None: # Testa se o ID gerado é None, ou seja, se não conseguiu inserir o hóspede
                raise RuntimeError("O banco não retornou o ID do hóspede.")
            return int(cursor.lastrowid) # Converte o ID gerado para int e retorna
    finally:
        conexao.close()

# Função para buscar um hóspede pelo seu ID, retornando None se não encontrado
def buscar_hospede(id_: int) -> Optional[Hospede]:
    """Busca um hóspede pelo ID."""
    conexao = obter_conexao()
    try:
        linha = conexao.execute(
            """
            SELECT id, nome, documento, email, telefone, preferencias
            FROM hospedes
            WHERE id = ?
            """,
            (id_,),
        ).fetchone()

        if linha is None: # Testa se a linha retornada é None, ou seja, se não encontrou o hóspede, se sim, retorna None
            return None

        return _hospede_da_linha(linha)
    finally:
        conexao.close()

# Função para listar todas as temporadas que abrangem uma data específica
def listar_temporadas(data_referencia: date) -> list[dict]:
    """Retorna temporadas que abrangem uma data."""
    conexao = obter_conexao()
    try:
        linhas = conexao.execute(
            """
            SELECT id, nome, data_inicio, data_fim, multiplicador
            FROM temporadas
            WHERE data_inicio <= ? AND data_fim >= ?
            ORDER BY data_inicio
            """,
            (
                data_referencia.isoformat(), # O método isoformat() converte a data em uma string no formato ISO 8601, que é aceito pelo SQLite
                data_referencia.isoformat(), #                                                                                                  #
            ),
        ).fetchall()

        return [dict(linha) for linha in linhas] # Método de compreensão de listas que transforma cada linha em um dicionário
    finally:
        conexao.close()

# Função para salvar uma reserva no banco de dados, retornando o ID gerado
def salvar_reserva(reserva: Reserva) -> int:
    """Insere uma reserva e retorna seu ID."""
    if reserva.hospede is None or reserva.quarto is None:
        raise ValueError("A reserva precisa ter um hóspede e um quarto.")

    agora = datetime.now().isoformat()
    conexao = obter_conexao()
    try:
        with conexao:
            cursor = conexao.execute(
                """
                INSERT INTO reservas (
                    hospede_id, quarto_numero, data_entrada, data_saida,
                    num_hospedes, origem, status, valor_total_diarias,
                    checkin_real, checkout_real, pagamentos, adicionais,
                    data_criacao, data_atualizacao
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    reserva.hospede.id,
                    reserva.quarto.numero,
                    reserva.data_entrada.isoformat(), # Converte a data para texto no formato aceito pelo SQLite.
                    reserva.data_saida.isoformat(),  # Converte a data de saída para texto ISO.
                    reserva.num_hospedes,
                    reserva.origem.value,
                    reserva.status.value,
                    reserva.valor_total_diarias,

                    ( # Salva o check-in como texto ou NULL se ainda não aconteceu.
                        reserva.checkin_real.isoformat()
                        if reserva.checkin_real is not None
                        else None
                    ),

                    ( # Salva o check-out como texto ou NULL se ainda não aconteceu.
                        reserva.checkout_real.isoformat()
                        if reserva.checkout_real is not None
                        else None
                    ),

                    json.dumps( # Converte os pagamentos em uma lista de dicionários e depois em JSON.
                        [pagamento.to_dict() for pagamento in reserva.pagamentos]
                    ),

                    json.dumps( # Converte os adicionais em uma lista de dicionários e depois em JSON.
                        [adicional.to_dict() for adicional in reserva.adicionais]
                    ),
                    agora, # Salva a data de criação como o momento atual.
                    agora, # Salva a data de atualização como o momento atual.
                ),
            )

            if cursor.lastrowid is None:
                raise RuntimeError("O banco não retornou o ID da reserva.")
            return int(cursor.lastrowid)
    finally:
        conexao.close()

# Função para buscar uma reserva pelo seu ID, retornando None se não encontrado
def buscar_reserva(id_: int) -> Optional[Reserva]:
    """Busca uma reserva pelo ID."""
    conexao = obter_conexao()
    try:
        linha = conexao.execute(
            "SELECT * FROM reservas WHERE id = ?",
            (id_,),
        ).fetchone()

        if linha is None:
            return None

        dados = dict(linha) # Converte a linha retornada pelo SQLite em um dicionário mutável.
        hospede = conexao.execute( # Busca os dados completos do hóspede relacionado pela chave estrangeira.
            """
            SELECT id, nome, documento, email, telefone, preferencias
            FROM hospedes
            WHERE id = ?
            """,
            (dados["hospede_id"],),
        ).fetchone()

        quarto = conexao.execute( # Busca os dados completos do quarto relacionado pela chave estrangeira.
            "SELECT * FROM quartos WHERE numero = ?",
            (dados["quarto_numero"],),
        ).fetchone()

        if hospede is None or quarto is None:
            raise RuntimeError("A reserva possui um hóspede ou quarto inválido.")

        dados["hospede"] = dict(hospede)
        dados["quarto"] = dict(quarto)
        dados["pagamentos"] = json.loads(dados["pagamentos"])
        dados["adicionais"] = json.loads(dados["adicionais"])

        return Reserva.from_dict(dados) # Reconstrói e retorna um objeto Reserva a partir dos dados completos.
    finally:
        conexao.close()