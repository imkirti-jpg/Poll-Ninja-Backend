from fastapi import FastAPI

app = FastAPI(title="PollNinja Backend")



@app.get("/")
def root():
    return {"message": "QuickPoll API is running 🚀"}