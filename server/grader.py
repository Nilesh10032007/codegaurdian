from typing import List, Dict, Any, Set
from models import CodeAction, RewardDetail

def compute_step_reward(action: CodeAction, task: Dict[str, Any], actions_taken: List[CodeAction] = None) -> RewardDetail:
    actions_taken = actions_taken or []
    
    if action.action in ["flag_bug", "suggest_fix"]:
        if action.line is None:
            return RewardDetail(score=-0.3, reason="Action missing line number", partial=True)
            
        matched_bug = None
        for bug in task["bugs"]:
            if abs(action.line - bug["line"]) <= 2:
                matched_bug = bug
                break
                
        if matched_bug:
            if action.action == "flag_bug" and action.bug_type == matched_bug["bug_type"]:
                return RewardDetail(score=1.0, reason="Correctly flagged a real bug.", partial=True)
            elif action.action == "suggest_fix":
                return RewardDetail(score=0.5, reason="Good fix suggestion.", partial=True)
            else:
                return RewardDetail(score=0.3, reason="Flagged bug on correct line but wrong type.", partial=True)
        else:
            return RewardDetail(score=-0.3, reason="Wrong action: flagged bug on clean line.", partial=True)
            
    elif action.action in ["approve", "reject"]:
        found_bugs = set()
        for past_action in actions_taken:
            if past_action.action in ["flag_bug", "suggest_fix"] and past_action.line is not None:
                for idx, bug in enumerate(task["bugs"]):
                    if abs(past_action.line - bug["line"]) <= 2:
                        found_bugs.add(idx)
                        
        if len(found_bugs) < len(task["bugs"]):
            return RewardDetail(score=-1.0, reason=f"{action.action} when critical bugs remain undetected.", partial=True)
        else:
            return RewardDetail(score=0.0, reason=f"{action.action} when all bugs found (correct!).", partial=True)
            
    return RewardDetail(score=0.0, reason="Unknown action.", partial=True)

def evaluate_score(task: Dict[str, Any], actions_taken: List[CodeAction]) -> float:
    bugs = task.get("bugs", [])
    if not bugs:
        return 1.0
        
    found_bugs = set()
    for action in actions_taken:
        if action.action in ["flag_bug", "suggest_fix"] and action.line is not None:
            for idx, bug in enumerate(bugs):
                if abs(action.line - bug["line"]) <= 2:
                    if action.bug_type == bug["bug_type"] or action.action == "suggest_fix":
                        found_bugs.add(idx)
                        
    score = len(found_bugs) / len(bugs)
    return float(max(0.0, min(1.0, score)))
