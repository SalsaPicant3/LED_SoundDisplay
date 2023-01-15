from fastapi import FastAPI
app = FastAPI()


# uvicorn api:app --reload --host 192.168.1.35
k = 0


@app.get("/LED_AMP")
def hello():
    global k
    a = ''
    for i in range(0, 12):
        a += str((i + k) % 12) + '.'
    k += 1
    return a[:-1]
