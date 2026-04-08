import random
import uuid
from typing import Any, Dict, Optional

from models import CodeAction, CodeObservation, EnvState, IssueFound
from server.grader import (
    LOW_REWARD,
    MIN_STRICT_VALUE,
    clamp_strict,
    compute_step_reward,
    evaluate_score,
)
from server.tasks import TASKS


def clamp_score(value: float) -> float:
    """Clamp any float to the strict open interval (0, 1)."""
    return clamp_strict(value)


class CodeGuardianEnvironment:
    def __init__(self):
        self.current_task = None
        self.episode_id = ""
        self.step_count = 0
        self.total_reward = MIN_STRICT_VALUE
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
        self.total_reward = MIN_STRICT_VALUE
        self.actions_history = []
        self.issues_found = []
        self.done = False

        return self.get_observation()

    def step(self, action: CodeAction) -> Dict[str, Any]:
        if self.done:
            return {
                "observation": self.get_observation(),
                "reward": clamp_score(LOW_REWARD),
                "done": True,
                "info": {"error": "Environment is already done."},
            }

        reward_detail = compute_step_reward(action, self.current_task, self.actions_history)

        self.actions_history.append(action)
        if action.action in ["flag_bug", "suggest_fix"] and action.line is not None:
            self.issues_found.append(
                IssueFound(
                    line=action.line,
                    bug_type=action.bug_type or "unknown",
                    comment=action.comment,
                )
            )

        self.step_count += 1
        step_reward = clamp_score(reward_detail.step_reward)
        self.total_reward = clamp_score(self.total_reward + step_reward)

        if action.action in ["approve", "reject"] or self.step_count >= self.current_task["max_steps"]:
            self.done = True

        info = {
            "step_reward": step_reward,
            "reason": reward_detail.reason,
            "partial": reward_detail.partial,
            "episode_score": None,
            "score": None,
        }

        if self.done:
            final_score = clamp_score(evaluate_score(self.current_task, self.actions_history))
            info["episode_score"] = final_score
            info["score"] = final_score

        return {
            "observation": self.get_observation(),
            "reward": step_reward,
            "done": self.done,
            "info": info,
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
            done=self.done,
        )

    def state(self) -> EnvState:
        if not self.current_task:
            return EnvState(
                episode_id="",
                task_id="",
                step_count=0,
                total_reward=MIN_STRICT_VALUE,
                done=False,
                task_difficulty="easy",
            )
        return EnvState(
            episode_id=self.episode_id,
            task_id=self.current_task["task_id"],
            step_count=self.step_count,
            total_reward=clamp_score(self.total_reward),
            done=self.done,
            task_difficulty=self.current_task["difficulty"],
        )
