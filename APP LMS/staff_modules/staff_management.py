import streamlit as st
from database import execute_query, execute_procedure

def render_staff_management():
    """Quản lý Staff - Module chính"""
    
    st.title("👔 Quản lý Staff")
    
    # Check if current user is admin
    current_staff = execute_query("""
        SELECT Role FROM Staff WHERE UserID = ? 
    """, [st.session_state.user_id])
    
    is_admin = False
    if not current_staff.empty:
        is_admin = current_staff. iloc[0]['Role'] == 'Admin'
    
    if not is_admin:
        st. error("❌ Chỉ Staff có role 'Admin' mới có quyền quản lý Staff!")
        st.info(f"💡 Role hiện tại của bạn: **{st.session_state.user_data. get('Role', 'N/A')}**")
        return
    
    # Tabs
    tab1, tab2, tab3 = st.tabs([
        "➕ Thêm Staff", 
        "📋 Danh sách Staff",
        "✏️ Sửa/Xóa"
    ])
    
    with tab1:
        render_add_staff_form()
    
    with tab2:
        render_staff_list()
    
    with tab3:
        render_edit_delete_staff()


def render_add_staff_form():
    """Form thêm staff mới - TẠO LUÔN USER"""
    
    st.subheader("➕ Thêm Staff mới")
    
    st. info("""
    ℹ️ **Hướng dẫn:**
    - Điền đầy đủ thông tin nhân viên
    - Chọn Role (Academic Advisor, Admin, HR...)
    - Hệ thống sẽ tự động tạo User + Staff
    """)
    
    with st.form("add_staff_form", clear_on_submit=True):
        st.markdown("### 📝 Thông tin Staff")
        
        # User info
        col1, col2 = st. columns(2)
        
        with col1:
            lname = st.text_input(
                "Họ *",
                placeholder="VD: Nguyễn",
                help="Họ của nhân viên"
            )
            
            email = st.text_input(
                "Email *",
                placeholder="example@university.edu",
                help="Email phải unique"
            )
        
        with col2:
            fname = st.text_input(
                "Tên *",
                placeholder="VD: Văn An",
                help="Tên của nhân viên"
            )
            
            phone = st.text_input(
                "Số điện thoại",
                placeholder="0901234567",
                help="Số điện thoại (không bắt buộc)"
            )
        
        # Role
        st.markdown("---")
        st.markdown("### 👔 Vai trò Staff")
        
        role = st.selectbox(
            "Chọn Role *",
            [
                "Academic Advisor",
                "Admin",
                "HR Manager",
                "Finance Officer",
                "IT Support",
                "Registrar"
            ],
            help="Vai trò/chức vụ của staff"
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        col1, col2 = st. columns(2)
        
        with col1:
            submit_btn = st.form_submit_button(
                "✅ Tạo Staff",
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
                    "SELECT COUNT(*) as cnt FROM Users WHERE Email_Address = ? ",
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
                            
                            # Step 2: Insert Staff
                            success2, msg2 = execute_procedure(
                                "EXEC InsertStaff @p_UserID=?, @p_Role=?",
                                (user_id, role)
                            )
                            
                            if not success2:
                                st.error(f"❌ Lỗi tạo Staff: {msg2}")
                                # Rollback: Delete User
                                execute_procedure("EXEC DeleteUser @p_UserID=?", [user_id])
                            else:
                                # Success! 
                                st.success(f"✅ Đã tạo Staff thành công!")
                                st.info(f"🆔 **Staff ID: {user_id}**")
                                st.info(f"👤 **Họ tên: {fname} {lname}**")
                                st.info(f"📧 **Email: {email}**")
                                st.info(f"👔 **Role: {role}**")
                                st.balloons()


def render_staff_list():
    """Hiển thị danh sách staff"""
    
    st.subheader("📋 Danh sách Staff")
    
    # Filters
    col1, col2 = st. columns([2, 1])
    
    with col1:
        # Get all unique roles
        all_roles = execute_query("SELECT DISTINCT Role FROM Staff ORDER BY Role")
        
        if not all_roles.empty:
            role_filter_options = ["Tất cả"] + all_roles['Role'].tolist()
            selected_role_filter = st.selectbox("Lọc theo Role:", role_filter_options)
        else:
            selected_role_filter = "Tất cả"
    
    with col2:
        sort_order = st.selectbox("Sắp xếp:", ["Mới nhất", "Cũ nhất", "Tên A-Z"])
    
    # Query
    if selected_role_filter == "Tất cả":
        staff_list = execute_query("""
            SELECT 
                S.UserID,
                dbo.GetFullName(S.UserID) as FullName,
                U.Email_Address,
                U.Phone_Number,
                S.Role
            FROM Staff S
            JOIN Users U ON S.UserID = U.UserID
            ORDER BY S.UserID DESC
        """)
    else:
        staff_list = execute_query("""
            SELECT 
                S.UserID,
                dbo.GetFullName(S.UserID) as FullName,
                U.Email_Address,
                U.Phone_Number,
                S.Role
            FROM Staff S
            JOIN Users U ON S.UserID = U. UserID
            WHERE S.Role = ?
            ORDER BY S. UserID DESC
        """, [selected_role_filter])
    
    # Display
    if staff_list.empty:
        st.info("📭 Chưa có staff nào")
    else:
        st.success(f"✅ Tìm thấy {len(staff_list)} staff members")
        
        st.dataframe(
            staff_list,
            column_config={
                "UserID": st.column_config.NumberColumn("Staff ID", width="small"),
                "FullName": st.column_config. TextColumn("Họ tên", width="large"),
                "Email_Address": st.column_config. TextColumn("Email", width="large"),
                "Phone_Number": st.column_config.TextColumn("SĐT", width="medium"),
                "Role": st. column_config.TextColumn("Vai trò", width="medium")
            },
            use_container_width=True,
            hide_index=True
        )


def render_edit_delete_staff():
    """Sửa/Xóa staff"""
    
    st.subheader("✏️ Sửa/Xóa Staff")
    
    st.markdown("### 🔍 Tìm Staff")
    
    search_method = st.radio("Tìm kiếm theo:", ["ID", "Email"], horizontal=True, key="edit_staff_search")
    
    if search_method == "ID":
        staff_id = st.number_input("Nhập Staff ID:", min_value=1, step=1)
        
        if st.button("🔍 Tìm kiếm", type="primary", key="edit_staff_find"):
            staff_info = execute_query("""
                SELECT 
                    S.UserID,
                    U.LName,
                    U.FName,
                    dbo.GetFullName(S.UserID) as FullName,
                    U.Email_Address,
                    U.Phone_Number,
                    S.Role
                FROM Staff S
                JOIN Users U ON S.UserID = U.UserID
                WHERE S.UserID = ?
            """, [staff_id])
            
            if staff_info.empty:
                st.error(f"❌ Không tìm thấy Staff ID: {staff_id}")
            else:
                st.session_state.selected_staff_edit = staff_info.iloc[0]. to_dict()
                st.rerun()
    
    else:
        email = st.text_input("Nhập Email:")
        
        if st.button("🔍 Tìm kiếm", type="primary", key="edit_staff_find_email"):
            staff_info = execute_query("""
                SELECT 
                    S.UserID,
                    U.LName,
                    U.FName,
                    dbo.GetFullName(S.UserID) as FullName,
                    U.Email_Address,
                    U.Phone_Number,
                    S.Role
                FROM Staff S
                JOIN Users U ON S.UserID = U.UserID
                WHERE U.Email_Address = ?
            """, [email])
            
            if staff_info.empty:
                st.error(f"❌ Không tìm thấy staff với email: {email}")
            else:
                st.session_state. selected_staff_edit = staff_info.iloc[0].to_dict()
                st.rerun()
    
    if 'selected_staff_edit' in st.session_state:
        staff = st.session_state.selected_staff_edit
        
        # Prevent deleting yourself
        if staff['UserID'] == st.session_state.user_id:
            st.warning("⚠️ Bạn đang xem thông tin của chính mình!")
        
        st.markdown("---")
        st.markdown("### 👤 Thông tin Staff")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            **Staff ID:** {staff['UserID']}  
            **Họ tên:** {staff['FullName']}  
            **Email:** {staff['Email_Address']}
            """)
        
        with col2:
            st.markdown(f"""
            **SĐT:** {staff['Phone_Number']}  
            **Role:** {staff['Role']}
            """)
        
        st.markdown("---")
        st.markdown("### ✏️ Sửa thông tin")
        
        with st.form("edit_staff_form"):
            col1, col2 = st. columns(2)
            
            with col1:
                new_lname = st.text_input("Họ mới:", value=staff['LName'])
                new_email = st.text_input("Email mới:", value=staff['Email_Address'])
            
            with col2:
                new_fname = st.text_input("Tên mới:", value=staff['FName'])
                new_phone = st.text_input("SĐT mới:", value=staff['Phone_Number'] if staff['Phone_Number'] else "")
            
            new_role = st.selectbox(
                "Role mới:",
                [
                    "Academic Advisor",
                    "Admin",
                    "HR Manager",
                    "Finance Officer",
                    "IT Support",
                    "Registrar"
                ],
                index=["Academic Advisor", "Admin", "HR Manager", "Finance Officer", "IT Support", "Registrar"]. index(staff['Role']) if staff['Role'] in ["Academic Advisor", "Admin", "HR Manager", "Finance Officer", "IT Support", "Registrar"] else 0
            )
            
            col1, col2 = st. columns(2)
            
            with col1:
                if st.form_submit_button("💾 Lưu thay đổi", type="primary", use_container_width=True):
                    # Update User
                    success1, msg1 = execute_procedure(
                        "EXEC UpdateUser @p_UserID=?, @p_NewLName=?, @p_NewFName=?, @p_NewEmail=?, @p_NewPhone=?",
                        (staff['UserID'], new_lname, new_fname, new_email, new_phone if new_phone else None)
                    )
                    
                    # Update Staff role
                    success2, msg2 = execute_procedure(
                        "EXEC UpdateStaff @p_UserID=?, @p_NewRole=?",
                        (staff['UserID'], new_role)
                    )
                    
                    if success1 and success2:
                        st.success("✅ Đã cập nhật thông tin!")
                        del st.session_state.selected_staff_edit
                        st. rerun()
                    else:
                        st.error(f"❌ Lỗi: {msg1 or msg2}")
            
            with col2:
                if st.form_submit_button("🔄 Hủy", use_container_width=True):
                    del st.session_state.selected_staff_edit
                    st.rerun()
        
        st.markdown("---")
        st.markdown("### 🗑️ Xóa Staff")
        
        # Prevent self-deletion
        if staff['UserID'] == st.session_state.user_id:
            st.error("❌ Bạn không thể xóa chính mình!")
        else:
            st.warning(f"⚠️ **Cảnh báo:** Xóa staff sẽ xóa cả User và tất cả dữ liệu liên quan!")
            
            if st.button("🗑️ XÓA STAFF NÀY", type="secondary"):
                # Delete Staff
                success, msg = execute_procedure(
                    "EXEC DeleteStaff @p_UserID=?",
                    [staff['UserID']]
                )
                
                if success:
                    # Delete User
                    execute_procedure("EXEC DeleteUser @p_UserID=?", [staff['UserID']])
                    
                    st.success("✅ Đã xóa staff!")
                    del st.session_state.selected_staff_edit
                    st. rerun()
                else:
                    st.error(f"❌ Lỗi: {msg}")