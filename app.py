import io
from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st

from database import initialize_database, get_connection


# -------------------------
# تنظیمات برنامه
# -------------------------
st.set_page_config(
    page_title="Factory Automation",
    page_icon="🏭",
    layout="wide"
)

initialize_database()

STATUSES = [
    "ثبت‌شده",
    "در انتظار تأیید",
    "تأییدشده",
    "در حال انجام",
    "تکمیل‌شده",
    "ردشده"
]

PRIORITIES = ["کم", "متوسط", "زیاد", "بحرانی"]

CATEGORIES = [
    "خرید قطعه و تجهیزات",
    "تعمیر و نگهداری",
    "تأمین مواد اولیه",
    "امور اداری",
    "منابع انسانی",
    "بازرگانی",
    "سایر"
]

DEPARTMENTS = [
    "تولید",
    "انبار",
    "تعمیر و نگهداری",
    "مالی",
    "منابع انسانی",
    "بازرگانی",
    "مدیریت"
]

CLOSED_STATUSES = ["تکمیل‌شده", "ردشده"]


# -------------------------
# توابع پایگاه داده
# -------------------------
def load_requests():
    with get_connection() as connection:
        return pd.read_sql_query(
            "SELECT * FROM requests ORDER BY id DESC",
            connection
        )


def load_history(request_id):
    with get_connection() as connection:
        return pd.read_sql_query(
            """
            SELECT old_status, new_status, note, changed_at
            FROM request_history
            WHERE request_id = ?
            ORDER BY id DESC
            """,
            connection,
            params=(int(request_id),)
        )


def save_history(
    connection, request_id, old_status, new_status, note
):
    connection.execute(
        """
        INSERT INTO request_history
        (request_id, old_status, new_status, note)
        VALUES (?, ?, ?, ?)
        """,
        (
            int(request_id),
            old_status,
            new_status,
            note.strip() if note else ""
        )
    )


# -------------------------
# قواعد پیشنهادی فوریت
# -------------------------
def suggest_priority(title, description, category):
    text = f"{title} {description} {category}".lower()

    critical_words = [
        "بحرانی", "توقف خط", "توقف تولید",
        "حادثه", "خطر ایمنی", "اضطراری"
    ]

    high_words = [
        "فوری", "خرابی", "از کار افتاده",
        "کمبود مواد", "تأخیر تولید"
    ]

    low_words = [
        "پیشنهادی", "بهبود", "غیرفوری"
    ]

    if any(word in text for word in critical_words):
        return "بحرانی"

    if any(word in text for word in high_words):
        return "زیاد"

    if any(word in text for word in low_words):
        return "کم"

    return "متوسط"


def add_overdue_column(df):
    result = df.copy()

    if result.empty:
        result["معوق"] = pd.Series(dtype=bool)
        return result

    due_dates = pd.to_datetime(
        result["due_date"], errors="coerce"
    )

    today = pd.Timestamp(date.today())

    active = ~result["status"].isin(CLOSED_STATUSES)

    result["معوق"] = (
        due_dates.notna()
        & (due_dates < today)
        & active
    )

    return result


# -------------------------
# عنوان و منو
# -------------------------
st.title("🏭 سیستم اتوماسیون اداری و مدیریتی کارخانه")
st.caption(
    "ثبت، پیگیری، گزارش‌گیری و پایش درخواست‌های داخلی"
)

page = st.sidebar.radio(
    "انتخاب بخش",
    [
        "داشبورد مدیریتی",
        "ثبت درخواست",
        "مدیریت درخواست‌ها",
        "گزارش‌ها"
    ]
)

df = load_requests()
df = add_overdue_column(df)


# =====================================================
# 1. داشبورد
# =====================================================
if page == "داشبورد مدیریتی":
    st.header("داشبورد مدیریتی")

    total = len(df)
    pending = int((df["status"] == "ثبت‌شده").sum())
    in_progress = int(
        (df["status"] == "در حال انجام").sum()
    )
    overdue = int(df["معوق"].sum())

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("کل درخواست‌ها", total)
    col2.metric("ثبت‌شده", pending)
    col3.metric("در حال انجام", in_progress)
    col4.metric("درخواست‌های معوق", overdue)

    if df.empty:
        st.info("برای مشاهده نمودارها ابتدا یک درخواست ثبت کنید.")
    
    else:
        left, right = st.columns(2)

        with left:
            st.subheader("درخواست‌ها بر اساس وضعیت")
            status_data = (
                df["status"]
                .value_counts()
                .rename_axis("وضعیت")
                .reset_index(name="تعداد")
            )

            fig = px.bar(
                status_data,
                x="وضعیت",
                y="تعداد",
                title="توزیع وضعیت درخواست‌ها",
                text="تعداد"
            )
            st.plotly_chart(fig, use_container_width=True)

        with right:
            st.subheader("درخواست‌ها بر اساس واحد")

            department_data = (
                df["department"]
                .value_counts()
                .rename_axis("واحد")
                .reset_index(name="تعداد")
            )

            fig = px.bar(
                department_data,
                x="واحد",
                y="تعداد",
                title="توزیع درخواست‌ها بین واحدها",
                text="تعداد"
            )
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("درخواست‌ها بر اساس فوریت")

        priority_data = (
            df["priority"]
            .value_counts()
            .reindex(PRIORITIES, fill_value=0)
            .rename_axis("فوریت")
            .reset_index(name="تعداد")
        )

        fig = px.bar(
            priority_data,
            x="فوریت",
            y="تعداد",
            text="تعداد",
            title="توزیع سطح فوریت"
        )
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("آخرین درخواست‌ها")

        display_cols = [
            "id", "title", "department",
            "priority", "status", "due_date", "معوق"
        ]

        st.dataframe(
            df[display_cols].head(10),
            use_container_width=True,
            hide_index=True
        )


