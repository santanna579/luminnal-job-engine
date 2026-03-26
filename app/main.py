from fastapi import FastAPI

app = FastAPI(
    title="Luminnal Job Engine",
    description="API inicial do motor de vagas da Luminnal",
    version="0.1.0"
)

@app.get("/")
def read_root():
    return {"message": "Luminnal Job Engine no ar"}

@app.get("/health")
def health_check():
    return {"status": "ok"}