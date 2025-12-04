import streamlit as st
import plotly.express as px
from database import execute_query, get_current_semester
from styles import get_common_styles

st.set_page_config(page_title="Professor Dashboard", page_icon="👨‍🏫", layout="wide")

# Check authentication
if 'logged_in' not in st.session_state or not st.session_state.logged_in or st.session_state.role != "Professor":
    st.error("❌ Vui lòng đăng nhập!")
    if st.button("🔐 Đăng nhập"):
        st.switch_page("pages/1_Login.py")
    st.stop()

# Apply styles
st.markdown(get_common_styles(), unsafe_allow_html=True)

# Sidebar menu
with st.sidebar:
    st. markdown("## 👨‍🏫 Professor Menu")
    st.markdown(f"**{st.session_state.full_name}**")
    st.caption(f"ID: {st.session_state. user_id}")
    st. caption(f"Khoa: {st.session_state.user_data. get('Department', 'N/A')}")
    st.markdown("---")
    
    menu = st.radio(
        "Chọn chức năng:",
        ["🏠 Dashboard", "📚 Môn học của tôi", "👥 Sinh viên", "📊 Thống kê"],
        key="prof_menu"
    )
    
    st.markdown("---")
    
    if st.button("🚪 Đăng xuất", use_container_width=True):
        st.session_state.clear()
        st.switch_page("app.py")

# Thay đoạn selectbox học kỳ:

# ✅ LẤY TẤT CẢ HỌC KỲ + đánh dấu có teaching assignment
all_semesters_with_teaching = execute_query("""
    SELECT 
        S.SemesterID,
        S. Semester_Name,
        S. Start_Date,
        COUNT(DISTINCT PC.CourseID) as CourseCount,
        COUNT(DISTINCT A.StudentID) as StudentCount
    FROM Semesters S
    LEFT JOIN Professor_Course PC 
        ON S.SemesterID = PC.SemesterID 
        AND PC.ProfessorID = ?
    LEFT JOIN Activities A 
        ON PC.CourseID = A.CourseID 
        AND PC.SemesterID = A. SemesterID
        AND A.ActivityType = 'Enrollment'
        AND A.RequestStatus = 'Approved'
    GROUP BY S.SemesterID, S.Semester_Name, S.Start_Date
    ORDER BY S.Start_Date DESC
""", [st.session_state. user_id])

if not all_semesters_with_teaching.empty:
    # ✅ Tạo display với indicator
    semester_options = []
    for _, sem in all_semesters_with_teaching. iterrows():
        if sem['CourseCount'] > 0:
            display = f"👨‍🏫 {sem['Semester_Name']} ({sem['CourseCount']} môn, {sem['StudentCount']} SV)"
        else:
            display = f"📭 {sem['Semester_Name']} (Chưa có phân công)"
        semester_options.append(display)
    
    # ✅ SELECTBOX
    selected_display = st.selectbox(
        "📆 Chọn học kỳ:",
        semester_options,
        help="👨‍🏫 = Có giảng dạy | 📭 = Chưa có phân công"
    )
    
    # Parse ra SemesterID
    selected_index = semester_options.index(selected_display)
    sem_id = int(all_semesters_with_teaching.iloc[selected_index]['SemesterID'])
    sem_name = all_semesters_with_teaching.iloc[selected_index]['Semester_Name']
else:
    st. error("❌ Không có học kỳ nào")
    st.stop()

