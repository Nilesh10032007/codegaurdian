from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, Dict, Any
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

# ✅ Root endpoint
@app.get("/")
def root():
    return {"message": "CodeGuardian API is running"}

# ✅ Prevent GET misuse
@app.get("/reset")
def reset_get():
    return {"error": "Use POST /reset"}

# ✅ Fixed reset
@app.post("/reset", response_model=CodeObservation)
def reset_env(req: ResetRequest = ResetRequest()):
    return env.reset(req.task_id)

# ✅ Step endpoint
@app.post("/step")
def step_env(action: CodeAction) -> Dict[str, Any]:
    if not env.current_task:
        raise HTTPException(status_code=400, detail="Environment not initialized. Call /reset first.")
    return env.step(action)

# ✅ State endpoint
@app.get("/state", response_model=EnvState)
def get_state():
    if not env.current_task:
        raise HTTPException(status_code=400, detail="Environment not initialized.")
    return env.state()

# ✅ Health
@app.get("/health")
def health():
    return {"status": "ok"}

def main():
    import uvicorn
    uvicorn.run("server.app:app", host="0.0.0.0", port=7860)

if __name__ == "__main__":
    main()