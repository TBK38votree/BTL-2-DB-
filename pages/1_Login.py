import streamlit as st
from database import authenticate_user, execute_query
from styles import get_login_styles

st.set_page_config(page_title="Login", page_icon="🔐", layout="centered")

# Apply styles
st. markdown(get_login_styles(), unsafe_allow_html=True)

# Check if role is selected
if 'role' not in st.session_state:
    st.error("❌ Vui lòng chọn vai trò từ trang chủ!")
    if st.button("🏠 Về trang chủ", use_container_width=True):
        st.switch_page("app.py")
    st.stop()

role = st.session_state. role

# Login form
st.markdown(f'<p class="login-title">🔐 Đăng nhập {role}</p>', unsafe_allow_html=True)

with st. form("login_form", clear_on_submit=False):
    st.markdown(f"### Nhập {role} ID")
    
    user_id = st.number_input(
        "User ID",
        min_value=1,
        step=1,
        help=f"Nhập ID của bạn"
    )
    
    col1, col2 = st. columns(2)
    
    with col1:
        login_btn = st.form_submit_button("🔓 Đăng nhập", use_container_width=True, type="primary")
    
    with col2:
        if st.form_submit_button("🏠 Quay lại", use_container_width=True):
            st.session_state.clear()
            st.switch_page("app.py")
    
    if login_btn:
        success, user_data = authenticate_user(user_id, role)
        
        if success:
            # Save session data
            st.session_state. logged_in = True
            st. session_state.user_id = user_id
            st.session_state. user_data = user_data
            st.session_state.full_name = f"{user_data['FName']} {user_data['LName']}"
            
            st.success(f"✅ Đăng nhập thành công! Xin chào {st.session_state.full_name}")
            st.balloons()
            
            # Redirect to appropriate dashboard
            if role == "Student":
                st.switch_page("pages/2_Student.py")
            elif role == "Professor":
                st.switch_page("pages/3_Professor.py")
            else:
                st.switch_page("pages/4_Staff.py")
        else:
            st.error(f"❌ Không tìm thấy {role} với ID: {user_id}")

# ✅ INFO - HIỂN THỊ THEO DỮ LIỆU THỰC
st.markdown("<br>", unsafe_allow_html=True)

# Lấy danh sách ID thực từ database
if role == "Student":
    user_list = execute_query("""
        SELECT 
            S. UserID,
            dbo. GetFullName(S.UserID) as FullName
        FROM Students S
        ORDER BY S. UserID
    """)
    icon = "👨‍🎓"
    
elif role == "Professor":
    user_list = execute_query("""
        SELECT 
            P.UserID,
            dbo.GetFullName(P.UserID) as FullName
        FROM Professors P
        ORDER BY P. UserID
    """)
    icon = "👨‍🏫"
    
else:  # Staff
    user_list = execute_query("""
        SELECT 
            S.UserID,
            dbo.GetFullName(S.UserID) as FullName
        FROM Staff S
        ORDER BY S.UserID
    """)
    icon = "👔"

# Hiển thị danh sách
if not user_list.empty:
    total_users = len(user_list)
    
    # ✅ TẠO DANH SÁCH ID THỰC TẾ
    id_list = user_list['UserID'].tolist()
    
    # ✅ KIỂM TRA LIÊN TỤC HAY KHÔNG
    min_id = int(min(id_list))
    max_id = int(max(id_list))
    is_continuous = (len(id_list) == (max_id - min_id + 1))
    
    # ✅ HIỂN THỊ THÔNG MINH
    if is_continuous:
        # Nếu liên tiếp: "Từ 11 đến 30"
        id_display = f"**Từ ID {min_id} đến {max_id}**"
    else:
        # Nếu không liên tiếp: Hiển thị danh sách
        if total_users <= 10:
            # Ít người: Hiện tất cả
            id_display = f"**IDs: {', '.join(map(str, id_list))}**"
        else:
            # Nhiều người: Hiện vài cái đầu + ... 
            first_ids = ', '.join(map(str, id_list[:5]))
            last_ids = ', '.join(map(str, id_list[-2:]))
            id_display = f"**IDs: {first_ids}, ..., {last_ids}**"
    
    # Hiển thị info box
    st.info(f"""
💡 **{role} IDs có sẵn:**
- {id_display}
- Tổng: **{total_users} người**
- Click "Xem danh sách" bên dưới để xem đầy đủ
    """)
    
    # Expander với danh sách chi tiết
    with st.expander(f"📋 Xem danh sách đầy đủ ({total_users} người)"):
        # Chia thành các cột
        num_cols = 3
        cols = st.  columns(num_cols)
        
        for idx, row in user_list. iterrows():
            col_idx = idx % num_cols
            with cols[col_idx]:
                st.markdown(f"{icon} **{row['UserID']}** - {row['FullName']}")
else:
    st.warning(f"⚠️ Không tìm thấy {role} nào trong hệ thống")