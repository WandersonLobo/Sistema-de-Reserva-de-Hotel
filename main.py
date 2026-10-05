import uvicorn

if __name__ == "__main__":
    print("Iniciando Sistema de Reservas de Hotel...")
    print("Documentação interativa disponível em: http://127.0.0.1:8000/docs")
    uvicorn.run("src.api.app:app", host="127.0.0.1", port=8000, reload=True)