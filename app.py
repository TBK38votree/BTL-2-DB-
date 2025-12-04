import streamlit as st
from styles import get_login_styles

st.set_page_config(
    page_title="University Management System",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Apply styles
st.markdown(get_login_styles(), unsafe_allow_html=True)

# Clear session when returning to home
if 'reset' not in st.session_state:
    st.session_state. clear()
    st.session_state.reset = True

# Header
st.markdown("""
<div style='text-align: center; margin: 50px 0;'>
    <h1 style='font-size: 56px; color: #667eea; margin-bottom: 20px;'>🎓 UNIVERSITY MANAGEMENT SYSTEM</h1>
    <p style='font-size: 20px; color: #666;'>Hệ thống Quản lý Đại học - Chọn vai trò để đăng nhập</p>
</div>
""", unsafe_allow_html=True)

# Role selection
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="role-card">
        <h2>👨‍🎓</h2>
        <h3>STUDENT</h3>
        <p>Sinh viên</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("Đăng nhập Student", use_container_width=True, type="primary", key="s"):
        st.session_state.role = "Student"
        st. switch_page("pages/1_Login.py")

with col2:
    st.markdown("""
    <div class="role-card">
        <h2>👨‍🏫</h2>
        <h3>PROFESSOR</h3>
        <p>Giảng viên</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("Đăng nhập Professor", use_container_width=True, type="primary", key="p"):
        st.session_state. role = "Professor"
        st.switch_page("pages/1_Login.py")

with col3:
    st.markdown("""
    <div class="role-card">
        <h2>👔</h2>
        <h3>STAFF</h3>
        <p>Nhân viên</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("Đăng nhập Staff", use_container_width=True, type="primary", key="st"):
        st.session_state.role = "Staff"
        st.switch_page("pages/1_Login.py")

# Footer
st.markdown("""
<div style='text-align: center; margin-top: 100px; color: #666;'>
    <p><b>🎓 University Management System</b></p>
    <p>Built with Streamlit & SQL Server | BTL2 - Hệ Quản Trị CSDL</p>
</div>
""", unsafe_allow_html=True)