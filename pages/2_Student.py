import streamlit as st
from datetime import date, timedelta
from database import execute_query, execute_procedure, get_student_stats, get_current_semester
from styles import get_common_styles

st.set_page_config(page_title="Student Dashboard", page_icon="👨‍🎓", layout="wide")

# Check authentication
if 'logged_in' not in st.session_state or not st.session_state.logged_in or st.session_state.role != "Student":
    st.error("❌ Vui lòng đăng nhập!")
    if st.button("🔐 Đăng nhập"):
        st.switch_page("pages/1_Login.py")
    st.stop()

# Apply styles
st.markdown(get_common_styles(), unsafe_allow_html=True)

# Sidebar menu
with st.sidebar:
    st. markdown("## 👨‍🎓 Student Menu")
    st.markdown(f"**{st.session_state.full_name}**")
    st.caption(f"ID: {st.session_state. user_id}")
    st.markdown("---")
    
    menu = st.radio(
        "Chọn chức năng:",
        ["🏠 Dashboard", "📚 Đăng ký môn", "🚫 Rút môn", "📅 Hoãn thi", "📋 Lịch sử"],
        key="student_menu"
    )
    
    st.markdown("---")
    
    if st.button("🚪 Đăng xuất", use_container_width=True):
        st.session_state. clear()
        st.switch_page("app.py")

# Get current semester
sem_id, sem_name = get_current_semester()

# ✅ LẤY TẤT CẢ HỌC KỲ + đánh dấu có dữ liệu
all_semesters_with_data = execute_query("""
    SELECT 
        S.SemesterID,
        S. Semester_Name,
        S. Start_Date,
        COUNT(DISTINCT A.ActivityID) as ActivityCount
    FROM Semesters S
    LEFT JOIN Activities A 
        ON S.SemesterID = A.SemesterID 
        AND A.StudentID = ? 
        AND A.ActivityType = 'Enrollment'
    GROUP BY S.SemesterID, S. Semester_Name, S.Start_Date
    ORDER BY S.Start_Date DESC
""", [st. session_state.user_id])

if not all_semesters_with_data. empty:
    # ✅ Tạo display với indicator
    semester_options = []
    for _, sem in all_semesters_with_data.iterrows():
        if sem['ActivityCount'] > 0:
            display = f"📚 {sem['Semester_Name']} ({sem['ActivityCount']} môn)"
        else:
            display = f"📭 {sem['Semester_Name']} (Chưa có dữ liệu)"
        semester_options.append(display)
    
    # ✅ SELECTBOX
    selected_display = st.selectbox(
        "📆 Chọn học kỳ:",
        semester_options,
        help="📚 = Có dữ liệu | 📭 = Chưa có dữ liệu"
    )
    
    # Parse ra SemesterID
    selected_index = semester_options.index(selected_display)
    sem_id = int(all_semesters_with_data.iloc[selected_index]['SemesterID'])
    sem_name = all_semesters_with_data.iloc[selected_index]['Semester_Name']
else:
    st.error("❌ Không có học kỳ nào")
    st.stop()

