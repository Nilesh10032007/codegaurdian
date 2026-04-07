TASKS = [
    {
        "task_id": "syntax_check",
        "difficulty": "easy",
        "filename": "calculator.py",
        "code": """def add(a, b):
    return a + b

def subtract(a, b)
    return a - b

def multiply(a, b):
return a * b
""",
        "bugs": [
            {
                "line": 4,
                "bug_type": "syntax_error",
                "description": "Missing colon after function definition.",
                "correct_fix": "def subtract(a, b):"
            },
            {
                "line": 8,
                "bug_type": "syntax_error",
                "description": "Incorrect indentation.",
                "correct_fix": "    return a * b"
            }
        ],
        "max_steps": 5
    },
    {
        "task_id": "logic_review",
        "difficulty": "medium",
        "filename": "inventory.py",
        "code": """def get_last_item(items):
    # Bug: Off-by-one error
    last_index = len(items)
    return items[last_index]

def is_valid_quantity(quantity):
    # Bug: Wrong operator instead of >=
    if quantity > 0:
        return True
    return False
""",
        "bugs": [
            {
                "line": 3,
                "bug_type": "logic_error",
                "description": "Off-by-one error, should be len(items) - 1.",
                "correct_fix": "last_index = len(items) - 1"
            },
            {
                "line": 8,
                "bug_type": "logic_error",
                "description": "Wrong operator > instead of >= to allow 0 inventory.",
                "correct_fix": "if quantity >= 0:"
            }
        ],
        "max_steps": 10
    },
    {
        "task_id": "full_review",
        "difficulty": "hard",
        "filename": "app_backend.py",
        "code": """import sqlite3

def get_user_data(user_id):
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    # Security Bug
    query = f"SELECT * FROM users WHERE id = {user_id}"
    cursor.execute(query)
    
    data = cursor.fetchone()
    # Logic Bug
    username = data[1]
    
    # Syntax Bug
    print(f"User found: {username}"
    
    conn.close()
    return username
""",
        "bugs": [
            {
                "line": 7,
                "bug_type": "security",
                "description": "SQL injection vulnerability due to direct string formatting.",
                "correct_fix": "query = 'SELECT * FROM users WHERE id = ?'; cursor.execute(query, (user_id,))"
            },
            {
                "line": 12,
                "bug_type": "logic_error",
                "description": "Does not check if 'data' is None before index access.",
                "correct_fix": "if not data: return None\\nusername = data[1]"
            },
            {
                "line": 15,
                "bug_type": "syntax_error",
                "description": "Missing closing parenthesis on print statement.",
                "correct_fix": 'print(f"User found: {username}")'
            }
        ],
        "max_steps": 15
    }
]

def load_tasks():
    return TASKS
