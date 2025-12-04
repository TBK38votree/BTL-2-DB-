import streamlit as st
from database import execute_query, execute_procedure

def render_professors_management():
    """Quản lý Professors - Module chính"""
    
    st.title("👨‍🏫 Quản lý Professors")
    
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "➕ Thêm Professor", 
        "📋 Danh sách Professors", 
        "📚 Phân công Giảng dạy",
        "✏️ Sửa/Xóa"
    ])
    
    with tab1:
        render_add_professor_form()
    
    with tab2:
        render_professors_list()
    
    with tab3:
        render_assign_teaching()
    
    with tab4:
        render_edit_delete_professor()


def render_add_professor_form():
    """Form thêm professor mới - TẠO LUÔN USER"""
    
    st.subheader("➕ Thêm Professor mới")
    
    st.info("""
    ℹ️ **Hướng dẫn:**
    - Điền đầy đủ thông tin giảng viên
    - Chọn Department (Khoa)
    - Hệ thống sẽ tự động tạo User + Professor
    """)
    
    # Lấy danh sách Departments
    departments = execute_query("""
        SELECT 
            DepartmentID,
            Name,
            Office_Location
        FROM Departments
        ORDER BY Name
    """)
    
    if departments.empty:
        st.warning("⚠️ Chưa có Department nào!")
        st.info("💡 Vào tab **🏢 Organizations** để tạo Department trước")
        return
    
    with st.form("add_professor_form", clear_on_submit=True):
        st.markdown("### 📝 Thông tin Professor")
        
        # User info
        col1, col2 = st. columns(2)
        
        with col1:
            lname = st.text_input(
                "Họ *",
                placeholder="VD: Nguyễn",
                help="Họ của giảng viên"
            )
            
            email = st.text_input(
                "Email *",
                placeholder="example@university.edu",
                help="Email phải unique"
            )
            
            office_location = st.text_input(
                "Office Location *",
                placeholder="VD: Building A, Room 105",
                help="Vị trí văn phòng"
            )
        
        with col2:
            fname = st.text_input(
                "Tên *",
                placeholder="VD: Văn An",
                help="Tên của giảng viên"
            )
            
            phone = st.text_input(
                "Số điện thoại",
                placeholder="0901234567",
                help="Số điện thoại (không bắt buộc)"
            )
            
            # Department selection
            dept_options = departments.apply(
                lambda row: f"{row['Name']} (Office: {row['Office_Location']})", 
                axis=1
            ).tolist()
            
            selected_dept_display = st.selectbox(
                "Department *",
                options=dept_options,
                help="Chọn khoa mà professor thuộc về"
            )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        col1, col2 = st. columns(2)
        
        with col1:
            submit_btn = st.form_submit_button(
                "✅ Tạo Professor",
                type="primary",
                use_container_width=True
            )
        
        with col2:
            if st.form_submit_button("🔄 Reset", use_container_width=True):
                st.rerun()
        
        if submit_btn:
            # Validation
            if not lname or not fname or not email or not office_location:
                st.error("❌ Vui lòng điền đầy đủ các trường bắt buộc (*)")
            else:
                # Check email duplicate
                existing = execute_query(
                    "SELECT COUNT(*) as cnt FROM Users WHERE Email_Address = ?",
                    [email]
                )
                
                if not existing.empty and existing.iloc[0]['cnt'] > 0:
                    st.error(f"❌ Email '{email}' đã tồn tại!")
                else:
                    # Parse Department ID
                    selected_dept_index = dept_options.index(selected_dept_display)
                    dept_id = int(departments.iloc[selected_dept_index]['DepartmentID'])
                    
                    # Step 1: Insert User
                    success1, msg1 = execute_procedure(
                        "EXEC InsertUser @p_LName=?, @p_FName=?, @p_Email_Address=?, @p_Phone_Number=?",
                        (lname, fname, email, phone if phone else None)
                    )
                    
                    if not success1:
                        st. error(f"❌ Lỗi tạo User: {msg1}")
                    else:
                        # Get new UserID
                        new_user = execute_query(
                            "SELECT UserID FROM Users WHERE Email_Address = ?",
                            [email]
                        )
                        
                        if new_user.empty:
                            st.error("❌ Không tìm thấy User vừa tạo!")
                        else:
                            user_id = int(new_user.iloc[0]['UserID'])
                            
                            # Step 2: Insert Professor
                            success2, msg2 = execute_procedure(
                                "EXEC InsertProfessor @p_UserID=?, @p_Office_Location=?, @p_DepartmentID=?",
                                (user_id, office_location, dept_id)
                            )
                            
                            if not success2:
                                st.error(f"❌ Lỗi tạo Professor: {msg2}")
                                # Rollback: Delete User
                                execute_procedure("EXEC DeleteUser @p_UserID=?", [user_id])
                            else:
                                # Success! 
                                st.success(f"✅ Đã tạo Professor thành công!")
                                st. info(f"🆔 **Professor ID: {user_id}**")
                                st.info(f"👤 **Họ tên: {fname} {lname}**")
                                st.info(f"📧 **Email: {email}**")
                                st.info(f"🏢 **Department: {departments.iloc[selected_dept_index]['Name']}**")
                                st.info(f"📍 **Office: {office_location}**")
                                st.balloons()


