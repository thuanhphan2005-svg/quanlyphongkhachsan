import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date
import plotly.express as px

# ---------------------------------------------------------
# 1. CẤU HÌNH TRANG VÀ THIẾT KẾ GIAO DIỆN (UI/UX)
# ---------------------------------------------------------
st.set_page_config(
    page_title="Hotel Management System",
    page_icon="🏨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS cho giao diện hiện đại, chuyên nghiệp
st.markdown("""
    <style>
    .main { padding: 1.5rem; }
    .stMetric {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .status-card {
        padding: 15px;
        border-radius: 8px;
        text-align: center;
        font-weight: bold;
        color: white;
        margin-bottom: 10px;
    }
    .status-available { background-color: #28a745; }
    .status-occupied { background-color: #dc3545; }
    .status-cleaning { background-color: #ffc107; color: #333; }
    .status-maintenance { background-color: #6c757d; }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. KHỞI TẠO VÀ XỬ LÝ CƠ SỞ DỮ LIỆU (SQLITE)
# ---------------------------------------------------------
DB_FILE = "hotel_management.db"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Bảng phòng
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rooms (
            room_number TEXT PRIMARY KEY,
            room_type TEXT NOT NULL,
            price_per_night REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'Trống'
        )
    """)
    
    # Bảng đặt phòng / giao dịch
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guest_name TEXT NOT NULL,
            guest_phone TEXT NOT NULL,
            room_number TEXT NOT NULL,
            check_in_date TEXT NOT NULL,
            check_out_date TEXT NOT NULL,
            total_price REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'Đang ở',
            FOREIGN KEY (room_number) REFERENCES rooms (room_number)
        )
    """)
    
    # Thêm dữ liệu mẫu nếu bảng phòng đang trống
    cursor.execute("SELECT COUNT(*) FROM rooms")
    if cursor.fetchone()[0] == 0:
        sample_rooms = [
            ('101', 'Đơn (Standard)', 500000, 'Trống'),
            ('102', 'Đơn (Standard)', 500000, 'Trống'),
            ('201', 'Đôi (Deluxe)', 800000, 'Trống'),
            ('202', 'Đôi (Deluxe)', 800000, 'Trống'),
            ('301', 'VIP Suite', 1500000, 'Trống'),
        ]
        cursor.executemany("INSERT INTO rooms VALUES (?, ?, ?, ?)", sample_rooms)
        conn.commit()
    
    conn.close()

init_db()

# ---------------------------------------------------------
# 3. CÁC HÀM TRUY VẤN DỮ LIỆU
# ---------------------------------------------------------
def fetch_rooms():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM rooms ORDER BY room_number ASC", conn)
    conn.close()
    return df

def fetch_bookings(active_only=False):
    conn = get_db_connection()
    query = "SELECT * FROM bookings"
    if active_only:
        query += " WHERE status = 'Đang ở'"
    query += " ORDER BY id DESC"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def add_room(number, r_type, price):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO rooms VALUES (?, ?, ?, 'Trống')", (number, r_type, price))
        conn.commit()
        return True, "Thêm phòng thành công!"
    except sqlite3.IntegrityError:
        return False, "Số phòng đã tồn tại!"
    finally:
        conn.close()

def update_room_status(number, status):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE rooms SET status = ? WHERE room_number = ?", (status, number))
    conn.commit()
    conn.close()

def create_booking(guest_name, guest_phone, room_number, check_in, check_out, total_price):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO bookings (guest_name, guest_phone, room_number, check_in_date, check_out_date, total_price, status)
        VALUES (?, ?, ?, ?, ?, ?, 'Đang ở')
    """, (guest_name, guest_phone, room_number, str(check_in), str(check_out), total_price))
    cursor.execute("UPDATE rooms SET status = 'Đang có khách' WHERE room_number = ?", (room_number,))
    conn.commit()
    conn.close()

def checkout_booking(booking_id, room_number):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE bookings SET status = 'Đã trả phòng' WHERE id = ?", (booking_id,))
    cursor.execute("UPDATE rooms SET status = 'Đang dọn' WHERE room_number = ?", (room_number,))
    conn.commit()
    conn.close()

# ---------------------------------------------------------
# 4. THANH ĐIỀU HƯỚNG (SIDEBAR)
# ---------------------------------------------------------
st.sidebar.title("🏨 Khách Sạn Management")
st.sidebar.caption("Hệ thống quản lý phòng & đặt phòng")

