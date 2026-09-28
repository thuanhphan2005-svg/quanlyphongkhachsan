import streamlit as st
import sqlite3
from datetime import datetime, date
import pandas as pd

DB = "hotel.db"


# =========================
# DATABASE
# =========================

def get_conn():
    conn = sqlite3.connect(DB, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_number TEXT UNIQUE NOT NULL,
            room_type TEXT NOT NULL,
            price REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'Trống'
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guest_name TEXT NOT NULL,
            phone TEXT,
            room_id INTEGER NOT NULL,
            check_in TEXT NOT NULL,
            check_out TEXT NOT NULL,
            guests INTEGER DEFAULT 1,
            total REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'Đã đặt',
            created_at TEXT NOT NULL,
            FOREIGN KEY(room_id) REFERENCES rooms(id)
        )
    """)

    # Tạo dữ liệu mẫu lần đầu
    cur.execute("SELECT COUNT(*) FROM rooms")

    if cur.fetchone()[0] == 0:
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

        cur.executemany(
            """
            INSERT INTO rooms
            (room_number, room_type, price, status)
            VALUES (?, ?, ?, ?)
            """,
            rooms
        )

    conn.commit()
    conn.close()


def query(sql, params=()):
    conn = get_conn()
    df = pd.read_sql_query(sql, conn, params=params)
    conn.close()
    return df


def execute(sql, params=()):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(sql, params)

    conn.commit()
    last_id = cur.lastrowid
    conn.close()

    return last_id


def money(value):
    return f"{value:,.0f} ₫"


# =========================
# PAGE CONFIG
# =========================

st.set_page_config(
    page_title="Hotel Manager",
    page_icon="🏨",
    layout="wide"
)

init_db()


# =========================
# SIDEBAR
# =========================

st.sidebar.title("🏨 HOTEL MANAGER")

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


# =========================
# DASHBOARD
# =========================

if menu == "📊 Tổng quan":

    st.title("📊 Tổng quan khách sạn")
    st.caption("Hệ thống quản lý phòng khách sạn")

    rooms = query("SELECT * FROM rooms")
    bookings = query("SELECT * FROM bookings")

    total_rooms = len(rooms)

    occupied_rooms = int(
        (rooms["status"] == "Đang ở").sum()
    )

    reserved_rooms = int(
        (rooms["status"] == "Đã đặt").sum()
    )

    available_rooms = total_rooms - occupied_rooms - reserved_rooms

    if not bookings.empty:
        revenue = float(
            bookings.loc[
                bookings["status"] == "Đã trả phòng",
                "total"
            ].sum()
        )
    else:
        revenue = 0

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

    st.subheader("📈 Tình trạng phòng")

    if total_rooms > 0:

        status_counts = (
            rooms["status"]
            .value_counts()
            .rename_axis("Trạng thái")
            .reset_index(name="Số phòng")
        )

        st.bar_chart(
            status_counts.set_index("Trạng thái")
        )

    st.subheader("🛏️ Danh sách phòng")

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


# =========================
# ROOM MANAGEMENT
# =========================

elif menu == "🛏️ Quản lý phòng":

    st.title("🛏️ Quản lý phòng")

    tab1, tab2 = st.tabs(
        [
            "📋 Danh sách phòng",
            "➕ Thêm phòng"
        ]
    )

    # ---------------------
    # LIST ROOMS
    # ---------------------

    with tab1:

        rooms = query(
            "SELECT * FROM rooms ORDER BY room_number"
        )

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

        if not rooms.empty:

            selected_room = st.selectbox(
                "Chọn phòng cần cập nhật",
                rooms["room_number"].tolist()
            )

            room = rooms[
                rooms["room_number"] == selected_room
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
                    value=float(room["price"]),
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

                    execute(
                        """
                        UPDATE rooms
                        SET room_type = ?,
                            price = ?,
                            status = ?
                        WHERE id = ?
                        """,
                        (
                            new_type,
                            new_price,
                            new_status,
                            int(room["id"])
                        )
                    )

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

                        execute(
                            "DELETE FROM rooms WHERE id = ?",
                            (int(room["id"]),)
                        )

                        st.success(
                            "Đã xóa phòng."
                        )

                        st.rerun()

    # ---------------------
    # ADD ROOM
    # ---------------------

    with tab2:

        with st.form("add_room"):

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

                        execute(
                            """
                            INSERT INTO rooms
                            (room_number, room_type, price, status)
                            VALUES (?, ?, ?, ?)
                            """,
                            (
                                room_number.strip(),
                                room_type,
                                price,
                                "Trống"
                            )
                        )

                        st.success(
                            f"Đã thêm phòng {room_number}!"
                        )

                        st.rerun()

                    except sqlite3.IntegrityError:

                        st.error(
                            "Số phòng này đã tồn tại."
                        )


# =========================
# BOOKING
# =========================

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

        with st.form("booking_form"):

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

            selected_room = room_map[room_label]

            nights = max(
                (check_out - check_in).days,
                0
            )

            total = (
                selected_room["price"] * nights
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

                    execute(
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
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            guest_name.strip(),
                            phone.strip(),
                            int(selected_room["id"]),
                            str(check_in),
                            str(check_out),
                            int(guests),
                            total,
                            "Đã đặt",
                            datetime.now().isoformat(
                                timespec="seconds"
                            )
                        )
                    )

                    execute(
                        """
                        UPDATE rooms
                        SET status = 'Đã đặt'
                        WHERE id = ?
                        """,
                        (int(selected_room["id"]),)
                    )

                    st.success(
                        "🎉 Đặt phòng thành công!"
                    )

                    st.rerun()


# =========================
# CHECK-IN / CHECK-OUT
# =========================

elif menu == "👤 Nhận / Trả phòng":

    st.title("👤 Nhận / Trả phòng")

    bookings = query(
        """
        SELECT
            b.*,
            r.room_number,
            r.room_type
        FROM bookings b
        JOIN rooms r
            ON b.room_id = r.id
        WHERE b.status IN ('Đã đặt', 'Đang ở')
        ORDER BY b.check_in
        """
    )

    if bookings.empty:

        st.info(
            "Không có khách đang đặt hoặc đang ở."
        )

    else:

        for _, booking in bookings.iterrows():

            with st.container(border=True):

                st.write(
                    f"**{booking['guest_name']}** "
                    f"• Phòng **{booking['room_number']}** "
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
                                WHERE id = ?
                                """,
                                (int(booking["id"]),)
                            )

                            execute(
                                """
                                UPDATE rooms
                                SET status = 'Đang ở'
                                WHERE id = ?
                                """,
                                (int(booking["room_id"]),)
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
                            WHERE id = ?
                            """,
                            (int(booking["id"]),)
                        )

                        execute(
                            """
                            UPDATE rooms
                            SET status = 'Trống'
                            WHERE id = ?
                            """,
                            (int(booking["room_id"]),)
                        )

                        st.success(
                            "Đã trả phòng."
                        )

                        st.rerun()


# =========================
# BOOKING LIST
# =========================

elif menu == "📋 Danh sách đặt phòng":

    st.title("📋 Danh sách đặt phòng")

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