# =============================================================================
# DASHBOARD
# =============================================================================
if menu == "🏠 Dashboard":
    st.markdown(f"""
    <div class="welcome-box">
        <h1>👨‍🏫 Professor Dashboard</h1>
        <h2>Xin chào, {st. session_state.full_name}!</h2>
        <p>Professor ID: {st.session_state.user_id}</p>
        <p>Khoa: {st.session_state.user_data.get('Department', 'N/A')}</p>
        <p>Học kỳ: {sem_name}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # ✅ QUERY ĐÃ SỬA - Dùng INNER JOIN rõ ràng
    courses_teaching = execute_query("""
        SELECT COUNT(*) as cnt
        FROM Professor_Course
        WHERE ProfessorID = ? AND SemesterID = ?
    """, [st.session_state.user_id, sem_id])
    
    # ✅ SỬA: INNER JOIN + điều kiện rõ ràng
    total_students = execute_query("""
        SELECT COUNT(DISTINCT A.StudentID) as cnt
        FROM Activities A
        INNER JOIN Professor_Course PC 
            ON A.CourseID = PC.CourseID 
            AND A.SemesterID = PC. SemesterID
        WHERE PC.ProfessorID = ?  
        AND PC.SemesterID = ? 
        AND A.ActivityType = 'Enrollment' 
        AND A.RequestStatus = 'Approved'
    """, [st.session_state.user_id, sem_id])
    
    pending_activities = execute_query("""
        SELECT COUNT(*) as cnt
        FROM Activities A
        INNER JOIN Professor_Course PC 
            ON A.CourseID = PC.CourseID 
            AND A.SemesterID = PC.SemesterID
        WHERE PC.ProfessorID = ?   
        AND PC.SemesterID = ?
        AND A.ActivityType = 'Enrollment'  -- ✅ CHỈ ĐẾM ENROLLMENT
        AND A.RequestStatus = 'Pending'
    """, [st.session_state.user_id, sem_id])
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="stat-box">
            <h2>{courses_teaching.iloc[0]['cnt'] if not courses_teaching.empty else 0}</h2>
            <p>📚 Môn đang dạy</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="stat-box">
            <h2>{total_students.iloc[0]['cnt'] if not total_students.empty else 0}</h2>
            <p>👥 Tổng sinh viên</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="stat-box">
            <h2>{pending_activities.iloc[0]['cnt'] if not pending_activities.empty else 0}</h2>
            <p>⏳ Yêu cầu chờ duyệt</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Overview
    st.markdown("## 📋 Tổng quan môn học")
    
    overview = execute_query("""
        SELECT 
            C.Course_Code,
            C.Title,
            C.Credit,
            (SELECT COUNT(DISTINCT StudentID) 
             FROM Activities 
             WHERE CourseID = C.CourseID 
             AND SemesterID = ?  
             AND ActivityType = 'Enrollment' 
             AND RequestStatus = 'Approved') as EnrolledStudents
        FROM Professor_Course PC
        JOIN Courses C ON PC.CourseID = C. CourseID
        WHERE PC. ProfessorID = ? AND PC.SemesterID = ? 
        ORDER BY C.Course_Code
    """, [sem_id, st.session_state.user_id, sem_id])
    
    if not overview.empty:
        st.dataframe(overview, use_container_width=True, hide_index=True)
    else:
        st.info("📭 Chưa được phân công môn học nào")

# =============================================================================
# MÔN HỌC CỦA TÔI
# =============================================================================
elif menu == "📚 Môn học của tôi":
    st.title("📚 Môn học đang giảng dạy")
    
    my_courses = execute_query("""
        SELECT 
            C.CourseID,
            C.Course_Code,
            C.Title,
            C.Credit,
            C.Passing_Score,
            (SELECT COUNT(DISTINCT StudentID) 
             FROM Activities 
             WHERE CourseID = C.CourseID 
             AND SemesterID = ? 
             AND ActivityType = 'Enrollment' 
             AND RequestStatus = 'Approved') as EnrolledStudents
        FROM Professor_Course PC
        JOIN Courses C ON PC.CourseID = C. CourseID
        WHERE PC. ProfessorID = ? AND PC.SemesterID = ? 
        ORDER BY C.Course_Code
    """, [sem_id, st.session_state. user_id, sem_id])
    
    if my_courses.empty:
        st.info("📭 Chưa được phân công môn học nào")
    else:
        for _, course in my_courses.iterrows():
            with st.expander(f"📖 [{course['Course_Code']}] {course['Title']} - {course['EnrolledStudents']} sinh viên"):
                col1, col2 = st. columns(2)
                
                with col1:
                    st.markdown(f"""
                    **Mã môn:** {course['Course_Code']}  
                    **Tên môn:** {course['Title']}  
                    **Tín chỉ:** {course['Credit']}  
                    **Điểm đạt:** {course['Passing_Score']}  
                    **Sinh viên:** {course['EnrolledStudents']}
                    """)
                
                with col2:
                    status_breakdown = execute_query("""
                        SELECT 
                            RequestStatus,
                            COUNT(*) as Count
                        FROM Activities
                        WHERE CourseID = ?  AND SemesterID = ?  AND ActivityType = 'Enrollment'
                        GROUP BY RequestStatus
                    """, [course['CourseID'], sem_id])
                    
                    if not status_breakdown.empty:
                        st.markdown("**Phân bố trạng thái:**")
                        for _, status in status_breakdown.iterrows():
                            if status['RequestStatus'] == 'Approved':
                                st.markdown(f'<span class="status-approved">{status["RequestStatus"]}: {status["Count"]}</span>', unsafe_allow_html=True)
                            elif status['RequestStatus'] == 'Pending':
                                st.markdown(f'<span class="status-pending">{status["RequestStatus"]}: {status["Count"]}</span>', unsafe_allow_html=True)
                            else:
                                st. markdown(f'<span class="status-rejected">{status["RequestStatus"]}: {status["Count"]}</span>', unsafe_allow_html=True)
                
                st.markdown("### 👥 Danh sách sinh viên")
                
                students = execute_query("""
                    SELECT 
                        A.StudentID,
                        dbo.GetFullName(A.StudentID) as StudentName,
                        U.Email_Address,
                        A.RequestStatus,
                        CONVERT(VARCHAR, A. Submission_Date, 23) as EnrollDate
                    FROM Activities A
                    JOIN Students S ON A.StudentID = S. UserID
                    JOIN Users U ON S.UserID = U.UserID
                    WHERE A.CourseID = ? AND A.SemesterID = ? AND A. ActivityType = 'Enrollment'
                    ORDER BY A.RequestStatus, StudentName
                """, [course['CourseID'], sem_id])
                
                if not students. empty:
                    st.dataframe(students, use_container_width=True, hide_index=True)
                else:
                    st.info("Chưa có sinh viên đăng ký")

# =============================================================================
# SINH VIÊN
# =============================================================================
elif menu == "👥 Sinh viên":
    st.title("👥 Tra cứu sinh viên")
    
    # ✅ LẤY DANH SÁCH SINH VIÊN
    all_students = execute_query("""
        SELECT 
            S. UserID,
            dbo. GetFullName(S.UserID) as FullName,
            U.Email_Address,
            U.Phone_Number,
            CONVERT(VARCHAR, S.Birthday, 23) as Birthday
        FROM Students S
        JOIN Users U ON S.UserID = U.UserID
        ORDER BY S.UserID
    """)
    
    if all_students.empty:
        st.warning("⚠️ Không có sinh viên nào trong hệ thống")
    else:
        # ✅ TẠO DISPLAY STRING
        all_students['SearchDisplay'] = all_students.apply(
            lambda row: f"ID: {row['UserID']} - {row['FullName']} ({row['Email_Address']})", 
            axis=1
        )
        
        # ✅ SELECTBOX VỚI SEARCH
        st.markdown("### 🔍 Tìm kiếm sinh viên")
        
        selected_student_display = st.selectbox(
            "**Chọn sinh viên** (Gõ ID, tên hoặc email để tìm kiếm)",
            options=["-- Chọn sinh viên --"] + all_students['SearchDisplay'].tolist(),
            help="💡 Bạn có thể gõ ID (VD: 11), tên (VD: Mai) hoặc email để tìm nhanh",
            key="student_search"
        )
        
        # ✅ HIỂN THỊ CHI TIẾT KHI CHỌN
        if selected_student_display != "-- Chọn sinh viên --":
            # Lấy thông tin sinh viên được chọn
            selected_student = all_students[all_students['SearchDisplay'] == selected_student_display]. iloc[0]
            search_id = selected_student['UserID']
            
            # Student info card
            st.markdown('<div class="card">', unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"""
                ### 👨‍🎓 Thông tin sinh viên
                **Student ID:** {selected_student['UserID']}  
                **Họ tên:** {selected_student['FullName']}  
                **Email:** {selected_student['Email_Address']}
                """)
            
            with col2:
                st.markdown(f"""
                ### 📞 Liên hệ
                **Điện thoại:** {selected_student['Phone_Number']}  
                **Ngày sinh:** {selected_student['Birthday']}
                """)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # ✅ THÔNG TIN HỌC TẬP
            st.markdown("---")
            
            # Tổng credits
            total_credits = execute_query(
                "SELECT dbo.GetTotalCredits(?, ?) as Total",
                [search_id, sem_id]
            )
            
            if not total_credits.empty:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        f"📊 Tổng tín chỉ HK {sem_name}",
                        f"{total_credits. iloc[0]['Total']} tín chỉ"
                    )
                
                with col2:
                    # Đếm môn đã đăng ký
                    enrolled_count = execute_query("""
                        SELECT COUNT(*) as cnt
                        FROM Activities
                        WHERE StudentID = ? AND SemesterID = ? 
                        AND ActivityType = 'Enrollment' AND RequestStatus = 'Approved'
                    """, [search_id, sem_id])
                    
                    st.metric(
                        "📚 Môn đã đăng ký",
                        enrolled_count.iloc[0]['cnt'] if not enrolled_count.empty else 0
                    )
                
                with col3:
                    # Pending requests
                    pending_count = execute_query("""
                        SELECT COUNT(*) as cnt
                        FROM Activities
                        WHERE StudentID = ? AND RequestStatus = 'Pending'
                    """, [search_id])
                    
                    st.metric(
                        "⏳ Yêu cầu chờ duyệt",
                        pending_count.iloc[0]['cnt'] if not pending_count. empty else 0
                    )
            
            # ✅ DANH SÁCH MÔN HỌC ĐÃ ĐĂNG KÝ
            st.markdown("### 📚 Lịch sử đăng ký môn học")
            
            # Tabs: All semesters vs Current semester
            tab1, tab2 = st.tabs(["📅 Tất cả học kỳ", f"📆 Học kỳ {sem_name}"])
            
            with tab1:
                all_courses = execute_query("""
                    SELECT 
                        C.Course_Code,
                        C. Title,
                        C.Credit,
                        S. Semester_Name,
                        A.RequestStatus,
                        CONVERT(VARCHAR, A.Submission_Date, 23) as EnrollDate
                    FROM Activities A
                    JOIN Courses C ON A.CourseID = C.CourseID
                    JOIN Semesters S ON A.SemesterID = S. SemesterID
                    WHERE A.StudentID = ? AND A.ActivityType = 'Enrollment'
                    ORDER BY S.Start_Date DESC, C.Course_Code
                """, [search_id])
                
                if not all_courses. empty:
                    st.dataframe(all_courses, use_container_width=True, hide_index=True)
                else:
                    st.info("📭 Chưa đăng ký môn nào")
            
            with tab2:
                current_courses = execute_query("""
                    SELECT 
                        C. Course_Code,
                        C.Title,
                        C. Credit,
                        A.RequestStatus,
                        CONVERT(VARCHAR, A.Submission_Date, 23) as EnrollDate
                    FROM Activities A
                    JOIN Courses C ON A.CourseID = C. CourseID
                    WHERE A.StudentID = ? 
                    AND A.SemesterID = ?  
                    AND A.ActivityType = 'Enrollment'
                    ORDER BY A.Submission_Date DESC
                """, [search_id, sem_id])
                
                if not current_courses.empty:
                    st.dataframe(current_courses, use_container_width=True, hide_index=True)
                else:
                    st.info(f"📭 Chưa đăng ký môn nào trong học kỳ {sem_name}")
            
            # ✅ BIỂU ĐỒ PHÂN BỐ TRẠNG THÁI
            st. markdown("### 📊 Phân bố trạng thái đăng ký")
            
            status_dist = execute_query("""
                SELECT 
                    RequestStatus,
                    COUNT(*) as Count
                FROM Activities
                WHERE StudentID = ? AND ActivityType = 'Enrollment'
                GROUP BY RequestStatus
            """, [search_id])
            
            if not status_dist.empty:
                import plotly.express as px
                
                fig = px.pie(
                    status_dist,
                    values='Count',
                    names='RequestStatus',
                    title='Trạng thái các yêu cầu đăng ký',
                    color='RequestStatus',
                    color_discrete_map={
                        'Approved': '#28a745',
                        'Pending': '#ffc107',
                        'Rejected': '#dc3545'
                    }
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # ✅ THÔNG TIN THÊM
            with st.expander("📋 Thông tin chi tiết"):
                # Chương trình đào tạo
                program_info = execute_query("""
                    SELECT 
                        DP.Name as ProgramName,
                        DP.Code as ProgramCode,
                        CONVERT(VARCHAR, SP. Enrollment_Date, 23) as EnrollmentDate
                    FROM Student_Program SP
                    JOIN Degree_Programs DP ON SP.ProgramID = DP.ProgramID
                    WHERE SP.StudentID = ? 
                """, [search_id])
                
                if not program_info.empty:
                    st.markdown("**🎓 Chương trình đào tạo:**")
                    for _, prog in program_info.iterrows():
                        st.markdown(f"- [{prog['ProgramCode']}] {prog['ProgramName']} (Từ {prog['EnrollmentDate']})")
                else:
                    st.info("Chưa đăng ký chương trình đào tạo")
                
                # Activities summary
                st.markdown("---")
                st.markdown("**📈 Tổng quan hoạt động:**")
                
                activities_summary = execute_query("""
                    SELECT 
                        ActivityType,
                        RequestStatus,
                        COUNT(*) as Count
                    FROM Activities
                    WHERE StudentID = ? 
                    GROUP BY ActivityType, RequestStatus
                    ORDER BY ActivityType, RequestStatus
                """, [search_id])
                
                if not activities_summary.empty:
                    st.dataframe(activities_summary, use_container_width=True, hide_index=True)
                    
# =============================================================================
# THỐNG KÊ
# =============================================================================
elif menu == "📊 Thống kê":
    st.title("📊 Thống kê và báo cáo")
    
    tab1, tab2 = st. tabs(["📈 Báo cáo tín chỉ", "📊 Thống kê môn học"])
    
    with tab1:
        st.subheader("📚 Báo cáo tín chỉ sinh viên")
        
        if st.button("📊 Tạo báo cáo", type="primary", key="credits"):
            credits_report = execute_query(
                "EXEC GetStudentsCreditsBySemester @p_SemesterID=? ",
                [sem_id]
            )
            
            if credits_report.empty:
                st.warning("⚠️ Không có dữ liệu")
            else:
                st. success(f"✅ Tìm thấy {len(credits_report)} sinh viên")
                st.dataframe(credits_report, use_container_width=True, hide_index=True)
                
                fig = px.histogram(
                    credits_report,
                    x='TotalCredits',
                    title=f'Phân bố tín chỉ sinh viên - {sem_name}',
                    labels={'TotalCredits': 'Tổng tín chỉ', 'count': 'Số sinh viên'},
                    nbins=20,
                    color_discrete_sequence=['#667eea']
                )
                st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.subheader("📈 Thống kê môn học")
        
        if st.button("📊 Xem thống kê", type="primary", key="courses"):
            all_courses = execute_query("EXEC GetCoursesWithStudentCount")
            
            if all_courses.empty:
                st.warning("⚠️ Không có dữ liệu")
            else:
                my_course_ids = execute_query("""
                    SELECT CourseID FROM Professor_Course
                    WHERE ProfessorID = ? AND SemesterID = ?
                """, [st.session_state. user_id, sem_id])
                
                if not my_course_ids.empty:
                    my_ids = my_course_ids['CourseID'].tolist()
                    my_stats = all_courses[all_courses['CourseID'].isin(my_ids)]
                    
                    if not my_stats.empty:
                        st.markdown("### 📚 Môn học của bạn")
                        st. dataframe(my_stats, use_container_width=True, hide_index=True)
                        
                        fig = px.bar(
                            my_stats,
                            x='Title',
                            y='StudentCount',
                            title='Số lượng sinh viên đăng ký môn của bạn',
                            color='StudentCount',
                            color_continuous_scale='Blues'
                        )
                        st.plotly_chart(fig, use_container_width=True)
                
                st.markdown("---")
                st.markdown("### 🌐 Tất cả môn học")
                st.dataframe(all_courses, use_container_width=True, hide_index=True)