def render_professors_list():
    """Hiển thị danh sách professors"""
    
    st.subheader("📋 Danh sách Professors")
    
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
        sort_order = st.selectbox("Sắp xếp:", ["Mới nhất", "Cũ nhất", "Tên A-Z"])
    
    # Query
    if selected_dept_filter == "Tất cả":
        professors = execute_query("""
            SELECT 
                P.UserID,
                dbo.GetFullName(P. UserID) as FullName,
                U.Email_Address,
                U.Phone_Number,
                D.Name as Department,
                P.Office_Location,
                (SELECT COUNT(DISTINCT CourseID) 
                 FROM Professor_Course 
                 WHERE ProfessorID = P.UserID) as CourseCount
            FROM Professors P
            JOIN Users U ON P.UserID = U.UserID
            LEFT JOIN Departments D ON P.DepartmentID = D.DepartmentID
            ORDER BY P.UserID DESC
        """)
    else:
        dept_id = departments[departments['Name'] == selected_dept_filter]['DepartmentID'].values[0]
        professors = execute_query("""
            SELECT 
                P.UserID,
                dbo.GetFullName(P.UserID) as FullName,
                U.Email_Address,
                U.Phone_Number,
                D.Name as Department,
                P.Office_Location,
                (SELECT COUNT(DISTINCT CourseID) 
                 FROM Professor_Course 
                 WHERE ProfessorID = P.UserID) as CourseCount
            FROM Professors P
            JOIN Users U ON P. UserID = U.UserID
            LEFT JOIN Departments D ON P.DepartmentID = D. DepartmentID
            WHERE P.DepartmentID = ? 
            ORDER BY P.UserID DESC
        """, [dept_id])
    
    # Display
    if professors.empty:
        st. info("📭 Chưa có professor nào")
    else:
        st. success(f"✅ Tìm thấy {len(professors)} professors")
        
        st.dataframe(
            professors,
            column_config={
                "UserID": st.column_config.NumberColumn("Professor ID", width="small"),
                "FullName": st.column_config.TextColumn("Họ tên", width="large"),
                "Email_Address": st.column_config. TextColumn("Email", width="large"),
                "Phone_Number": st.column_config.TextColumn("SĐT", width="medium"),
                "Department": st. column_config.TextColumn("Khoa", width="medium"),
                "Office_Location": st. column_config.TextColumn("Văn phòng", width="medium"),
                "CourseCount": st.column_config.NumberColumn("Số môn", width="small")
            },
            use_container_width=True,
            hide_index=True
        )


