import os
import json
import requests
from openai import OpenAI

BASE_URL = "http://localhost:7860"
MAX_STEPS_FALLBACK = 20

def main():
    api_base = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
    model_name = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
    api_key = os.getenv("HF_TOKEN")
    
    client = OpenAI(api_key=api_key, base_url=api_base)
    
    tasks = ["syntax_check", "logic_review", "full_review"]
    total_score = 0
    
    for task_name in tasks:
        print(f"[START] task={task_name} env=codeguardian model={model_name}")
        
        try:
            res = requests.post(f"{BASE_URL}/reset", json={"task_id": task_name})
            res.raise_for_status()
            obs = res.json()
        except Exception as e:
            print(f"Error connecting to env: {e}")
            return
            
        done = False
        step = 0
        rewards = []
        score = 0.0
        success = False
        
        while not done and step < MAX_STEPS_FALLBACK:
            step += 1
            
            prompt = f"""You are an expert code reviewer. You will be shown Python code and must identify bugs.
Respond ONLY with a valid JSON object with these fields:
{{
  "action": "flag_bug" | "suggest_fix" | "approve" | "reject",
  "line": <integer or null>,
  "comment": "<your explanation>",
  "bug_type": "syntax_error" | "logic_error" | "security" | "performance" | "style" | null
}}
If you find a bug, use flag_bug and specify the line.
If you want to suggest a fix, use suggest_fix.
If the code looks clean, use approve.
Never respond with anything other than the JSON object.

Code to review:
{obs['code']}

Previous issues found:
{json.dumps(obs['issues_found'])}

Step count: {obs['step_count']} / {MAX_STEPS_FALLBACK}
"""
            error_msg = "null"
            action_dict = {}
            try:
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"}
                )
                action_content = response.choices[0].message.content.strip()
                if action_content.startswith("```json"):
                    action_content = action_content[7:]
                if action_content.startswith("```"):
                    action_content = action_content[3:]
                if action_content.endswith("```"):
                    action_content = action_content[:-3]
                action_content = action_content.strip()
                action_dict = json.loads(action_content)
            except Exception as e:
                error_msg = str(e)
                action_dict = {
                    "action": "approve",
                    "comment": "Fallback due to LLM error",
                    "line": None,
                    "bug_type": None
                }
            
            try:
                res = requests.post(f"{BASE_URL}/step", json=action_dict)
                res.raise_for_status()
                step_data = res.json()
                
                obs = step_data["observation"]
                reward = step_data["reward"]
                done = step_data["done"]
                rewards.append(reward)
                
                if done and "episode_score" in step_data["info"] and step_data["info"]["episode_score"] is not None:
                    score = step_data["info"]["episode_score"]
            except Exception as e:
                # Capture issues with steps.
                error_msg = str(e)
                reward = 0.0
                done = True
                
            print(f"[STEP] step={step} action={action_dict.get('action', 'none')} reward={reward:.2f} done={str(done).lower()} error={error_msg}")
        
        success = done
        score = max(0.0, min(1.0, score))
        total_score += score
        
        rewards_str = ",".join([f"{r:.2f}" for r in rewards])
        print(f"[END] success={str(success).lower()} steps={step} score={score:.2f} rewards={rewards_str}")
        
    avg_score = total_score / len(tasks)
    print(f"Average score: {avg_score:.2f}")

if __name__ == "__main__":
    main()