# =====================================================
# 2. ثبت درخواست
# =====================================================
elif page == "ثبت درخواست":
    st.header("ثبت درخواست جدید")

    with st.form("request_form", clear_on_submit=True):
        title = st.text_input("عنوان درخواست")

        category = st.selectbox(
            "نوع درخواست", CATEGORIES
        )

        department = st.selectbox(
            "واحد درخواست‌دهنده", DEPARTMENTS
        )

        description = st.text_area("شرح درخواست")

        priority_choice = st.selectbox(
            "فوریت درخواست",
            ["پیشنهاد سیستم"] + PRIORITIES
        )

        due_date = st.date_input(
            "مهلت انجام",
            value=date.today()
        )

        submitted = st.form_submit_button("ثبت درخواست")

        if submitted:
            if not title.strip():
                st.error("عنوان درخواست الزامی است.")
            else:
                suggested = suggest_priority(
                    title, description, category
                )

                final_priority = (
                    suggested
                    if priority_choice == "پیشنهاد سیستم"
                    else priority_choice
                )

                with get_connection() as connection:
                    cursor = connection.execute(
                        """
                        INSERT INTO requests
                        (
                            title, category, department,
                            description, priority, status, due_date
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            title.strip(),
                            category,
                            department,
                            description.strip(),
                            final_priority,
                            "ثبت‌شده",
                            due_date.isoformat()
                        )
                    )

                    request_id = cursor.lastrowid

                    initial_note = (
                        f"درخواست ثبت شد. فوریت پیشنهادی سیستم: "  
                        f"{suggested}. فوریت نهایی: {final_priority}.")

                    save_history(
                        connection,
                        request_id,
                        "—",
                        "ثبت‌شده",
                        initial_note
                    )

                st.success(
                    f"درخواست ثبت شد. شماره: {request_id}؛ "
                    f"فوریت ثبت‌شده: {final_priority}"
                )

                if priority_choice == "پیشنهاد سیستم":
                    st.info(
                        "فوریت با قواعد ساده متنی پیشنهاد شده است؛ "
                        "این پیشنهاد را مسئول مربوطه باید بررسی کند."
                    )


# =====================================================
# 3. مدیریت و پیگیری درخواست‌ها
# =====================================================
elif page == "مدیریت درخواست‌ها":
    st.header("مدیریت و پیگیری درخواست‌ها")

    if df.empty:
        st.info("هنوز درخواستی ثبت نشده است.")
    else:
        col1, col2, col3 = st.columns(3)

        with col1:
            status_filter = st.selectbox(
                "فیلتر وضعیت",
                ["همه"] + STATUSES
            )

        with col2:
            department_filter = st.selectbox(
                "فیلتر واحد",
                ["همه"] + sorted(df["department"].unique())
            )

        with col3:
            priority_filter = st.selectbox(
                "فیلتر فوریت",
                ["همه"] + PRIORITIES
            )

        filtered = df.copy()

        if status_filter != "همه":
            filtered = filtered[
                filtered["status"] == status_filter
            ]

        if department_filter != "همه":
            filtered = filtered[
                filtered["department"] == department_filter
            ]

        if priority_filter != "همه":
            filtered = filtered[
                filtered["priority"] == priority_filter
            ]

        st.dataframe(
            filtered[
                [
                    "id", "title", "department", "priority",
                    "status", "created_at", "due_date", "معوق"
                ]
            ],
            use_container_width=True,
            hide_index=True
        )

        st.divider()
        st.subheader("به‌روزرسانی و تاریخچه پیگیری")

        request_ids = filtered["id"].tolist()

        if request_ids:
            selected_id = st.selectbox(
                "شماره درخواست برای پیگیری",
                request_ids
            )

            row = df[df["id"] == selected_id].iloc[0]

            st.write(f"**عنوان:** {row['title']}")
            st.write(f"**واحد:** {row['department']}")
            st.write(f"**فوریت:** {row['priority']}")
            st.write(f"**شرح:** {row['description']}")
            st.write(f"**مهلت:** {row['due_date']}")

            if row["معوق"]:
                st.warning("این درخواست از مهلت خود عبور کرده است.")

            current_status = row["status"]
            status_index = (
                STATUSES.index(current_status)
                if current_status in STATUSES else 0
            )

            with st.form("update_request_form"):
                new_status = st.selectbox(
                    "وضعیت جدید",
                    STATUSES,
                    index=status_index
                )

                new_priority = st.selectbox(
                    "فوریت جدید",
                    PRIORITIES,
                    index=(
                        PRIORITIES.index(row["priority"])
                        if row["priority"] in PRIORITIES else 1
                    )
                )

                note = st.text_area(
                    "یادداشت پیگیری",
                    placeholder="مثلاً: قطعه سفارش داده شد."
                )

                update = st.form_submit_button("ذخیره تغییرات")

                if update:
                    if (
                        new_status == current_status
                        and new_priority == row["priority"]
                        and not note.strip()
                    ):
                        st.warning("تغییری برای ذخیره وارد نشده است.")
                    else:
                        with get_connection() as connection:
                            connection.execute(
                                """
                                UPDATE requests
                                SET status = ?, priority = ?
                                WHERE id = ?
                                """,
                                (
                                    new_status,
                                    new_priority,
                                    int(selected_id)
                                )
                            )

                            history_note = note.strip()

                            if new_priority != row["priority"]:
                                priority_note = (
                                    f"تغییر فوریت از {row['priority']} "
                                    f"به {new_priority}."
                                )
                                history_note = (
                                    f"{history_note} {priority_note}"
                                ).strip()

                            save_history(
                                connection,
                                selected_id,
                                current_status,
                                new_status,
                                history_note
                            )

                        st.success("تغییرات و یادداشت ذخیره شدند.")
                        st.rerun()

            st.subheader("تاریخچه پیگیری این درخواست")

            history = load_history(selected_id)

            if history.empty:
                st.info("هنوز سابقه پیگیری وجود ندارد.")
            else:
                st.dataframe(
                    history,
                    use_container_width=True,
                    hide_index=True
                )
        else:
            st.info("درخواستی با فیلترهای انتخاب‌شده وجود ندارد.")


# =====================================================
# 4. گزارش‌ها
# =====================================================
elif page == "گزارش‌ها":
    st.header("گزارش‌گیری و خروجی داده‌ها")

    if df.empty:
        st.info("برای گزارش‌گیری ابتدا درخواست ثبت کنید.")
    else:
        created_dates = pd.to_datetime(
            df["created_at"], errors="coerce"
        ).dropna()

        if created_dates.empty:
            min_date = date.today()
            max_date = date.today()
        else:
            min_date = created_dates.min().date()
            max_date = max(
                created_dates.max().date(), date.today()
            )

        col1, col2 = st.columns(2)

        with col1:
            start_date = st.date_input(
                "از تاریخ ثبت",
                value=min_date,
                key="report_start"
            )

        with col2:
            end_date = st.date_input(
                "تا تاریخ ثبت",
                value=max_date,
                key="report_end"
            )

        col3, col4 = st.columns(2)

        with col3:
            report_status = st.selectbox(
                "وضعیت گزارش",
                ["همه"] + STATUSES,
                key="report_status"
            )

        with col4:
            report_department = st.selectbox(
                "واحد گزارش",
                ["همه"] + sorted(df["department"].unique()),
                key="report_department"
            )

        if start_date > end_date:
            st.error("تاریخ شروع نباید بعد از تاریخ پایان باشد.")
        else:
            created = pd.to_datetime(
                df["created_at"], errors="coerce"
            ).dt.date

            report_df = df[
                created.notna()
                & (created >= start_date)
                & (created <= end_date)
            ].copy()

            if report_status != "همه":
                report_df = report_df[
                    report_df["status"] == report_status
                ]

            if report_department != "همه":
                report_df = report_df[
                    report_df["department"] == report_department
                ]

            st.metric("تعداد درخواست‌های گزارش", len(report_df))

            st.dataframe(
                report_df,
                use_container_width=True,
                hide_index=True
            )

            # خروجی CSV
            csv_data = report_df.to_csv(
                index=False
            ).encode("utf-8-sig")

            st.download_button(
                "دانلود گزارش CSV",
                data=csv_data,
                file_name="factory_requests.csv",
                mime="text/csv"
            )

            # خروجی Excel
            excel_buffer = io.BytesIO()

            with pd.ExcelWriter(
                excel_buffer, engine="openpyxl"
            ) as writer:
                report_df.to_excel(
                    writer,
                    index=False,
                    sheet_name="Requests"
                )

                if not report_df.empty:
                    summary = (
                        report_df.groupby(
                            ["department", "status"],
                            dropna=False
                        )
                        .size()
                        .reset_index(name="count")
                    )

                    summary.to_excel(
                        writer,
                        index=False,
                        sheet_name="Summary"
                    )

            st.download_button(
                "دانلود گزارش Excel",
                data=excel_buffer.getvalue(),
                file_name="factory_requests.xlsx",
                mime=(
                    "application/vnd.openxmlformats-officedocument."
                    "spreadsheetml.sheet"
                )
            )