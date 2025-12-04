import streamlit as st
from datetime import date
from database import execute_query, execute_procedure
from styles import get_common_styles

st. set_page_config(page_title="Staff Dashboard", page_icon="👔", layout="wide")

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
    st.caption(f"Role: {st.session_state.user_data. get('Role', 'N/A')}")
    st. markdown("---")
    
    menu = st.radio(
        "Chọn chức năng:",
        ["🏠 Dashboard", "📚 Enrollments", "🚫 Withdrawals", "📅 Exam Delays", "🗓️ Quản lý Học kỳ"],  # ✅ THÊM MENU MỚI
        key="staff_menu"
    )
    
    st.markdown("---")
    
    if st.button("🚪 Đăng xuất", use_container_width=True):
        st.session_state.clear()
        st.switch_page("app.py")

# =============================================================================
# DASHBOARD
# =============================================================================
if menu == "🏠 Dashboard":
    # Header
    st.markdown(f"""
    <div class="welcome-box">
        <h1>👔 Staff Dashboard</h1>
        <h2>Xin chào, {st.session_state.full_name}!</h2>
        <p>Staff ID: {st.session_state.user_id}</p>
        <p>Vai trò: {st.session_state.user_data.get('Role', 'N/A')}</p>
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
        st.markdown(f"""
        <div class="stat-box">
            <h2>{pending_withdraw.iloc[0]['cnt'] if not pending_withdraw.empty else 0}</h2>
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
        st.dataframe(recent, use_container_width=True, hide_index=True)
    else:
        st.info("📭 Chưa có hoạt động")

# =============================================================================
# ENROLLMENTS (giữ nguyên code cũ)
# =============================================================================
elif menu == "📚 Enrollments":
    st. title("📚 Quản lý Enrollments")
    
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
            A.StudentID,
            dbo.GetFullName(A.StudentID) as StudentName,
            C. Course_Code,
            C. Title,
            C.Credit,
            S. Semester_Name,
            A. RequestStatus,
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
                    st. markdown(f"**Ngày:** {activity['SubmitDate']}")
                
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
                                    (activity['ActivityID'], 'Approved', st.session_state. user_id)
                                )
                                if success:
                                    st.success("✅ Đã duyệt!")
                                    st.rerun()
                                else:
                                    st.error(msg)
                        
                        with col_b:
                            if st.button("❌", key=f"rej_e_{activity['ActivityID']}", help="Từ chối"):
                                success, msg = execute_procedure(
                                    "EXEC UpdateActivityStatus @p_ActivityID=?, @p_NewStatus=?, @p_StaffID=?",
                                    (activity['ActivityID'], 'Rejected', st.session_state.user_id)
                                )
                                if success:
                                    st.success("✅ Đã từ chối!")
                                    st.rerun()
                                else:
                                    st.error(msg)
                
                st.markdown('</div>', unsafe_allow_html=True)

# =============================================================================
# WITHDRAWALS (giữ nguyên code cũ)
# =============================================================================
elif menu == "🚫 Withdrawals":
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
                    st. markdown(f"**ID:** {activity['ActivityID']}")
                    st.markdown(f"**SV:** {activity['StudentName']} (ID: {activity['StudentID']})")
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
                            if st.button("✅", key=f"app_w_{activity['ActivityID']}", help="Duyệt"):
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
                                    (activity['ActivityID'], 'Rejected', st.session_state.user_id)
                                )
                                if success:
                                    st.success("✅ Đã từ chối!")
                                    st. rerun()
                                else:
                                    st.error(msg)
                
                st. markdown('</div>', unsafe_allow_html=True)

