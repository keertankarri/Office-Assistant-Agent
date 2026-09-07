import sqlite3
import pandas as pd

DB_PATH = "data/company_data.db"

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Create core tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            emp_id TEXT PRIMARY KEY,
            name TEXT,
            department TEXT,
            role TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leave_balances (
            emp_id TEXT PRIMARY KEY,
            casual_leave INTEGER,
            earned_leave INTEGER,
            sick_leave INTEGER,
            FOREIGN KEY(emp_id) REFERENCES employees(emp_id)
        )
    ''')

    # Create analytics logging table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analytics_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            emp_id TEXT,
            category TEXT,
            prompt TEXT
        )
    ''')

    # Seed initial data ONLY if tables are completely empty
    cursor.execute("SELECT COUNT(*) FROM employees")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO employees VALUES ('EMP101', 'Alice Smith', 'Engineering', 'Developer')")
        cursor.execute("INSERT INTO employees VALUES ('EMP102', 'Bob Jones', 'Human Resources', 'HR Specialist')")

    cursor.execute("SELECT COUNT(*) FROM leave_balances")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO leave_balances VALUES ('EMP101', 8, 12, 5)")
        cursor.execute("INSERT INTO leave_balances VALUES ('EMP102', 10, 15, 8)")
    
    conn.commit()
    conn.close()

def log_analytics_event(emp_id: str, category: str, prompt: str):
    """Logs user query events to SQLite for analytics tracking."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO analytics_logs (emp_id, category, prompt) VALUES (?, ?, ?)",
        (emp_id, category, prompt)
    )
    conn.commit()
    conn.close()

def get_leave_balance(emp_id: str):
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM leave_balances WHERE emp_id = ?", conn, params=(emp_id,))
    conn.close()
    if df.empty:
        return f"No records found for Employee ID: {emp_id}"
    return df.to_dict(orient="records")[0]

def fetch_table_data(table_name: str) -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
    conn.close()
    return df

def save_table_data(table_name: str, df: pd.DataFrame):
    conn = get_connection()
    df.to_sql(table_name, conn, if_exists="replace", index=False)
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully at data/company_data.db")