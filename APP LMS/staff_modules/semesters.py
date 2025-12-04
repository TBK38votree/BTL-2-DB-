import streamlit as st
from datetime import date, timedelta
from database import execute_query, execute_procedure

def render_semesters_management():
    """Quản lý Semesters - Module chính"""
    
    st.title("🗓️ Quản lý Học kỳ")
    
    tab1, tab2 = st. tabs(["📋 Danh sách Học kỳ", "➕ Thêm Học kỳ mới"])
    
    with tab1:
        render_semesters_list()
    
    with tab2:
        render_add_semester()


def render_semesters_list():
    """Danh sách học kỳ"""
    
    st.subheader("📋 Tất cả Học kỳ")
    
    all_semesters = execute_query("""
        SELECT 
            S.SemesterID,
            S. Semester_Name,
            CONVERT(VARCHAR, S.Start_Date, 23) as Start_Date,
            CONVERT(VARCHAR, S.End_Date, 23) as End_Date,
            COUNT(DISTINCT A.StudentID) as TotalStudents,
            COUNT(DISTINCT PC.ProfessorID) as TotalProfessors,
            COUNT(DISTINCT PC.CourseID) as TotalCourses
        FROM Semesters S
        LEFT JOIN Activities A ON S.SemesterID = A.SemesterID
        LEFT JOIN Professor_Course PC ON S.SemesterID = PC.SemesterID
        GROUP BY S.SemesterID, S.Semester_Name, S.Start_Date, S.End_Date
        ORDER BY S. Start_Date DESC
    """)
    
    if all_semesters.empty:
        st.info("📭 Chưa có học kỳ nào")
    else:
        st.success(f"✅ Tổng số: {len(all_semesters)} học kỳ")
        
        for _, semester in all_semesters.iterrows():
            with st.expander(f"📅 Học kỳ {semester['Semester_Name']} ({semester['Start_Date']} → {semester['End_Date']})"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("👥 Sinh viên", semester['TotalStudents'])
                with col2:
                    st. metric("👨‍🏫 Giảng viên", semester['TotalProfessors'])
                with col3:
                    st.metric("📚 Môn học", semester['TotalCourses'])
                
                st.markdown("---")
                st.markdown(f"""
                **SemesterID:** {semester['SemesterID']}  
                **Tên:** {semester['Semester_Name']}  
                **Ngày bắt đầu:** {semester['Start_Date']}  
                **Ngày kết thúc:** {semester['End_Date']}
                """)
                
                if semester['TotalStudents'] == 0 and semester['TotalProfessors'] == 0:
                    if st.button(f"🗑️ Xóa học kỳ {semester['Semester_Name']}", key=f"del_sem_{semester['SemesterID']}", type="secondary"):
                        success, msg = execute_procedure(
                            "EXEC DeleteSemester @p_SemesterID=?",
                            [semester['SemesterID']]
                        )
                        if success:
                            st.success("✅ Đã xóa học kỳ!")
                            st.rerun()
                        else:
                            st.error(msg)
                else:
                    st.warning("⚠️ Không thể xóa học kỳ đã có dữ liệu")


def render_add_semester():
    """Thêm học kỳ mới"""
    
    st.subheader("➕ Tạo Học kỳ mới")
    
    st.info("""
    ℹ️ **Hướng dẫn:**
    - Tên học kỳ sẽ tự động tạo theo định dạng: **YY1** (Fall) hoặc **YY2** (Spring)
    - Fall: Tháng 9-12 → Học kỳ 1
    - Spring: Tháng 1-5 → Học kỳ 2
    - VD: Học kỳ bắt đầu 2024-09-01 → Tên: **241**
    """)
    
    with st.form("add_semester_form"):
        st.markdown("### 📝 Thông tin Học kỳ")
        
        col1, col2 = st. columns(2)
        
        with col1:
            start_date = st.date_input(
                "Ngày bắt đầu *",
                value=date.today(),
                help="Chọn ngày bắt đầu học kỳ"
            )
        
        with col2:
            default_end = start_date + timedelta(days=120)
            
            end_date = st.date_input(
                "Ngày kết thúc *",
                value=default_end,
                help="Chọn ngày kết thúc học kỳ"
            )
        
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
            if end_date <= start_date:
                st. error("❌ Ngày kết thúc phải sau ngày bắt đầu!")
            else:
                existing = execute_query("""
                    SELECT COUNT(*) as cnt
                    FROM Semesters
                    WHERE Start_Date = ?  OR End_Date = ?
                """, [start_date, end_date])
                
                if not existing.empty and existing.iloc[0]['cnt'] > 0:
                    st.warning("⚠️ Đã có học kỳ với ngày này!")
                else:
                    success, msg = execute_procedure(
                        "EXEC InsertSemester @p_Start_Date=?, @p_End_Date=?",
                        (start_date, end_date)
                    )
                    
                    if success:
                        st.success(f"✅ Đã tạo học kỳ **{preview_name}** thành công!")
                        st. balloons()
                        st. info("💡 Chuyển sang tab 'Danh sách Học kỳ' để xem")
                        st.rerun()
                    else:
                        st.error(msg)