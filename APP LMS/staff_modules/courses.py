import streamlit as st
from database import execute_query, execute_procedure

def render_courses_management():
    """Quản lý Courses - Module chính"""
    
    st. title("📚 Quản lý Courses (Môn học)")
    
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "➕ Thêm Course", 
        "📋 Danh sách Courses",
        "🔗 Prerequisites",
        "✏️ Sửa/Xóa"
    ])
    
    with tab1:
        render_add_course_form()
    
    with tab2:
        render_courses_list()
    
    with tab3:
        render_prerequisites()
    
    with tab4:
        render_edit_delete_course()


def render_add_course_form():
    """Form thêm course mới"""
    
    st.subheader("➕ Thêm Course mới")
    
    st. info("""
    ℹ️ **Hướng dẫn:**
    - Nhập thông tin môn học
    - Chọn Department (Khoa quản lý)
    - Điểm đạt (Passing Score) từ 0-100
    """)
    
    # Lấy departments
    departments = execute_query("""
        SELECT 
            DepartmentID,
            Name
        FROM Departments
        ORDER BY Name
    """)
    
    if departments.empty:
        st.warning("⚠️ Chưa có Department nào!")
        st.info("💡 Vào tab **🏢 Organizations** để tạo Department trước")
        return
    
    with st.form("add_course_form", clear_on_submit=True):
        st.markdown("### 📝 Thông tin Course")
        
        col1, col2 = st. columns(2)
        
        with col1:
            course_code = st.text_input(
                "Mã môn *",
                placeholder="VD: CS101",
                help="Mã môn học (unique)"
            )
            
            title = st.text_input(
                "Tên môn *",
                placeholder="VD: Nhập môn Lập trình",
                help="Tên đầy đủ của môn học"
            )
            
            credit = st.number_input(
                "Số tín chỉ *",
                min_value=1,
                max_value=10,
                value=3,
                help="Số tín chỉ (1-10)"
            )
        
        with col2:
            passing_score = st.number_input(
                "Điểm đạt *",
                min_value=0,
                max_value=100,
                value=50,
                help="Điểm tối thiểu để đạt môn (0-100)"
            )
            
            dept_options = departments['Name'].tolist()
            selected_dept = st.selectbox(
                "Department *",
                dept_options,
                help="Khoa quản lý môn học này"
            )
        
        description = st.text_area(
            "Mô tả",
            placeholder="Mô tả nội dung môn học.. .",
            help="Mô tả chi tiết (không bắt buộc)"
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        col1, col2 = st. columns(2)
        
        with col1:
            submit_btn = st.form_submit_button(
                "✅ Tạo Course",
                type="primary",
                use_container_width=True
            )
        
        with col2:
            if st.form_submit_button("🔄 Reset", use_container_width=True):
                st.rerun()
        
        if submit_btn:
            if not course_code or not title:
                st.error("❌ Vui lòng điền đầy đủ các trường bắt buộc (*)")
            else:
                # Check duplicate course code
                existing = execute_query(
                    "SELECT COUNT(*) as cnt FROM Courses WHERE Course_Code = ?",
                    [course_code]
                )
                
                if not existing.empty and existing.iloc[0]['cnt'] > 0:
                    st.error(f"❌ Mã môn '{course_code}' đã tồn tại!")
                else:
                    dept_id = int(departments[departments['Name'] == selected_dept]['DepartmentID'].values[0])
                    
                    success, msg = execute_procedure(
                        "EXEC InsertCourse @p_Passing_Score=?, @p_Course_Code=?, @p_Description=?, @p_Title=?, @p_Credit=?, @p_DepartmentID=?",
                        (passing_score, course_code, description if description else None, title, credit, dept_id)
                    )
                    
                    if success:
                        # Get new CourseID
                        new_course = execute_query(
                            "SELECT CourseID FROM Courses WHERE Course_Code = ?",
                            [course_code]
                        )
                        
                        if not new_course.empty:
                            course_id = int(new_course.iloc[0]['CourseID'])
                            
                            st.success(f"✅ Đã tạo Course thành công!")
                            st.info(f"🆔 **CourseID: {course_id}**")
                            st.info(f"📚 **[{course_code}] {title}**")
                            st.info(f"🎓 **{credit} tín chỉ - Điểm đạt: {passing_score}**")
                            st.balloons()
                    else:
                        st.error(f"❌ Lỗi: {msg}")


def render_courses_list():
    """Hiển thị danh sách courses"""
    
    st.subheader("📋 Danh sách Courses")
    
    # Filters
    col1, col2 = st. columns([2, 1])
    
    with col1:
        departments = execute_query("SELECT DepartmentID, Name FROM Departments ORDER BY Name")
        
        if not departments.empty:
            dept_filter_options = ["Tất cả"] + departments['Name'].tolist()
            selected_dept_filter = st.selectbox("Lọc theo Department:", dept_filter_options)
        else:
            selected_dept_filter = "Tất cả"
    
    with col2:
        sort_order = st.selectbox("Sắp xếp:", ["Mã môn A-Z", "Mã môn Z-A", "Tín chỉ cao-thấp"])
    
    # Query
    if selected_dept_filter == "Tất cả":
        courses = execute_query("""
            SELECT 
                C. CourseID,
                C. Course_Code,
                C. Title,
                C.Credit,
                C.Passing_Score,
                D.Name as Department,
                dbo.GetStudentCountByCourse(C.CourseID) as StudentCount
            FROM Courses C
            LEFT JOIN Departments D ON C.DepartmentID = D. DepartmentID
            ORDER BY C.Course_Code
        """)
    else:
        dept_id = departments[departments['Name'] == selected_dept_filter]['DepartmentID'].values[0]
        courses = execute_query("""
            SELECT 
                C.CourseID,
                C.Course_Code,
                C.Title,
                C.Credit,
                C.Passing_Score,
                D.Name as Department,
                dbo.GetStudentCountByCourse(C.CourseID) as StudentCount
            FROM Courses C
            LEFT JOIN Departments D ON C.DepartmentID = D.DepartmentID
            WHERE C.DepartmentID = ? 
            ORDER BY C.Course_Code
        """, [dept_id])
    
    # Display
    if courses.empty:
        st.info("📭 Chưa có course nào")
    else:
        st.success(f"✅ Tìm thấy {len(courses)} courses")
        
        st.dataframe(
            courses,
            column_config={
                "CourseID": st.column_config.NumberColumn("ID", width="small"),
                "Course_Code": st.column_config. TextColumn("Mã môn", width="small"),
                "Title": st.column_config.TextColumn("Tên môn", width="large"),
                "Credit": st. column_config.NumberColumn("TC", width="small"),
                "Passing_Score": st.column_config.NumberColumn("Điểm đạt", width="small"),
                "Department": st.column_config.TextColumn("Khoa", width="medium"),
                "StudentCount": st.column_config. NumberColumn("SV", width="small")
            },
            use_container_width=True,
            hide_index=True
        )


def render_prerequisites():
    """Quản lý Prerequisites (Môn tiên quyết)"""
    
    st.subheader("🔗 Quản lý Prerequisites")
    
    st.info("""
    ℹ️ **Prerequisites (Môn tiên quyết):**
    - Source Course: Môn cần học trước
    - Target Course: Môn tiên quyết (phải học trước Source)
    - VD: CS102 (Source) requires CS101 (Target)
    """)
    
    tab1, tab2 = st. tabs(["➕ Thêm Prerequisite", "📋 Danh sách"])
    
    with tab1:
        all_courses = execute_query("""
            SELECT 
                CourseID,
                Course_Code,
                Title
            FROM Courses
            ORDER BY Course_Code
        """)
        
        if all_courses. empty:
            st.warning("⚠️ Chưa có course nào!")
            return
        
        with st.form("add_prereq_form"):
            st.markdown("### ➕ Thêm Prerequisite mới")
            
            course_options = all_courses. apply(
                lambda row: f"[{row['Course_Code']}] {row['Title']}", 
                axis=1
            ).tolist()
            
            source_course = st.selectbox(
                "Source Course (Môn cần học):",
                course_options,
                help="Chọn môn cần thêm điều kiện tiên quyết"
            )
            
            target_course = st.selectbox(
                "Target Course (Môn tiên quyết):",
                course_options,
                help="Chọn môn phải học trước Source"
            )
            
            if st.form_submit_button("✅ Thêm Prerequisite", type="primary"):
                source_index = course_options.index(source_course)
                source_id = int(all_courses. iloc[source_index]['CourseID'])
                
                target_index = course_options.index(target_course)
                target_id = int(all_courses. iloc[target_index]['CourseID'])
                
                if source_id == target_id:
                    st.error("❌ Không thể thêm chính nó làm prerequisite!")
                else:
                    # Check existing
                    existing = execute_query("""
                        SELECT COUNT(*) as cnt
                        FROM CoursePrerequisites
                        WHERE SourceCourseID = ? AND TargetCourseID = ?
                    """, [source_id, target_id])
                    
                    if not existing.empty and existing.iloc[0]['cnt'] > 0:
                        st.error("❌ Prerequisite này đã tồn tại!")
                    else:
                        success, msg = execute_procedure(
                            "EXEC InsertCoursePrerequisite @p_SourceCourseID=?, @p_TargetCourseID=?",
                            (source_id, target_id)
                        )
                        
                        if success:
                            st.success("✅ Đã thêm prerequisite!")
                            st. rerun()
                        else:
                            st.error(f"❌ Lỗi: {msg}")
    
    with tab2:
        prerequisites = execute_query("""
            SELECT 
                CP. SourceCourseID,
                CP.TargetCourseID,
                C1.Course_Code as SourceCode,
                C1.Title as SourceTitle,
                C2.Course_Code as TargetCode,
                C2.Title as TargetTitle
            FROM CoursePrerequisites CP
            JOIN Courses C1 ON CP.SourceCourseID = C1.CourseID
            JOIN Courses C2 ON CP.TargetCourseID = C2. CourseID
            ORDER BY C1.Course_Code
        """)
        
        if prerequisites.empty:
            st. info("📭 Chưa có prerequisite nào")
        else:
            st. success(f"✅ Có {len(prerequisites)} prerequisites")
            
            for _, prereq in prerequisites.iterrows():
                col1, col2 = st. columns([4, 1])
                
                with col1:
                    st.markdown(f"""
                    📚 **[{prereq['SourceCode']}] {prereq['SourceTitle']}**  
                    ⬅️ Requires: **[{prereq['TargetCode']}] {prereq['TargetTitle']}**
                    """)
                
                with col2:
                    if st.button("🗑️ Xóa", key=f"del_prereq_{prereq['SourceCourseID']}_{prereq['TargetCourseID']}"):
                        success, msg = execute_procedure(
                            "EXEC DeleteCoursePrerequisite @p_SourceCourseID=?, @p_TargetCourseID=?",
                            (prereq['SourceCourseID'], prereq['TargetCourseID'])
                        )
                        
                        if success:
                            st.success("✅ Đã xóa!")
                            st.rerun()
                        else:
                            st.error(msg)
                
                st.markdown("---")


def render_edit_delete_course():
    """Sửa/Xóa course"""
    
    st.subheader("✏️ Sửa/Xóa Course")
    
    st.markdown("### 🔍 Tìm Course")
    
    search_method = st.radio("Tìm theo:", ["Mã môn", "Tên môn"], horizontal=True)
    
    if search_method == "Mã môn":
        course_code = st.text_input("Nhập mã môn:", placeholder="VD: CS101")
        
        if st.button("🔍 Tìm kiếm", type="primary"):
            course_info = execute_query("""
                SELECT 
                    C.CourseID,
                    C. Course_Code,
                    C.Title,
                    C. Credit,
                    C. Passing_Score,
                    C.Description,
                    C.DepartmentID,
                    D.Name as Department
                FROM Courses C
                LEFT JOIN Departments D ON C.DepartmentID = D.DepartmentID
                WHERE C.Course_Code = ?
            """, [course_code])
            
            if course_info.empty:
                st.error(f"❌ Không tìm thấy mã môn: {course_code}")
            else:
                st.session_state. selected_course_edit = course_info.iloc[0]. to_dict()
                st.rerun()
    
    else:
        all_courses = execute_query("""
            SELECT 
                CourseID,
                Course_Code,
                Title
            FROM Courses
            ORDER BY Course_Code
        """)
        
        if not all_courses.empty:
            course_options = all_courses.apply(
                lambda row: f"[{row['Course_Code']}] {row['Title']}", 
                axis=1
            ).tolist()
            
            selected = st.selectbox("Chọn môn:", course_options)
            
            if st.button("✅ Chọn", type="primary"):
                selected_index = course_options.index(selected)
                course_id = int(all_courses.iloc[selected_index]['CourseID'])
                
                course_info = execute_query("""
                    SELECT 
                        C.CourseID,
                        C.Course_Code,
                        C.Title,
                        C.Credit,
                        C.Passing_Score,
                        C.Description,
                        C.DepartmentID,
                        D.Name as Department
                    FROM Courses C
                    LEFT JOIN Departments D ON C.DepartmentID = D.DepartmentID
                    WHERE C.CourseID = ? 
                """, [course_id])
                
                st.session_state.selected_course_edit = course_info.iloc[0].to_dict()
                st.rerun()
    
    if 'selected_course_edit' in st.session_state:
        st.markdown("---")
        st.markdown("### 📚 Thông tin Course")
        
        course = st.session_state.selected_course_edit
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            **Course ID:** {course['CourseID']}  
            **Mã môn:** {course['Course_Code']}  
            **Tên môn:** {course['Title']}
            """)
        
        with col2:
            st.markdown(f"""
            **Tín chỉ:** {course['Credit']}  
            **Điểm đạt:** {course['Passing_Score']}  
            **Khoa:** {course['Department']}
            """)
        
        st.markdown("---")
        st.markdown("### ✏️ Sửa thông tin")
        
        with st.form("edit_course_form"):
            new_title = st.text_input("Tên môn mới:", value=course['Title'])
            
            col1, col2 = st. columns(2)
            
            with col1:
                new_credit = st.number_input("Tín chỉ mới:", min_value=1, max_value=10, value=int(course['Credit']))
                new_passing = st.number_input("Điểm đạt mới:", min_value=0, max_value=100, value=int(course['Passing_Score']))
            
            with col2:
                new_desc = st.text_area("Mô tả mới:", value=course['Description'] if course['Description'] else "")
            
            col1, col2 = st. columns(2)
            
            with col1:
                if st.form_submit_button("💾 Lưu thay đổi", type="primary", use_container_width=True):
                    success, msg = execute_procedure(
                        "EXEC UpdateCourse @p_CourseID=?, @p_NewPassingScore=?, @p_NewDescription=?, @p_NewTitle=?, @p_NewCredit=? ",
                        (course['CourseID'], new_passing, new_desc if new_desc else None, new_title, new_credit)
                    )
                    
                    if success:
                        st. success("✅ Đã cập nhật!")
                        del st.session_state.selected_course_edit
                        st. rerun()
                    else:
                        st.error(f"❌ Lỗi: {msg}")
            
            with col2:
                if st.form_submit_button("🔄 Hủy", use_container_width=True):
                    del st.session_state.selected_course_edit
                    st.rerun()
        
        st. markdown("---")
        st. markdown("### 🗑️ Xóa Course")
        
        # Check dependencies
        enrollments = execute_query("""
            SELECT COUNT(*) as cnt
            FROM Activities
            WHERE CourseID = ? 
        """, [course['CourseID']])
        
        count = enrollments.iloc[0]['cnt'] if not enrollments.empty else 0
        
        if count > 0:
            st.error(f"❌ Không thể xóa!  Course này có {count} enrollments")
            st.info("💡 Xóa tất cả activities trước")
        else:
            st.warning(f"⚠️ **Cảnh báo:** Xóa course sẽ xóa tất cả prerequisites liên quan!")
            
            if st.button("🗑️ XÓA COURSE NÀY", type="secondary"):
                success, msg = execute_procedure(
                    "EXEC DeleteCourse @p_CourseID=? ",
                    [course['CourseID']]
                )
                
                if success:
                    st.success("✅ Đã xóa course!")
                    del st.session_state.selected_course_edit
                    st.rerun()
                else:
                    st.error(f"❌ Lỗi: {msg}")