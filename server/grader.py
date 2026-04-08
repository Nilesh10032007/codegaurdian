from typing import List, Dict, Any
from models import CodeAction, RewardDetail

MIN_STRICT_VALUE = 0.001
MAX_STRICT_VALUE = 0.999
LOW_REWARD = 0.1
PARTIAL_REWARD = 0.3
MEDIUM_REWARD = 0.5
HIGH_REWARD = 0.9


def clamp_strict(value: float) -> float:
    return max(MIN_STRICT_VALUE, min(MAX_STRICT_VALUE, float(value)))


def compute_step_reward(action: CodeAction, task: Dict[str, Any], actions_taken: List[CodeAction] = None) -> RewardDetail:
    actions_taken = actions_taken or []
    
    if action.action in ["flag_bug", "suggest_fix"]:
        if action.line is None:
            return RewardDetail(
                step_reward=LOW_REWARD,
                reason="Action missing line number",
                partial=True,
            )
            
        matched_bug = None
        for bug in task["bugs"]:
            if abs(action.line - bug["line"]) <= 2:
                matched_bug = bug
                break
                
        if matched_bug:
            if action.action == "flag_bug" and action.bug_type == matched_bug["bug_type"]:
                return RewardDetail(
                    step_reward=HIGH_REWARD,
                    reason="Correctly flagged a real bug.",
                    partial=True,
                )
            elif action.action == "suggest_fix":
                return RewardDetail(
                    step_reward=MEDIUM_REWARD,
                    reason="Good fix suggestion.",
                    partial=True,
                )
            else:
                return RewardDetail(
                    step_reward=PARTIAL_REWARD,
                    reason="Flagged bug on correct line but wrong type.",
                    partial=True,
                )
        else:
            return RewardDetail(
                step_reward=LOW_REWARD,
                reason="Wrong action: flagged bug on clean line.",
                partial=True,
            )
            
    elif action.action in ["approve", "reject"]:
        found_bugs = set()
        for past_action in actions_taken:
            if past_action.action in ["flag_bug", "suggest_fix"] and past_action.line is not None:
                for idx, bug in enumerate(task["bugs"]):
                    if abs(past_action.line - bug["line"]) <= 2:
                        found_bugs.add(idx)
                        
        if len(found_bugs) < len(task["bugs"]):
            return RewardDetail(
                step_reward=LOW_REWARD,
                reason=f"{action.action} when critical bugs remain undetected.",
                partial=True,
            )
        else:
            return RewardDetail(
                step_reward=MEDIUM_REWARD,
                reason=f"{action.action} when all bugs found (correct!).",
                partial=True,
            )
            
    return RewardDetail(step_reward=LOW_REWARD, reason="Unknown action.", partial=True)

import numpy as np

def evaluate_score(task: Dict[str, Any], actions_taken: List[CodeAction]) -> float:
    bugs = task.get("bugs", [])
    if not bugs:
        score = MAX_STRICT_VALUE
    else:
        found_bugs = set()
        for action in actions_taken:
            if action.action in ["flag_bug", "suggest_fix"] and action.line is not None:
                for idx, bug in enumerate(bugs):
                    if abs(action.line - bug["line"]) <= 2:
                        if action.bug_type == bug["bug_type"] or action.action == "suggest_fix":
                            found_bugs.add(idx)
                            
        score = len(found_bugs) / len(bugs)
        
    if score == 0.0 or score == 1.0:
        print(f"WARNING: Task score is exactly {score}, which is out of range. Clipping to strictly between 0 and 1.")
        
    clipped_score = float(np.clip(score, MIN_STRICT_VALUE, MAX_STRICT_VALUE))
    return clamp_strict(clipped_score)
