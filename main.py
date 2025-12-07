from fastmcp import FastMCP
import os
import sqlite3
import json
from datetime import datetime, date
from typing import List, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "expenses.db")
MEMBERS_PATH = os.path.join(os.path.dirname(__file__), "members.json")


mcp = FastMCP("ExpenseTracker")

def init_db():
    """Initialize database with all required tables"""
    with sqlite3.connect(DB_PATH) as conn:
        # Main expenses table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS expenses(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                subcategory TEXT DEFAULT '',
                paid_by TEXT NOT NULL,
                note TEXT DEFAULT '',
                time_of_day TEXT DEFAULT 'morning',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """) 
        
        # Split details table (who owes whom)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS expense_splits(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                expense_id INTEGER NOT NULL,
                member_name TEXT NOT NULL,
                share_amount REAL NOT NULL,
                is_paid BOOLEAN DEFAULT 0,
                paid_date TEXT,
                FOREIGN KEY (expense_id) REFERENCES expenses(id) ON DELETE CASCADE
            )
        """)
        
        # Settlement history
        conn.execute("""
            CREATE TABLE IF NOT EXISTS settlements(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_member TEXT NOT NULL,
                to_member TEXT NOT NULL,
                amount REAL NOT NULL,
                settlement_date TEXT NOT NULL,
                note TEXT DEFAULT '',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()

init_db()

def get_current_time():
    """Get current time in HH:MM format"""
    return datetime.now().strftime("%H:%M")

def determine_time_of_day(time_str: str = None) -> str:
    """Determine if it's morning, afternoon, evening, or night"""
    if time_str is None:
        time_str = get_current_time()
    
    hour = int(time_str.split(':')[0])
    
    if 5 <= hour < 12:
        return "morning"
    elif 12 <= hour < 17:
        return "afternoon"
    elif 17 <= hour < 21:
        return "evening"
    else:
        return "night"

@mcp.tool()
def add_shared_expense(
    amount: float,
    paid_by: str,
    members: List[str],
    category: str = "travel",
    subcategory: str = "",
    note: str = "",
    date: str = None,
    time: str = None,
    include_payer: bool = True
):
    """
    Add a shared expense and automatically split it among members.
    
    Args:
        amount: Total amount paid
        paid_by: Name of person who paid
        members: List of member names who share this expense
        category: Expense category (travel, food, entertainment, etc.)
        subcategory: More specific category
        note: Additional notes
        date: Date in YYYY-MM-DD format (defaults to today)
        time: Time in HH:MM format (defaults to current time)
        include_payer: Whether to include the payer in the split (default: True)
    
    Example:
        add_shared_expense(60, "Me", ["Aman", "Amit", "Apoorva", "Aditya Shahu"], "travel", "auto", "Morning office ride")
    """
    try:
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        if time is None:
            time = get_current_time()
        
        time_of_day = determine_time_of_day(time)
        
        # Include payer in members if specified
        if include_payer and paid_by not in members:
            members = [paid_by] + members
        
        total_members = len(members)
        share_per_person = round(amount / total_members, 2)
        
        with sqlite3.connect(DB_PATH) as conn:
            # Insert main expense
            cur = conn.execute(
                """INSERT INTO expenses(date, time, amount, category, subcategory, 
                   paid_by, note, time_of_day) VALUES (?,?,?,?,?,?,?,?)""",
                (date, time, amount, category, subcategory, paid_by, note, time_of_day)
            )
            expense_id = cur.lastrowid
            
            # Insert splits for each member
            for member in members:
                is_paid = 1 if member == paid_by else 0
                paid_date_val = date if is_paid else None
                
                conn.execute(
                    """INSERT INTO expense_splits(expense_id, member_name, share_amount, 
                       is_paid, paid_date) VALUES (?,?,?,?,?)""",
                    (expense_id, member, share_per_person, is_paid, paid_date_val)
                )
            
            conn.commit()
            
            return {
                "status": "success",
                "expense_id": expense_id,
                "total_amount": amount,
                "split_among": total_members,
                "per_person": share_per_person,
                "members": members,
                "time_of_day": time_of_day
            }
    
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
def add_personal_expense(
    amount: float,
    category: str,
    subcategory: str = "",
    note: str = "",
    date: str = None,
    time: str = None
):
    """
    Add a personal expense (not shared with others).
    
    Args:
        amount: Amount spent
        category: Expense category
        subcategory: More specific category
        note: Additional notes
        date: Date in YYYY-MM-DD format (defaults to today)
        time: Time in HH:MM format (defaults to current time)
    """
    try:
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        if time is None:
            time = get_current_time()
        
        time_of_day = determine_time_of_day(time)
        
        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.execute(
                """INSERT INTO expenses(date, time, amount, category, subcategory, 
                   paid_by, note, time_of_day) VALUES (?,?,?,?,?,?,?,?)""",
                (date, time, amount, category, subcategory, "Me", note, time_of_day)
            )
            expense_id = cur.lastrowid
            
            # Add a split entry for yourself
            conn.execute(
                """INSERT INTO expense_splits(expense_id, member_name, share_amount, 
                   is_paid, paid_date) VALUES (?,?,?,?,?)""",
                (expense_id, "Me", amount, 1, date)
            )
            
            conn.commit()
            
            return {
                "status": "success",
                "expense_id": expense_id,
                "amount": amount,
                "time_of_day": time_of_day
            }
    
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
def get_balances():
    """
    Calculate who owes whom and how much.
    Returns a summary of all pending payments.
    """
    try:
        with sqlite3.connect(DB_PATH) as conn:
            # Get all unpaid splits with expense details
            cur = conn.execute("""
                SELECT 
                    es.member_name,
                    e.paid_by,
                    SUM(es.share_amount) as total_owed
                FROM expense_splits es
                JOIN expenses e ON es.expense_id = e.id
                WHERE es.is_paid = 0 AND es.member_name != e.paid_by
                GROUP BY es.member_name, e.paid_by
                ORDER BY es.member_name, e.paid_by
            """)
            
            balances = []
            for row in cur.fetchall():
                balances.append({
                    "from": row[0],
                    "to": row[1],
                    "amount": round(row[2], 2)
                })
            
            # Calculate net balances
            net_balances = {}
            for balance in balances:
                from_member = balance["from"]
                to_member = balance["to"]
                amount = balance["amount"]
                
                if from_member not in net_balances:
                    net_balances[from_member] = {}
                if to_member not in net_balances[from_member]:
                    net_balances[from_member][to_member] = 0
                
                net_balances[from_member][to_member] += amount
            
            result = {
                "detailed_balances": balances,
                "net_balances": net_balances,
                "total_pending": sum(b["amount"] for b in balances)
            }
            
            return result
    
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
def settle_payment(from_member: str, to_member: str, amount: float, note: str = ""):
    """
    Record a settlement payment between two members.
    
    Args:
        from_member: Person who is paying
        to_member: Person who is receiving
        amount: Amount being paid
        note: Optional note about the settlement
    """
    try:
        settlement_date = datetime.now().strftime("%Y-%m-%d")
        
        with sqlite3.connect(DB_PATH) as conn:
            # Record the settlement
            conn.execute(
                """INSERT INTO settlements(from_member, to_member, amount, 
                   settlement_date, note) VALUES (?,?,?,?,?)""",
                (from_member, to_member, amount, settlement_date, note)
            )
            
            # Mark relevant splits as paid (oldest first)
            cur = conn.execute("""
                SELECT es.id, es.share_amount
                FROM expense_splits es
                JOIN expenses e ON es.expense_id = e.id
                WHERE es.member_name = ? 
                  AND e.paid_by = ? 
                  AND es.is_paid = 0
                ORDER BY e.date ASC, e.time ASC
            """, (from_member, to_member))
            
            remaining_amount = amount
            splits_to_update = []
            
            for split_id, share_amount in cur.fetchall():
                if remaining_amount >= share_amount:
                    splits_to_update.append(split_id)
                    remaining_amount -= share_amount
                else:
                    break
            
            # Update the paid splits
            for split_id in splits_to_update:
                conn.execute(
                    "UPDATE expense_splits SET is_paid = 1, paid_date = ? WHERE id = ?",
                    (settlement_date, split_id)
                )
            
            conn.commit()
            
            return {
                "status": "success",
                "from": from_member,
                "to": to_member,
                "amount_settled": amount,
                "splits_settled": len(splits_to_update),
                "remaining_to_settle": remaining_amount
            }
    
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
def list_expenses(
    start_date: str = None,
    end_date: str = None,
    category: str = None,
    time_of_day: str = None,
    paid_by: str = None,
    limit: int = 50
):
    """
    List expenses with various filters.
    
    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        category: Filter by category
        time_of_day: Filter by time_of_day (morning/afternoon/evening/night)
        paid_by: Filter by who paid
        limit: Maximum number of results
    """
    try:
        with sqlite3.connect(DB_PATH) as conn:
            query = """
                SELECT 
                    e.id,
                    e.date,
                    e.time,
                    e.time_of_day,
                    e.amount,
                    e.category,
                    e.subcategory,
                    e.paid_by,
                    e.note,
                    COUNT(es.id) as split_count
                FROM expenses e
                LEFT JOIN expense_splits es ON e.id = es.expense_id
                WHERE 1=1
            """
            params = []
            
            if start_date:
                query += " AND e.date >= ?"
                params.append(start_date)
            
            if end_date:
                query += " AND e.date <= ?"
                params.append(end_date)
            
            if category:
                query += " AND e.category = ?"
                params.append(category)
            
            if time_of_day:
                query += " AND e.time_of_day = ?"
                params.append(time_of_day)
            
            if paid_by:
                query += " AND e.paid_by = ?"
                params.append(paid_by)
            
            query += " GROUP BY e.id ORDER BY e.date DESC, e.time DESC LIMIT ?"
            params.append(limit)
            
            cur = conn.execute(query, params)
            
            expenses = []
            for row in cur.fetchall():
                expenses.append({
                    "id": row[0],
                    "date": row[1],
                    "time": row[2],
                    "time_of_day": row[3],
                    "amount": row[4],
                    "category": row[5],
                    "subcategory": row[6],
                    "paid_by": row[7],
                    "note": row[8],
                    "split_count": row[9]
                })
            
            return {"status": "success", "expenses": expenses, "count": len(expenses)}
    
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
def get_expense_details(expense_id: int):
    """Get detailed information about a specific expense including all splits."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            # Get expense details
            cur = conn.execute("""
                SELECT id, date, time, time_of_day, amount, category, 
                       subcategory, paid_by, note
                FROM expenses WHERE id = ?
            """, (expense_id,))
            
            expense_row = cur.fetchone()
            if not expense_row:
                return {"status": "error", "message": "Expense not found"}
            
            expense = {
                "id": expense_row[0],
                "date": expense_row[1],
                "time": expense_row[2],
                "time_of_day": expense_row[3],
                "amount": expense_row[4],
                "category": expense_row[5],
                "subcategory": expense_row[6],
                "paid_by": expense_row[7],
                "note": expense_row[8]
            }
            
            # Get split details
            cur = conn.execute("""
                SELECT member_name, share_amount, is_paid, paid_date
                FROM expense_splits WHERE expense_id = ?
                ORDER BY member_name
            """, (expense_id,))
            
            splits = []
            for row in cur.fetchall():
                splits.append({
                    "member": row[0],
                    "share": row[1],
                    "paid": bool(row[2]),
                    "paid_date": row[3]
                })
            
            expense["splits"] = splits
            
            return {"status": "success", "expense": expense}
    
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
def summarize_expenses(
    start_date: str = None,
    end_date: str = None,
    group_by: str = "category"
):
    """
    Get expense summary grouped by various dimensions.
    
    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        group_by: Group by 'category', 'time_of_day', 'paid_by', or 'date'
    """
    try:
        with sqlite3.connect(DB_PATH) as conn:
            group_fields = {
                "category": "e.category",
                "time_of_day": "e.time_of_day",
                "paid_by": "e.paid_by",
                "date": "e.date"
            }
            
            if group_by not in group_fields:
                return {"status": "error", "message": f"Invalid group_by. Use: {', '.join(group_fields.keys())}"}
            
            query = f"""
                SELECT 
                    {group_fields[group_by]} as group_name,
                    COUNT(*) as transaction_count,
                    SUM(e.amount) as total_amount,
                    AVG(e.amount) as avg_amount,
                    MIN(e.amount) as min_amount,
                    MAX(e.amount) as max_amount
                FROM expenses e
                WHERE 1=1
            """
            params = []
            
            if start_date:
                query += " AND e.date >= ?"
                params.append(start_date)
            
            if end_date:
                query += " AND e.date <= ?"
                params.append(end_date)
            
            query += f" GROUP BY {group_fields[group_by]} ORDER BY total_amount DESC"
            
            cur = conn.execute(query, params)
            
            summary = []
            total_all = 0
            for row in cur.fetchall():
                summary.append({
                    "group": row[0],
                    "count": row[1],
                    "total": round(row[2], 2),
                    "average": round(row[3], 2),
                    "min": round(row[4], 2),
                    "max": round(row[5], 2)
                })
                total_all += row[2]
            
            return {
                "status": "success",
                "grouped_by": group_by,
                "summary": summary,
                "grand_total": round(total_all, 2)
            }
    
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
def get_member_report(member_name: str, start_date: str = None, end_date: str = None):
    """
    Get a detailed report for a specific member showing what they paid and owe.
    
    Args:
        member_name: Name of the member
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
    """
    try:
        with sqlite3.connect(DB_PATH) as conn:
            # Amount paid by member
            query_paid = """
                SELECT SUM(amount) FROM expenses 
                WHERE paid_by = ?
            """
            params_paid = [member_name]
            
            if start_date:
                query_paid += " AND date >= ?"
                params_paid.append(start_date)
            if end_date:
                query_paid += " AND date <= ?"
                params_paid.append(end_date)
            
            cur = conn.execute(query_paid, params_paid)
            total_paid = cur.fetchone()[0] or 0
            
            # Amount member owes (their share)
            query_owes = """
                SELECT SUM(es.share_amount) 
                FROM expense_splits es
                JOIN expenses e ON es.expense_id = e.id
                WHERE es.member_name = ?
            """
            params_owes = [member_name]
            
            if start_date:
                query_owes += " AND e.date >= ?"
                params_owes.append(start_date)
            if end_date:
                query_owes += " AND e.date <= ?"
                params_owes.append(end_date)
            
            cur = conn.execute(query_owes, params_owes)
            total_share = cur.fetchone()[0] or 0
            
            # Pending payments
            query_pending = """
                SELECT SUM(es.share_amount) 
                FROM expense_splits es
                JOIN expenses e ON es.expense_id = e.id
                WHERE es.member_name = ? AND es.is_paid = 0
            """
            params_pending = [member_name]
            
            if start_date:
                query_pending += " AND e.date >= ?"
                params_pending.append(start_date)
            if end_date:
                query_pending += " AND e.date <= ?"
                params_pending.append(end_date)
            
            cur = conn.execute(query_pending, params_pending)
            pending_amount = cur.fetchone()[0] or 0
            
            balance = total_paid - total_share
            
            return {
                "status": "success",
                "member": member_name,
                "total_paid": round(total_paid, 2),
                "total_share": round(total_share, 2),
                "balance": round(balance, 2),
                "pending_payments": round(pending_amount, 2),
                "interpretation": "positive means they are owed money, negative means they owe money"
            }
    
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
def delete_expense(expense_id: int):
    """Delete an expense and all its splits."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            # Check if expense exists
            cur = conn.execute("SELECT id FROM expenses WHERE id = ?", (expense_id,))
            if not cur.fetchone():
                return {"status": "error", "message": "Expense not found"}
            
            # Delete splits (will cascade if FK is set up properly, but let's be explicit)
            conn.execute("DELETE FROM expense_splits WHERE expense_id = ?", (expense_id,))
            
            # Delete expense
            conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
            
            conn.commit()
            
            return {"status": "success", "message": f"Expense {expense_id} deleted"}
    
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.resource("expense://members")
def get_members():
    """Get list of all members from the members.json file"""
    try:
        if os.path.exists(MEMBERS_PATH):
            with open(MEMBERS_PATH, "r", encoding="utf-8") as f:
                return f.read()
        else:
            # Create default members file
            default_members = {
                "members": [
                    "Me",
                    "Aman",
                    "Amit",
                    "Apoorva",
                    "Aditya Shahu"
                ],
                "categories": [
                    "travel",
                    "food",
                    "entertainment",
                    "shopping",
                    "utilities",
                    "other"
                ]
            }
            with open(MEMBERS_PATH, "w", encoding="utf-8") as f:
                json.dump(default_members, f, indent=2)
            return json.dumps(default_members)
    except Exception as e:
        return json.dumps({"error": str(e)})



if __name__ == "__main__":
    mcp.run()