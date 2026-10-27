"""Ponto de entrada da API FastAPI do Sistema de Reservas de Hotel."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from src.api.routes import router
from src.database.connection import inicializar_banco
from src.database.seed import executar_seed


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Inicializa o banco de dados e a carga de quartos ao subir a aplicação."""
    inicializar_banco()
    executar_seed()
    yield


app = FastAPI(
    title="Sistema de Reservas de Hotel",
    description="API mínima para gerenciamento de quartos, hóspedes e reservas.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(router)
