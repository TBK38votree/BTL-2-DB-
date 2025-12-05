"""
Database operations and queries
"""

import sys
import subprocess

def install_if_missing(package):
    try:
        __import__(package)
    except ImportError:
        print(f"📦 Installing {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package, "-q"])

install_if_missing("pyodbc")
install_if_missing("pandas")
install_if_missing("streamlit")
install_if_missing("plotly")

import pyodbc
import pandas as pd
import streamlit as st
import numpy as np

# =============================================================================
# DATABASE CONNECTION
# =============================================================================
DB_CONFIG = {
    'server': 'localhost',
    'database': 'UniversityDB',
    'username': 'sa',
    'password': 'password',
    'driver': '{ODBC Driver 17 for SQL Server}'
}

def get_connection():
    """Get database connection"""
    try:
        conn_str = (
            f"DRIVER={DB_CONFIG['driver']};"
            f"SERVER={DB_CONFIG['server']};"
            f"DATABASE={DB_CONFIG['database']};"
            f"UID={DB_CONFIG['username']};"
            f"PWD={DB_CONFIG['password']}"
        )
        return pyodbc.connect(conn_str)
    except pyodbc. Error as e:
        st. error(f"❌ Không thể kết nối database: {e}")
        return None

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================
def convert_params(params):
    """Convert numpy types to Python native types"""
    if params is None:
        return None
    
    if isinstance(params, (list, tuple)):
        return [
            int(p) if isinstance(p, (np.integer, np.int64, np.int32)) else
            float(p) if isinstance(p, (np.floating, np.float64, np.float32)) else
            str(p) if isinstance(p, (np.str_, np.bytes_)) else
            p
            for p in params
        ]
    return params

def parse_sql_error(error_str):
    """Parse SQL error messages to user-friendly text"""
    error_map = {
        '50007': 'Student không tồn tại',
        '50011': 'Course không tồn tại',
        '50012': 'Semester không tồn tại',
        '50019': 'Vượt quá credit tối đa (21 credits)',
        '50001': 'Credit tối thiểu là 14',
        '50002': 'Credit tối đa là 21',
        '50003': 'Chưa hoàn thành môn tiên quyết',
        '50004': 'Ngày thi không hợp lệ (ngoài học kỳ)',
        '50020': 'Activity không tồn tại',
        'unique_student_course_activity': 'Đã có activity này cho môn học này rồi',
    }
    
    for code, msg in error_map.items():
        if code in error_str:
            return f"❌ {msg}"
    
    return f"❌ Lỗi: {error_str[:200]}"

# =============================================================================
# QUERY FUNCTIONS
# =============================================================================
def execute_query(query, params=None):
    """Execute SELECT query and return DataFrame"""
    conn = get_connection()
    if conn is None:
        return pd. DataFrame()
    
    try:
        converted_params = convert_params(params)
        if converted_params:
            df = pd.read_sql(query, conn, params=converted_params)
        else:
            df = pd.read_sql(query, conn)
        return df
    except Exception as e:
        st.error(f"❌ Query error: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def execute_procedure(proc_query, params=None):
    """Execute stored procedure"""
    conn = get_connection()
    if conn is None:
        return False, "Không thể kết nối database"
    
    cursor = conn.cursor()
    try:
        converted_params = convert_params(params)
        if converted_params:
            cursor. execute(proc_query, converted_params)
        else:
            cursor.execute(proc_query)
        
        conn.commit()
        return True, "Success"
    except pyodbc.Error as e:
        conn.rollback()
        return False, parse_sql_error(str(e))
    finally:
        cursor.close()
        conn.close()

# =============================================================================
# USER AUTHENTICATION
# =============================================================================
def authenticate_user(user_id, role):
    """Authenticate user by ID and role"""
    if role == "Student":
        query = """
            SELECT s.UserID, u.FName, u.LName, u. Email_Address
            FROM Students s
            JOIN Users u ON s.UserID = u.UserID
            WHERE s. UserID = ?
        """
    elif role == "Professor":
        query = """
            SELECT p.UserID, u.FName, u.LName, u. Email_Address, d.Name as Department
            FROM Professors p
            JOIN Users u ON p. UserID = u.UserID
            LEFT JOIN Departments d ON p.DepartmentID = d.DepartmentID
            WHERE p.UserID = ?
        """
    else:  # Staff
        query = """
            SELECT s.UserID, u.FName, u.LName, u. Email_Address, s.Role
            FROM Staff s
            JOIN Users u ON s.UserID = u.UserID
            WHERE s.UserID = ? 
        """
    
    result = execute_query(query, [user_id])
    
    if not result.empty:
        user_data = result.iloc[0]. to_dict()
        return True, user_data
    else:
        return False, None

# =============================================================================
# QUICK STATS
# =============================================================================
def get_student_stats(student_id, semester_id=None):
    """Get statistics for a student"""
    
    # ✅ Nếu không truyền semester_id, đếm tất cả
    semester_filter = f"AND A.SemesterID = {semester_id}" if semester_id else ""
    
    # Enrolled courses (Approved)
    enrolled = execute_query(f"""
        SELECT COUNT(*) as cnt
        FROM Activities A
        WHERE A.StudentID = ?  
        AND A.ActivityType = 'Enrollment'
        AND A.RequestStatus = 'Approved'
        {semester_filter}
    """, [student_id])
    
    # Total credits (Approved only)
    total_credits = execute_query(f"""
        SELECT ISNULL(SUM(C.Credit), 0) as total
        FROM Activities A
        JOIN Courses C ON A.CourseID = C.CourseID
        WHERE A.StudentID = ?   
        AND A.ActivityType = 'Enrollment'
        AND A.RequestStatus = 'Approved'
        {semester_filter}
    """, [student_id])
    
    # Pending activities (all types)
    pending = execute_query("""
        SELECT COUNT(*) as cnt
        FROM Activities
        WHERE StudentID = ?   
        AND RequestStatus = 'Pending'
    """, [student_id])
    
    return {
        'enrolled': enrolled. iloc[0]['cnt'] if not enrolled.empty else 0,
        'credits': total_credits. iloc[0]['total'] if not total_credits.empty else 0,
        'pending': pending. iloc[0]['cnt'] if not pending.empty else 0
    }

def get_current_semester():
    """Get current active semester"""
    result = execute_query("SELECT TOP 1 SemesterID, Semester_Name FROM Semesters ORDER BY Start_Date DESC")
    if not result.empty:
        return result.iloc[0]['SemesterID'], result.iloc[0]['Semester_Name']

    return None, None