def render_assign_teaching():
    """Phân công giảng dạy"""
    
    st. subheader("📚 Phân công Giảng dạy")
    
    st.info("""
    ℹ️ **Hướng dẫn:**
    - Chọn Professor
    - Chọn Course (Môn học)
    - Chọn Semester (Học kỳ)
    """)
    
    col1, col2 = st. columns(2)
    
    with col1:
        st.markdown("### 🔍 Chọn Professor")
        
        all_professors = execute_query("""
            SELECT 
                P. UserID,
                dbo. GetFullName(P.UserID) as FullName,
                D.Name as Department
            FROM Professors P
            LEFT JOIN Departments D ON P.DepartmentID = D.DepartmentID
            ORDER BY P. UserID DESC
        """)
        
        if all_professors.empty:
            st.warning("⚠️ Chưa có professor nào!")
            return
        
        prof_options = all_professors. apply(
            lambda row: f"ID: {row['UserID']} - {row['FullName']} ({row['Department']})", 
            axis=1
        ).tolist()
        
        selected_prof = st.selectbox("Chọn Professor:", prof_options)
        
        if st.button("✅ Chọn", type="primary", key="select_prof"):
            selected_index = prof_options.index(selected_prof)
            prof_id = int(all_professors.iloc[selected_index]['UserID'])
            
            st.session_state.selected_prof_for_teaching = {
                'UserID': prof_id,
                'FullName': all_professors.iloc[selected_index]['FullName'],
                'Department': all_professors.iloc[selected_index]['Department']
            }
            st.rerun()
    
    with col2:
        if 'selected_prof_for_teaching' in st.session_state:
            prof = st.session_state. selected_prof_for_teaching
            
            st.markdown("### 👨‍🏫 Professor đã chọn")
            st.markdown(f"""
            **ID:** {prof['UserID']}  
            **Họ tên:** {prof['FullName']}  
            **Khoa:** {prof['Department']}
            """)
            
            # Hiện courses đang dạy
            current_teaching = execute_query("""
                SELECT 
                    C.Course_Code,
                    C.Title,
                    S.Semester_Name
                FROM Professor_Course PC
                JOIN Courses C ON PC.CourseID = C.CourseID
                JOIN Semesters S ON PC.SemesterID = S. SemesterID
                WHERE PC.ProfessorID = ? 
                ORDER BY S.Start_Date DESC
            """, [prof['UserID']])
            
            if not current_teaching.empty:
                st.markdown("**Đang dạy:**")
                for _, course in current_teaching.iterrows():
                    st.success(f"✅ [{course['Course_Code']}] {course['Title']} - {course['Semester_Name']}")
    
    # Form phân công
    if 'selected_prof_for_teaching' in st.session_state:
        st.markdown("---")
        st.markdown("### ➕ Phân công mới")
        
        # Lấy courses và semesters
        all_courses = execute_query("""
            SELECT 
                CourseID,
                Course_Code,
                Title,
                Credit
            FROM Courses
            ORDER BY Course_Code
        """)
        
        all_semesters = execute_query("""
            SELECT 
                SemesterID,
                Semester_Name,
                CONVERT(VARCHAR, Start_Date, 23) as Start_Date,
                CONVERT(VARCHAR, End_Date, 23) as End_Date
            FROM Semesters
            ORDER BY Start_Date DESC
        """)
        
        if all_courses.empty:
            st.warning("⚠️ Chưa có course nào!")
            return
        
        if all_semesters.empty:
            st.warning("⚠️ Chưa có semester nào!")
            return
        
        with st.form("assign_teaching_form"):
            course_options = all_courses.apply(
                lambda row: f"[{row['Course_Code']}] {row['Title']} ({row['Credit']} TC)", 
                axis=1
            ).tolist()
            
            selected_course = st.selectbox("Chọn Course:", course_options)
            
            semester_options = all_semesters.apply(
                lambda row: f"{row['Semester_Name']} ({row['Start_Date']} → {row['End_Date']})", 
                axis=1
            ).tolist()
            
            selected_semester = st.selectbox("Chọn Semester:", semester_options)
            
            col1, col2 = st. columns(2)
            
            with col1:
                if st.form_submit_button("✅ Phân công", type="primary", use_container_width=True):
                    course_index = course_options.index(selected_course)
                    course_id = int(all_courses.iloc[course_index]['CourseID'])
                    
                    semester_index = semester_options.index(selected_semester)
                    semester_id = int(all_semesters. iloc[semester_index]['SemesterID'])
                    
                    # Check if already assigned
                    existing = execute_query("""
                        SELECT COUNT(*) as cnt
                        FROM Professor_Course
                        WHERE ProfessorID = ? AND CourseID = ?  AND SemesterID = ? 
                    """, [prof['UserID'], course_id, semester_id])
                    
                    if not existing.empty and existing. iloc[0]['cnt'] > 0:
                        st.error("❌ Đã phân công rồi!")
                    else:
                        success, msg = execute_procedure(
                            "EXEC AssignProfessorToCourse @p_ProfessorID=?, @p_CourseID=?, @p_SemesterID=?",
                            (prof['UserID'], course_id, semester_id)
                        )
                        
                        if success:
                            st.success("✅ Đã phân công thành công!")
                            st.balloons()
                            del st.session_state. selected_prof_for_teaching
                            st.rerun()
                        else:
                            st.error(f"❌ Lỗi: {msg}")
            
            with col2:
                if st.form_submit_button("🔄 Hủy", use_container_width=True):
                    del st.session_state.selected_prof_for_teaching
                    st.rerun()