# =============================================================================
# DASHBOARD
# =============================================================================
if menu == "🏠 Dashboard":
    # Header
    st.markdown(f"""
    <div class="welcome-box">
        <h1>👋 Xin chào, {st.session_state.full_name}!</h1>
        <p>Student ID: {st.session_state.user_id}</p>
        <p>Học kỳ: {sem_name}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Statistics
    stats = get_student_stats(st.session_state.user_id, sem_id)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="stat-box">
            <h2>{stats['enrolled']}</h2>
            <p>Môn đã đăng ký</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="stat-box">
            <h2>{stats['credits']}</h2>
            <p>Tổng tín chỉ</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="stat-box">
            <h2>{stats['pending']}</h2>
            <p>Yêu cầu chờ duyệt</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Recent activities
    st.markdown("## 📋 Hoạt động gần đây")
    
    activities = execute_query("""
        SELECT TOP 10
            A.ActivityID,
            A.ActivityType,
            C.Course_Code,
            C.Title as CourseTitle,
            A.Credit,
            CONVERT(VARCHAR, A. Submission_Date, 23) as SubmitDate,
            S. Semester_Name,
            A.RequestStatus
        FROM Activities A
        JOIN Courses C ON A.CourseID = C.CourseID
        JOIN Semesters S ON A.SemesterID = S. SemesterID
        WHERE A.StudentID = ? 
        ORDER BY A.Submission_Date DESC
    """, [st.session_state.user_id])
    
    if not activities.empty:
        st.dataframe(activities, use_container_width=True, hide_index=True)
    else:
        st.info("📭 Chưa có hoạt động nào")

# =============================================================================
# ĐĂNG KÝ MÔN
# =============================================================================
# Thay thế phần tìm kiếm trong menu "📚 Đăng ký môn"

elif menu == "📚 Đăng ký môn":
    st.title("📚 Đăng ký môn học")
    
    # Current credits
    current_credits = execute_query(
        "SELECT dbo. GetTotalCredits(?, ?) as total",
        [st.session_state.user_id, sem_id]
    )
    credits = current_credits. iloc[0]['total'] if not current_credits.empty else 0
    remaining = 21 - credits
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📆 Học kỳ", sem_name)
    with col2:
        st.metric("📊 Tổng tín chỉ", f"{credits}/21")
    with col3:
        st.metric("✨ Còn lại", f"{remaining} tín chỉ")
    
    st.markdown("---")
    
    # ✅ TÌM KIẾM MÔN HỌC VỚI GỢI Ý
    st.subheader("🔍 Tìm và đăng ký môn học")
    
    # Lấy tất cả môn học
    all_courses = execute_query("""
        SELECT 
            C.CourseID,
            C.Course_Code,
            C.Title,
            C. Credit,
            C.Passing_Score,
            D.Name as Department,
            dbo. GetStudentCountByCourse(C.CourseID) as StudentCount
        FROM Courses C
        LEFT JOIN Departments D ON C.DepartmentID = D. DepartmentID
        ORDER BY C.Course_Code
    """)
    
    if all_courses.empty:
        st. warning("⚠️ Không có môn học nào")
    else:
        # ✅ TẠO DANH SÁCH GỢI Ý
        # Format: "CS101 - Nhập môn Lập trình (3 TC)"
        all_courses['SearchDisplay'] = all_courses. apply(
            lambda row: f"{row['Course_Code']} - {row['Title']} ({row['Credit']} TC)", 
            axis=1
        )
        
        # ✅ SELECTBOX VỚI SEARCH (Gõ để lọc)
        selected_course_display = st.selectbox(
            "**Chọn môn học** (Gõ mã môn hoặc tên môn để tìm kiếm)",
            options=["-- Chọn môn học --"] + all_courses['SearchDisplay'].tolist(),
            help="💡 Bạn có thể gõ 'CS' hoặc 'Lập trình' để tìm nhanh",
            key="course_search"
        )
        
        # ✅ HIỂN THỊ CHI TIẾT MÔN HỌC KHI CHỌN
        if selected_course_display != "-- Chọn môn học --":
            # Lấy thông tin môn học được chọn
            selected_course = all_courses[all_courses['SearchDisplay'] == selected_course_display]. iloc[0]
            
            st.markdown('<div class="card">', unsafe_allow_html=True)
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"### 📖 [{selected_course['Course_Code']}] {selected_course['Title']}")
                st. markdown(f"**📚 Khoa:** {selected_course['Department']}")
                st.markdown(f"**🎓 Tín chỉ:** {selected_course['Credit']} | **📊 Điểm đạt:** {selected_course['Passing_Score']}")
                st.markdown(f"**👥 Sinh viên đã đăng ký:** {selected_course['StudentCount']}")
            
            with col2:
                st.markdown("<br>", unsafe_allow_html=True)
                
                # Check if already enrolled
                already_enrolled = execute_query("""
                    SELECT A.RequestStatus
                    FROM Activities A
                    WHERE A.StudentID = ? AND A. CourseID = ? AND A. ActivityType = 'Enrollment'
                """, [st.session_state.user_id, selected_course['CourseID']])
                
                if not already_enrolled.empty:
                    status = already_enrolled.iloc[0]['RequestStatus']
                    if status == 'Approved':
                        st.success("✅ Đã đăng ký")
                    elif status == 'Pending':
                        st.warning("⏳ Chờ duyệt")
                    else:
                        st. error("❌ Bị từ chối")
                else:
                    # Calculate new total credits
                    new_total = credits + selected_course['Credit']
                    
                    if new_total > 21:
                        st.error(f"❌ Vượt quá 21 TC!")
                        st.caption(f"Hiện tại: {credits} TC")
                        st.caption(f"Sau khi đăng ký: {new_total} TC")
                    else:
                        if st.button("📝 Đăng ký môn này", type="primary", use_container_width=True):
                            from datetime import date
                            from database import execute_procedure
                            
                            success, msg = execute_procedure(
                                "EXEC InsertActivity @p_StudentID=?, @p_CourseID=?, @p_SubmissionDate=?, @p_SemesterID=?, @p_ActivityType=? ",
                                (st.session_state.user_id, selected_course['CourseID'], date.today(), sem_id, 'Enrollment')
                            )
                            
                            if success:
                                st.success("✅ Đăng ký thành công!")
                                st.balloons()
                                st.rerun()
                            else:
                                st.error(msg)
                        
                        # Preview credits
                        st.caption(f"Tín chỉ sau khi đăng ký: {new_total}/21")
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    # ✅ DANH SÁCH ĐÃ ĐĂNG KÝ (giữ nguyên như cũ)
    st.markdown("---")
    st.subheader("📋 Môn đã đăng ký")
    
    enrolled_courses = execute_query("""
        SELECT 
            A.ActivityID,
            C.Course_Code,
            C.Title,
            C.Credit,
            A.RequestStatus,
            CONVERT(VARCHAR, A. Submission_Date, 23) as EnrollDate
        FROM Activities A
        JOIN Courses C ON A.CourseID = C.CourseID
        WHERE A.StudentID = ?  AND A.SemesterID = ?  AND A.ActivityType = 'Enrollment'
        ORDER BY A.Submission_Date DESC
    """, [st. session_state.user_id, sem_id])
    
    if not enrolled_courses.empty:
        st.dataframe(enrolled_courses, use_container_width=True, hide_index=True)
    else:
        st.info("📭 Chưa đăng ký môn nào")

# =============================================================================
# RÚT MÔN
# =============================================================================
elif menu == "🚫 Rút môn":
    st.title("🚫 Rút môn học")
    
    st.markdown("""
    <div class="warning-box">
        <h3>⚠️ Lưu ý:</h3>
        <ul>
            <li>Chỉ rút được môn đã DUYỆT</li>
            <li>Tổng tín chỉ sau khi rút phải ≥ 14</li>
            <li>Cần Staff phê duyệt</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Get approved enrollments
    approved = execute_query("""
        SELECT 
            A.ActivityID,
            A.CourseID,
            C.Course_Code,
            C.Title,
            C.Credit,
            CONVERT(VARCHAR, A.Submission_Date, 23) as EnrollDate
        FROM Activities A
        JOIN Courses C ON A.CourseID = C.CourseID
        WHERE A.StudentID = ? AND A.SemesterID = ? 
        AND A.ActivityType = 'Enrollment' AND A.RequestStatus = 'Approved'
    """, [st.session_state.user_id, sem_id])
    
    if approved.empty:
        st.warning("📭 Không có môn nào được duyệt để rút")
    else:
        current_credits = execute_query(
            "SELECT dbo.GetTotalCredits(?, ?) as total",
            [st.session_state.user_id, sem_id]
        )
        credits = current_credits.iloc[0]['total'] if not current_credits.empty else 0
        
        st.info(f"📊 Tổng tín chỉ hiện tại: **{credits}**")
        
        for _, course in approved.iterrows():
            with st.container():
                st.markdown('<div class="card">', unsafe_allow_html=True)
                
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"### [{course['Course_Code']}] {course['Title']}")
                    st.markdown(f"**Tín chỉ:** {course['Credit']} | **Ngày đăng ký:** {course['EnrollDate']}")
                
                with col2:
                    # Check if already requested withdrawal
                    existing = execute_query("""
                        SELECT RequestStatus FROM Activities
                        WHERE StudentID = ? AND CourseID = ? AND ActivityType = 'Withdrawal'
                    """, [st.session_state.user_id, course['CourseID']])
                    
                    if not existing.empty:
                        st.info(f"⏳ {existing.iloc[0]['RequestStatus']}")
                    else:
                        if st.button("🚫 Rút", key=f"wd_{course['CourseID']}", type="primary"):
                            remaining = credits - course['Credit']
                            
                            if remaining < 14 and remaining > 0:
                                st.warning(f"⚠️ Sau khi rút còn {remaining} < 14 tín chỉ!")
                            
                            success, msg = execute_procedure(
                                "EXEC InsertActivity @p_StudentID=?, @p_CourseID=?, @p_SubmissionDate=?, @p_SemesterID=?, @p_ActivityType=? ",
                                (st.session_state.user_id, course['CourseID'], date.today(), sem_id, 'Withdrawal')
                            )
                            
                            if success:
                                st.success("✅ Yêu cầu rút môn đã gửi!")
                                st.rerun()
                            else:
                                st.error(msg)
                
                st.markdown('</div>', unsafe_allow_html=True)

