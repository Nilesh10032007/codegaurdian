from pydantic import BaseModel, Field
from typing import List, Literal, Optional

class IssueFound(BaseModel):
    line: int
    bug_type: str
    comment: str

class CodeObservation(BaseModel):
    code: str
    filename: str
    language: str = "python"
    task_id: str
    task_difficulty: Literal["easy", "medium", "hard"]
    issues_found: List[IssueFound] = Field(default_factory=list)
    step_count: int = 0
    done: bool = False

class CodeAction(BaseModel):
    action: Literal["flag_bug", "suggest_fix", "approve", "reject"]
    line: Optional[int] = None
    comment: str
    bug_type: Optional[str] = None

class RewardDetail(BaseModel):
    step_reward: float
    reason: str
    partial: bool

class EnvState(BaseModel):
    episode_id: str
    task_id: str
    step_count: int
    total_reward: float
    done: bool
    task_difficulty: str
