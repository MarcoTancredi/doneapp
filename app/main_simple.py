

from fastapi import FastAPI, Form

from fastapi.responses import JSONResponse



app = FastAPI(title="DoneApp", description="Teste de APIs")



@app.get("/")

async def home():

    return {"message": "DoneApp funcionando"}



@app.post("/api/test")

async def test_endpoint():

    return {"status": "working", "message": "Endpoint funcionando"}



@app.post("/api/login")

async def simple_login(login: str = Form(...), password: str = Form(...)):

    return {"message": "Login recebido", "login": login, "password": "***"}



@app.post("/api/register") 

async def simple_register(

    username: str = Form(...),

    email: str = Form(...),

    password: str = Form(...)

):

    return {"message": "Registro recebido", "username": username, "email": email}



if __name__ == "__main__":

    import uvicorn

    uvicorn.run("app.main_simple:app", host="0.0.0.0", port=8000, reload=True)
