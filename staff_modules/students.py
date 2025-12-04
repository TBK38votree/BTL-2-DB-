import streamlit as st
from datetime import date
from database import execute_query, execute_procedure

def render_students_management():
    """Quản lý Students - Module chính"""
    
    st. title("🎓 Quản lý Students")
    
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "➕ Thêm Student", 
        "📋 Danh sách Students",
        "🎓 Gán Program",
        "✏️ Sửa/Xóa"
    ])
    
    with tab1:
        render_add_student_form()
    
    with tab2:
        render_students_list()
    
    with tab3:
        render_assign_program()
    
    with tab4:
        render_edit_delete_student()


def render_add_student_form():
    """Form thêm student mới - TẠO LUÔN USER"""
    
    st.subheader("➕ Thêm Student mới")
    
    st.info("""
    ℹ️ **Hướng dẫn:**
    - Điền đầy đủ thông tin sinh viên
    - Hệ thống sẽ tự động tạo User + Student
    """)
    
    with st.form("add_student_form", clear_on_submit=True):
        st.markdown("### 📝 Thông tin Student")
        
        # User info
        col1, col2 = st.columns(2)
        
        with col1:
            lname = st.text_input(
                "Họ *",
                placeholder="VD: Nguyễn",
                help="Họ của sinh viên"
            )
            
            email = st.text_input(
                "Email *",
                placeholder="example@student.edu",
                help="Email phải unique"
            )
            
            birthday = st.date_input(
                "Ngày sinh *",
                value=date(2003, 1, 1),
                min_value=date(1990, 1, 1),
                max_value=date. today(),
                help="Ngày sinh"
            )
        
        with col2:
            fname = st.text_input(
                "Tên *",
                placeholder="VD: Văn An",
                help="Tên của sinh viên"
            )
            
            phone = st.text_input(
                "Số điện thoại",
                placeholder="0901234567",
                help="Số điện thoại (không bắt buộc)"
            )
        
        # Program selection (optional)
        st.markdown("---")
        st.markdown("### 🎓 Chương trình Đào tạo (Tùy chọn)")
        
        programs = execute_query("SELECT ProgramID, Code, Name FROM Degree_Programs ORDER BY Code")
        
        assign_program = st.checkbox("Gán chương trình đào tạo ngay", value=False)
        
        selected_program_id = None
        enrollment_date = date.today()
        
        if assign_program and not programs.empty:
            program_options = programs.apply(
                lambda row: f"[{row['Code']}] {row['Name']}", 
                axis=1
            ). tolist()
            
            selected_program = st.selectbox("Chọn Program:", program_options)
            enrollment_date = st.date_input("Ngày bắt đầu:", value=date.today())
            
            selected_index = program_options.index(selected_program)
            selected_program_id = int(programs.iloc[selected_index]['ProgramID'])
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        col1, col2 = st. columns(2)
        
        with col1:
            submit_btn = st.form_submit_button(
                "✅ Tạo Student",
                type="primary",
                use_container_width=True
            )
        
        with col2:
            if st.form_submit_button("🔄 Reset", use_container_width=True):
                st.rerun()
        
        if submit_btn:
            # Validation
            if not lname or not fname or not email:
                st. error("❌ Vui lòng điền đầy đủ các trường bắt buộc (*)")
            else:
                # Check email duplicate
                existing = execute_query(
                    "SELECT COUNT(*) as cnt FROM Users WHERE Email_Address = ?",
                    [email]
                )
                
                if not existing.empty and existing.iloc[0]['cnt'] > 0:
                    st.error(f"❌ Email '{email}' đã tồn tại!")
                else:
                    # Step 1: Insert User
                    success1, msg1 = execute_procedure(
                        "EXEC InsertUser @p_LName=?, @p_FName=?, @p_Email_Address=?, @p_Phone_Number=? ",
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
                            
                            # Step 2: Insert Student
                            success2, msg2 = execute_procedure(
                                "EXEC InsertStudent @p_UserID=?, @p_Birthday=?",
                                (user_id, birthday)
                            )
                            
                            if not success2:
                                st.error(f"❌ Lỗi tạo Student: {msg2}")
                                # Rollback: Delete User
                                execute_procedure("EXEC DeleteUser @p_UserID=?", [user_id])
                            else:
                                # Step 3: Assign Program (if selected)
                                if assign_program and selected_program_id:
                                    execute_procedure(
                                        "EXEC EnrollStudentInProgram @p_StudentID=?, @p_ProgramID=?, @p_Enrollment_Date=?",
                                        (user_id, selected_program_id, enrollment_date)
                                    )
                                
                                # Success! 
                                st.success(f"✅ Đã tạo Student thành công!")
                                st. info(f"🆔 **Student ID: {user_id}**")
                                st.info(f"👤 **Họ tên: {fname} {lname}**")
                                st.info(f"📧 **Email: {email}**")
                                st.info(f"🎂 **Ngày sinh: {birthday}**")
                                
                                if assign_program and selected_program_id:
                                    st.info(f"🎓 **Đã gán Program**")
                                
                                st.balloons()


def render_students_list():
    """Hiển thị danh sách students"""
    
    st.subheader("📋 Danh sách Students")
    
    # Filters
    col1, col2 = st.columns([2, 1])
    
    with col1:
        filter_program = st.selectbox(
            "Lọc theo chương trình:",
            ["Tất cả", "Có Program", "Chưa có Program"]
        )
    
    with col2:
        sort_order = st.selectbox("Sắp xếp:", ["Mới nhất", "Cũ nhất", "Tên A-Z"])
    
    # Query
    if filter_program == "Tất cả":
        students = execute_query("""
            SELECT 
                S.UserID,
                dbo.GetFullName(S.UserID) as FullName,
                U.Email_Address,
                U.Phone_Number,
                CONVERT(VARCHAR, S. Birthday, 23) as Birthday,
                (SELECT COUNT(*) 
                 FROM Student_Program SP 
                 WHERE SP.StudentID = S.UserID) as ProgramCount
            FROM Students S
            JOIN Users U ON S.UserID = U.UserID
            ORDER BY S.UserID DESC
        """)
    
    elif filter_program == "Có Program":
        students = execute_query("""
            SELECT DISTINCT
                S.UserID,
                dbo.GetFullName(S.UserID) as FullName,
                U.Email_Address,
                U.Phone_Number,
                CONVERT(VARCHAR, S.Birthday, 23) as Birthday,
                (SELECT COUNT(*) 
                 FROM Student_Program SP 
                 WHERE SP.StudentID = S.UserID) as ProgramCount
            FROM Students S
            JOIN Users U ON S.UserID = U.UserID
            WHERE EXISTS(SELECT 1 FROM Student_Program WHERE StudentID = S.UserID)
            ORDER BY S.UserID DESC
        """)
    
    else:  # Chưa có Program
        students = execute_query("""
            SELECT 
                S.UserID,
                dbo.GetFullName(S. UserID) as FullName,
                U.Email_Address,
                U.Phone_Number,
                CONVERT(VARCHAR, S.Birthday, 23) as Birthday,
                0 as ProgramCount
            FROM Students S
            JOIN Users U ON S.UserID = U.UserID
            WHERE NOT EXISTS(SELECT 1 FROM Student_Program WHERE StudentID = S. UserID)
            ORDER BY S.UserID DESC
        """)
    
    # Display
    if students.empty:
        st.info("📭 Chưa có student nào")
    else:
        st.success(f"✅ Tìm thấy {len(students)} students")
        
        st.dataframe(
            students,
            column_config={
                "UserID": st.column_config. NumberColumn("Student ID", width="small"),
                "FullName": st.column_config. TextColumn("Họ tên", width="large"),
                "Email_Address": st.column_config. TextColumn("Email", width="large"),
                "Phone_Number": st.column_config.TextColumn("SĐT", width="medium"),
                "Birthday": st. column_config.TextColumn("Ngày sinh", width="medium"),
                "ProgramCount": st.column_config. NumberColumn("Số Program", width="small")
            },
            use_container_width=True,
            hide_index=True
        )


def render_assign_program():
    """Gán chương trình đào tạo cho student"""
    
    st.subheader("🎓 Gán Chương trình Đào tạo")
    
    st.info("""
    ℹ️ **Hướng dẫn:**
    - Chọn Student cần gán program
    - Chọn chương trình đào tạo
    - Nhập ngày bắt đầu
    """)
    
    col1, col2 = st. columns(2)
    
    with col1:
        # Tìm student
        st.markdown("### 🔍 Chọn Student")
        
        search_method = st.radio("Tìm theo:", ["ID", "Tên"], horizontal=True, key="search_student")
        
        if search_method == "ID":
            student_id = st.number_input("Student ID:", min_value=1, step=1)
            
            if st.button("🔍 Tìm", type="primary", key="find_student"):
                student_info = execute_query("""
                    SELECT 
                        S.UserID,
                        dbo.GetFullName(S.UserID) as FullName,
                        U.Email_Address,
                        CONVERT(VARCHAR, S.Birthday, 23) as Birthday
                    FROM Students S
                    JOIN Users U ON S.UserID = U.UserID
                    WHERE S.UserID = ? 
                """, [student_id])
                
                if student_info.empty:
                    st. error(f"❌ Không tìm thấy Student ID: {student_id}")
                else:
                    st.session_state.selected_student_for_program = student_info.iloc[0]. to_dict()
                    st. rerun()
        
        else:  # Tìm theo tên
            all_students = execute_query("""
                SELECT 
                    S.UserID,
                    dbo.GetFullName(S. UserID) as FullName
                FROM Students S
                ORDER BY S.UserID DESC
            """)
            
            if not all_students.empty:
                student_options = all_students.apply(
                    lambda row: f"ID: {row['UserID']} - {row['FullName']}", 
                    axis=1
                ).tolist()
                
                selected = st.selectbox("Chọn Student:", student_options)
                
                if st.button("✅ Chọn", type="primary", key="select_student"):
                    selected_index = student_options.index(selected)
                    student_id = int(all_students.iloc[selected_index]['UserID'])
                    
                    student_info = execute_query("""
                        SELECT 
                            S.UserID,
                            dbo.GetFullName(S.UserID) as FullName,
                            U.Email_Address,
                            CONVERT(VARCHAR, S.Birthday, 23) as Birthday
                        FROM Students S
                        JOIN Users U ON S.UserID = U.UserID
                        WHERE S.UserID = ?
                    """, [student_id])
                    
                    st.session_state.selected_student_for_program = student_info.iloc[0].to_dict()
                    st.rerun()
    
    with col2:
        if 'selected_student_for_program' in st.session_state:
            student = st.session_state. selected_student_for_program
            
            st.markdown("### 👤 Student đã chọn")
            st.markdown(f"""
            **ID:** {student['UserID']}  
            **Họ tên:** {student['FullName']}  
            **Email:** {student['Email_Address']}  
            **Ngày sinh:** {student['Birthday']}
            """)
            
            # Hiện programs đã gán
            current_programs = execute_query("""
                SELECT 
                    DP.Code,
                    DP.Name,
                    CONVERT(VARCHAR, SP.Enrollment_Date, 23) as EnrollmentDate
                FROM Student_Program SP
                JOIN Degree_Programs DP ON SP.ProgramID = DP.ProgramID
                WHERE SP.StudentID = ?
            """, [student['UserID']])
            
            if not current_programs.empty:
                st.markdown("**Programs hiện tại:**")
                for _, prog in current_programs.iterrows():
                    st.success(f"✅ [{prog['Code']}] {prog['Name']} (từ {prog['EnrollmentDate']})")
    
    # Form gán program
    if 'selected_student_for_program' in st.session_state:
        st.markdown("---")
        st.markdown("### ➕ Gán Program mới")
        
        # Lấy danh sách programs
        all_programs = execute_query("""
            SELECT 
                ProgramID,
                Code,
                Name
            FROM Degree_Programs
            ORDER BY Code
        """)
        
        if all_programs.empty:
            st.warning("⚠️ Chưa có chương trình đào tạo nào!")
            st.info("💡 Vào tab **🎓 Programs** để tạo program trước")
        else:
            with st.form("assign_program_form"):
                program_options = all_programs.apply(
                    lambda row: f"[{row['Code']}] {row['Name']}", 
                    axis=1
                ).tolist()
                
                selected_program = st.selectbox("Chọn Program:", program_options)
                
                enrollment_date = st.date_input(
                    "Ngày bắt đầu:",
                    value=date.today()
                )
                
                col1, col2 = st. columns(2)
                
                with col1:
                    if st.form_submit_button("✅ Gán Program", type="primary", use_container_width=True):
                        selected_index = program_options.index(selected_program)
                        program_id = int(all_programs. iloc[selected_index]['ProgramID'])
                        
                        # Check if already assigned
                        existing = execute_query("""
                            SELECT COUNT(*) as cnt
                            FROM Student_Program
                            WHERE StudentID = ? AND ProgramID = ?
                        """, [student['UserID'], program_id])
                        
                        if not existing.empty and existing.iloc[0]['cnt'] > 0:
                            st.error("❌ Student đã được gán program này rồi!")
                        else:
                            success, msg = execute_procedure(
                                "EXEC EnrollStudentInProgram @p_StudentID=?, @p_ProgramID=?, @p_Enrollment_Date=?",
                                (student['UserID'], program_id, enrollment_date)
                            )
                            
                            if success:
                                st.success("✅ Đã gán program thành công!")
                                st.balloons()
                                del st.session_state. selected_student_for_program
                                st.rerun()
                            else:
                                st.error(f"❌ Lỗi: {msg}")
                
                with col2:
                    if st.form_submit_button("🔄 Hủy", use_container_width=True):
                        del st.session_state.selected_student_for_program
                        st.rerun()


def render_edit_delete_student():
    """Sửa/Xóa student"""
    
    st.subheader("✏️ Sửa/Xóa Student")
    
    st.markdown("### 🔍 Tìm Student")
    
    search_method = st.radio("Tìm kiếm theo:", ["ID", "Email"], horizontal=True, key="edit_search")
    
    if search_method == "ID":
        student_id = st.number_input("Nhập Student ID:", min_value=1, step=1, key="edit_id")
        
        if st. button("🔍 Tìm kiếm", type="primary", key="edit_find"):
            student_info = execute_query("""
                SELECT 
                    S.UserID,
                    U.LName,
                    U.FName,
                    dbo.GetFullName(S.UserID) as FullName,
                    U.Email_Address,
                    U.Phone_Number,
                    CONVERT(VARCHAR, S.Birthday, 23) as Birthday
                FROM Students S
                JOIN Users U ON S.UserID = U.UserID
                WHERE S. UserID = ?
            """, [student_id])
            
            if student_info.empty:
                st.error(f"❌ Không tìm thấy Student ID: {student_id}")
            else:
                st.session_state.selected_student_edit = student_info.iloc[0].to_dict()
                st.rerun()
    
    else:
        email = st.text_input("Nhập Email:", key="edit_email")
        
        if st.button("🔍 Tìm kiếm", type="primary", key="edit_find_email"):
            student_info = execute_query("""
                SELECT 
                    S.UserID,
                    U.LName,
                    U.FName,
                    dbo.GetFullName(S.UserID) as FullName,
                    U.Email_Address,
                    U.Phone_Number,
                    CONVERT(VARCHAR, S.Birthday, 23) as Birthday
                FROM Students S
                JOIN Users U ON S.UserID = U.UserID
                WHERE U.Email_Address = ?
            """, [email])
            
            if student_info.empty:
                st.error(f"❌ Không tìm thấy student với email: {email}")
            else:
                st.session_state. selected_student_edit = student_info.iloc[0].to_dict()
                st.rerun()
    
    if 'selected_student_edit' in st.session_state:
        st.markdown("---")
        st.markdown("### 👤 Thông tin Student")
        
        student = st.session_state.selected_student_edit
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            **Student ID:** {student['UserID']}  
            **Họ tên:** {student['FullName']}  
            **Email:** {student['Email_Address']}
            """)
        
        with col2:
            st.markdown(f"""
            **SĐT:** {student['Phone_Number']}  
            **Ngày sinh:** {student['Birthday']}
            """)
        
        st.markdown("---")
        st.markdown("### ✏️ Sửa thông tin")
        
        with st.form("edit_student_form"):
            col1, col2 = st. columns(2)
            
            with col1:
                new_lname = st.text_input("Họ mới:", value=student['LName'])
                new_email = st.text_input("Email mới:", value=student['Email_Address'])
            
            with col2:
                new_fname = st.text_input("Tên mới:", value=student['FName'])
                new_phone = st.text_input("SĐT mới:", value=student['Phone_Number'] if student['Phone_Number'] else "")
            
            from datetime import datetime
            current_birthday = datetime.strptime(student['Birthday'], '%Y-%m-%d').date()
            new_birthday = st.date_input("Ngày sinh mới:", value=current_birthday)
            
            col1, col2 = st. columns(2)
            
            with col1:
                if st.form_submit_button("💾 Lưu thay đổi", type="primary", use_container_width=True):
                    # Update User info
                    success1, msg1 = execute_procedure(
                        "EXEC UpdateUser @p_UserID=?, @p_NewLName=?, @p_NewFName=?, @p_NewEmail=?, @p_NewPhone=?",
                        (student['UserID'], new_lname, new_fname, new_email, new_phone if new_phone else None)
                    )
                    
                    # Update Student birthday
                    success2, msg2 = execute_procedure(
                        "EXEC UpdateStudent @p_UserID=?, @p_NewBirthday=?",
                        (student['UserID'], new_birthday)
                    )
                    
                    if success1 and success2:
                        st.success("✅ Đã cập nhật thông tin!")
                        del st.session_state.selected_student_edit
                        st. rerun()
                    else:
                        st.error(f"❌ Lỗi: {msg1 or msg2}")
            
            with col2:
                if st. form_submit_button("🔄 Hủy", use_container_width=True):
                    del st.session_state.selected_student_edit
                    st.rerun()
        
        st.markdown("---")
        st.markdown("### 🗑️ Xóa Student")
        
        # Check if student has activities
        has_activities = execute_query("""
            SELECT COUNT(*) as cnt
            FROM Activities
            WHERE StudentID = ?
        """, [student['UserID']])
        
        activity_count = has_activities.iloc[0]['cnt'] if not has_activities.empty else 0
        
        if activity_count > 0:
            st. error(f"❌ Không thể xóa!  Student này có {activity_count} hoạt động")
            st.info("💡 Xóa tất cả activities trước rồi mới xóa student")
        else:
            st.warning(f"⚠️ **Cảnh báo:** Xóa student sẽ xóa cả User và tất cả dữ liệu liên quan!")
            
            if st.button("🗑️ XÓA STUDENT NÀY", type="secondary"):
                # Delete Student first
                success, msg = execute_procedure(
                    "EXEC DeleteStudent @p_UserID=?",
                    [student['UserID']]
                )
                
                if success:
                    # Delete User
                    execute_procedure("EXEC DeleteUser @p_UserID=?", [student['UserID']])
                    
                    st.success("✅ Đã xóa student!")
                    del st.session_state. selected_student_edit
                    st.rerun()
                else:
                    st.error(f"❌ Lỗi: {msg}")