# =============================================================================
# HOÃN THI
# =============================================================================
elif menu == "📅 Hoãn thi":
    st.title("📅 Hoãn thi")
    
    st.markdown("""
    <div class="info-box">
        <h3>ℹ️ Thông tin:</h3>
        <ul>
            <li>Chỉ hoãn được môn đã DUYỆT</li>
            <li>Ngày thi mới phải trong học kỳ</li>
            <li>Cần lý do hợp lệ</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Get semester dates
    sem_info = execute_query("""
        SELECT Start_Date, End_Date 
        FROM Semesters 
        WHERE SemesterID = ? 
    """, [sem_id])
    
    if sem_info.empty:
        st. error("❌ Không tìm thấy thông tin học kỳ")
        st.stop()
    
    sem_start = sem_info.iloc[0]['Start_Date']
    sem_end = sem_info.iloc[0]['End_Date']
    
    # Get approved enrollments
    approved = execute_query("""
        SELECT 
            A.CourseID,
            C.Course_Code,
            C.Title,
            C.Credit
        FROM Activities A
        JOIN Courses C ON A.CourseID = C.CourseID
        WHERE A.StudentID = ? AND A.SemesterID = ?  
        AND A.ActivityType = 'Enrollment' AND A.RequestStatus = 'Approved'
    """, [st. session_state.user_id, sem_id])
    
    if approved.empty:
        st.warning("📭 Không có môn nào để hoãn thi")
    else:
        for _, course in approved.iterrows():
            with st.expander(f"📖 [{course['Course_Code']}] {course['Title']}"):
                # Check if already requested
                existing = execute_query("""
                    SELECT RequestStatus FROM Activities
                    WHERE StudentID = ? AND CourseID = ? AND ActivityType = 'Exam_Delay'
                """, [st. session_state.user_id, course['CourseID']])
                
                if not existing.empty:
                    st.info(f"⏳ Đã yêu cầu - {existing.iloc[0]['RequestStatus']}")
                else:
                    with st.form(f"delay_{course['CourseID']}"):
                        reason = st.text_area("Lý do hoãn thi *", height=100)
                        
                        col1, col2 = st. columns(2)
                        with col1:
                            old_date = st.date_input("Ngày thi cũ *", min_value=sem_start, max_value=sem_end)
                        with col2:
                            new_date = st.date_input("Ngày thi mới *", min_value=sem_start, max_value=sem_end)
                        
                        if st.form_submit_button("✅ Gửi yêu cầu", type="primary"):
                            if len(reason. strip()) < 10:
                                st.error("❌ Lý do phải ≥ 10 ký tự")
                            elif old_date >= new_date:
                                st.error("❌ Ngày mới phải sau ngày cũ")
                            else:
                                # Insert activity
                                success1, msg1 = execute_procedure(
                                    "EXEC InsertActivity @p_StudentID=?, @p_CourseID=?, @p_SubmissionDate=?, @p_SemesterID=?, @p_ActivityType=?",
                                    (st.session_state.user_id, course['CourseID'], date.today(), sem_id, 'Exam_Delay')
                                )
                                
                                if success1:
                                    # Get ActivityID
                                    activity = execute_query("""
                                        SELECT TOP 1 ActivityID
                                        FROM Activities
                                        WHERE StudentID = ? AND CourseID = ? AND ActivityType = 'Exam_Delay'
                                        ORDER BY ActivityID DESC
                                    """, [st.session_state.user_id, course['CourseID']])
                                    
                                    if not activity.empty:
                                        activity_id = activity.iloc[0]['ActivityID']
                                        
                                        # Insert exam delay
                                        success2, msg2 = execute_procedure(
                                            "EXEC InsertExamDelay @p_ActivityID=?, @p_Reason=?, @p_Old_Exam_Date=?, @p_Requested_New_Exam_Date=?",
                                            (activity_id, reason, old_date, new_date)
                                        )
                                        
                                        if success2:
                                            st.success("✅ Yêu cầu hoãn thi đã gửi!")
                                            st.rerun()
                                        else:
                                            st.error(msg2)
                                else:
                                    st.error(msg1)

# =============================================================================
# LỊCH SỬ
# =============================================================================
elif menu == "📋 Lịch sử":
    st.title("📋 Lịch sử Activities")
    
    tab1, tab2, tab3 = st.tabs(["📚 Enrollments", "🚫 Withdrawals", "📅 Exam Delays"])
    
    with tab1:
        enrollments = execute_query("""
            SELECT 
                A.ActivityID,
                C.Course_Code,
                C.Title,
                A.RequestStatus,
                CONVERT(VARCHAR, A.Submission_Date, 23) as Date
            FROM Activities A
            JOIN Courses C ON A.CourseID = C.CourseID
            WHERE A.StudentID = ?  AND A.ActivityType = 'Enrollment'
            ORDER BY A.Submission_Date DESC
        """, [st.session_state.user_id])
        
        if not enrollments.empty:
            st.dataframe(enrollments, use_container_width=True, hide_index=True)
        else:
            st.info("📭 Chưa có enrollment")
    
    with tab2:
        withdrawals = execute_query("""
            SELECT 
                A.ActivityID,
                C.Course_Code,
                C.Title,
                A.RequestStatus,
                CONVERT(VARCHAR, A.Submission_Date, 23) as Date
            FROM Activities A
            JOIN Courses C ON A.CourseID = C.CourseID
            WHERE A.StudentID = ? AND A. ActivityType = 'Withdrawal'
            ORDER BY A.Submission_Date DESC
        """, [st.session_state.user_id])
        
        if not withdrawals.empty:
            st.dataframe(withdrawals, use_container_width=True, hide_index=True)
        else:
            st.info("📭 Chưa có withdrawal")
    
    with tab3:
        delays = execute_query("""
            SELECT 
                A.ActivityID,
                C.Course_Code,
                C.Title,
                ED.Reason,
                CONVERT(VARCHAR, ED.Old_Exam_Date, 23) as OldDate,
                CONVERT(VARCHAR, ED.Requested_New_Exam_Date, 23) as NewDate,
                A.RequestStatus
            FROM Activities A
            JOIN Courses C ON A.CourseID = C.CourseID
            JOIN Exam_Delays ED ON A.ActivityID = ED.ActivityID
            WHERE A.StudentID = ? AND A.ActivityType = 'Exam_Delay'
            ORDER BY A.Submission_Date DESC
        """, [st.session_state.user_id])
        
        if not delays.empty:
            st.dataframe(delays, use_container_width=True, hide_index=True)
        else:
            st.info("📭 Chưa có exam delay")