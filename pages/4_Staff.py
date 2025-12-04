import streamlit as st
from datetime import date
from database import execute_query, execute_procedure
from styles import get_common_styles

st.set_page_config(page_title="Staff Dashboard", page_icon="👔", layout="wide")

# Check authentication
if 'logged_in' not in st.session_state or not st.session_state.logged_in or st.session_state.role != "Staff":
    st.error("❌ Vui lòng đăng nhập!")
    if st.button("🔐 Đăng nhập"):
        st.switch_page("pages/1_Login.py")
    st.stop()

# Apply styles
st.markdown(get_common_styles(), unsafe_allow_html=True)

# Sidebar menu
with st.sidebar:
    st.markdown("## 👔 Staff Menu")
    st.markdown(f"**{st.session_state.full_name}**")
    st.caption(f"ID: {st.session_state. user_id}")
    st.caption(f"Role: {st.session_state. user_data. get('Role', 'N/A')}")
    st.markdown("---")
    
    # Main menu
    main_menu = st.radio(
        "Chức năng chính:",
        ["🏠 Dashboard", "📋 Duyệt yêu cầu", "⚙️ Quản trị Hệ thống"],
        key="main_menu"
    )
    
    st.markdown("---")
    
    # Sub-menu based on main menu
    if main_menu == "📋 Duyệt yêu cầu":
        sub_menu = st.selectbox(
            "Loại yêu cầu:",
            ["📚 Enrollments", "🚫 Withdrawals", "📅 Exam Delays"]
        )
    
    elif main_menu == "⚙️ Quản trị Hệ thống":
        sub_menu = st.selectbox(
            "Quản lý:",
            [
                "🎓 Students",
                "👨‍🏫 Professors",      
                "📚 Courses",           
                "🗓️ Semesters",
                "🏢 Organizations",     
                "🎓 Programs" 
            ]
        )
    else:
        sub_menu = None
    
    st.markdown("---")
    
    if st.button("🚪 Đăng xuất", use_container_width=True):
        st.session_state.clear()
        st.switch_page("app.py")

