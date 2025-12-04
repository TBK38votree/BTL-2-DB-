"""
Centralized CSS styles for the application
"""

def get_common_styles():
    """Common styles used across all pages"""
    return """
    <style>
        /* Hide Streamlit default pages navigation */
        section[data-testid="stSidebarNav"] { display: none !important; }
        
        /* Hide sidebar toggle button on certain pages */
        button[kind="header"] { display: none; }
        
        /* Welcome/Header box gradient */
        .welcome-box {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 30px;
            box-shadow: 0 10px 20px rgba(0,0,0,0.1);
        }
        
        .welcome-box h1 {
            margin: 0 0 10px 0;
        }
        
        .welcome-box p {
            margin: 5px 0;
            opacity: 0.95;
        }
        
        /* Stat boxes */
        .stat-box {
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            text-align: center;
            transition: transform 0.2s;
        }
        
        .stat-box:hover {
            transform: translateY(-3px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.12);
        }
        
        .stat-box h2 {
            color: #667eea;
            margin: 0;
            font-size: 42px;
            font-weight: 700;
        }
        
        .stat-box p {
            color: #666;
            margin: 10px 0 0 0;
            font-size: 14px;
        }
        
        /* Status badges */
        .status-pending { 
            background: #ffc107; 
            color: #000; 
            padding: 6px 14px; 
            border-radius: 20px; 
            font-weight: 600; 
            font-size: 12px;
            display: inline-block;
        }
        
        .status-approved { 
            background: #28a745; 
            color: white; 
            padding: 6px 14px; 
            border-radius: 20px; 
            font-weight: 600; 
            font-size: 12px;
            display: inline-block;
        }
        
        .status-rejected { 
            background: #dc3545; 
            color: white; 
            padding: 6px 14px; 
            border-radius: 20px; 
            font-weight: 600; 
            font-size: 12px;
            display: inline-block;
        }
        
        /* Cards */
        .card {
            background: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            margin: 10px 0;
            border-left: 5px solid #667eea;
        }
        
        .card:hover {
            box-shadow: 0 4px 12px rgba(0,0,0,0.12);
        }
        
        /* Info/Warning boxes */
        .info-box {
            background: #e7f3ff;
            border: 2px solid #2196F3;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
        }
        
        .warning-box {
            background: #fff3cd;
            border: 2px solid #ffc107;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
        }
    </style>
    """

def get_login_styles():
    """Styles specifically for login page"""
    return """
    <style>
        [data-testid="stSidebar"] { display: none ! important; }
        
        . login-container {
            max-width: 500px;
            margin: 100px auto;
            padding: 40px;
            background: white;
            border-radius: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        }
        
        .login-title {
            text-align: center;
            color: #667eea;
            font-size: 36px;
            font-weight: 700;
            margin-bottom: 30px;
        }
        
        . role-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 30px;
            border-radius: 15px;
            text-align: center;
            cursor: pointer;
            transition: transform 0.3s, box-shadow 0.3s;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin: 20px 0;
        }
        
        . role-card:hover {
            transform: translateY(-10px);
            box-shadow: 0 20px 40px rgba(0,0,0,0.3);
        }
        
        .role-card h2 {
            font-size: 48px;
            margin: 20px 0;
        }
    </style>
    """