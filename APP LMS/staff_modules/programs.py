import streamlit as st
from datetime import date
from database import execute_query, execute_procedure

def render_programs_management():
    """Quản lý Degree Programs - Module chính"""
    
    st.title("🎓 Quản lý Degree Programs")
    
    st.info("""
    ℹ️ **Degree Programs (Chương trình Đào tạo):**
    - Cử nhân (Bachelor)
    - Thạc sĩ (Master)
    - Tiến sĩ (PhD)
    - Mỗi program có nhiều Specializations (Chuyên ngành)
    """)
    
    # Tabs
    tab1, tab2, tab3 = st.tabs([
        "➕ Thêm Program", 
        "📋 Danh sách Programs",
        "🎯 Specializations"
    ])
    
    with tab1:
        render_add_program()
    
    with tab2:
        render_programs_list()
    
    with tab3:
        render_specializations()


def render_add_program():
    """Thêm Degree Program mới"""
    
    st.subheader("➕ Thêm Degree Program mới")
    
    with st.form("add_program_form", clear_on_submit=True):
        st.markdown("### 📝 Thông tin Program")
        
        col1, col2 = st.columns(2)
        
        with col1:
            program_code = st. text_input(
                "Mã Program *",
                placeholder="VD: CS-BS",
                help="Mã chương trình đào tạo (unique)"
            )
        
        with col2:
            program_name = st.text_input(
                "Tên Program *",
                placeholder="VD: Cử nhân Khoa học Máy tính",
                help="Tên đầy đủ của chương trình"
            )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        col1, col2 = st. columns(2)
        
        with col1:
            submit_btn = st.form_submit_button(
                "✅ Tạo Program",
                type="primary",
                use_container_width=True
            )
        
        with col2:
            if st.form_submit_button("🔄 Reset", use_container_width=True):
                st.rerun()
        
        if submit_btn:
            if not program_code or not program_name:
                st.error("❌ Vui lòng điền đầy đủ các trường bắt buộc (*)")
            else:
                # Check duplicate
                existing = execute_query(
                    "SELECT COUNT(*) as cnt FROM Degree_Programs WHERE Code = ? ",
                    [program_code]
                )
                
                if not existing.empty and existing. iloc[0]['cnt'] > 0:
                    st.error(f"❌ Mã program '{program_code}' đã tồn tại!")
                else:
                    success, msg = execute_procedure(
                        "EXEC InsertDegreeProgram @p_Code=?, @p_Name=? ",
                        (program_code, program_name)
                    )
                    
                    if success:
                        new_program = execute_query(
                            "SELECT ProgramID FROM Degree_Programs WHERE Code = ?",
                            [program_code]
                        )
                        
                        if not new_program. empty:
                            program_id = int(new_program.iloc[0]['ProgramID'])
                            
                            st.success(f"✅ Đã tạo Program thành công!")
                            st. info(f"🆔 **Program ID: {program_id}**")
                            st. info(f"🎓 **[{program_code}] {program_name}**")
                            st.balloons()
                    else:
                        st.error(f"❌ Lỗi: {msg}")


def render_programs_list():
    """Danh sách Programs"""
    
    st.subheader("📋 Danh sách Degree Programs")
    
    programs = execute_query("""
        SELECT 
            DP.ProgramID,
            DP.Code,
            DP.Name,
            COUNT(DISTINCT SP.StudentID) as StudentCount,
            COUNT(DISTINCT S. SpecializationID) as SpecializationCount
        FROM Degree_Programs DP
        LEFT JOIN Student_Program SP ON DP.ProgramID = SP.ProgramID
        LEFT JOIN Specializations S ON DP.ProgramID = S.ProgramID
        GROUP BY DP.ProgramID, DP.Code, DP.Name
        ORDER BY DP.Code
    """)
    
    if programs.empty:
        st.info("📭 Chưa có program nào")
    else:
        st. success(f"✅ Có {len(programs)} programs")
        
        for _, program in programs.iterrows():
            with st.expander(f"🎓 [{program['Code']}] {program['Name']}"):
                col1, col2 = st. columns([3, 1])
                
                with col1:
                    st.markdown(f"""
                    **Program ID:** {program['ProgramID']}  
                    **Mã:** {program['Code']}  
                    **Tên:** {program['Name']}  
                    **Sinh viên:** {program['StudentCount']} | **Specializations:** {program['SpecializationCount']}
                    """)
                
                with col2:
                    if program['StudentCount'] == 0:
                        if st.button("🗑️ Xóa", key=f"del_prog_{program['ProgramID']}"):
                            success, msg = execute_procedure(
                                "EXEC DeleteDegreeProgram @p_ProgramID=?",
                                [program['ProgramID']]
                            )
                            if success:
                                st.success("✅ Đã xóa!")
                                st. rerun()
                            else:
                                st.error(msg)
                    else:
                        st. warning("⚠️ Có SV")


