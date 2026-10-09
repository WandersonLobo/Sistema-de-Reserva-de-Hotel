"""Conexão e inicialização do banco SQLite do sistema."""

from pathlib import Path
import sqlite3
from typing import Union

# Garante que hotel.db e connection.py terão caminhos limpos entre eles independetemente.
#de onde o programa será executado
DB_PATH = (Path(__file__).parent / "hotel.db").resolve() #Constante que guarda o endereço do arquivo DB.


def obter_conexao(caminho: Union[Path, str] = DB_PATH) -> sqlite3.Connection: #Recebe  por parâmetro o caminho do DB.
    """Abre uma conexão com as configurações necessárias para o projeto."""

    conexao = sqlite3.connect(str(caminho)) # O caminho foi convertido para str para garantir execução em versões antigas do python.
    conexao.row_factory = sqlite3.Row
    conexao.execute("PRAGMA foreign_keys = ON") # Ativa a utilização de chaves estrangeiras.
    return conexao


def inicializar_banco(caminho: Union[Path, str] = DB_PATH) -> None:
    """Cria as tabelas do sistema caso elas ainda não existam."""

    conexao = obter_conexao(caminho)
    try:
        with conexao:  #atomicidade: ou todas as tabelas são criadas, ou nenhuma
            conexao.executescript(    #O comando executescript executa diversos comando de uma só vez
                """
                CREATE TABLE IF NOT EXISTS hospedes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    documento TEXT NOT NULL UNIQUE,
                    email TEXT NOT NULL,
                    telefone TEXT NOT NULL,
                    preferencias TEXT
                );

                CREATE TABLE IF NOT EXISTS quartos (
                    numero INTEGER PRIMARY KEY,
                    tipo TEXT NOT NULL
                        CHECK (tipo IN ('SIMPLES', 'DUPLO', 'LUXO')), 
                    capacidade INTEGER NOT NULL
                        CHECK (capacidade >= 1),
                    tarifa_base REAL NOT NULL
                        CHECK (tarifa_base > 0),
                    status TEXT NOT NULL
                        CHECK (
                            status IN (
                                'DISPONIVEL',
                                'OCUPADO',
                                'MANUTENCAO',
                                'BLOQUEADO'
                            )
                        ),
                    motivo_manutencao TEXT,
                    inicio_manutencao TEXT,
                    fim_manutencao TEXT,
                    tem_varanda INTEGER NOT NULL DEFAULT 0
                        CHECK (tem_varanda IN (0, 1)),
                    tem_hidromassagem INTEGER NOT NULL DEFAULT 0
                        CHECK (tem_hidromassagem IN (0, 1)),
                    taxa_servico_adicional REAL NOT NULL DEFAULT 0
                        CHECK (taxa_servico_adicional >= 0)
                );

                CREATE TABLE IF NOT EXISTS reservas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    hospede_id INTEGER NOT NULL,
                    quarto_numero INTEGER NOT NULL,
                    data_entrada TEXT NOT NULL,
                    data_saida TEXT NOT NULL,
                    num_hospedes INTEGER NOT NULL
                        CHECK (num_hospedes >= 1),
                    origem TEXT NOT NULL
                        CHECK (origem IN ('SITE', 'TELEFONE', 'BALCAO')),
                    status TEXT NOT NULL
                        CHECK (
                            status IN (
                                'PENDENTE',
                                'CONFIRMADA',
                                'CHECKIN',
                                'CHECKOUT',
                                'CANCELADA',
                                'NO_SHOW'
                            )
                        ),
                    valor_total_diarias REAL NOT NULL
                        CHECK (valor_total_diarias >= 0),
                    checkin_real TEXT,
                    checkout_real TEXT,
                    pagamentos TEXT NOT NULL DEFAULT '[]',
                    adicionais TEXT NOT NULL DEFAULT '[]',
                    data_criacao TEXT NOT NULL,
                    data_atualizacao TEXT NOT NULL,
                    FOREIGN KEY (hospede_id)
                        REFERENCES hospedes (id),
                    FOREIGN KEY (quarto_numero)
                        REFERENCES quartos (numero),
                    CHECK (data_entrada < data_saida)
                );

                CREATE INDEX IF NOT EXISTS idx_reservas_hospede_id
                    ON reservas (hospede_id);

                CREATE INDEX IF NOT EXISTS idx_reservas_quarto_numero
                    ON reservas (quarto_numero);

                CREATE INDEX IF NOT EXISTS idx_reservas_periodo
                    ON reservas (data_entrada, data_saida);
                """
            )
    finally: #finaliza a execução.
        conexao.close()


if __name__ == "__main__":
    inicializar_banco()
