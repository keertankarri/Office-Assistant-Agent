import json
import sqlite3 #import sqlite3 for database operations
import os
from dotenv import load_dotenv

# Force load environment variables from .env file
load_dotenv(override=True)

from langchain_google_genai import ChatGoogleGenerativeAI
from database import get_leave_balance, get_connection, log_analytics_event
from rag_engine import query_policy_rag

# Explicitly pull key and handle missing key case
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY is missing or empty. Please verify your .env file!")

# Initialize Gemini LLM with current model string
llm = ChatGoogleGenerativeAI(
    model="gemini-3.6-flash", 
    google_api_key=api_key, 
    temperature=0
)


def submit_leave_request(emp_id: str, leave_type: str, days: int) -> str:
    conn = get_connection()
    cursor = conn.cursor()

    column_map = {
        "casual": "casual_leave",
        "earned": "earned_leave",
        "sick": "sick_leave"
    }
    
    col_name = column_map.get(leave_type.lower())
    if not col_name:
        conn.close()
        return f"Error: Unsupported leave type '{leave_type}'. Valid types: casual, earned, sick."

    cursor.execute(f"SELECT {col_name} FROM leave_balances WHERE emp_id = ?", (emp_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return f"Error: No record found for Employee ID: {emp_id}."

    current_balance = row[0]

    if current_balance < days:
        conn.close()
        return f"Request Denied: You requested {days} day(s) of {leave_type} leave, but only have {current_balance} day(s) remaining."

    new_balance = current_balance - days
    cursor.execute(f"UPDATE leave_balances SET {col_name} = ? WHERE emp_id = ?", (new_balance, emp_id))
    conn.commit()
    conn.close()

    return f"Success: Applied for {days} day(s) of {leave_type} leave. Remaining {leave_type} leave balance: {new_balance} day(s)."


def handle_user_request(user_prompt: str, emp_id: str = "EMP101", ocr_text: str = None) -> str:
    if ocr_text:
        log_analytics_event(emp_id, "OCR_ANALYSIS", user_prompt)
        prompt = f"""
        An employee uploaded a document scan. Extracted text:
        ---
        {ocr_text}
        ---
        User Intent: {user_prompt}
        Extract and summarize key details (dates, monetary amounts, or medical notes).
        """
        response = llm.invoke(prompt)
        return str(response.content)

    router_prompt = f"""
    Classify the user prompt into EXACTLY ONE tag:
    - 'LEAVE_SUBMIT': If the user explicitly wants to apply for or request leave.
    - 'EMPLOYEE_DATA': If the user asks to check or view their balance/records.
    - 'POLICY': If the user asks a general company policy question.

    User Prompt: "{user_prompt}"
    Output strictly in JSON format: {{"category": "<CATEGORY_NAME>", "days": <number_or_null>, "leave_type": "<casual|earned|sick|null>"}}
    """
    
    try:
        raw_response = llm.invoke(router_prompt).content
        if isinstance(raw_response, list):
            raw_response = "".join([part.get("text", "") if isinstance(part, dict) else str(part) for part in raw_response])
        
        raw_response = str(raw_response).strip()
        
        if raw_response.startswith("```json"):
            raw_response = raw_response[7:-3].strip()
        elif raw_response.startswith("```"):
            raw_response = raw_response[3:-3].strip()
            
        intent_data = json.loads(raw_response)
    except Exception:
        intent_data = {"category": "POLICY", "days": None, "leave_type": None}

    category = intent_data.get("category", "POLICY")
    
    # Log the interaction for analytics tracking
    log_analytics_event(emp_id, category, user_prompt)

    if category == "LEAVE_SUBMIT":
        days = intent_data.get("days") or 1
        leave_type = intent_data.get("leave_type") or "casual"
        return submit_leave_request(emp_id, leave_type, int(days))

    elif category == "EMPLOYEE_DATA":
        data = get_leave_balance(emp_id)
        return f"Employee Record ({emp_id}): {data}"

    else:
        context = query_policy_rag(user_prompt)
        synthesis_prompt = f"""
        Answer the question using ONLY the provided context snippets. Always cite document sources.
        
        Context:
        {context}
        
        Question: {user_prompt} 
        """
        response = llm.invoke(synthesis_prompt)
        
        if isinstance(response.content, str):
            return response.content
        elif isinstance(response.content, list):
            return "".join([part.get("text", "") if isinstance(part, dict) else str(part) for part in response.content])
        else:
            return str(response.content)