menu = st.sidebar.radio(
    "Điều hướng",
    ["📊 Dashboard Tổng quan", "🛎️ Sơ đồ & Đặt phòng", "📥 Check-out & Thanh toán", "⚙️ Quản lý danh mục phòng"]
)

# ---------------------------------------------------------
# 5. MÀN HÌNH: DASHBOARD TỔNG QUAN
# ---------------------------------------------------------
if menu == "📊 Dashboard Tổng quan":
    st.header("📊 Dashboard Tổng quan Khách sạn")
    
    rooms_df = fetch_rooms()
    bookings_df = fetch_bookings()
    
    total_rooms = len(rooms_df)
    occupied_rooms = len(rooms_df[rooms_df['status'] == 'Đang có khách'])
    available_rooms = len(rooms_df[rooms_df['status'] == 'Trống'])
    cleaning_rooms = len(rooms_df[rooms_df['status'] == 'Đang dọn'])
    
    total_revenue = bookings_df['total_price'].sum() if not bookings_df.empty else 0
    occupancy_rate = (occupied_rooms / total_rooms * 100) if total_rooms > 0 else 0

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Tổng số phòng", f"{total_rooms} phòng")
    col2.metric("Phòng đang có khách", f"{occupied_rooms}", f"{occupancy_rate:.1f}% công suất")
    col3.metric("Phòng trống sẵn sàng", f"{available_rooms}")
    col4.metric("Phòng đang dọn", f"{cleaning_rooms}")
    col5.metric("Tổng doanh thu", f"{total_revenue:,.0f} VNĐ")

    st.markdown("---")
    
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.subheader("📈 Trạng thái phòng hiện tại")
        if not rooms_df.empty:
            fig_status = px.pie(
                rooms_df, 
                names='status', 
                title='Tỷ lệ trạng thái phòng',
                color='status',
                color_discrete_map={
                    'Trống': '#28a745',
                    'Đang có khách': '#dc3545',
                    'Đang dọn': '#ffc107',
                    'Bảo trì': '#6c757d'
                }
            )
            st.plotly_chart(fig_status, use_container_width=True)

    with col_chart2:
        st.subheader("📋 Lịch sử đặt phòng gần đây")
        if not bookings_df.empty:
            st.dataframe(
                bookings_df[['id', 'guest_name', 'room_number', 'check_in_date', 'check_out_date', 'total_price', 'status']],
                hide_index=True,
                use_container_width=True
            )
        else:
            st.info("Chưa có dữ liệu đặt phòng.")

