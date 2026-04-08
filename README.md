---
title: CodeGuardian
emoji: 🤖
colorFrom: blue
colorTo: green
sdk: docker
app_file: server/app.py
pinned: false
---
# CodeGuardian

## 1. Problem Description
CodeGuardian is a Reinforcement Learning environment where an AI agent learns to review code. By analyzing code snippets, identifying vulnerabilities, and suggesting robust fixes, the AI functions as an autonomous code reviewer. It adheres to the OpenEnv standard by Meta PyTorch, making it easy to benchmark and deploy to Hugging Face Spaces.

## 2. Environment Explanation
- **State**: Tracks the task, episode, total reward, step count, and completion status.
- **Action**: Actions an AI agent takes on the code (e.g., flagging bugs, suggesting a fix).
- **Reward**: Floating-point values are always clamped to the strict open interval `(0, 1)` so validation never sees `0.0` or `1.0`.

## 3. Observation Space
The observation space provides details for evaluating the code.
```json
{
  "code": "def add(a, b):\n    return a + b",
  "filename": "calculator.py",
  "language": "python",
  "task_id": "syntax_check",
  "task_difficulty": "easy",
  "issues_found": [],
  "step_count": 0,
  "done": false
}
```

## 4. Action Space
The agent responds using a structured JSON object.
```json
{
  "action": "flag_bug",
  "line": 4,
  "comment": "Missing colon after function definition.",
  "bug_type": "syntax_error"
}
```

## 5. Reward Logic
| Action & Condition | Reward | Reason |
| --- | --- | --- |
| `flag_bug` (right line, right type) | +0.9 | Correctly flagged a real bug |
| `suggest_fix` (right line) | +0.5 | Good fix suggestion |
| `flag_bug` (right line, wrong type)| +0.3 | Flagged bug on correct line but wrong type |
| `flag_bug` (wrong line) | +0.1 | Wrong action still stays validator-safe |
| `approve` / `reject` (bugs remain) | +0.1 | Critical bugs remain undetected |
| `approve` / `reject` (all bugs found) | +0.5 | Episode handled correctly |

All rewards, accumulated `total_reward`, and final task scores use the same strict clamp:

```python
value = max(0.001, min(0.999, value))
```

## 6. Task Descriptions
- **Easy (syntax_check)**: Detect trivial syntax errors across 15-20 lines. (Max steps: 5)
- **Medium (logic_review)**: Discover off-by-one errors and illogical comparators. (Max steps: 10)
- **Hard (full_review)**: Audit Python functions for syntax errors along with unvalidated state and SQL injection flaws. (Max steps: 15)

## 7. Setup Steps
1. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```
2. Build the Docker image:
   ```bash
   docker build -t codeguardian .
   ```
3. Run the Docker container:
   ```bash
   docker run -p 7860:7860 codeguardian
   ```

## 8. Baseline Scores
Using inference.py with standard open-weights LLMs:
- **Easy**: Expected ~0.9 - 0.999
- **Medium**: Expected ~0.5 - 0.999
- **Hard**: Expected ~0.3 - 0.6

## 9. API Endpoints
- `POST /reset` - Resets the environment and returns the initial state. Optional `{ "task_id": "syntax_check" }` payload.
- `POST /step` - Exert an action on the environment; returns `observation`, `reward`, `done`, and `info`.
- `GET /state` - Emits current environmental state.
- `GET /health` - Liveness check for the container running FastAPI.