def render_edit_delete_professor():
    """Sửa/Xóa professor"""
    
    st.subheader("✏️ Sửa/Xóa Professor")
    
    st.markdown("### 🔍 Tìm Professor")
    
    search_method = st.radio("Tìm kiếm theo:", ["ID", "Email"], horizontal=True, key="edit_prof_search")
    
    if search_method == "ID":
        prof_id = st.number_input("Nhập Professor ID:", min_value=1, step=1)
        
        if st.button("🔍 Tìm kiếm", type="primary", key="edit_prof_find"):
            prof_info = execute_query("""
                SELECT 
                    P.UserID,
                    U.LName,
                    U.FName,
                    dbo.GetFullName(P.UserID) as FullName,
                    U.Email_Address,
                    U.Phone_Number,
                    P.Office_Location,
                    P. DepartmentID,
                    D.Name as Department
                FROM Professors P
                JOIN Users U ON P.UserID = U.UserID
                LEFT JOIN Departments D ON P.DepartmentID = D.DepartmentID
                WHERE P.UserID = ?
            """, [prof_id])
            
            if prof_info.empty:
                st.error(f"❌ Không tìm thấy Professor ID: {prof_id}")
            else:
                st.session_state.selected_prof_edit = prof_info.iloc[0]. to_dict()
                st.rerun()
    
    else:
        email = st.text_input("Nhập Email:")
        
        if st.button("🔍 Tìm kiếm", type="primary", key="edit_prof_find_email"):
            prof_info = execute_query("""
                SELECT 
                    P.UserID,
                    U.LName,
                    U.FName,
                    dbo.GetFullName(P.UserID) as FullName,
                    U.Email_Address,
                    U.Phone_Number,
                    P.Office_Location,
                    P.DepartmentID,
                    D.Name as Department
                FROM Professors P
                JOIN Users U ON P. UserID = U.UserID
                LEFT JOIN Departments D ON P.DepartmentID = D. DepartmentID
                WHERE U.Email_Address = ?
            """, [email])
            
            if prof_info.empty:
                st.error(f"❌ Không tìm thấy professor với email: {email}")
            else:
                st.session_state.selected_prof_edit = prof_info.iloc[0].to_dict()
                st.rerun()
    
    if 'selected_prof_edit' in st.session_state:
        st.markdown("---")
        st.markdown("### 👤 Thông tin Professor")
        
        prof = st.session_state. selected_prof_edit
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            **Professor ID:** {prof['UserID']}  
            **Họ tên:** {prof['FullName']}  
            **Email:** {prof['Email_Address']}
            """)
        
        with col2:
            st.markdown(f"""
            **SĐT:** {prof['Phone_Number']}  
            **Khoa:** {prof['Department']}  
            **Văn phòng:** {prof['Office_Location']}
            """)
        
        st.markdown("---")
        st.markdown("### ✏️ Sửa thông tin")
        
        departments = execute_query("SELECT DepartmentID, Name FROM Departments ORDER BY Name")
        
        if departments.empty:
            st.warning("⚠️ Không có department nào!")
        else:
            with st.form("edit_prof_form"):
                col1, col2 = st. columns(2)
                
                with col1:
                    new_lname = st.text_input("Họ mới:", value=prof['LName'])
                    new_email = st.text_input("Email mới:", value=prof['Email_Address'])
                
                with col2:
                    new_fname = st.text_input("Tên mới:", value=prof['FName'])
                    new_phone = st.text_input("SĐT mới:", value=prof['Phone_Number'] if prof['Phone_Number'] else "")
                
                dept_options = departments['Name'].tolist()
                current_dept_index = dept_options.index(prof['Department']) if prof['Department'] in dept_options else 0
                
                new_dept = st.selectbox(
                    "Department mới:",
                    dept_options,
                    index=current_dept_index
                )
                
                new_office = st.text_input(
                    "Office Location mới:",
                    value=prof['Office_Location']
                )
                
                col1, col2 = st. columns(2)
                
                with col1:
                    if st.form_submit_button("💾 Lưu thay đổi", type="primary", use_container_width=True):
                        new_dept_id = int(departments[departments['Name'] == new_dept]['DepartmentID'].values[0])
                        
                        # Update User
                        success1, msg1 = execute_procedure(
                            "EXEC UpdateUser @p_UserID=?, @p_NewLName=?, @p_NewFName=?, @p_NewEmail=?, @p_NewPhone=? ",
                            (prof['UserID'], new_lname, new_fname, new_email, new_phone if new_phone else None)
                        )
                        
                        # Update Professor
                        success2, msg2 = execute_procedure(
                            "EXEC UpdateProfessor @p_UserID=?, @p_NewOfficeLocation=?, @p_NewDepartmentID=?",
                            (prof['UserID'], new_office, new_dept_id)
                        )
                        
                        if success1 and success2:
                            st.success("✅ Đã cập nhật thông tin!")
                            del st.session_state.selected_prof_edit
                            st. rerun()
                        else:
                            st.error(f"❌ Lỗi: {msg1 or msg2}")
                
                with col2:
                    if st.form_submit_button("🔄 Hủy", use_container_width=True):
                        del st.session_state.selected_prof_edit
                        st.rerun()
        
        st.markdown("---")
        st.markdown("### 🗑️ Xóa Professor")
        
        # Check teaching assignments
        teaching_count = execute_query("""
            SELECT COUNT(*) as cnt
            FROM Professor_Course
            WHERE ProfessorID = ?
        """, [prof['UserID']])
        
        count = teaching_count.iloc[0]['cnt'] if not teaching_count.empty else 0
        
        if count > 0:
            st.error(f"❌ Không thể xóa!  Professor này có {count} phân công giảng dạy")
            st.info("💡 Xóa tất cả phân công trước rồi mới xóa professor")
        else:
            st. warning(f"⚠️ **Cảnh báo:** Xóa professor sẽ xóa cả User và tất cả dữ liệu liên quan!")
            
            if st.button("🗑️ XÓA PROFESSOR NÀY", type="secondary"):
                # Delete Professor
                success, msg = execute_procedure(
                    "EXEC DeleteProfessor @p_UserID=?",
                    [prof['UserID']]
                )
                
                if success:
                    # Delete User
                    execute_procedure("EXEC DeleteUser @p_UserID=?", [prof['UserID']])
                    
                    st.success("✅ Đã xóa professor!")
                    del st.session_state.selected_prof_edit
                    st. rerun()
                else:
                    st.error(f"❌ Lỗi: {msg}")