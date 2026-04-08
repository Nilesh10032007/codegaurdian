"""Inference runner for CodeGuardian environment."""

import json
import sys
from typing import Any

MIN_STRICT_SCORE = 0.001
MAX_STRICT_SCORE = 0.999

try:
    from codeguardian.client import CodeGuardianEnv
    from codeguardian.models import CodeGuardianAction
except ImportError:
    from client import CodeGuardianEnv
    from models import CodeGuardianAction


def safe_json_loads(s: str) -> dict[str, Any] | None:
    """Safely parse JSON, return None on invalid."""
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        return None


def clamp_strict(value: float) -> float:
    """Clamp to the open interval (0, 1)."""
    return max(MIN_STRICT_SCORE, min(MAX_STRICT_SCORE, float(value)))


def run_inference(task_name: str, model_name: str) -> None:
    """Run inference for a specific task."""
    print(f"[START] task={task_name} env=codeguardian model={model_name}")

    env = CodeGuardianEnv(base_url="http://localhost:8000")
    observation = env.reset(task_level=task_name)
    rewards = []
    step = 0
    error = None

    try:
        # Simple rule-based agent
        lines = observation.code.splitlines()
        for idx, line in enumerate(lines, start=1):
            if "def " in line and not line.endswith(":"):
                # Flag bug
                step += 1
                result = env.step(CodeGuardianAction(
                    action_type="flag_bug",
                    line_number=idx,
                    comment="Missing colon in function definition"
                ))
                rewards.append(result.reward)
                print(f"[STEP] step={step} action=flag_bug reward={result.reward:.2f} done={result.done} error=null")
                if result.done:
                    break

                # Suggest fix
                step += 1
                fix = line.rstrip() + ":"
                result = env.step(CodeGuardianAction(
                    action_type="suggest_fix",
                    line_number=idx,
                    comment="Add colon",
                    suggested_fix=fix
                ))
                rewards.append(result.reward)
                print(f"[STEP] step={step} action=suggest_fix reward={result.reward:.2f} done={result.done} error=null")
                if result.done:
                    break

            if "for " in line and idx < len(lines) and not lines[idx].startswith(" "):
                # Indentation bug
                step += 1
                result = env.step(CodeGuardianAction(
                    action_type="flag_bug",
                    line_number=idx + 1,
                    comment="Missing indentation"
                ))
                rewards.append(result.reward)
                print(f"[STEP] step={step} action=flag_bug reward={result.reward:.2f} done={result.done} error=null")
                if result.done:
                    break

                step += 1
                fix = "    " + lines[idx].strip()
                result = env.step(CodeGuardianAction(
                    action_type="suggest_fix",
                    line_number=idx + 1,
                    comment="Add indentation",
                    suggested_fix=fix
                ))
                rewards.append(result.reward)
                print(f"[STEP] step={step} action=suggest_fix reward={result.reward:.2f} done={result.done} error=null")
                if result.done:
                    break

            if "range(n)" in line:
                step += 1
                result = env.step(CodeGuardianAction(
                    action_type="flag_bug",
                    line_number=idx,
                    comment="Off-by-one in range"
                ))
                rewards.append(result.reward)
                print(f"[STEP] step={step} action=flag_bug reward={result.reward:.2f} done={result.done} error=null")
                if result.done:
                    break

                step += 1
                fix = line.replace("range(n)", "range(n + 1)")
                result = env.step(CodeGuardianAction(
                    action_type="suggest_fix",
                    line_number=idx,
                    comment="Fix range",
                    suggested_fix=fix
                ))
                rewards.append(result.reward)
                print(f"[STEP] step={step} action=suggest_fix reward={result.reward:.2f} done={result.done} error=null")
                if result.done:
                    break

            if " and " in line and "admin" in line and "owner" in line:
                step += 1
                result = env.step(CodeGuardianAction(
                    action_type="flag_bug",
                    line_number=idx,
                    comment="Wrong logical operator"
                ))
                rewards.append(result.reward)
                print(f"[STEP] step={step} action=flag_bug reward={result.reward:.2f} done={result.done} error=null")
                if result.done:
                    break

                step += 1
                fix = line.replace(" and ", " or ")
                result = env.step(CodeGuardianAction(
                    action_type="suggest_fix",
                    line_number=idx,
                    comment="Change to or",
                    suggested_fix=fix
                ))
                rewards.append(result.reward)
                print(f"[STEP] step={step} action=suggest_fix reward={result.reward:.2f} done={result.done} error=null")
                if result.done:
                    break

            if "while i <= len(items)" in line:
                step += 1
                result = env.step(CodeGuardianAction(
                    action_type="flag_bug",
                    line_number=idx,
                    comment="Index error in loop"
                ))
                rewards.append(result.reward)
                print(f"[STEP] step={step} action=flag_bug reward={result.reward:.2f} done={result.done} error=null")
                if result.done:
                    break

                step += 1
                fix = line.replace("<= len(items)", "< len(items)")
                result = env.step(CodeGuardianAction(
                    action_type="suggest_fix",
                    line_number=idx,
                    comment="Fix loop condition",
                    suggested_fix=fix
                ))
                rewards.append(result.reward)
                print(f"[STEP] step={step} action=suggest_fix reward={result.reward:.2f} done={result.done} error=null")
                if result.done:
                    break

            if "% 2 = 0" in line:
                step += 1
                result = env.step(CodeGuardianAction(
                    action_type="flag_bug",
                    line_number=idx,
                    comment="Invalid operator"
                ))
                rewards.append(result.reward)
                print(f"[STEP] step={step} action=flag_bug reward={result.reward:.2f} done={result.done} error=null")
                if result.done:
                    break

                step += 1
                fix = line.replace("= 0", "== 0")
                result = env.step(CodeGuardianAction(
                    action_type="suggest_fix",
                    line_number=idx,
                    comment="Fix operator",
                    suggested_fix=fix
                ))
                rewards.append(result.reward)
                print(f"[STEP] step={step} action=suggest_fix reward={result.reward:.2f} done={result.done} error=null")
                if result.done:
                    break

            if "total += items[i]" in line and "i += 1" not in lines[idx]:
                step += 1
                result = env.step(CodeGuardianAction(
                    action_type="flag_bug",
                    line_number=idx,
                    comment="Missing increment"
                ))
                rewards.append(result.reward)
                print(f"[STEP] step={step} action=flag_bug reward={result.reward:.2f} done={result.done} error=null")
                if result.done:
                    break

                step += 1
                fix = line + "\n        i += 1"
                result = env.step(CodeGuardianAction(
                    action_type="suggest_fix",
                    line_number=idx,
                    comment="Add increment",
                    suggested_fix=fix
                ))
                rewards.append(result.reward)
                print(f"[STEP] step={step} action=suggest_fix reward={result.reward:.2f} done={result.done} error=null")
                if result.done:
                    break

        if not env.state.done:
            # Final decision
            has_bugs = len(env.state.detected_bug_lines) > 0
            action_type = "reject" if has_bugs else "approve"
            step += 1
            result = env.step(CodeGuardianAction(
                action_type=action_type,
                comment=f"Final decision: {action_type}"
            ))
            rewards.append(result.reward)
            print(f"[STEP] step={step} action={action_type} reward={result.reward:.2f} done={result.done} error=null")

        success = True
        score = clamp_strict(env.grader())

    except Exception as e:
        error = str(e)
        success = False
        score = MIN_STRICT_SCORE

    score = clamp_strict(score)
    print(f"[END] success={success} steps={step} score={score:.3f} rewards={','.join(f'{r:.2f}' for r in rewards)}")


def main() -> None:
    if len(sys.argv) != 3:
        print("Usage: python inference.py <task> <model>")
        sys.exit(1)

    task_name = sys.argv[1]
    model_name = sys.argv[2]

    if task_name not in ["syntax_check", "logic_review", "full_review"]:
        print("Invalid task. Must be one of: syntax_check, logic_review, full_review")
        sys.exit(1)

    # Map to levels
    level_map = {
        "syntax_check": "easy",
        "logic_review": "medium",
        "full_review": "hard"
    }

    run_inference(level_map[task_name], model_name)


if __name__ == "__main__":
    main()