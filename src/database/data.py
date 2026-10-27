"""Operações de persistência do sistema."""

import json
from datetime import date, datetime
from typing import Optional

from .connection import obter_conexao
from src.models.person import Hospede
from src.models.reservation import Reserva
from src.models.room import Quarto

# --- Funções auxiliares para transformar uma linha do banco em um objeto Quarto --- #
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

# Função para salvar ou atualizar um quarto no banco de dados, retornando o número do quarto
def salvar_quarto(quarto: Quarto) -> int:
    """Insere ou atualiza um quarto e retorna seu número."""
    if not isinstance(quarto, Quarto):
        raise ValueError("O quarto fornecido para salvamento é inválido.")

    inicio_manut = (
        quarto.inicio_manutencao.isoformat()
        if quarto.inicio_manutencao is not None
        else None
    )
    fim_manut = (
        quarto.fim_manutencao.isoformat()
        if quarto.fim_manutencao is not None
        else None
    )

    conexao = obter_conexao()
    try:
        with conexao:
            conexao.execute(
                """
                INSERT OR REPLACE INTO quartos (
                    numero, tipo, capacidade, tarifa_base, status,
                    motivo_manutencao, inicio_manutencao, fim_manutencao,
                    tem_varanda, tem_hidromassagem, taxa_servico_adicional
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    quarto.numero,
                    quarto.tipo.value,
                    quarto.capacidade,
                    quarto.tarifa_base,
                    quarto.status.value,
                    quarto.motivo_manutencao,
                    inicio_manut,
                    fim_manut,
                    int(getattr(quarto, "tem_varanda", False)),
                    int(getattr(quarto, "tem_hidromassagem", False)),
                    float(getattr(quarto, "taxa_servico_adicional", 0.0)),
                ),
            )
        return quarto.numero
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
    """Insere ou atualiza uma reserva e retorna seu ID."""
    if reserva.hospede is None or reserva.quarto is None:
        raise ValueError("A reserva precisa ter um hóspede e um quarto.")

    agora = datetime.now().isoformat()
    checkin_str = reserva.checkin_real.isoformat() if reserva.checkin_real else None
    checkout_str = reserva.checkout_real.isoformat() if reserva.checkout_real else None
    pagamentos_json = json.dumps([p.to_dict() for p in reserva.pagamentos])
    adicionais_json = json.dumps([a.to_dict() for a in reserva.adicionais])

    conexao = obter_conexao()
    try:
        with conexao:
            if reserva.id and reserva.id > 0:
                conexao.execute(
                    """
                    UPDATE reservas SET
                        hospede_id = ?, quarto_numero = ?, data_entrada = ?, data_saida = ?,
                        num_hospedes = ?, origem = ?, status = ?, valor_total_diarias = ?,
                        checkin_real = ?, checkout_real = ?, pagamentos = ?, adicionais = ?,
                        data_atualizacao = ?
                    WHERE id = ?
                    """,
                    (
                        reserva.hospede.id,
                        reserva.quarto.numero,
                        reserva.data_entrada.isoformat(),
                        reserva.data_saida.isoformat(),
                        reserva.num_hospedes,
                        reserva.origem.value,
                        reserva.status.value,
                        reserva.valor_total_diarias,
                        checkin_str,
                        checkout_str,
                        pagamentos_json,
                        adicionais_json,
                        agora,
                        reserva.id,
                    ),
                )
                return reserva.id
            else:
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
                        reserva.data_entrada.isoformat(),
                        reserva.data_saida.isoformat(),
                        reserva.num_hospedes,
                        reserva.origem.value,
                        reserva.status.value,
                        reserva.valor_total_diarias,
                        checkin_str,
                        checkout_str,
                        pagamentos_json,
                        adicionais_json,
                        agora,
                        agora,
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

def buscar_quartos_ocupados_no_periodo(inicio: date, fim: date) -> set[int]:
    """Retorna os números dos quartos com reservas ativas (CONFIRMADA ou CHECKIN) no período."""
    conexao = obter_conexao()
    try:
        linhas = conexao.execute(
            """
            SELECT DISTINCT quarto_numero FROM reservas
            WHERE status IN ('CONFIRMADA', 'CHECKIN')
              AND data_entrada < ? AND data_saida > ?
            """,
            (fim.isoformat(), inicio.isoformat()),
        ).fetchall()
        return {int(linha["quarto_numero"]) for linha in linhas}
    finally:
        conexao.close()

def listar_reservas(status: Optional[str] = None) -> list[Reserva]:
    """Retorna reservas cadastradas, opcionalmente filtradas por status."""
    conexao = obter_conexao()
    try:
        if status:
            linhas = conexao.execute(
                "SELECT id FROM reservas WHERE status = ? ORDER BY id", (status,)
            ).fetchall()
        else:
            linhas = conexao.execute("SELECT id FROM reservas ORDER BY id").fetchall()
        
        # Reaproveita a reconstrução segura já feita em buscar_reserva
        reservas = []
        for linha in linhas:
            r = buscar_reserva(linha["id"])
            if r is not None:
                reservas.append(r)
        return reservas
    finally:
        conexao.close()