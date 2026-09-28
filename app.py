import streamlit as st
import mysql.connector
from mysql.connector import Error
from datetime import datetime, date
import pandas as pd
import os


# =========================================================
# CẤU HÌNH MYSQL AIVEN
# =========================================================

DB_CONFIG = {
    "host": "mysql-31631392-thuanhphan2005-ad8b.c.aivencloud.com",
    "port": 27590,
    "user": "avnadmin",
    "password": "AVNS_upB8uNn3pMtP9iw0afh",
    "database": "defaultdb",
    "ssl_disabled": False,
    "ssl_verify_cert": False,
    "ssl_verify_identity": False,
}


# =========================================================
# KẾT NỐI DATABASE
# =========================================================

def get_conn():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)

        if conn.is_connected():
            return conn

        return None

    except Error as e:
        st.error(f"❌ Không thể kết nối MySQL Aiven: {e}")
        return None


# =========================================================
# KHỞI TẠO DATABASE
# =========================================================

def init_db():

    conn = get_conn()

    if conn is None:
        return False

    try:
        cur = conn.cursor()

        # -----------------------------------------
        # BẢNG ROOMS
        # -----------------------------------------

        cur.execute("""
            CREATE TABLE IF NOT EXISTS rooms (
                id INT AUTO_INCREMENT PRIMARY KEY,
                room_number VARCHAR(20) NOT NULL UNIQUE,
                room_type VARCHAR(50) NOT NULL,
                price DECIMAL(15,2) NOT NULL,
                status VARCHAR(30) NOT NULL DEFAULT 'Trống'
            )
        """)

        # -----------------------------------------
        # BẢNG BOOKINGS
        # -----------------------------------------

        cur.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                id INT AUTO_INCREMENT PRIMARY KEY,
                guest_name VARCHAR(255) NOT NULL,
                phone VARCHAR(30),
                room_id INT NOT NULL,
                check_in DATE NOT NULL,
                check_out DATE NOT NULL,
                guests INT DEFAULT 1,
                total DECIMAL(15,2) NOT NULL,
                status VARCHAR(30) NOT NULL DEFAULT 'Đã đặt',
                created_at DATETIME NOT NULL,
                CONSTRAINT fk_booking_room
                    FOREIGN KEY (room_id)
                    REFERENCES rooms(id)
                    ON DELETE RESTRICT
                    ON UPDATE CASCADE
            )
        """)

        conn.commit()

        # -----------------------------------------
        # KIỂM TRA DỮ LIỆU PHÒNG
        # -----------------------------------------

        cur.execute("SELECT COUNT(*) FROM rooms")
        count = cur.fetchone()[0]

        # -----------------------------------------
        # THÊM DỮ LIỆU MẪU NẾU DATABASE TRỐNG
        # -----------------------------------------

        if count == 0:

            rooms = [
                ("101", "Standard", 500000, "Trống"),
                ("102", "Standard", 500000, "Trống"),
                ("103", "Deluxe", 750000, "Trống"),
                ("104", "Deluxe", 750000, "Trống"),
                ("201", "Suite", 1200000, "Trống"),
                ("202", "Suite", 1200000, "Trống"),
                ("301", "VIP", 1800000, "Trống"),
                ("302", "VIP", 1800000, "Trống"),
            ]

            cur.executemany("""
                INSERT INTO rooms
                (
                    room_number,
                    room_type,
                    price,
                    status
                )
                VALUES (%s, %s, %s, %s)
            """, rooms)

            conn.commit()

        cur.close()
        conn.close()

        return True

    except Error as e:

        st.error(
            f"❌ Lỗi khởi tạo database: {e}"
        )

        try:
            conn.close()
        except:
            pass

        return False


# =========================================================
# QUERY DATABASE
# =========================================================

def query(sql, params=()):

    conn = get_conn()

    if conn is None:
        return pd.DataFrame()

    try:

        cur = conn.cursor(dictionary=True)

        cur.execute(sql, params)

        rows = cur.fetchall()

        cur.close()
        conn.close()

        return pd.DataFrame(rows)

    except Error as e:

        st.error(
            f"❌ Lỗi truy vấn database: {e}"
        )

        try:
            conn.close()
        except:
            pass

        return pd.DataFrame()


# =========================================================
# EXECUTE DATABASE
# =========================================================

def execute(sql, params=()):

    conn = get_conn()

    if conn is None:
        return None

    try:

        cur = conn.cursor()

        cur.execute(sql, params)

        conn.commit()

        last_id = cur.lastrowid

        cur.close()
        conn.close()

        return last_id

    except Error as e:

        st.error(
            f"❌ Lỗi thực thi database: {e}"
        )

        try:
            conn.rollback()
            conn.close()
        except:
            pass

        return None


# =========================================================
# FORMAT TIỀN
# =========================================================

def money(value):

    if value is None:
        return "0 ₫"

    return f"{float(value):,.0f} ₫"


# =========================================================
# CẤU HÌNH STREAMLIT
# =========================================================

st.set_page_config(
    page_title="Hotel Manager",
    page_icon="🏨",
    layout="wide"
)


# =========================================================
# KHỞI TẠO DATABASE
# =========================================================

database_ready = init_db()

if not database_ready:

    st.error(
        "❌ Không thể kết nối tới MySQL Aiven."
    )

    st.info(
        "Kiểm tra Host, Port, User, Password và Database trên Aiven."
    )

    st.stop()

else:
    st.sidebar.success("✅ MySQL Aiven đã kết nối!")


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title("🏨 HOTEL MANAGER")

st.sidebar.caption(
    "MySQL Database • Aiven Cloud"
)

menu = st.sidebar.radio(
    "MENU",
    [
        "📊 Tổng quan",
        "🛏️ Quản lý phòng",
        "📅 Đặt phòng",
        "👤 Nhận / Trả phòng",
        "📋 Danh sách đặt phòng"
    ]
)


# =========================================================
# DASHBOARD
# =========================================================

if menu == "📊 Tổng quan":

    st.title("📊 Tổng quan khách sạn")

    # -----------------------------------------
    # HÌNH ẢNH KHÁCH SẠN
    # -----------------------------------------

    if os.path.exists("VT.jpg"):

        st.image(
            "VT.jpg",
            caption="🏨 Khách sạn của chúng tôi",
            use_container_width=True
        )

    st.caption(
        "Hệ thống quản lý phòng khách sạn"
    )

    # -----------------------------------------
    # LẤY DỮ LIỆU
    # -----------------------------------------

    rooms = query(
        "SELECT * FROM rooms"
    )

    bookings = query(
        "SELECT * FROM bookings"
    )

    total_rooms = len(rooms)

    if not rooms.empty:

        occupied_rooms = int(
            (rooms["status"] == "Đang ở").sum()
        )

        reserved_rooms = int(
            (rooms["status"] == "Đã đặt").sum()
        )

        available_rooms = int(
            (rooms["status"] == "Trống").sum()
        )

    else:

        occupied_rooms = 0
        reserved_rooms = 0
        available_rooms = 0

    # -----------------------------------------
    # DOANH THU
    # -----------------------------------------

    if not bookings.empty:

        revenue = float(
            bookings.loc[
                bookings["status"] == "Đã trả phòng",
                "total"
            ].sum()
        )

    else:

        revenue = 0

    # -----------------------------------------
    # METRICS
    # -----------------------------------------

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "🏨 Tổng phòng",
        total_rooms
    )

    col2.metric(
        "🟢 Phòng trống",
        available_rooms
    )

    col3.metric(
        "🔴 Đang sử dụng",
        occupied_rooms
    )

    col4.metric(
        "💰 Doanh thu",
        money(revenue)
    )

    st.divider()

    # -----------------------------------------
    # BIỂU ĐỒ
    # -----------------------------------------

    st.subheader("📈 Tình trạng phòng")

    if total_rooms > 0:

        status_counts = (
            rooms["status"]
            .value_counts()
            .rename_axis("Trạng thái")
            .reset_index(
                name="Số phòng"
            )
        )

        st.bar_chart(
            status_counts.set_index(
                "Trạng thái"
            )
        )

    # -----------------------------------------
    # DANH SÁCH PHÒNG
    # -----------------------------------------

    st.subheader(
        "🛏️ Danh sách phòng"
    )

    if not rooms.empty:

        room_display = rooms[
            [
                "room_number",
                "room_type",
                "price",
                "status"
            ]
        ].rename(
            columns={
                "room_number": "Phòng",
                "room_type": "Loại phòng",
                "price": "Giá / đêm",
                "status": "Trạng thái"
            }
        )

        st.dataframe(
            room_display,
            use_container_width=True,
            hide_index=True
        )


# =========================================================
# QUẢN LÝ PHÒNG
# =========================================================

elif menu == "🛏️ Quản lý phòng":

    st.title("🛏️ Quản lý phòng")

    tab1, tab2 = st.tabs(
        [
            "📋 Danh sách phòng",
            "➕ Thêm phòng"
        ]
    )

    # =====================================================
    # DANH SÁCH PHÒNG
    # =====================================================

    with tab1:

        rooms = query(
            """
            SELECT *
            FROM rooms
            ORDER BY room_number
            """
        )

        if not rooms.empty:

            display = rooms.rename(
                columns={
                    "id": "ID",
                    "room_number": "Phòng",
                    "room_type": "Loại phòng",
                    "price": "Giá / đêm",
                    "status": "Trạng thái"
                }
            )

            st.dataframe(
                display,
                use_container_width=True,
                hide_index=True
            )

            st.divider()

            selected_room = st.selectbox(
                "Chọn phòng cần cập nhật",
                rooms["room_number"].tolist()
            )

            room = rooms[
                rooms["room_number"]
                == selected_room
            ].iloc[0]

            col1, col2, col3 = st.columns(3)

            room_types = [
                "Standard",
                "Deluxe",
                "Suite",
                "VIP"
            ]

            statuses = [
                "Trống",
                "Đã đặt",
                "Đang ở",
                "Bảo trì"
            ]

            with col1:

                new_type = st.selectbox(
                    "Loại phòng",
                    room_types,
                    index=room_types.index(
                        room["room_type"]
                    )
                )

            with col2:

                new_price = st.number_input(
                    "Giá / đêm",
                    min_value=0.0,
                    value=float(
                        room["price"]
                    ),
                    step=50000.0
                )

            with col3:

                new_status = st.selectbox(
                    "Trạng thái",
                    statuses,
                    index=statuses.index(
                        room["status"]
                    )
                )

            col1, col2 = st.columns(2)

            with col1:

                if st.button(
                    "💾 Lưu thay đổi",
                    type="primary",
                    use_container_width=True
                ):

                    result = execute(
                        """
                        UPDATE rooms
                        SET
                            room_type = %s,
                            price = %s,
                            status = %s
                        WHERE id = %s
                        """,
                        (
                            new_type,
                            new_price,
                            new_status,
                            int(room["id"])
                        )
                    )

                    if result is not None:

                        st.success(
                            "Đã cập nhật phòng thành công!"
                        )

                        st.rerun()

            with col2:

                if st.button(
                    "🗑️ Xóa phòng",
                    use_container_width=True
                ):

                    if room["status"] != "Trống":

                        st.error(
                            "Chỉ được xóa phòng đang trống."
                        )

                    else:

                        result = execute(
                            """
                            DELETE FROM rooms
                            WHERE id = %s
                            """,
                            (int(room["id"]),)
                        )

                        if result is not None:

                            st.success(
                                "Đã xóa phòng."
                            )

                            st.rerun()

        else:

            st.info(
                "Chưa có phòng nào."
            )

    # =====================================================
    # THÊM PHÒNG
    # =====================================================

    with tab2:

        with st.form(
            "add_room"
        ):

            col1, col2, col3 = st.columns(3)

            with col1:

                room_number = st.text_input(
                    "Số phòng *",
                    placeholder="Ví dụ: 401"
                )

            with col2:

                room_type = st.selectbox(
                    "Loại phòng",
                    [
                        "Standard",
                        "Deluxe",
                        "Suite",
                        "VIP"
                    ]
                )

            with col3:

                price = st.number_input(
                    "Giá / đêm",
                    min_value=0.0,
                    value=500000.0,
                    step=50000.0
                )

            submitted = st.form_submit_button(
                "➕ Thêm phòng",
                type="primary"
            )

            if submitted:

                if not room_number.strip():

                    st.error(
                        "Vui lòng nhập số phòng."
                    )

                else:

                    try:

                        result = execute(
                            """
                            INSERT INTO rooms
                            (
                                room_number,
                                room_type,
                                price,
                                status
                            )
                            VALUES (%s, %s, %s, %s)
                            """,
                            (
                                room_number.strip(),
                                room_type,
                                price,
                                "Trống"
                            )
                        )

                        if result is not None:

                            st.success(
                                f"Đã thêm phòng "
                                f"{room_number}!"
                            )

                            st.rerun()

                    except Error as e:

                        if "Duplicate" in str(e):

                            st.error(
                                "Số phòng này đã tồn tại."
                            )

                        else:

                            st.error(
                                f"Lỗi: {e}"
                            )


# =========================================================
# ĐẶT PHÒNG
# =========================================================

elif menu == "📅 Đặt phòng":

    st.title("📅 Đặt phòng")

    rooms = query(
        """
        SELECT *
        FROM rooms
        WHERE status = 'Trống'
        ORDER BY room_number
        """
    )

    if rooms.empty:

        st.warning(
            "Hiện tại không còn phòng trống."
        )

    else:

        room_map = {}

        for _, room in rooms.iterrows():

            label = (
                f"{room['room_number']} - "
                f"{room['room_type']} "
                f"({money(room['price'])}/đêm)"
            )

            room_map[label] = room

        with st.form(
            "booking_form"
        ):

            guest_name = st.text_input(
                "Tên khách *"
            )

            phone = st.text_input(
                "Số điện thoại"
            )

            room_label = st.selectbox(
                "Phòng *",
                list(room_map.keys())
            )

            col1, col2, col3 = st.columns(3)

            with col1:

                check_in = st.date_input(
                    "Ngày nhận",
                    value=date.today()
                )

            with col2:

                check_out = st.date_input(
                    "Ngày trả",
                    value=date.today()
                )

            with col3:

                guests = st.number_input(
                    "Số khách",
                    min_value=1,
                    max_value=20,
                    value=1
                )

            selected_room = room_map[
                room_label
            ]

            nights = max(
                (check_out - check_in).days,
                0
            )

            total = (
                float(selected_room["price"])
                * nights
            )

            st.info(
                f"💰 Thành tiền dự kiến: "
                f"**{money(total)}** "
                f"({nights} đêm)"
            )

            submitted = st.form_submit_button(
                "📅 Xác nhận đặt phòng",
                type="primary"
            )

            if submitted:

                if not guest_name.strip():

                    st.error(
                        "Vui lòng nhập tên khách."
                    )

                elif check_out <= check_in:

                    st.error(
                        "Ngày trả phải sau ngày nhận."
                    )

                else:

                    result = execute(
                        """
                        INSERT INTO bookings
                        (
                            guest_name,
                            phone,
                            room_id,
                            check_in,
                            check_out,
                            guests,
                            total,
                            status,
                            created_at
                        )
                        VALUES
                        (
                            %s, %s, %s, %s, %s,
                            %s, %s, %s, %s
                        )
                        """,
                        (
                            guest_name.strip(),
                            phone.strip(),
                            int(selected_room["id"]),
                            check_in,
                            check_out,
                            int(guests),
                            total,
                            "Đã đặt",
                            datetime.now()
                        )
                    )

                    if result is not None:

                        execute(
                            """
                            UPDATE rooms
                            SET status = 'Đã đặt'
                            WHERE id = %s
                            """,
                            (
                                int(
                                    selected_room["id"]
                                ),
                            )
                        )

                        st.success(
                            "🎉 Đặt phòng thành công!"
                        )

                        st.rerun()


# =========================================================
# NHẬN / TRẢ PHÒNG
# =========================================================

elif menu == "👤 Nhận / Trả phòng":

    st.title(
        "👤 Nhận / Trả phòng"
    )

    bookings = query(
        """
        SELECT
            b.*,
            r.room_number,
            r.room_type
        FROM bookings b
        JOIN rooms r
            ON b.room_id = r.id
        WHERE b.status IN
            ('Đã đặt', 'Đang ở')
        ORDER BY b.check_in
        """
    )

    if bookings.empty:

        st.info(
            "Không có khách đang đặt hoặc đang ở."
        )

    else:

        for _, booking in bookings.iterrows():

            with st.container(
                border=True
            ):

                st.write(
                    f"**{booking['guest_name']}** "
                    f"• Phòng "
                    f"**{booking['room_number']}** "
                    f"• {booking['check_in']} → "
                    f"{booking['check_out']} "
                    f"• **{money(booking['total'])}**"
                )

                st.caption(
                    f"SĐT: "
                    f"{booking['phone'] or 'Chưa có'} "
                    f"• {booking['guests']} khách "
                    f"• Trạng thái: "
                    f"{booking['status']}"
                )

                col1, col2 = st.columns(2)

                if booking["status"] == "Đã đặt":

                    with col1:

                        if st.button(
                            "🔑 Nhận phòng",
                            key=f"checkin_{booking['id']}",
                            use_container_width=True
                        ):

                            execute(
                                """
                                UPDATE bookings
                                SET status = 'Đang ở'
                                WHERE id = %s
                                """,
                                (
                                    int(
                                        booking["id"]
                                    ),
                                )
                            )

                            execute(
                                """
                                UPDATE rooms
                                SET status = 'Đang ở'
                                WHERE id = %s
                                """,
                                (
                                    int(
                                        booking["room_id"]
                                    ),
                                )
                            )

                            st.success(
                                "Đã nhận phòng."
                            )

                            st.rerun()

                with col2:

                    if st.button(
                        "🚪 Trả phòng",
                        key=f"checkout_{booking['id']}",
                        use_container_width=True
                    ):

                        execute(
                            """
                            UPDATE bookings
                            SET status = 'Đã trả phòng'
                            WHERE id = %s
                            """,
                            (
                                int(
                                    booking["id"]
                                ),
                            )
                        )

                        execute(
                            """
                            UPDATE rooms
                            SET status = 'Trống'
                            WHERE id = %s
                            """,
                            (
                                int(
                                    booking["room_id"]
                                ),
                            )
                        )

                        st.success(
                            "Đã trả phòng."
                        )

                        st.rerun()


# =========================================================
# DANH SÁCH ĐẶT PHÒNG
# =========================================================

elif menu == "📋 Danh sách đặt phòng":

    st.title(
        "📋 Danh sách đặt phòng"
    )

    bookings = query(
        """
        SELECT
            b.id,
            b.guest_name,
            b.phone,
            r.room_number,
            r.room_type,
            b.check_in,
            b.check_out,
            b.guests,
            b.total,
            b.status,
            b.created_at
        FROM bookings b
        JOIN rooms r
            ON b.room_id = r.id
        ORDER BY b.id DESC
        """
    )

    if bookings.empty:

        st.info(
            "Chưa có dữ liệu đặt phòng."
        )

    else:

        display = bookings.rename(
            columns={
                "id": "ID",
                "guest_name": "Khách",
                "phone": "SĐT",
                "room_number": "Phòng",
                "room_type": "Loại phòng",
                "check_in": "Ngày nhận",
                "check_out": "Ngày trả",
                "guests": "Số khách",
                "total": "Tổng tiền",
                "status": "Trạng thái",
                "created_at": "Thời gian tạo"
            }
        )

        st.dataframe(
            display,
            use_container_width=True,
            hide_index=True
        )

        csv = bookings.to_csv(
            index=False
        ).encode("utf-8-sig")

        st.download_button(
            "⬇️ Xuất danh sách CSV",
            data=csv,
            file_name="bookings.csv",
            mime="text/csv"
        )