# =============================================================================
# DASHBOARD
# =============================================================================
if main_menu == "🏠 Dashboard":
    st.markdown(f"""
    <div class="welcome-box">
        <h1>👔 Staff Dashboard</h1>
        <h2>Xin chào, {st. session_state.full_name}!</h2>
        <p>Staff ID: {st.session_state.user_id}</p>
        <p>Vai trò: {st.session_state. user_data.get('Role', 'N/A')}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Statistics
    pending_enroll = execute_query("SELECT COUNT(*) as cnt FROM Activities WHERE ActivityType='Enrollment' AND RequestStatus='Pending'")
    pending_withdraw = execute_query("SELECT COUNT(*) as cnt FROM Activities WHERE ActivityType='Withdrawal' AND RequestStatus='Pending'")
    pending_delay = execute_query("SELECT COUNT(*) as cnt FROM Activities WHERE ActivityType='Exam_Delay' AND RequestStatus='Pending'")
    total_pending = execute_query("SELECT COUNT(*) as cnt FROM Activities WHERE RequestStatus='Pending'")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="stat-box">
            <h2>{pending_enroll.iloc[0]['cnt'] if not pending_enroll.empty else 0}</h2>
            <p>📚 Enrollment</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st. markdown(f"""
        <div class="stat-box">
            <h2>{pending_withdraw. iloc[0]['cnt'] if not pending_withdraw.empty else 0}</h2>
            <p>🚫 Withdrawal</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="stat-box">
            <h2>{pending_delay.iloc[0]['cnt'] if not pending_delay.empty else 0}</h2>
            <p>📅 Exam Delay</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="stat-box">
            <h2>{total_pending.iloc[0]['cnt'] if not total_pending.empty else 0}</h2>
            <p>⏳ Tổng chờ duyệt</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Recent activities
    st.markdown("## 📋 Hoạt động gần đây")
    
    recent = execute_query("""
        SELECT TOP 20
            A.ActivityID,
            A.ActivityType,
            A.StudentID,
            dbo.GetFullName(A.StudentID) as StudentName,
            C.Course_Code,
            C.Title,
            A.RequestStatus,
            CONVERT(VARCHAR, A. Submission_Date, 23) as SubmitDate
        FROM Activities A
        JOIN Courses C ON A.CourseID = C.CourseID
        ORDER BY A.Submission_Date DESC
    """)
    
    if not recent.empty:
        st. dataframe(recent, use_container_width=True, hide_index=True)
    else:
        st.info("📭 Chưa có hoạt động")

# =============================================================================
# DUYỆT YÊU CẦU
# =============================================================================
elif main_menu == "📋 Duyệt yêu cầu":
    
    if sub_menu == "📚 Enrollments":
        st.title("📚 Quản lý Enrollments")
        
        # Filter
        col1, col2 = st. columns(2)
        with col1:
            status_filter = st.selectbox("Lọc trạng thái", ["All", "Pending", "Approved", "Rejected"])
        with col2:
            sort_order = st.selectbox("Sắp xếp", ["Mới nhất", "Cũ nhất"])
        
        # Query
        query = f"""
            SELECT 
                A.ActivityID,
                A. StudentID,
                dbo.GetFullName(A.StudentID) as StudentName,
                C. Course_Code,
                C. Title,
                C.Credit,
                S.Semester_Name,
                A.RequestStatus,
                CONVERT(VARCHAR, A.Submission_Date, 23) as SubmitDate
            FROM Activities A
            JOIN Courses C ON A.CourseID = C.CourseID
            JOIN Semesters S ON A.SemesterID = S. SemesterID
            WHERE A.ActivityType = 'Enrollment'
            {"AND A.RequestStatus = '" + status_filter + "'" if status_filter != "All" else ""}
            ORDER BY A.Submission_Date {"DESC" if sort_order == "Mới nhất" else "ASC"}
        """
        
        enrollments = execute_query(query)
        
        if enrollments.empty:
            st. info("📭 Không có enrollment")
        else:
            st. success(f"✅ Tìm thấy {len(enrollments)} yêu cầu")
            
            for _, activity in enrollments.iterrows():
                with st.container():
                    st.markdown('<div class="card">', unsafe_allow_html=True)
                    
                    col1, col2, col3 = st.columns([3, 2, 2])
                    
                    with col1:
                        st.markdown(f"**ID:** {activity['ActivityID']}")
                        st.markdown(f"**SV:** {activity['StudentName']} (ID: {activity['StudentID']})")
                        st.markdown(f"**MH:** [{activity['Course_Code']}] {activity['Title']}")
                    
                    with col2:
                        st.markdown(f"**Tín chỉ:** {activity['Credit']}")
                        st. markdown(f"**HK:** {activity['Semester_Name']}")
                        st.markdown(f"**Ngày:** {activity['SubmitDate']}")
                    
                    with col3:
                        status = activity['RequestStatus']
                        
                        if status == 'Approved':
                            st.markdown(f'<span class="status-approved">{status}</span>', unsafe_allow_html=True)
                        elif status == 'Rejected':
                            st.markdown(f'<span class="status-rejected">{status}</span>', unsafe_allow_html=True)
                        else:
                            st. markdown(f'<span class="status-pending">{status}</span>', unsafe_allow_html=True)
                        
                        if status == 'Pending':
                            col_a, col_b = st.columns(2)
                            
                            with col_a:
                                if st.button("✅", key=f"app_e_{activity['ActivityID']}", help="Duyệt"):
                                    success, msg = execute_procedure(
                                        "EXEC UpdateActivityStatus @p_ActivityID=?, @p_NewStatus=?, @p_StaffID=?",
                                        (activity['ActivityID'], 'Approved', st.session_state.user_id)
                                    )
                                    if success:
                                        st. success("✅ Đã duyệt!")
                                        st.rerun()
                                    else:
                                        st.error(msg)
                            
                            with col_b:
                                if st. button("❌", key=f"rej_e_{activity['ActivityID']}", help="Từ chối"):
                                    success, msg = execute_procedure(
                                        "EXEC UpdateActivityStatus @p_ActivityID=?, @p_NewStatus=?, @p_StaffID=? ",
                                        (activity['ActivityID'], 'Rejected', st.session_state.user_id)
                                    )
                                    if success:
                                        st.success("✅ Đã từ chối!")
                                        st.rerun()
                                    else:
                                        st.error(msg)
                    
                    st.markdown('</div>', unsafe_allow_html=True)
    
    elif sub_menu == "🚫 Withdrawals":
        st.title("🚫 Quản lý Withdrawals")
        
        col1, col2 = st. columns(2)
        with col1:
            status_filter = st.selectbox("Lọc trạng thái", ["All", "Pending", "Approved", "Rejected"])
        with col2:
            sort_order = st.selectbox("Sắp xếp", ["Mới nhất", "Cũ nhất"])
        
        query = f"""
            SELECT 
                A.ActivityID,
                A.StudentID,
                dbo.GetFullName(A. StudentID) as StudentName,
                C.Course_Code,
                C.Title,
                C.Credit,
                A.RequestStatus,
                CONVERT(VARCHAR, A.Submission_Date, 23) as SubmitDate
            FROM Activities A
            JOIN Courses C ON A. CourseID = C.CourseID
            WHERE A.ActivityType = 'Withdrawal'
            {"AND A. RequestStatus = '" + status_filter + "'" if status_filter != "All" else ""}
            ORDER BY A.Submission_Date {"DESC" if sort_order == "Mới nhất" else "ASC"}
        """
        
        withdrawals = execute_query(query)
        
        if withdrawals.empty:
            st.info("📭 Không có withdrawal")
        else:
            st.success(f"✅ Tìm thấy {len(withdrawals)} yêu cầu")
            
            for _, activity in withdrawals.iterrows():
                with st.container():
                    st.markdown('<div class="card">', unsafe_allow_html=True)
                    
                    col1, col2, col3 = st.columns([3, 2, 2])
                    
                    with col1:
                        st.markdown(f"**ID:** {activity['ActivityID']}")
                        st. markdown(f"**SV:** {activity['StudentName']} (ID: {activity['StudentID']})")
                        st.markdown(f"**MH:** [{activity['Course_Code']}] {activity['Title']}")
                    
                    with col2:
                        st.markdown(f"**Tín chỉ:** {activity['Credit']}")
                        st.markdown(f"**Ngày:** {activity['SubmitDate']}")
                    
                    with col3:
                        status = activity['RequestStatus']
                        
                        if status == 'Approved':
                            st.markdown(f'<span class="status-approved">{status}</span>', unsafe_allow_html=True)
                        elif status == 'Rejected':
                            st.markdown(f'<span class="status-rejected">{status}</span>', unsafe_allow_html=True)
                        else:
                            st.markdown(f'<span class="status-pending">{status}</span>', unsafe_allow_html=True)
                        
                        if status == 'Pending':
                            col_a, col_b = st.columns(2)
                            
                            with col_a:
                                if st. button("✅", key=f"app_w_{activity['ActivityID']}", help="Duyệt"):
                                    success, msg = execute_procedure(
                                        "EXEC UpdateActivityStatus @p_ActivityID=?, @p_NewStatus=?, @p_StaffID=?",
                                        (activity['ActivityID'], 'Approved', st.session_state.user_id)
                                    )
                                    if success:
                                        st.success("✅ Đã duyệt!")
                                        st.rerun()
                                    else:
                                        st.error(msg)
                            
                            with col_b:
                                if st.button("❌", key=f"rej_w_{activity['ActivityID']}", help="Từ chối"):
                                    success, msg = execute_procedure(
                                        "EXEC UpdateActivityStatus @p_ActivityID=?, @p_NewStatus=?, @p_StaffID=?",
                                        (activity['ActivityID'], 'Rejected', st.session_state. user_id)
                                    )
                                    if success:
                                        st.success("✅ Đã từ chối!")
                                        st.rerun()
                                    else:
                                        st. error(msg)
                    
                    st.markdown('</div>', unsafe_allow_html=True)
    
    elif sub_menu == "📅 Exam Delays":
        st.title("📅 Quản lý Exam Delays")
        
        col1, col2 = st.columns(2)
        with col1:
            status_filter = st.selectbox("Lọc trạng thái", ["All", "Pending", "Approved", "Rejected"])
        with col2:
            sort_order = st.selectbox("Sắp xếp", ["Mới nhất", "Cũ nhất"])
        
        query = f"""
            SELECT 
                A.ActivityID,
                A. StudentID,
                dbo. GetFullName(A.StudentID) as StudentName,
                C.Course_Code,
                C.Title,
                ED. Reason,
                CONVERT(VARCHAR, ED.Old_Exam_Date, 23) as OldDate,
                CONVERT(VARCHAR, ED. Requested_New_Exam_Date, 23) as NewDate,
                A.RequestStatus,
                CONVERT(VARCHAR, A.Submission_Date, 23) as SubmitDate
            FROM Activities A
            JOIN Courses C ON A. CourseID = C.CourseID
            JOIN Exam_Delays ED ON A.ActivityID = ED.ActivityID
            WHERE A.ActivityType = 'Exam_Delay'
            {"AND A.RequestStatus = '" + status_filter + "'" if status_filter != "All" else ""}
            ORDER BY A.Submission_Date {"DESC" if sort_order == "Mới nhất" else "ASC"}
        """
        
        delays = execute_query(query)
        
        if delays.empty:
            st.info("📭 Không có exam delay")
        else:
            st. success(f"✅ Tìm thấy {len(delays)} yêu cầu")
            
            for _, activity in delays.iterrows():
                with st.container():
                    st.markdown('<div class="card">', unsafe_allow_html=True)
                    
                    col1, col2, col3 = st.columns([3, 2, 2])
                    
                    with col1:
                        st.markdown(f"**ID:** {activity['ActivityID']}")
                        st.markdown(f"**SV:** {activity['StudentName']} (ID: {activity['StudentID']})")
                        st. markdown(f"**MH:** [{activity['Course_Code']}] {activity['Title']}")
                        
                        with st.expander("📝 Lý do"):
                            st.write(activity['Reason'])
                    
                    with col2:
                        st.markdown(f"**Ngày cũ:** {activity['OldDate']}")
                        st.markdown(f"**Ngày mới:** {activity['NewDate']}")
                        st.markdown(f"**Ngày nộp:** {activity['SubmitDate']}")
                    
                    with col3:
                        status = activity['RequestStatus']
                        
                        if status == 'Approved':
                            st.markdown(f'<span class="status-approved">{status}</span>', unsafe_allow_html=True)
                        elif status == 'Rejected':
                            st.markdown(f'<span class="status-rejected">{status}</span>', unsafe_allow_html=True)
                        else:
                            st.markdown(f'<span class="status-pending">{status}</span>', unsafe_allow_html=True)
                        
                        if status == 'Pending':
                            col_a, col_b = st.columns(2)
                            
                            with col_a:
                                if st. button("✅", key=f"app_d_{activity['ActivityID']}", help="Duyệt"):
                                    success, msg = execute_procedure(
                                        "EXEC UpdateActivityStatus @p_ActivityID=?, @p_NewStatus=?, @p_StaffID=?",
                                        (activity['ActivityID'], 'Approved', st.session_state.user_id)
                                    )
                                    if success:
                                        st.success("✅ Đã duyệt!")
                                        st.rerun()
                                    else:
                                        st.error(msg)
                            
                            with col_b:
                                if st.button("❌", key=f"rej_d_{activity['ActivityID']}", help="Từ chối"):
                                    success, msg = execute_procedure(
                                        "EXEC UpdateActivityStatus @p_ActivityID=?, @p_NewStatus=?, @p_StaffID=?",
                                        (activity['ActivityID'], 'Rejected', st.session_state. user_id)
                                    )
                                    if success:
                                        st.success("✅ Đã từ chối!")
                                        st.rerun()
                                    else:
                                        st. error(msg)
                    
                    st.markdown('</div>', unsafe_allow_html=True)

# =============================================================================
# QUẢN TRỊ HỆ THỐNG
# =============================================================================
elif main_menu == "⚙️ Quản trị Hệ thống":
    if sub_menu == "🎓 Students":
        from staff_modules. students import render_students_management
        render_students_management()
    
    elif sub_menu == "👨‍🏫 Professors":
        from staff_modules.professors import render_professors_management
        render_professors_management()
    elif sub_menu == "📚 Courses":          
        from staff_modules. courses import render_courses_management
        render_courses_management()
    
    elif sub_menu == "🗓️ Semesters":
        from staff_modules.semesters import render_semesters_management
        render_semesters_management()
    
    elif sub_menu == "🏢 Organizations":   
        from staff_modules. organizations import render_organizations_management
        render_organizations_management()
    
    elif sub_menu == "🎓 Programs":         
        from staff_modules. programs import render_programs_management
        render_programs_management()
        