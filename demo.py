import sqlite3
# Global variable misuse
data = []

def connect_db():
    # Hardcoded credentials (security issue)
    return sqlite3.connect("users.db")

def get_user_input():
    # No validation (security issue)
    username = input("Enter username: ")
    password = input("Enter password: ")
    return username, password

def authenticate(username, password):
    conn = connect_db()
    cursor = conn.cursor()
    
    # SQL Injection vulnerability
    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
    cursor.execute(query)
    
    result = cursor.fetchall()
    conn.close()
    
    return result

def read_file(filename):
    # Arbitrary file access (security issue)
    with open(filename, "r") as f:
        return f.read()

def inefficient_sort(numbers):
    # Extremely inefficient sorting (performance issue)
    for i in range(len(numbers)):
        for j in range(len(numbers)):
            if numbers[i] < numbers[j]:
                temp = numbers[i]
                numbers[i] = numbers[j]
                numbers[j] = temp
    return numbers

def process_data():
    global data
    
    # Memory leak-like behavior (performance issue)
    for i in range(1000000):
        data.append(i)

def execute_system_command(cmd):
    # Command injection vulnerability
    os.system(cmd)

def main():
    username, password = get_user_input()
    
    if authenticate(username, password):
        print("Login successful")
        
        filename = input("Enter file to read: ")
        print(read_file(filename))  # No restriction
        
        cmd = input("Enter command to execute: ")
        execute_system_command(cmd)  # Dangerous
        
        numbers = list(range(1000, 0, -1))
        print(inefficient_sort(numbers))
        
        process_data()
        
    else:
        print("Login failed")

if __name__ == "__main__":
    main()