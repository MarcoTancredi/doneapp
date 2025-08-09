

# Arquivo de debug para testar carregamento

try:

    from fastapi import FastAPI, Form

    print("✅ FastAPI importado")

    

    from fastapi.responses import JSONResponse

    print("✅ JSONResponse importado")

    

    import jwt

    print("✅ JWT importado")

    

    import sqlite3

    print("✅ SQLite importado")

    

    print("🎉 Todas as dependências OK!")

    

except Exception as e:

    print(f"❌ ERRO: {e}")



# Teste simples

app = FastAPI(title="Debug Test")



@app.post("/api/register")  

async def test_register():

    return {"status": "endpoint funcionando"}



if __name__ == "__main__":

    print("Iniciando servidor de debug na porta 8001...")

    import uvicorn

    uvicorn.run("debug_main:app", host="0.0.0.0", port=8001, reload=True)