# ---------------------------------------------------------
# 6. MÀN HÌNH: SƠ ĐỒ PHÒNG & ĐẶT PHÒNG (CHECK-IN)
# ---------------------------------------------------------
elif menu == "🛎️ Sơ đồ & Đặt phòng":
    st.header("🛎️ Sơ đồ Phòng & Đặt phòng mới")
    
    rooms_df = fetch_rooms()
    
    # Hiển thị grid sơ đồ phòng
    st.subheader("Sơ đồ trạng thái phòng")
    cols = st.columns(4)
    
    for idx, row in rooms_df.iterrows():
        col = cols[idx % 4]
        status = row['status']
        
        status_class = "status-available"
        if status == "Đang có khách":
            status_class = "status-occupied"
        elif status == "Đang dọn":
            status_class = "status-cleaning"
        elif status == "Bảo trì":
            status_class = "status-maintenance"
            
        with col:
            st.markdown(f"""
                <div class="status-card {status_class}">
                    <h3>Phòng {row['room_number']}</h3>
                    <p>{row['room_type']}</p>
                    <p><b>{status}</b></p>
                    <p>{row['price_per_night']:,.0f} VNĐ/đêm</p>
                </div>
            """, unsafe_allow_html=True)
            
            # Nút đổi trạng thái dọn dẹp nhanh
            if status == "Đang dọn":
                if st.button(f"✅ Đã dọn xong {row['room_number']}", key=f"clean_{row['room_number']}"):
                    update_room_status(row['room_number'], "Trống")
                    st.rerun()

    st.markdown("---")
    
    # Form Check-in Đặt phòng
    st.subheader("📝 Check-in Đặt phòng")
    
    available_rooms = rooms_df[rooms_df['status'] == 'Trống']
    
    if available_rooms.empty:
        st.warning("Hiện tại không có phòng nào trống để đặt!")
    else:
        with st.form("checkin_form"):
            col_a, col_b = st.columns(2)
            
            with col_a:
                guest_name = st.text_input("Tên khách hàng (*)")
                guest_phone = st.text_input("Số điện thoại (*)")
                selected_room_num = st.selectbox(
                    "Chọn phòng trống (*)", 
                    options=available_rooms['room_number'].tolist(),
                    format_func=lambda x: f"Phòng {x} - {available_rooms[available_rooms['room_number']==x]['room_type'].values[0]}"
                )
                
            with col_b:
                check_in = st.date_input("Ngày nhận phòng", date.today())
                check_out = st.date_input("Ngày trả phòng dự kiến", date.today())
                
                # Tính tổng tiền dự kiến
                room_price = available_rooms[available_rooms['room_number'] == selected_room_num]['price_per_night'].values[0]
                num_nights = (check_out - check_in).days
                if num_nights <= 0:
                    num_nights = 1 # Mặc định tối thiểu 1 đêm nếu ở trong ngày
                
                est_total = room_price * num_nights
                st.info(f"💵 Số đêm: **{num_nights}** | Tạm tính: **{est_total:,.0f} VNĐ**")

            submit_btn = st.form_submit_button("✅ Xác nhận Check-in")
            
            if submit_btn:
                if not guest_name or not guest_phone:
                    st.error("Vui lòng điền đầy đủ thông tin khách hàng!")
                else:
                    create_booking(guest_name, guest_phone, selected_room_num, check_in, check_out, est_total)
                    st.success(f"Check-in thành công cho khách {guest_name} - Phòng {selected_room_num}!")
                    st.rerun()

# ---------------------------------------------------------
# 7. MÀN HÌNH: CHECK-OUT & THANH TOÁN
# ---------------------------------------------------------
elif menu == "📥 Check-out & Thanh toán":
    st.header("📥 Check-out & Thanh toán")
    
    active_bookings = fetch_bookings(active_only=True)
    
    if active_bookings.empty:
        st.info("Hiện không có phòng nào đang sử dụng.")
    else:
        st.subheader("Danh sách khách đang lưu trú")
        
        for idx, row in active_bookings.iterrows():
            with st.expander(f"🔴 Phòng {row['room_number']} - Khách: {row['guest_name']} (SĐT: {row['guest_phone']})"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Ngày vào:** {row['check_in_date']}")
                    st.write(f"**Ngày ra dự kiến:** {row['check_out_date']}")
                    st.write(f"**Tổng tiền thanh toán:** {row['total_price']:,.0f} VNĐ")
                
                with col2:
                    if st.button(f"💳 Xử lý Check-out & Thanh toán", key=f"checkout_{row['id']}"):
                        checkout_booking(row['id'], row['room_number'])
                        st.success(f"Check-out thành công cho Phòng {row['room_number']}. Phòng đã chuyển sang trạng thái 'Đang dọn'.")
                        st.rerun()

# ---------------------------------------------------------
# 8. MÀN HÌNH: QUẢN LÝ DANH MỤC PHÒNG
# ---------------------------------------------------------
elif menu == "⚙️ Quản lý danh mục phòng":
    st.header("⚙️ Quản lý danh mục phòng")
    
    tab1, tab2 = st.tabs(["📋 Danh sách phòng", "➕ Thêm phòng mới"])
    
    with tab1:
        rooms_df = fetch_rooms()
        st.dataframe(rooms_df, use_container_width=True, hide_index=True)
        
    with tab2:
        st.subheader("Thêm phòng mới vào hệ thống")
        with st.form("add_room_form"):
            new_room_num = st.text_input("Số phòng (Ví dụ: 103, 302)")
            new_room_type = st.selectbox("Loại phòng", ["Đơn (Standard)", "Đôi (Deluxe)", "VIP Suite", "Gia đình (Family)"])
            new_room_price = st.number_input("Giá phòng / đêm (VNĐ)", min_value=100000, step=50000, value=500000)
            
            add_btn = st.form_submit_button("Thêm phòng")
            
            if add_btn:
                if not new_room_num:
                    st.error("Vui lòng nhập số phòng!")
                else:
                    success, msg = add_room(new_room_num, new_room_type, new_room_price)
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