# =============================================================================
# EXAM DELAYS (giữ nguyên code cũ)
# =============================================================================
elif menu == "📅 Exam Delays":
    st.title("📅 Quản lý Exam Delays")
    
    col1, col2 = st.columns(2)
    with col1:
        status_filter = st. selectbox("Lọc trạng thái", ["All", "Pending", "Approved", "Rejected"])
    with col2:
        sort_order = st.selectbox("Sắp xếp", ["Mới nhất", "Cũ nhất"])
    
    query = f"""
        SELECT 
            A.ActivityID,
            A.StudentID,
            dbo.GetFullName(A.StudentID) as StudentName,
            C.Course_Code,
            C.Title,
            ED.Reason,
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
                    st.markdown(f"**MH:** [{activity['Course_Code']}] {activity['Title']}")
                    
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
                            if st.button("✅", key=f"app_d_{activity['ActivityID']}", help="Duyệt"):
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
                                    (activity['ActivityID'], 'Rejected', st.session_state.user_id)
                                )
                                if success:
                                    st.success("✅ Đã từ chối!")
                                    st. rerun()
                                else:
                                    st.error(msg)
                
                st. markdown('</div>', unsafe_allow_html=True)

# =============================================================================
# ✅ QUẢN LÝ HỌC KỲ - CHỨC NĂNG MỚI
# =============================================================================
elif menu == "🗓️ Quản lý Học kỳ":
    st. title("🗓️ Quản lý Học kỳ")
    
    tab1, tab2 = st. tabs(["📋 Danh sách Học kỳ", "➕ Thêm Học kỳ mới"])
    
    # =============================================================================
    # TAB 1: DANH SÁCH HỌC KỲ
    # =============================================================================
    with tab1:
        st.subheader("📋 Tất cả Học kỳ")
        
        # Lấy danh sách học kỳ
        all_semesters = execute_query("""
            SELECT 
                S.SemesterID,
                S.Semester_Name,
                CONVERT(VARCHAR, S.Start_Date, 23) as Start_Date,
                CONVERT(VARCHAR, S.End_Date, 23) as End_Date,
                COUNT(DISTINCT A.StudentID) as TotalStudents,
                COUNT(DISTINCT PC.ProfessorID) as TotalProfessors,
                COUNT(DISTINCT PC.CourseID) as TotalCourses
            FROM Semesters S
            LEFT JOIN Activities A ON S.SemesterID = A.SemesterID
            LEFT JOIN Professor_Course PC ON S.SemesterID = PC. SemesterID
            GROUP BY S.SemesterID, S.Semester_Name, S.Start_Date, S. End_Date
            ORDER BY S.Start_Date DESC
        """)
        
        if all_semesters.empty:
            st.info("📭 Chưa có học kỳ nào")
        else:
            st.success(f"✅ Tổng số: {len(all_semesters)} học kỳ")
            
            # Hiển thị từng học kỳ
            for _, semester in all_semesters. iterrows():
                with st. expander(f"📅 Học kỳ {semester['Semester_Name']} ({semester['Start_Date']} → {semester['End_Date']})"):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("👥 Sinh viên", semester['TotalStudents'])
                    with col2:
                        st. metric("👨‍🏫 Giảng viên", semester['TotalProfessors'])
                    with col3:
                        st.metric("📚 Môn học", semester['TotalCourses'])
                    
                    # Thông tin chi tiết
                    st.markdown("---")
                    st. markdown(f"""
                    **SemesterID:** {semester['SemesterID']}  
                    **Tên:** {semester['Semester_Name']}  
                    **Ngày bắt đầu:** {semester['Start_Date']}  
                    **Ngày kết thúc:** {semester['End_Date']}
                    """)
                    
                    # Nút xóa (chỉ nếu chưa có dữ liệu)
                    if semester['TotalStudents'] == 0 and semester['TotalProfessors'] == 0:
                        if st.button(f"🗑️ Xóa học kỳ {semester['Semester_Name']}", key=f"del_sem_{semester['SemesterID']}", type="secondary"):
                            success, msg = execute_procedure(
                                "EXEC DeleteSemester @p_SemesterID=?",
                                [semester['SemesterID']]
                            )
                            if success:
                                st. success("✅ Đã xóa học kỳ!")
                                st.rerun()
                            else:
                                st.error(msg)
                    else:
                        st.warning("⚠️ Không thể xóa học kỳ đã có dữ liệu")
    
    # =============================================================================
    # TAB 2: THÊM HỌC KỲ MỚI
    # =============================================================================
    with tab2:
        st.subheader("➕ Tạo Học kỳ mới")
        
        st.markdown("""
        <div class="info-box">
            <h3>ℹ️ Hướng dẫn:</h3>
            <ul>
                <li>Tên học kỳ sẽ tự động tạo theo định dạng: <b>YY1</b> (Fall) hoặc <b>YY2</b> (Spring)</li>
                <li>Fall: Tháng 9-12 → Học kỳ 1</li>
                <li>Spring: Tháng 1-5 → Học kỳ 2</li>
                <li>VD: Học kỳ bắt đầu 2024-09-01 → Tên: <b>241</b></li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("add_semester_form"):
            st.markdown("### 📝 Thông tin Học kỳ")
            
            col1, col2 = st. columns(2)
            
            with col1:
                start_date = st.date_input(
                    "Ngày bắt đầu *",
                    value=date. today(),
                    help="Chọn ngày bắt đầu học kỳ"
                )
            
            with col2:
                # Tự động tính ngày kết thúc (khoảng 4 tháng sau)
                from datetime import timedelta
                default_end = start_date + timedelta(days=120)
                
                end_date = st.date_input(
                    "Ngày kết thúc *",
                    value=default_end,
                    help="Chọn ngày kết thúc học kỳ"
                )
            
            # Preview tên học kỳ
            if start_date:
                year = start_date.year % 100
                semester_num = 1 if start_date.month >= 9 else 2
                preview_name = f"{year}{semester_num}"
                
                st.info(f"📌 Tên học kỳ sẽ là: **{preview_name}**")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            col1, col2 = st. columns(2)
            
            with col1:
                submit_btn = st.form_submit_button("✅ Tạo Học kỳ", type="primary", use_container_width=True)
            
            with col2:
                if st.form_submit_button("🔄 Reset", use_container_width=True):
                    st.rerun()
            
            if submit_btn:
                # Validate
                if end_date <= start_date:
                    st.error("❌ Ngày kết thúc phải sau ngày bắt đầu!")
                else:
                    # Kiểm tra trùng lặp
                    existing = execute_query("""
                        SELECT COUNT(*) as cnt
                        FROM Semesters
                        WHERE Start_Date = ?  OR End_Date = ?
                    """, [start_date, end_date])
                    
                    if not existing.empty and existing.iloc[0]['cnt'] > 0:
                        st.warning("⚠️ Đã có học kỳ với ngày này!")
                    else:
                        # Thêm học kỳ mới
                        success, msg = execute_procedure(
                            "EXEC InsertSemester @p_Start_Date=?, @p_End_Date=?",
                            (start_date, end_date)
                        )
                        
                        if success:
                            st.success(f"✅ Đã tạo học kỳ **{preview_name}** thành công!")
                            st. balloons()
                            st.info("💡 Chuyển sang tab 'Danh sách Học kỳ' để xem")
                            st.rerun()
                        else:
                            st. error(msg)