def render_specializations():
    """Quản lý Specializations"""
    
    st.subheader("🎯 Specializations (Chuyên ngành)")
    
    # Display list
    specializations = execute_query("""
        SELECT 
            S.SpecializationID,
            S. Proj_ID,
            S.Name,
            CONVERT(VARCHAR, S.Start_Date, 23) as Start_Date,
            DP.Code as ProgramCode,
            DP. Name as ProgramName
        FROM Specializations S
        JOIN Degree_Programs DP ON S. ProgramID = DP. ProgramID
        ORDER BY S.Name
    """)
    
    if not specializations.empty:
        st.success(f"✅ Có {len(specializations)} specializations")
        
        for _, spec in specializations.iterrows():
            col1, col2 = st. columns([4, 1])
            
            with col1:
                st. markdown(f"""
                **🎯 {spec['Name']}**  
                ID: {spec['Proj_ID']} | Program: [{spec['ProgramCode']}] {spec['ProgramName']} | Từ: {spec['Start_Date']}
                """)
            
            with col2:
                if st.button("🗑️ Xóa", key=f"del_spec_{spec['SpecializationID']}"):
                    success, msg = execute_procedure(
                        "EXEC DeleteSpecialization @p_SpecializationID=?",
                        [spec['SpecializationID']]
                    )
                    if success:
                        st.success("✅ Đã xóa!")
                        st.rerun()
                    else:
                        st.error(msg)
            
            st.markdown("---")
    else:
        st.info("📭 Chưa có specialization nào")
    
    # Add new specialization
    st.markdown("---")
    st.markdown("### ➕ Thêm Specialization mới")
    
    # Lấy Programs
    programs = execute_query("SELECT ProgramID, Code, Name FROM Degree_Programs ORDER BY Code")
    
    if programs.empty:
        st.warning("⚠️ Chưa có Program nào!  Tạo Program trước.")
        return
    
    with st.form("add_spec_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            spec_proj_id = st.text_input(
                "Proj ID *",
                placeholder="VD: SP-CS-AI",
                help="Mã dự án chuyên ngành (unique)"
            )
            
            spec_name = st.text_input(
                "Tên Specialization *",
                placeholder="VD: Trí tuệ Nhân tạo",
                help="Tên chuyên ngành"
            )
        
        with col2:
            start_date = st. date_input(
                "Ngày bắt đầu *",
                value=date.today(),
                help="Ngày bắt đầu chuyên ngành"
            )
            
            program_options = programs.apply(
                lambda row: f"[{row['Code']}] {row['Name']}", 
                axis=1
            ). tolist()
            
            selected_program = st.selectbox("Program *", program_options)
        
        if st.form_submit_button("✅ Tạo Specialization", type="primary"):
            if not spec_proj_id or not spec_name:
                st.error("❌ Vui lòng điền đầy đủ các trường bắt buộc (*)")
            else:
                # Check duplicate
                existing = execute_query(
                    "SELECT COUNT(*) as cnt FROM Specializations WHERE Proj_ID = ? ",
                    [spec_proj_id]
                )
                
                if not existing.empty and existing.iloc[0]['cnt'] > 0:
                    st.error(f"❌ Proj ID '{spec_proj_id}' đã tồn tại!")
                else:
                    program_index = program_options.index(selected_program)
                    program_id = int(programs.iloc[program_index]['ProgramID'])
                    
                    success, msg = execute_procedure(
                        "EXEC InsertSpecialization @p_Proj_ID=?, @p_Start_Date=?, @p_Name=?, @p_ProgramID=? ",
                        (spec_proj_id, start_date, spec_name, program_id)
                    )
                    
                    if success:
                        st.success("✅ Đã tạo Specialization!")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(f"❌ Lỗi: {msg}")