import streamlit as st
from database import execute_query, execute_procedure

def render_organizations_management():
    """Quản lý Organizations - Module chính"""
    
    st.title("🏢 Quản lý Organizations")
    
    st.info("""
    ℹ️ **Cấu trúc tổ chức:**
    - **Education Centers** (Trung tâm): Đơn vị lớn nhất
    - **Departments** (Khoa): Thuộc về Education Center
    """)
    
    # Tabs
    tab1, tab2 = st.tabs(["🏛️ Education Centers", "🏢 Departments"])
    
    with tab1:
        render_education_centers()
    
    with tab2:
        render_departments()


def render_education_centers():
    """Quản lý Education Centers"""
    
    st. subheader("🏛️ Education Centers")
    
    # Display list
    centers = execute_query("""
        SELECT 
            EC.CenterID,
            EC.Name,
            EC.Phone_Number,
            COUNT(D.DepartmentID) as DepartmentCount
        FROM Education_Centers EC
        LEFT JOIN Departments D ON EC.CenterID = D.CenterID
        GROUP BY EC.CenterID, EC.Name, EC. Phone_Number
        ORDER BY EC.Name
    """)
    
    if not centers.empty:
        st. success(f"✅ Có {len(centers)} Education Centers")
        
        for _, center in centers.iterrows():
            with st.expander(f"🏛️ {center['Name']} ({center['DepartmentCount']} khoa)"):
                col1, col2 = st. columns([3, 1])
                
                with col1:
                    st.markdown(f"""
                    **Center ID:** {center['CenterID']}  
                    **Tên:** {center['Name']}  
                    **SĐT:** {center['Phone_Number']}  
                    **Số Departments:** {center['DepartmentCount']}
                    """)
                
                with col2:
                    if center['DepartmentCount'] == 0:
                        if st.button("🗑️ Xóa", key=f"del_center_{center['CenterID']}"):
                            success, msg = execute_procedure(
                                "EXEC DeleteEducationCenter @p_CenterID=?",
                                [center['CenterID']]
                            )
                            if success:
                                st.success("✅ Đã xóa!")
                                st. rerun()
                            else:
                                st.error(msg)
                    else:
                        st.warning("⚠️ Có khoa")
    else:
        st.info("📭 Chưa có Education Center nào")
    
    # Add new center
    st.markdown("---")
    st.markdown("### ➕ Thêm Education Center mới")
    
    with st.form("add_center_form"):
        col1, col2 = st. columns(2)
        
        with col1:
            center_name = st.text_input("Tên Center *", placeholder="VD: Trung tâm Công nghệ")
        
        with col2:
            center_phone = st.text_input("Số điện thoại", placeholder="0281234567")
        
        if st.form_submit_button("✅ Tạo Center", type="primary"):
            if not center_name:
                st.error("❌ Vui lòng nhập tên Center")
            else:
                success, msg = execute_procedure(
                    "EXEC InsertEducationCenter @p_Name=?, @p_Phone_Number=?",
                    (center_name, center_phone if center_phone else None)
                )
                
                if success:
                    st.success("✅ Đã tạo Education Center!")
                    st.balloons()
                    st.rerun()
                else:
                    st.error(f"❌ Lỗi: {msg}")


def render_departments():
    """Quản lý Departments"""
    
    st.subheader("🏢 Departments (Khoa)")
    
    # Display list
    departments = execute_query("""
        SELECT 
            D.DepartmentID,
            D.Name,
            D.Office_Location,
            D.Phone_Number,
            EC.Name as CenterName,
            COUNT(DISTINCT P.UserID) as ProfessorCount,
            COUNT(DISTINCT C.CourseID) as CourseCount
        FROM Departments D
        LEFT JOIN Education_Centers EC ON D. CenterID = EC.CenterID
        LEFT JOIN Professors P ON D.DepartmentID = P.DepartmentID
        LEFT JOIN Courses C ON D. DepartmentID = C.DepartmentID
        GROUP BY D.DepartmentID, D. Name, D.Office_Location, D.Phone_Number, EC. Name
        ORDER BY D.Name
    """)
    
    if not departments.empty:
        st.success(f"✅ Có {len(departments)} Departments")
        
        for _, dept in departments.iterrows():
            with st.expander(f"🏢 {dept['Name']} - {dept['CenterName']}"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st. markdown(f"""
                    **Department ID:** {dept['DepartmentID']}  
                    **Tên:** {dept['Name']}  
                    **Văn phòng:** {dept['Office_Location']}  
                    **SĐT:** {dept['Phone_Number']}  
                    **Trung tâm:** {dept['CenterName']}  
                    **Professors:** {dept['ProfessorCount']} | **Courses:** {dept['CourseCount']}
                    """)
                
                with col2:
                    if dept['ProfessorCount'] == 0 and dept['CourseCount'] == 0:
                        if st.button("🗑️ Xóa", key=f"del_dept_{dept['DepartmentID']}"):
                            success, msg = execute_procedure(
                                "EXEC DeleteDepartment @p_DepartmentID=?",
                                [dept['DepartmentID']]
                            )
                            if success:
                                st. success("✅ Đã xóa!")
                                st.rerun()
                            else:
                                st.error(msg)
                    else:
                        st.warning("⚠️ Có dữ liệu")
    else:
        st. info("📭 Chưa có Department nào")
    
    # Add new department
    st.markdown("---")
    st.markdown("### ➕ Thêm Department mới")
    
    # Lấy Education Centers
    centers = execute_query("SELECT CenterID, Name FROM Education_Centers ORDER BY Name")
    
    if centers.empty:
        st. warning("⚠️ Chưa có Education Center nào!  Tạo Center trước.")
        return
    
    with st.form("add_dept_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            dept_name = st.text_input("Tên Department *", placeholder="VD: Khoa Công nghệ Thông tin")
            dept_office = st.text_input("Văn phòng", placeholder="VD: Building A, Room 101")
        
        with col2:
            dept_phone = st.text_input("Số điện thoại", placeholder="0281234567")
            
            center_options = centers['Name'].tolist()
            selected_center = st.selectbox("Education Center *", center_options)
        
        if st.form_submit_button("✅ Tạo Department", type="primary"):
            if not dept_name:
                st.error("❌ Vui lòng nhập tên Department")
            else:
                center_id = int(centers[centers['Name'] == selected_center]['CenterID']. values[0])
                
                success, msg = execute_procedure(
                    "EXEC InsertDepartment @p_Name=?, @p_Office_Location=?, @p_Phone_Number=?, @p_CenterID=?",
                    (dept_name, dept_office if dept_office else None, dept_phone if dept_phone else None, center_id)
                )
                
                if success:
                    st.success("✅ Đã tạo Department!")
                    st.balloons()
                    st.rerun()
                else:
                    st.error(f"❌ Lỗi: {msg}")