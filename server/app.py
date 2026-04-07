from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from pydantic import BaseModel

from models import CodeObservation, CodeAction, EnvState
from server.environment import CodeGuardianEnvironment

app = FastAPI(title="CodeGuardian AI Code Review Environment")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

env = CodeGuardianEnvironment()

class ResetRequest(BaseModel):
    task_id: Optional[str] = None

@app.post("/reset", response_model=CodeObservation)
def reset_env(req: Optional[ResetRequest] = None):
    task_id = req.task_id if req else None
    return env.reset(task_id)

@app.post("/step")
def step_env(action: CodeAction):
    if not env.current_task:
        raise HTTPException(status_code=400, detail="Environment not initialized. Call /reset first.")
    return env.step(action)

@app.get("/state", response_model=EnvState)
def get_state():
    if not env.current_task:
        raise HTTPException(status_code=400, detail="Environment not initialized.")
    return env.state()

@app.get("/health")
def health():
    return {"status": "ok"}
