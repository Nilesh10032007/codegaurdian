import uuid
import random
from typing import Optional, Dict, Any

from models import CodeObservation, CodeAction, EnvState, IssueFound
from server.tasks import TASKS
from server.grader import compute_step_reward, evaluate_score


def clamp_score(value: float) -> float:
    """Maps any float to strictly (0, 1) open interval."""
    normalized = (value + 1.0) / 2.0  # [-1, 1] → [0, 1]
    return max(1e-6, min(1 - 1e-6, normalized))


class CodeGuardianEnvironment:
    def __init__(self):
        self.current_task = None
        self.episode_id = ""
        self.step_count = 0
        self.total_reward = 0.0
        self.actions_history = []
        self.issues_found = []
        self.done = False

    def reset(self, task_id: Optional[str] = None) -> CodeObservation:
        if task_id:
            self.current_task = next((t for t in TASKS if t["task_id"] == task_id), None)
        else:
            self.current_task = random.choice(TASKS)

        if not self.current_task:
            self.current_task = TASKS[0]

        self.episode_id = str(uuid.uuid4())
        self.step_count = 0
        self.total_reward = 0.0
        self.actions_history = []
        self.issues_found = []
        self.done = False

        return self.get_observation()

    def step(self, action: CodeAction) -> Dict[str, Any]:
        if self.done:
            return {
                "observation": self.get_observation(),
                "reward": clamp_score(0.0),  # 0.5 — safely in (0, 1)
                "done": True,
                "info": {"error": "Environment is already done."}
            }

        reward_detail = compute_step_reward(action, self.current_task, self.actions_history)

        self.actions_history.append(action)
        if action.action in ["flag_bug", "suggest_fix"] and action.line is not None:
            self.issues_found.append(IssueFound(
                line=action.line,
                bug_type=action.bug_type or "unknown",
                comment=action.comment
            ))

        self.step_count += 1
        self.total_reward += reward_detail.step_reward

        if action.action in ["approve", "reject"] or self.step_count >= self.current_task["max_steps"]:
            self.done = True

        info = {
                "step_reward": clamp_score(reward_detail.step_reward),  # ✅ clamped
                "reason": reward_detail.reason,
                "partial": reward_detail.partial,
                "episode_score": None,
                "score": None
                }
                
        if self.done:
            final_score = evaluate_score(self.current_task, self.actions_history)
            info["episode_score"] = final_score
            info["score"] = final_score

        return {
            "observation": self.get_observation(),
            "reward": clamp_score(reward_detail.step_reward),  # ✅ always in (0, 1)
            "done": self.done,
            "info": info
        }

    def get_observation(self) -> CodeObservation:
        return CodeObservation(
            code=self.current_task["code"] if self.current_task else "",
            filename=self.current_task["filename"] if self.current_task else "",
            language="python",
            task_id=self.current_task["task_id"] if self.current_task else "",
            task_difficulty=self.current_task["difficulty"] if self.current_task else "easy",
            issues_found=self.issues_found,
            step_count=self.step_count,
            done=self.done
        )

    def state(self) -> EnvState:
        if not self.current_task:
            return EnvState(
                episode_id="", task_id="", step_count=0, total_reward=0.0, done=False, task_difficulty="easy"
            )
        return EnvState(
            episode_id=self.episode_id,
            task_id=self.current_task["task_id"],
            step_count=self.step_count,
            total_reward=self.total_reward,
            done=self.done,
            task_difficulty=self.current_task["difficulty"]
        )