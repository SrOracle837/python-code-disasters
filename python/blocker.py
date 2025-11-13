import os

# BLOCKER: SQL Injection
def get_user(username):
    query = "SELECT * FROM users WHERE name = '" + username + "'"
    return query

# BLOCKER: Hardcoded password
PASSWORD = "admin123"

# BLOCKER: Command injection
def run_cmd(user_input):
    os.system("ping " + user_input)
