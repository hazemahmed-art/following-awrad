import streamlit as st
import pandas as pd
import os
from datetime import date, timedelta
import plotly.graph_objects as go
import plotly.express as px
import io
import calendar

if "selected_date" not in st.session_state:
    st.session_state.selected_date = None
if "has_unsaved_changes" not in st.session_state:
    st.session_state.has_unsaved_changes = False
if "selected_student" not in st.session_state:
    st.session_state.selected_student = None

USERS_CONFIG_PATH = "database/users_config"
os.makedirs(USERS_CONFIG_PATH, exist_ok=True)

def load_or_create_user_config(username, level):
    config_file = os.path.join(
        USERS_CONFIG_PATH,
        f"{username}_level{level}.xlsx"
    )
    if os.path.exists(config_file):
        return config_file
    template_file = os.path.join(
        TEMPLATE_PATH,
        f"level {level}.xlsx"
    )
    if not os.path.exists(template_file):
        st.error("❌ ملف الأوراد الأساسي غير موجود")
        return None
    df = pd.read_excel(template_file)
    df.to_excel(config_file, index=False)
    return config_file

# ───────── إعداد المسارات
TEMPLATE_PATH = "database/templet"
USERS_PATH = "database/users"
os.makedirs(USERS_PATH, exist_ok=True)

# ───────── دالة قراءة ملف المستخدم أو إنشاؤه
def load_or_create_user_file(username, level):
    level_file = os.path.join(TEMPLATE_PATH, f"level {level}.xlsx")
    user_file = os.path.join(USERS_PATH, f"{username}.xlsx")
    if not os.path.exists(user_file):
        if os.path.exists(level_file):
            df = pd.read_excel(level_file)
            with pd.ExcelWriter(user_file) as writer:
                today_sheet = date.today().strftime("%Y-%m-%d")
                df.to_excel(writer, sheet_name=today_sheet, index=False)
        else:
            st.error(f"ملف المستوى للمستخدم غير موجود: {level_file}")
            return None
    return user_file

# ───────── دالة تحميل بيانات اليوم
def load_today_sheet(user_file):
    today_sheet = date.today().strftime("%Y-%m-%d")
    try:
        xls = pd.ExcelFile(user_file)
        if today_sheet in xls.sheet_names:
            df = pd.read_excel(user_file, sheet_name=today_sheet)
        else:
            df = pd.read_excel(user_file, sheet_name=xls.sheet_names[0])
        return df, today_sheet
    except Exception as e:
        st.error(f"مشكلة في فتح ملف المستخدم: {e}")
        return None, None

# ───────── دالة تحميل Sheet بتاريخ معيّن
def load_sheet_by_date(user_file, selected_date):
    sheet_name = selected_date.strftime("%Y-%m-%d")
    try:
        df = pd.read_excel(user_file, sheet_name=sheet_name)
        if "الحالة" not in df.columns:
            df["الحالة"] = ""
        return df, sheet_name
    except:
        return None, sheet_name

# ───────── دالة حفظ الأوراد
def save_daily_tasks(user_file, sheet_name, df):
    try:
        with pd.ExcelWriter(user_file, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
        st.success("✅ تم حفظ الأوراد بنجاح")
    except Exception as e:
        st.error(f"مشكلة في حفظ الملف: {e}")

# ────────────────────────────────────────────────
# إعداد الاتجاه العربي (RTL) مرة واحدة فقط
# ────────────────────────────────────────────────
def apply_rtl_style():
    """تطبيق الـ RTL والتنسيق العربي على كامل التطبيق"""
    st.markdown("""
    <style>
        html, body, [class*="css"], [data-testid="stAppViewContainer"] {
            direction: rtl !important;
            text-align: right !important;
            font-family: 'Segoe UI', Tahoma, Arial, sans-serif !important;
        }
        h1, h2, h3, h4, h5, h6, p, div, span, label {
            direction: rtl !important;
            text-align: right !important;
        }
        .stButton > button {
            width: 100%;
            font-size: 17px;
            padding: 0.8rem 1rem;
            margin: 0.5rem 0;
            border-radius: 10px;
        }
        .full-width-button {
            width: 100% !important;
            margin: 0.7rem 0 !important;
            font-size: 1.15rem !important;
            font-weight: 500 !important;
            height: 3.4rem !important;
            border-radius: 12px !important;
            box-shadow: 0 3px 10px rgba(0,0,0,0.15) !important;
            transition: all 0.25s ease !important;
        }
       
        .full-width-button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 16px rgba(0,0,0,0.22) !important;
        }
    </style>
    """, unsafe_allow_html=True)

st.markdown("""
<style>
    hr.custom-divider {
        border: none;
        height: 2px;
        background: linear-gradient(to right, #4f46e5, #ec4899, #f59e0b);
        margin: 2.5rem 0;
        border-radius: 5px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    }
</style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# إعداد الصفحة
# ────────────────────────────────────────────────
st.set_page_config(
    page_title="متابعة الأوراد",
    layout="wide",
    page_icon="🕌",
    initial_sidebar_state="collapsed"
)
apply_rtl_style()

# ────────────────────────────────────────────────
# تحميل بيانات المستخدمين (بدون cache)
# ────────────────────────────────────────────────
def load_users():
    """تحميل بيانات المستخدمين من ملف Excel"""
    try:
        return pd.read_excel("users.xlsx")
    except:
        st.error("ملف users.xlsx غير موجود أو فيه مشكلة")
        return pd.DataFrame()

def get_students_users(users_df):
    if users_df.empty:
        return pd.DataFrame()
    return users_df[users_df["role"].astype(str).str.lower() == "user"]

# ────────────────────────────────────────────────
# Session State Initialization
# ────────────────────────────────────────────────
if "page" not in st.session_state:
    st.session_state.page = "login"
if "username" not in st.session_state:
    st.session_state.username = ""
if "role" not in st.session_state:
    st.session_state.role = ""
if "level" not in st.session_state:
    st.session_state.level = None

# ────────────────────────────────────────────────
# شاشة تسجيل الدخول
# ────────────────────────────────────────────────
def login_screen():
    st.header("🔐 تسجيل الدخول")
    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)
    username = st.text_input("👤 اسم المستخدم")
    password = st.text_input("🔑 كلمة المرور", type="password")
    if st.button("دخول", use_container_width=True):
        # تحميل البيانات من الملف مباشرة
        users_df = load_users()
        
        if users_df.empty:
            st.error("لا توجد بيانات مستخدمين")
            return
        user = users_df[
            (users_df["username"].astype(str) == username.strip()) &
            (users_df["password"].astype(str) == password)
        ]
        if not user.empty:
            st.session_state.username = username
            st.session_state.role = str(user.iloc[0]["role"]).strip()
            level_value = str(user.iloc[0]["level"]).strip()
            if "level" in level_value.lower():
                level_value = level_value.lower().replace("level", "").strip()
                level_value = level_value.lstrip(" _-").strip()
            st.session_state.level = level_value
            if st.session_state.role.lower() == "admin":
                st.session_state.page = "admin"
            else:
                st.session_state.page = "user_home"
            st.rerun()
        else:
            st.error("اسم المستخدم أو كلمة المرور غير صحيحة")
            
    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)
    st.header("صل على النبي ﷺ")

# ────────────────────────────────────────────────
# الصفحة الرئيسية للمستخدم
# ────────────────────────────────────────────────
def user_home_screen():
    # ──── CSS مخصص للأزرار ────
    st.markdown("""
    <style>
    /* زر عادي */
    div.stButton > button:first-child {
        background: linear-gradient(to right, #00467f, #a5cc82);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 14px 24px;
        font-size: 18px;
        font-weight: 600;
        margin-bottom: 12px;
        width: 100%;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }

    /* hover */
    div.stButton > button:first-child:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px rgba(0,0,0,0.2);
        background: linear-gradient(135deg, #6366f1, #a78bfa);
    }

    /* زر تسجيل الخروج (لونه أحمر) */
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #ef4444, #f87171) !important;
    }
    
    div.stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #dc2626, #f87171) !important;
        transform: translateY(-2px);
        box-shadow: 0 10px 15px rgba(239, 68, 68, 0.4);
    }

    /* إخفاء الـ border الافتراضي إذا أردت */
    div.stButton > button {
        border: none !important;
    }
    </style>
    """, unsafe_allow_html=True)


    st.markdown("### ﴿مِّنَ الْمُؤْمِنِينَ رِجَالٌ صَدَقُوا مَا عَاهَدُوا اللَّهَ عَلَيْهِ﴾")
    st.success(f"مرحبًا بك يا {st.session_state.username}")
    st.markdown("### 📌 اختر العملية المطلوبة")
    if st.button("📅 المتابعة اليومية", key="btn_daily", use_container_width=True):
        st.session_state.page = "daily"
        st.rerun()
    if st.button("📂 السجلات القديمة", key="btn_records", use_container_width=True):
        st.session_state.page = "records"
        st.rerun()
    if st.button("⭐ التقييمات", key="btn_reviews", use_container_width=True):
        st.session_state.page = "evaluations"
        st.rerun()
    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)
    if st.button("🚪 تسجيل الخروج", type="primary", use_container_width=True):
        logout()



# ────────────────────────────────────────────────
# عرض واجبات اليوم حسب المستوى
# ────────────────────────────────────────────────
def daily_followup_screen():
    import streamlit as st

    # ================== CSS ==================
    st.markdown("""
    <style>
    /* --- Section Box Styles (Your existing code) --- */
    .section-box {
        margin-bottom: 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 12px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        color: white;
        text-align: center;
        font-size: 30px;
        font-weight: bold;
    }

    .task-title {
        margin-right: 10px;
        font-size: 25px;
        font-weight: bold;
    }

    .custom-divider {
        border: none;
        height: 1px;
        background: linear-gradient(to right, transparent, #ccc, transparent);
        margin: 18px 0;
    }

    /* --- NEW CUSTOM CHECKBOX CSS --- */
    
    /* 1. Hide the default browser checkbox */
    .stCheckbox > label > div[data-testid="stMarkdownContainer"] > p,
    .stCheckbox input[type="checkbox"] {
        visibility: hidden;
        position: absolute;
        width: 0;
        height: 0;
    }

    /* 2. Create a custom label (the visible box) */
    .stCheckbox > label {
        position: relative;
        cursor: pointer;
        display: inline-flex;
        align-items: center;
        margin-bottom: 0; /* Remove extra spacing */
        margin-top: 10px;
    }

    /* 3. Design the checkmark box */
    .stCheckbox > label::before {
        content: "تم";
        display: inline-block;
        color: white;
        width: 50px;
        height: 30px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); /* Default gray background */
        border-radius: 8px;
        margin-left: 10px;
        transition: all 0.3s ease;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        padding-right: 16px;
         font-weight: bold;
    }

    /* 4. Style when Checked */
    .stCheckbox input[type="checkbox"]:checked + div::before {
        /* Streamlit structure: Input -> Div -> Label text area. 
           We use Adjacent sibling selector (+) or General sibling (~) */
    }
    
    /* To target the label styling properly in Streamlit structure, 
       we often target the wrapper or use a specific class added via markdown. 
       However, a pure CSS approach that targets the parent label is tricky 
       because the input is inside the label. 
       
       Let's use a pseudo-element on the label itself to act as the background.
    */
    
    .stCheckbox > label > div[data-testid="stMarkdownContainer"] {
        position: relative;
        padding-left: 40px; /* Space for the custom checkbox */
    }

    /* Create the box */
    .stCheckbox > label > div[data-testid="stMarkdownContainer"]::before {
        content: "";
        position: absolute;
        left: 0;
        top: 50%;
        transform: translateY(-50%);
        width: 32px;
        height: 32px;
        background-color: #eee;
        border-radius: 10px;
        transition: background-color 0.2s;
    }

    /* Create the check icon (hidden by default) */
    .stCheckbox > label > div[data-testid="stMarkdownContainer"]::after {
        content: "";
        position: absolute;
        left: 10px;
        top: 50%;
        transform: translateY(-50%) scale(0); /* Hidden initially */
        width: 16px;
        height: 16px;
        /* Creating a checkmark shape using borders or an SVG */
        background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16' fill='white'%3e%3cpath d='M12.207 4.793a1 1 0 010 1.414l-5 5a1 1 0 01-1.414 0l-2-2a1 1 0 011.414-1.414L6.5 9.086l4.293-4.293a1 1 0 011.414 0z'/%3e%3c/svg%3e");
        background-repeat: no-repeat;
        background-size: contain;
        transition: transform 0.2s;
    }

    /* Styling when checked */
    .stCheckbox input[type="checkbox"]:checked ~ div[data-testid="stMarkdownContainer"]::before {
        background-color: #28a745 !important; /* Green background */
        box-shadow: 0 4px 10px rgba(40, 167, 69, 0.3);
    }

    .stCheckbox input[type="checkbox"]:checked ~ div[data-testid="stMarkdownContainer"]::after {
        transform: translateY(-50%) scale(1) !important; /* Show checkmark */
    }

    /* Optional: Hover effect */
    .stCheckbox > label:hover > div[data-testid="stMarkdownContainer"]::before {
        background-color: #e2e6ea;
    }
    .stCheckbox input[type="checkbox"]:checked ~ div[data-testid="stMarkdownContainer"]:hover::before {
        background-color: #218838 !important; /* Darker green */
    }

    </style>
    """, unsafe_allow_html=True)

    # ================== HEADER ==================
    st.header("📅 المتابعة اليومية")

    user_file = load_or_create_user_file(
        st.session_state.username,
        st.session_state.level
    )
    if not user_file:
        return

    df, today_sheet = load_today_sheet(user_file)
    if df is None:
        return

    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)

    # ================== SESSION STATE ==================
    if "daily_has_unsaved_changes" not in st.session_state:
        st.session_state.daily_has_unsaved_changes = False
    if "confirm_leave_daily" not in st.session_state:
        st.session_state.confirm_leave_daily = False

    if "الحالة" not in df.columns:
        df["الحالة"] = ""

    # ================== MAIN CONTENT ==================
    if "القسم" in df.columns and "الأعمال" in df.columns:

        sections = df["القسم"].drop_duplicates().tolist()

        for section in sections:
            # ----- Section Header -----
            st.markdown(
                f'<div class="section-box">--← 📌 {section}</div>',
                unsafe_allow_html=True
            )

            section_df = df[df["القسم"] == section]

            for i, row in section_df.iterrows():
                task = str(row["الأعمال"])
                current_val = str(row["الحالة"])
                key_id = f"{section}_{i}_{task}"

                # ======== Text Tasks ========
                if task.strip() in ["حضور القلب", "رقم آية تدبرتها", "حال قلبك"]:
                    st.markdown(
                        f'<div class="task-title">✍️ {task}</div>',
                        unsafe_allow_html=True
                    )

                    new_val = st.text_input(
                        "",
                        value=current_val,
                        key=key_id
                    )

                    if new_val != current_val:
                        st.session_state.daily_has_unsaved_changes = True

                    df.at[i, "الحالة"] = new_val

                # ======== Checkbox Tasks ========
                else:
                    st.markdown(
                        f"""
                        <div style="
                            margin-right: 10px;
                            font-size: 25px;
                            font-weight: bold;
                        ">
                            📝 {task}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    # --- CHANGED KEY HERE ---
                    # Added "check_" prefix to prevent key conflicts with text inputs
                    checked = st.checkbox(
                        "",
                        value=(current_val == "تم"),
                        key=f"check_{key_id}"
                    )

                    if checked != (current_val == "تم"):
                        st.session_state.daily_has_unsaved_changes = True

                    df.at[i, "الحالة"] = "تم" if checked else ""

            st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)

        # ================== SAVE ==================
        if st.button("💾 حفظ الأوراد", use_container_width=True):
            save_daily_tasks(user_file, today_sheet, df)
            st.session_state.daily_has_unsaved_changes = False

    else:
        st.warning("⚠️ الملف يجب أن يحتوي على عمودين: (القسم / الأعمال)")

    # ================== BACK BUTTON ==================
    if st.button("⬅️ الرجوع للصفحة الرئيسية", use_container_width=True):
        if st.session_state.daily_has_unsaved_changes:
            st.session_state.confirm_leave_daily = True
        else:
            st.session_state.page = "user_home"
            st.rerun()

    # ================== CONFIRM LEAVE ==================
    if st.session_state.confirm_leave_daily:
        st.warning("⚠️ لديك تعديلات لم تُحفظ، هل تريد الرجوع بدون حفظ؟")
        col1, col2 = st.columns(2)

        with col1:
            if st.button("🚪 رجوع بدون حفظ"):
                st.session_state.daily_has_unsaved_changes = False
                st.session_state.confirm_leave_daily = False
                st.session_state.page = "user_home"
                st.rerun()

        with col2:
            if st.button("💾 لا، سأحفظ أولًا"):
                st.session_state.confirm_leave_daily = False




# ────────────────────────────────────────────────
# صفحة السجلات القديمة
# ────────────────────────────────────────────────
import streamlit as st
from datetime import date

def old_records_screen():

    # ================== CSS ==================
    st.markdown("""
    <style>
    /* --- Section Box Styles (Your existing code) --- */
    .section-box {
        margin-bottom: 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 12px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        color: white;
        text-align: center;
        font-size: 30px;
        font-weight: bold;
    }

    .task-title {
        margin-right: 10px;
        font-size: 25px;
        font-weight: bold;
    }

    .custom-divider {
        border: none;
        height: 1px;
        background: linear-gradient(to right, transparent, #ccc, transparent);
        margin: 18px 0;
    }

    /* --- NEW CUSTOM CHECKBOX CSS --- */
    
    /* 1. Hide the default browser checkbox */
    .stCheckbox > label > div[data-testid="stMarkdownContainer"] > p,
    .stCheckbox input[type="checkbox"] {
        visibility: hidden;
        position: absolute;
        width: 0;
        height: 0;
    }

    /* 2. Create a custom label (the visible box) */
    .stCheckbox > label {
        position: relative;
        cursor: pointer;
        display: inline-flex;
        align-items: center;
        margin-bottom: 0; /* Remove extra spacing */
        margin-top: 10px;
    }

    /* 3. Design the checkmark box */
    .stCheckbox > label::before {
        content: "تم";
        display: inline-block;
        color: white;
        width: 50px;
        height: 30px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); /* Default gray background */
        border-radius: 8px;
        margin-left: 10px;
        transition: all 0.3s ease;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        padding-right: 16px;
         font-weight: bold;
    }

    /* 4. Style when Checked */
    .stCheckbox input[type="checkbox"]:checked + div::before {
        /* Streamlit structure: Input -> Div -> Label text area. 
           We use Adjacent sibling selector (+) or General sibling (~) */
    }
    
    /* To target the label styling properly in Streamlit structure, 
       we often target the wrapper or use a specific class added via markdown. 
       However, a pure CSS approach that targets the parent label is tricky 
       because the input is inside the label. 
       
       Let's use a pseudo-element on the label itself to act as the background.
    */
    
    .stCheckbox > label > div[data-testid="stMarkdownContainer"] {
        position: relative;
        padding-left: 40px; /* Space for the custom checkbox */
    }

    /* Create the box */
    .stCheckbox > label > div[data-testid="stMarkdownContainer"]::before {
        content: "";
        position: absolute;
        left: 0;
        top: 50%;
        transform: translateY(-50%);
        width: 32px;
        height: 32px;
        background-color: #eee;
        border-radius: 10px;
        transition: background-color 0.2s;
    }

    /* Create the check icon (hidden by default) */
    .stCheckbox > label > div[data-testid="stMarkdownContainer"]::after {
        content: "";
        position: absolute;
        left: 10px;
        top: 50%;
        transform: translateY(-50%) scale(0); /* Hidden initially */
        width: 16px;
        height: 16px;
        /* Creating a checkmark shape using borders or an SVG */
        background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16' fill='white'%3e%3cpath d='M12.207 4.793a1 1 0 010 1.414l-5 5a1 1 0 01-1.414 0l-2-2a1 1 0 011.414-1.414L6.5 9.086l4.293-4.293a1 1 0 011.414 0z'/%3e%3c/svg%3e");
        background-repeat: no-repeat;
        background-size: contain;
        transition: transform 0.2s;
    }

    /* Styling when checked */
    .stCheckbox input[type="checkbox"]:checked ~ div[data-testid="stMarkdownContainer"]::before {
        background-color: #28a745 !important; /* Green background */
        box-shadow: 0 4px 10px rgba(40, 167, 69, 0.3);
    }

    .stCheckbox input[type="checkbox"]:checked ~ div[data-testid="stMarkdownContainer"]::after {
        transform: translateY(-50%) scale(1) !important; /* Show checkmark */
    }

    /* Optional: Hover effect */
    .stCheckbox > label:hover > div[data-testid="stMarkdownContainer"]::before {
        background-color: #e2e6ea;
    }
    .stCheckbox input[type="checkbox"]:checked ~ div[data-testid="stMarkdownContainer"]:hover::before {
        background-color: #218838 !important; /* Darker green */
    }

    </style>
    """, unsafe_allow_html=True)

    # ================= HEADER =================
    st.header("📂 السجلات القديمة")

    if "selected_date" not in st.session_state:
        st.session_state.selected_date = None
    if "old_has_unsaved_changes" not in st.session_state:
        st.session_state.old_has_unsaved_changes = False
    if "confirm_leave_old" not in st.session_state:
        st.session_state.confirm_leave_old = False

    user_file = load_or_create_user_file(
        st.session_state.username,
        st.session_state.level
    )
    if not user_file:
        return

    selected_date = st.date_input("📅 اختر التاريخ", value=date.today())

    if st.button("📖 عرض السجل", use_container_width=True):
        st.session_state.selected_date = selected_date
        st.session_state.old_has_unsaved_changes = False

    if not st.session_state.selected_date:
        return

    df, sheet_name = load_sheet_by_date(
        user_file,
        st.session_state.selected_date
    )

    if df is None:
        st.warning("❌ لا توجد بيانات مسجلة في هذا اليوم")
        return

    if "الحالة" not in df.columns:
        df["الحالة"] = ""

    st.success(f"📅 سجل يوم {sheet_name}")
    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)

    # ================= DISPLAY DATA =================
    sections = df["القسم"].drop_duplicates().tolist()

    for section in sections:
        # ----- Section Header -----
        st.markdown(
            f'<div class="section-box">--← 📌 {section}</div>',
            unsafe_allow_html=True
        )

        section_df = df[df["القسم"] == section]

        for i, row in section_df.iterrows():
            task = str(row["الأعمال"])
            current_val = str(row["الحالة"])
            key_id = f"{section}_{i}_{task}"

            # ======== Text Tasks ========
            if task.strip() in ["حضور القلب", "رقم آية تدبرتها", "حال قلبك"]:
                st.markdown(
                    f'<div class="task-title">✍️ {task}</div>',
                    unsafe_allow_html=True
                )

                new_val = st.text_input(
                    "",
                    value=current_val,
                    key=key_id
                )

                if new_val != current_val:
                    st.session_state.daily_has_unsaved_changes = True

                df.at[i, "الحالة"] = new_val

            # ======== Checkbox Tasks ========
            else:
                st.markdown(
                    f"""
                    <div style="
                        margin-right: 10px;
                        font-size: 25px;
                        font-weight: bold;
                    ">
                        📝 {task}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                # --- CHANGED KEY HERE ---
                # Added "check_" prefix to prevent key conflicts with text inputs
                checked = st.checkbox(
                    "",
                    value=(current_val == "تم"),
                    key=f"check_{key_id}"
                )

                if checked != (current_val == "تم"):
                    st.session_state.daily_has_unsaved_changes = True

                df.at[i, "الحالة"] = "تم" if checked else ""

        st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)

    # ================= ACTIONS =================
    if st.button("💾 حفظ التعديلات", use_container_width=True):
        save_daily_tasks(user_file, sheet_name, df)
        st.session_state.old_has_unsaved_changes = False
        st.success("✅ تم حفظ التعديلات")

    if st.button("⬅️ الرجوع للصفحة الرئيسية", use_container_width=True):
        if st.session_state.old_has_unsaved_changes:
            st.session_state.confirm_leave_old = True
        else:
            st.session_state.page = "user_home"
            st.session_state.selected_date = None
            st.rerun()

    if st.session_state.confirm_leave_old:
        st.warning("⚠️ لديك تعديلات لم تُحفظ")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🚪 رجوع بدون حفظ"):
                st.session_state.confirm_leave_old = False
                st.session_state.page = "user_home"
                st.session_state.selected_date = None
                st.rerun()
        with col2:
            if st.button("💾 حفظ أولًا"):
                save_daily_tasks(user_file, sheet_name, df)
                st.session_state.page = "user_home"
                st.session_state.selected_date = None
                st.rerun()



# ────────────────────────────────────────────────
# شاشة التقييمات
# ────────────────────────────────────────────────
def calculate_wird_statistics(user_file):
    xls = pd.ExcelFile(user_file)

    wird_stats = {}

    excluded_tasks = ["حضور القلب", "رقم آية تدبرتها", "حال قلبك"]

    for sheet in xls.sheet_names:
        try:
            df = pd.read_excel(user_file, sheet_name=sheet)
        except:
            continue

        if "الأعمال" not in df.columns or "الحالة" not in df.columns:
            continue

        for _, row in df.iterrows():
            task = str(row["الأعمال"]).strip()
            status = str(row["الحالة"]).strip()

            if task in excluded_tasks:
                continue

            if task not in wird_stats:
                wird_stats[task] = {"تم": 0, "لم يتم": 0}

            if status == "تم":
                wird_stats[task]["تم"] += 1
            else:
                wird_stats[task]["لم يتم"] += 1

    if not wird_stats:
        return None

    stats_df = pd.DataFrame.from_dict(wird_stats, orient="index")
    stats_df["إجمالي"] = stats_df["تم"] + stats_df["لم يتم"]

    return stats_df



# ────────────────────────────────────────────────
# صفحة التقييمات للمستخدم
# ────────────────────────────────────────────────
# ────────────────────────────────────────────────
# صفحة التقييمات للمستخدم (محدثة بتصميم جذاب)
# ────────────────────────────────────────────────
def evaluations_screen():
    st.header("⭐ التقييمات والإحصائيات")
    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)

    # استرجاع بيانات المستخدم الحالي
    username = st.session_state.username
    level = st.session_state.level

    # تحميل ملف المستخدم
    user_file = load_or_create_user_file(username, level)
    if not user_file:
        st.error("لا يمكن العثور على ملف البيانات")
        return

    # اختيار طريقة العرض
    eval_period = st.selectbox("مدة التقييم", ["يومي", "أسبوعي", "شهري"])

    # ────────────── منطق تحديد التواريخ ──────────────
    dates = []
    year = None
    month = None
    week = None

    if eval_period == "يومي":
        selected_date = st.date_input("اختر اليوم", value=date.today())
        dates = [selected_date]

    elif eval_period == "أسبوعي":
        col1, col2, col3 = st.columns(3)
        with col1:
            year = st.selectbox("السنة", range(2024, 2055), index=1, key="user_week_year")
        with col2:
            month = st.selectbox("الشهر", range(1, 13), index=date.today().month - 1, key="user_week_month")
        with col3:
            week = st.selectbox(
                "الأسبوع",
                ["الأسبوع الأول", "الأسبوع الثاني", "الأسبوع الثالث", "الأسبوع الرابع"],
                key="user_week_select"
            )
        if year and month and week:
            week_number = ["الأسبوع الأول", "الأسبوع الثاني", "الأسبوع الثالث", "الأسبوع الرابع"].index(week)
            start_day = week_number * 7 + 1
            end_day = min(start_day + 6, calendar.monthrange(year, month)[1])
            dates = [date(year, month, day) for day in range(start_day, end_day + 1) if day <= calendar.monthrange(year, month)[1]]

    elif eval_period == "شهري":
        col1, col2 = st.columns(2)
        with col1:
            year = st.selectbox("السنة", range(2024, 2055), index=1, key="user_month_year")
        with col2:
            month = st.selectbox("الشهر", range(1, 13), index=date.today().month - 1, key="user_month_month")
        if year and month:
            days_in_month = calendar.monthrange(year, month)[1]
            dates = [date(year, month, day) for day in range(1, days_in_month + 1)]

    # ────────────── تجهيز البيانات ──────────────
    xls = pd.ExcelFile(user_file)
    if not xls.sheet_names:
        st.warning("لا توجد بيانات متاحة")
        return

    # استخراج الأقسام من أول ورقة (المعيار)
    df_sample = pd.read_excel(user_file, sheet_name=xls.sheet_names[0])
    
    if "القسم" not in df_sample.columns or "الأعمال" not in df_sample.columns:
        st.error("تنسيق الملف غير صحيح")
        return

    all_sections = sorted(df_sample["القسم"].dropna().unique().tolist())

    # فلترة الأقسام
    selected_sections = st.multiselect(
        "اختر الأقسام المطلوب عرضها",
        options=all_sections,
        default=all_sections, 
        placeholder="اختر قسم أو أكثر..."
    )

    if not selected_sections:
        st.info("يرجى اختيار قسم واحد على الأقل")
        return

    # ────────────── عرض الجدول عند الضغط ──────────────
    if st.button("عرض الجدول", use_container_width=True) and dates:
        # استخراج الأوراد مع الأقسام
        tasks_df = df_sample[df_sample["القسم"].isin(selected_sections)][["القسم", "الأعمال"]].copy()
        tasks_df["الأعمال"] = tasks_df["الأعمال"].str.strip()

        data = {
            "القسم": tasks_df["القسم"].tolist(),
            "الأعمال": tasks_df["الأعمال"].tolist()
        }

        # قوائم مؤقتة لحساب الإحصائيات
        stats_done_counts = {} 
        stats_not_done_counts = {}

        excluded = ["حضور القلب", "رقم آية تدبرتها", "حال قلبك"]

        for d in dates:
            sheet_name = d.strftime("%Y-%m-%d")
            statuses = []
            if sheet_name in xls.sheet_names:
                df_day = pd.read_excel(user_file, sheet_name=sheet_name)
                if "الأعمال" in df_day.columns:
                    df_day["الأعمال"] = df_day["الأعمال"].astype(str).str.strip()
                    
                    for _, row in tasks_df.iterrows():
                        mask = (df_day["القسم"] == row["القسم"]) & (df_day["الأعمال"] == row["الأعمال"])
                        task_name = row["الأعمال"]
                        
                        if mask.any():
                            status = str(df_day.loc[mask, "الحالة"].values[0]).strip()
                            
                            # تحديث الإحصائيات
                            if task_name not in stats_done_counts:
                                stats_done_counts[task_name] = 0
                            if task_name not in stats_not_done_counts:
                                stats_not_done_counts[task_name] = 0

                            if task_name in excluded:
                                statuses.append(status if status else "—")
                            else:
                                if status == "تم":
                                    stats_done_counts[task_name] += 1
                                    statuses.append("تم بفضل الله")
                                else:
                                    stats_not_done_counts[task_name] += 1
                                    statuses.append("✗")
                        else:
                            # إذا لم تكن المهمة موجودة في يوم معين، نحسبها كـ "لم يتم" في الإحصائيات
                            if task_name not in stats_not_done_counts:
                                stats_not_done_counts[task_name] = 0
                            stats_not_done_counts[task_name] += 1
                            statuses.append("—")
                else:
                    statuses = ["—"] * len(tasks_df)
            else:
                # إذا كان الورقة غير موجودة، نعتبر كل المهام غير منجزة
                for task_name in tasks_df["الأعمال"]:
                     if task_name not in stats_not_done_counts:
                        stats_not_done_counts[task_name] = 0
                     stats_not_done_counts[task_name] += 1
                statuses = ["—"] * len(tasks_df)
            data[d.strftime("%Y-%m-%d")] = statuses

        result_df = pd.DataFrame(data)

        # ────────────── تنسيق الجدول (توسيط وعرض) ──────────────
        # 1. Apply styles to the cells directly
        styled_df = result_df.style.set_properties(**{'text-align': 'center', 'vertical-align': 'middle'})
        
        # 2. Apply styles to the headers
        styled_df = styled_df.set_table_styles({
            'th': [{'selector': 'th', 'props': [('text-align', 'center')]}]
        })

        # عرض الجدول
        st.dataframe(
            styled_df,
            use_container_width=True
        )

        # ────────────── تصدير Excel ──────────────
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            result_df.to_excel(writer, index=False, sheet_name='تقرير')
        output.seek(0)

        st.download_button(
            label="تصدير الجدول إلى Excel",
            data=output,
            file_name=f"تقرير_{username}_{eval_period}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

        # ────────────── NEW: Attractive Statistics Section ──────────────
        st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)
        
        # HTML for a custom header
        st.markdown("""
            <h2 style='text-align: center;  margin-bottom: 20px;'>
                📊 تحليل الإنجاز والإحصائيات
            </h2>
        """, unsafe_allow_html=True)

        if stats_done_counts or stats_not_done_counts:
            # إنشاء DataFrames للإحصائيات
            df_stats = pd.DataFrame({
                "المهمة": list(set(list(stats_done_counts.keys()) + list(stats_not_done_counts.keys())))
            })
            
            # تعبئة الأصفار
            df_stats["عدد مرات الإنجاز"] = df_stats["المهمة"].apply(lambda x: stats_done_counts.get(x, 0))
            df_stats["عدد مرات عدم الإنجاز"] = df_stats["المهمة"].apply(lambda x: stats_not_done_counts.get(x, 0))
            
            # حساب المجموع والنسبة
            df_stats["المجموع"] = df_stats["عدد مرات الإنجاز"] + df_stats["عدد مرات عدم الإنجاز"]
            
            # حساب النسبة المئوية (مع تجنب القسمة على صفر)
            df_stats["نسبة الإنجاز (%)"] = (df_stats["عدد مرات الإنجاز"] / df_stats["المجموع"].replace(0, 1) * 100).round(1)
            df_stats["نسبة الإنجاز (%)"] = df_stats["نسبة الإنجاز (%)"].clip(0, 100)

            # البحث عن الأعلى والأدنى
            if not df_stats.empty:
                # 1. الأكثر إنجازاً
                best_task = df_stats.loc[df_stats["عدد مرات الإنجاز"].idxmax()]
                
                # 2. الأكثر إهمالاً (المهملة هي التي مرات عدم الإنجاز فيها أكبر)
                worst_task = df_stats.loc[df_stats["عدد مرات عدم الإنجاز"].idxmax()]

                # --- Display Metrics in Cards ---
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("""
                        <div style="
                            background-color: #d1fae5; 
                            padding: 10px; 
                            border-radius: 10px; 
                            text-align: center; 
                            border: 1px solid #10b981;
                            margin-bottom: 10px;
                            box-shadow: 0 4px 6px rgba(0,0,0,0.2);
                        ">
                            <h3 style="margin: 0; color: #065f46;">🏆 الأكثر التزامًا</h3>
                            <h3 style="margin: 5px 0; color: #064e3b;">{} | تم {} مرة </h3>
                        </div>
                    """.format(best_task["المهمة"], int(best_task["عدد مرات الإنجاز"])), unsafe_allow_html=True)
                
                with col2:
                    st.markdown("""
                        <div style="
                            background-color: #fee2e2; 
                            padding: 10px; 
                            border-radius: 10px; 
                            text-align: center; 
                            border: 1px solid #ef4444;
                            margin-bottom: 10px;
                            box-shadow: 0 4px 6px rgba(0,0,0,0.2);
                        ">
                            <h3 style="margin: 0; color: #991b1b;">⚠️ الأكثر إهمالاً</h3>
                            <h3 style="margin: 5px 0; color: #7f1d1d;">{} | لم يتم {} مرة</h3>
                        </div>
                    """.format(worst_task["المهمة"], int(worst_task["عدد مرات عدم الإنجاز"])), unsafe_allow_html=True)

                # --- Styled Stats Table ---
                
                # Define a function to color the progress bar background based on score
                def color_score(val):
                    color = '#ef4444' if val < 50 else '#f59e0b' if val < 80 else '#10b981'
                    return f'background-color: {color}; color: white; padding: 5px; border-radius: 5px; text-align: center;'

                # Apply styles to the dataframe
                styled_stats = df_stats.sort_values("عدد مرات الإنجاز", ascending=False).style
                
                # Apply background colors to the percentage column
                styled_stats = styled_stats.applymap(
                    color_score, 
                    subset=['نسبة الإنجاز (%)']
                )

        else:
            st.info("لا توجد بيانات كافية لحساب الإحصائيات للفترة المحددة.")

    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)

    if st.button("⬅️ الرجوع للصفحة الرئيسية", use_container_width=True):
        st.session_state.page = "user_home"
        st.rerun()

# ────────────────────────────────────────────────
# دالة عرض التقييم اليومي
# ────────────────────────────────────────────────
def display_daily_evaluation(df, sheet_name):
    st.success(f"📅 تقييم يوم {sheet_name}")
    
    total_tasks = 0
    completed_tasks = 0
    
    for _, row in df.iterrows():
        task = str(row["الأعمال"]).strip()
        status = str(row["الحالة"])
        
        if task not in ["حضور القلب", "رقم آية تدبرتها", "حال قلبك"]:
            total_tasks += 1
            if status == "تم":
                completed_tasks += 1
    
    if total_tasks == 0:
        st.warning("لا توجد مهام للتقييم")
        return
    
    completion_rate = (completed_tasks / total_tasks) * 100
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("✅ المكتمل", f"{completed_tasks}")
    with col2:
        st.metric("⏳ المتبقي", f"{total_tasks - completed_tasks}")
    with col3:
        st.metric("📊 نسبة الإنجاز", f"{completion_rate:.1f}%")
    
    st.progress(completion_rate / 100)
    
    if completion_rate == 100:
        st.balloons()
        st.success("🎉 ممتاز! أكملت جميع الأوراد، بارك الله فيك!")
    elif completion_rate >= 75:
        st.success("💪 أداء رائع! استمر على هذا المستوى")
    elif completion_rate >= 50:
        st.info("👍 جيد، لكن يمكنك تحسين أدائك")
    else:
        st.warning("📈 لا تستسلم، حاول إكمال المزيد غدًا")
    
    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)
    
    st.subheader("📊 التحليل حسب الأقسام")
    
    sections_data = []
    for section in df["القسم"].unique():
        section_df = df[df["القسم"] == section]
        section_total = 0
        section_completed = 0
        
        for _, row in section_df.iterrows():
            task = str(row["الأعمال"]).strip()
            status = str(row["الحالة"])
            
            if task not in ["حضور القلب", "رقم آية تدبرتها", "حال قلبك"]:
                section_total += 1
                if status == "تم":
                    section_completed += 1
        
        if section_total > 0:
            sections_data.append({
                "القسم": section,
                "المكتمل": section_completed,
                "المتبقي": section_total - section_completed,
                "النسبة": (section_completed / section_total) * 100
            })
    
    if sections_data:
        fig = go.Figure()
        sections_df = pd.DataFrame(sections_data)
        
        fig.add_trace(go.Bar(
            name="المكتمل",
            x=sections_df["القسم"],
            y=sections_df["المكتمل"],
            marker_color='#22c55e'
        ))
        
        fig.add_trace(go.Bar(
            name="المتبقي",
            x=sections_df["القسم"],
            y=sections_df["المتبقي"],
            marker_color='#ef4444'
        ))
        
        fig.update_layout(
            barmode='stack',
            title="توزيع الأوراد حسب الأقسام",
            xaxis_title="القسم",
            yaxis_title="عدد الأوراد",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(sections_df, use_container_width=True, hide_index=True)

# ────────────────────────────────────────────────
# دالة عرض التقييم الأسبوعي
# ────────────────────────────────────────────────
def display_weekly_evaluation(user_file, year, month, start_day, end_day):
    st.success(f"📅 تقييم من {start_day}/{month}/{year} إلى {end_day}/{month}/{year}")
    
    weekly_data = []
    
    for day in range(start_day, end_day + 1):
        try:
            check_date = date(year, month, day)
            df, _ = load_sheet_by_date(user_file, check_date)
            
            if df is not None:
                total = 0
                completed = 0
                
                for _, row in df.iterrows():
                    task = str(row["الأعمال"]).strip()
                    status = str(row["الحالة"])
                    
                    if task not in ["حضور القلب", "رقم آية تدبرتها", "حال قلبك"]:
                        total += 1
                        if status == "تم":
                            completed += 1
                
                if total > 0:
                    weekly_data.append({
                        "اليوم": f"{day}/{month}",
                        "المكتمل": completed,
                        "الإجمالي": total,
                        "النسبة": (completed / total) * 100
                    })
        except:
            pass
    
    if not weekly_data:
        st.warning("❌ لا توجد بيانات لهذا الأسبوع")
        return
    
    weekly_df = pd.DataFrame(weekly_data)
    
    total_completed = weekly_df["المكتمل"].sum()
    total_all = weekly_df["الإجمالي"].sum()
    avg_completion = (total_completed / total_all * 100) if total_all > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("✅ إجمالي المكتمل", f"{total_completed}")
    with col2:
        st.metric("📝 إجمالي الأوراد", f"{total_all}")
    with col3:
        st.metric("📊 متوسط الإنجاز", f"{avg_completion:.1f}%")
    
    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=weekly_df["اليوم"],
        y=weekly_df["النسبة"],
        mode='lines+markers',
        name='نسبة الإنجاز',
        line=dict(color='#3b82f6', width=3),
        marker=dict(size=10)
    ))
    
    fig.update_layout(
        title="تطور الأداء خلال الأسبوع",
        xaxis_title="اليوم",
        yaxis_title="نسبة الإنجاز (%)",
        height=400,
        yaxis=dict(range=[0, 105])
    )
    
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(weekly_df, use_container_width=True, hide_index=True)

# ────────────────────────────────────────────────
# دالة عرض التقييم الشهري
# ────────────────────────────────────────────────
def display_monthly_evaluation(user_file, year, month):
    st.success(f"📅 تقييم شهر {month}/{year}")
    
    import calendar
    days_in_month = calendar.monthrange(year, month)[1]
    
    monthly_data = []
    
    for day in range(1, days_in_month + 1):
        try:
            check_date = date(year, month, day)
            df, _ = load_sheet_by_date(user_file, check_date)
            
            if df is not None:
                total = 0
                completed = 0
                
                for _, row in df.iterrows():
                    task = str(row["الأعمال"]).strip()
                    status = str(row["الحالة"])
                    
                    if task not in ["حضور القلب", "رقم آية تدبرتها", "حال قلبك"]:
                        total += 1
                        if status == "تم":
                            completed += 1
                
                if total > 0:
                    monthly_data.append({
                        "اليوم": day,
                        "المكتمل": completed,
                        "الإجمالي": total,
                        "النسبة": (completed / total) * 100
                    })
        except:
            pass
    
    if not monthly_data:
        st.warning("❌ لا توجد بيانات لهذا الشهر")
        return
    
    monthly_df = pd.DataFrame(monthly_data)
    
    total_days = len(monthly_df)
    total_completed = monthly_df["المكتمل"].sum()
    total_all = monthly_df["الإجمالي"].sum()
    avg_completion = (total_completed / total_all * 100) if total_all > 0 else 0
    best_day = monthly_df.loc[monthly_df["النسبة"].idxmax(), "اليوم"]
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("📆 أيام الالتزام", f"{total_days} يوم")
        st.metric("✅ إجمالي المكتمل", f"{total_completed}")
    with col2:
        st.metric("📊 متوسط الإنجاز", f"{avg_completion:.1f}%")
        st.metric("🏆 أفضل يوم", f"يوم {best_day}")
    
    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)
    
    fig = go.Figure(data=[go.Pie(
        labels=['المكتمل', 'المتبقي'],
        values=[total_completed, total_all - total_completed],
        hole=.4,
        marker_colors=['#22c55e', '#ef4444']
    )])
    
    fig.update_layout(
        title="نسبة الإنجاز الشهري",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.subheader("📅 خريطة الأيام النشطة")
    
    weeks = []
    week = [None] * 7
    first_weekday = calendar.monthrange(year, month)[0]
    
    current_day = 1
    for i in range(first_weekday, 7):
        if current_day in monthly_df["اليوم"].values:
            completion = monthly_df[monthly_df["اليوم"] == current_day]["النسبة"].values[0]
            week[i] = completion
        else:
            week[i] = None
        current_day += 1
    weeks.append(week[:])
    
    while current_day <= days_in_month:
        week = [None] * 7
        for i in range(7):
            if current_day <= days_in_month:
                if current_day in monthly_df["اليوم"].values:
                    completion = monthly_df[monthly_df["اليوم"] == current_day]["النسبة"].values[0]
                    week[i] = completion
                else:
                    week[i] = None
                current_day += 1
        weeks.append(week[:])
    
    fig = go.Figure(data=go.Heatmap(
        z=weeks,
        x=['الأحد', 'الإثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت'],
        y=[f"أسبوع {i+1}" for i in range(len(weeks))],
        colorscale='RdYlGn',
        zmin=0,
        zmax=100
    ))
    
    fig.update_layout(
        title="نسبة الإنجاز اليومي",
        height=300
    )
    
    st.plotly_chart(fig, use_container_width=True)

# ────────────────────────────────────────────────
# دالة عرض التقييم المخصص
# ────────────────────────────────────────────────
def display_custom_evaluation(user_file, start_date, end_date):
    st.success(f"📅 تقييم من {start_date} إلى {end_date}")
    
    custom_data = []
    current_date = start_date
    
    while current_date <= end_date:
        df, _ = load_sheet_by_date(user_file, current_date)
        
        if df is not None:
            total = 0
            completed = 0
            
            for _, row in df.iterrows():
                task = str(row["الأعمال"]).strip()
                status = str(row["الحالة"])
                
                if task not in ["حضور القلب", "رقم آية تدبرتها", "حال قلبك"]:
                    total += 1
                    if status == "تم":
                        completed += 1
            
            if total > 0:
                custom_data.append({
                    "التاريخ": current_date.strftime("%Y-%m-%d"),
                    "المكتمل": completed,
                    "الإجمالي": total,
                    "النسبة": (completed / total) * 100
                })
        
        current_date += timedelta(days=1)
    
    if not custom_data:
        st.warning("❌ لا توجد بيانات لهذه الفترة")
        return
    
    custom_df = pd.DataFrame(custom_data)
    
    total_completed = custom_df["المكتمل"].sum()
    total_all = custom_df["الإجمالي"].sum()
    avg_completion = (total_completed / total_all * 100) if total_all > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📆 عدد الأيام", f"{len(custom_df)}")
    with col2:
        st.metric("✅ إجمالي المكتمل", f"{total_completed}")
    with col3:
        st.metric("📊 متوسط الإنجاز", f"{avg_completion:.1f}%")
    
    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=custom_df["التاريخ"],
        y=custom_df["النسبة"],
        mode='lines+markers',
        name='نسبة الإنجاز',
        fill='tozeroy',
        line=dict(color='#8b5cf6', width=2)
    ))
    
    fig.update_layout(
        title="تطور الأداء خلال الفترة المحددة",
        xaxis_title="التاريخ",
        yaxis_title="نسبة الإنجاز (%)",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(custom_df, use_container_width=True, hide_index=True)


# ────────────────────────────────────────────────
# تسجيل الخروج
# ────────────────────────────────────────────────
def logout():
    for key in list(st.session_state.keys()):
        if key not in ["page"]:
            del st.session_state[key]
    st.session_state.page = "login"
    st.rerun()

# ────────────────────────────────────────────────
# شاشة الأدمن
# ────────────────────────────────────────────────

def admin_screen():
    # ──── CSS مخصص للأزرار ────
    st.markdown("""
    <style>
    /* زر عادي */
    div.stButton > button:first-child {
        background: linear-gradient(to right, #00467f, #a5cc82);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 14px 24px;
        font-size: 18px;
        font-weight: 600;
        margin-bottom: 12px;
        width: 100%;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }

    /* hover */
    div.stButton > button:first-child:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px rgba(0,0,0,0.2);
        background: linear-gradient(135deg, #6366f1, #a78bfa);
    }

    /* زر تسجيل الخروج (لونه أحمر) */
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #ef4444, #f87171) !important;
    }
    
    div.stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #dc2626, #f87171) !important;
        transform: translateY(-2px);
        box-shadow: 0 10px 15px rgba(239, 68, 68, 0.4);
    }

    /* إخفاء الـ border الافتراضي إذا أردت */
    div.stButton > button {
        border: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("### ﴿مِّنَ الْمُؤْمِنِينَ رِجَالٌ صَدَقُوا مَا عَاهَدُوا اللَّهَ عَلَيْهِ﴾")
    st.markdown("### 📌 اختر العملية")

    if st.button("📋 متابعة الطلبة", use_container_width=True):
        st.session_state.page = "admin_students"
        st.rerun()

    if st.button("✏️ تعديل بيانات", use_container_width=True):
        st.session_state.page = "admin_edit"
        st.rerun()

    if st.button("➕ إضافة طلبة", use_container_width=True):
        st.session_state.page = "admin_add"
        st.rerun()
            
    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)

    if st.button("🚪 تسجيل الخروج", type="primary", use_container_width=True):
        logout()


# ────────────────────────────────────────────────
# شاشة متابعة الطلاب للأدمن
# ────────────────────────────────────────────────
def admin_students_screen():
    st.header("📋 متابعة الطلبة")
    
    # Custom CSS for student and back buttons
    st.markdown("""
        <style>
        /* Student buttons styling */
        div[data-testid="stButton"] > button:not([kind="secondary"]) {
            background: linear-gradient(to right, #159957, #155799); !important;
            color: white !important;
            border: none !important;
            padding: 0.75rem 1rem !important;
            font-size: 1rem !important;
            font-weight: 500 !important;
            border-radius: 8px !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
        }
        
        div[data-testid="stButton"] > button:not([kind="secondary"]):hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2) !important;
            opacity: 0.9 !important;
        }
        
        /* Back button styling */
        div[data-testid="stButton"]:last-child > button {
            background: linear-gradient(to right, #159957, #155799); !important;
            color: white !important;
            border: none !important;
            padding: 0.75rem 1rem !important;
            font-size: 1rem !important;
            font-weight: 600 !important;
            border-radius: 8px !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 2px 4px rgba(239, 68, 68, 0.3) !important;
        }
        
        div[data-testid="stButton"]:last-child > button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 4px 12px rgba(239, 68, 68, 0.4) !important;
            opacity: 0.95 !important;
        }
        
        /* Custom divider */
        .custom-divider {
            border: none;
            border-top: 2px solid #e5e7eb;
            margin: 2rem 0;
        }
        </style>
    """, unsafe_allow_html=True)
    
    users_df = load_users()
    students_df = get_students_users(users_df)
    
    if students_df.empty:
        st.warning("لا يوجد طلبة مسجلين")
        return
    
    for _, row in students_df.iterrows():
        username = row["username"]
        level = row["level"]
        if st.button(f"🎯 {username}", key=f"student_{username}", use_container_width=True):
            st.session_state.selected_student = {
                "username": username,
                "level": level
            }
            st.session_state.page = "admin_student_profile"
            st.rerun()
    
    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)
    
    if st.button("⬅️ رجوع", use_container_width=True):
        st.session_state.page = "admin"
        st.rerun()
 
        
# ────────────────────────────────────────────────
# صفحة ملف الطالب للأدمن
# ────────────────────────────────────────────────
def admin_student_profile_screen():
    if "selected_student" not in st.session_state or not st.session_state.selected_student:
        st.error("لم يتم اختيار طالب")
        return

    student = st.session_state.selected_student
    username = student["username"]
    level = student["level"]

    st.header(f"📋 متابعة الطالب: {username}")
    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)

    eval_period = st.selectbox("مدة التقييم", ["يومي", "أسبوعي", "شهري"])

    # ────────────── اختيار الفترة ──────────────
    dates = []
    year = None
    month = None
    week = None

    if eval_period == "يومي":
        selected_date = st.date_input("اختر اليوم", value=date.today())
        dates = [selected_date]
    elif eval_period == "أسبوعي":
        col1, col2, col3 = st.columns(3)
        with col1:
            year = st.selectbox("السنة", range(2024, 2027), index=1, key="week_year")
        with col2:
            month = st.selectbox("الشهر", range(1, 13), index=date.today().month - 1, key="week_month")
        with col3:
            week = st.selectbox(
                "الأسبوع",
                ["الأسبوع الأول", "الأسبوع الثاني", "الأسبوع الثالث", "الأسبوع الرابع"],
                key="week_select"
            )
        if year and month and week:
            week_number = ["الأسبوع الأول", "الأسبوع الثاني", "الأسبوع الثالث", "الأسبوع الرابع"].index(week)
            start_day = week_number * 7 + 1
            end_day = min(start_day + 6, calendar.monthrange(year, month)[1])
            dates = [date(year, month, day) for day in range(start_day, end_day + 1)]
    elif eval_period == "شهري":
        col1, col2 = st.columns(2)
        with col1:
            year = st.selectbox("السنة", range(2024, 2027), index=1, key="month_year")
        with col2:
            month = st.selectbox("الشهر", range(1, 13), index=date.today().month - 1, key="month_month")
        if year and month:
            days_in_month = calendar.monthrange(year, month)[1]
            dates = [date(year, month, day) for day in range(1, days_in_month + 1)]

    # ────────────── جلب ملف الطالب ──────────────
    user_file = load_or_create_user_file(username, level)
    if not user_file:
        st.error("ملف الطالب غير موجود")
        return

    xls = pd.ExcelFile(user_file)
    if not xls.sheet_names:
        st.warning("لا توجد بيانات متاحة")
        return

    # استخراج الأقسام المتاحة
    df_sample = pd.read_excel(user_file, sheet_name=xls.sheet_names[0])
    all_sections = sorted(df_sample["القسم"].dropna().unique().tolist())

    selected_sections = st.multiselect(
        "اختر الأقسام المطلوب عرضها",
        options=all_sections,
        default=all_sections,
        placeholder="اختر قسم أو أكثر..."
    )

    if not selected_sections:
        st.info("يرجى اختيار قسم واحد على الأقل")
        return

    if st.button("عرض الجدول", use_container_width=True) and dates:
        # استخراج المهام الأساسية
        tasks_df = df_sample[df_sample["القسم"].isin(selected_sections)][["القسم", "الأعمال"]].copy()
        tasks_df["الأعمال"] = tasks_df["الأعمال"].str.strip()

        data = {
            "القسم": tasks_df["القسم"].tolist(),
            "الأعمال": tasks_df["الأعمال"].tolist()
        }

        excluded = ["حضور القلب", "رقم آية تدبرتها", "حال قلبك"]

        # ──── إحصائيات جديدة ────
        stats_done_counts = {}
        stats_not_done_counts = {}

        for d in dates:
            sheet_name = d.strftime("%Y-%m-%d")
            statuses = []
            if sheet_name in xls.sheet_names:
                df_day = pd.read_excel(user_file, sheet_name=sheet_name)
                df_day["الأعمال"] = df_day["الأعمال"].str.strip()

                for _, row in tasks_df.iterrows():
                    mask = (df_day["القسم"] == row["القسم"]) & (df_day["الأعمال"] == row["الأعمال"])
                    if mask.any():
                        status = str(df_day.loc[mask, "الحالة"].values[0]).strip()
                        task_name = row["الأعمال"]

                        if task_name not in excluded:
                            if status == "تم":
                                stats_done_counts[task_name] = stats_done_counts.get(task_name, 0) + 1
                            else:
                                stats_not_done_counts[task_name] = stats_not_done_counts.get(task_name, 0) + 1

                        if task_name in excluded:
                            statuses.append(status if status else "—")
                        else:
                            statuses.append("تم بفضل الله" if status == "تم" else "✗")
                    else:
                        statuses.append("—")

            else:
                statuses = ["—"] * len(tasks_df)

            data[d.strftime("%Y-%m-%d")] = statuses

        result_df = pd.DataFrame(data)

        # عرض الجدول
        styled_df = result_df.style.set_properties(**{'text-align': 'center', 'vertical-align': 'middle'})
        styled_df = styled_df.set_table_styles({
            'th': [{'selector': 'th', 'props': [('text-align', 'center')]}]
        })

        st.dataframe(styled_df, use_container_width=True)

        # ────────────── NEW: قسم الإحصائيات الجذاب ──────────────
        st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)

        st.markdown("""
            <h2 style='text-align: center; margin-bottom: 20px;'>
                📊 تحليل الإنجاز والإحصائيات
            </h2>
        """, unsafe_allow_html=True)

        if stats_done_counts or stats_not_done_counts:
            # إنشاء DataFrame للإحصائيات
            df_stats = pd.DataFrame({
                "المهمة": list(set(list(stats_done_counts.keys()) + list(stats_not_done_counts.keys())))
            })

            df_stats["عدد مرات الإنجاز"] = df_stats["المهمة"].apply(lambda x: stats_done_counts.get(x, 0))
            df_stats["عدد مرات عدم الإنجاز"] = df_stats["المهمة"].apply(lambda x: stats_not_done_counts.get(x, 0))
            df_stats["المجموع"] = df_stats["عدد مرات الإنجاز"] + df_stats["عدد مرات عدم الإنجاز"]

            # نسبة الإنجاز (تجنب القسمة على صفر)
            df_stats["نسبة الإنجاز (%)"] = (df_stats["عدد مرات الإنجاز"] / df_stats["المجموع"].replace(0, 1) * 100).round(1)
            df_stats["نسبة الإنجاز (%)"] = df_stats["نسبة الإنجاز (%)"].clip(0, 100)

            if not df_stats.empty:
                # الأكثر إنجازاً
                best_task = df_stats.loc[df_stats["عدد مرات الإنجاز"].idxmax()]
                # الأكثر إهمالاً
                worst_task = df_stats.loc[df_stats["عدد مرات عدم الإنجاز"].idxmax()]

                # ─── عرض الكروت ───
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("""
                        <div style="
                            background-color: #d1fae5; 
                            padding: 10px; 
                            border-radius: 10px; 
                            text-align: center; 
                            border: 1px solid #10b981;
                            margin-bottom: 10px;
                            box-shadow: 0 4px 6px rgba(0,0,0,0.2);
                        ">
                            <h3 style="margin: 0; color: #065f46;">🏆 الأكثر التزامًا</h3>
                            <h3 style="margin: 5px 0; color: #064e3b;">{} | تم {} مرة </h3>
                        </div>
                    """.format(best_task["المهمة"], int(best_task["عدد مرات الإنجاز"])), unsafe_allow_html=True)
                
                with col2:
                    st.markdown("""
                        <div style="
                            background-color: #fee2e2; 
                            padding: 10px; 
                            border-radius: 10px; 
                            text-align: center; 
                            border: 1px solid #ef4444;
                            margin-bottom: 10px;
                            box-shadow: 0 4px 6px rgba(0,0,0,0.2);
                        ">
                            <h3 style="margin: 0; color: #991b1b;">⚠️ الأكثر إهمالاً</h3>
                            <h3 style="margin: 5px 0; color: #7f1d1d;">{} | لم يتم {} مرة</h3>
                        </div>
                    """.format(worst_task["المهمة"], int(worst_task["عدد مرات عدم الإنجاز"])), unsafe_allow_html=True)

        else:
            st.info("لا توجد بيانات كافية لحساب الإحصائيات في الفترة المحددة")

        # ─── تصدير الجدول ───
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            result_df.to_excel(writer, index=False, sheet_name='تقرير')
        output.seek(0)

        st.download_button(
            label="تصدير الجدول إلى Excel",
            data=output,
            file_name=f"تقرير_{username}_{eval_period}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)

    if st.button("⬅️ رجوع", use_container_width=True):
        st.session_state.selected_student = None
        st.session_state.page = "admin_students"
        st.rerun()


# ────────────────────────────────────────────────
# صفحة إضافة طالب جديد
# ────────────────────────────────────────────────
def admin_add_student_screen():
    st.header("➕ إضافة طالب جديد")
    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)

    # ─── استخراج أسماء المستويات من مجلد templet ───
    TEMPLATE_PATH = "database/templet"
    level_options = []

    if os.path.exists(TEMPLATE_PATH):
        try:
            files = os.listdir(TEMPLATE_PATH)
            excel_files = [f for f in files if f.lower().endswith(('.xlsx', '.xls'))]

            # نأخذ الاسم بدون الامتداد .xlsx
            level_options = []
            for f in excel_files:
                name_without_ext = os.path.splitext(f)[0].strip()
                # لو عايز تنظيف إضافي (اختياري)
                # name_without_ext = name_without_ext.replace("level ", "", 1).replace("Level ", "", 1).strip()
                if name_without_ext:  # تجاهل الملفات الفاضية
                    level_options.append(name_without_ext)

            # ترتيب منطقي (لو أرقام → رقميًا، وإلا أبجديًا)
            def sort_key(x):
                try:
                    # لو فيه رقم في البداية أو بعد كلمة level
                    num_part = ''.join(c for c in x if c.isdigit())
                    return (int(num_part) if num_part else 9999, x)
                except:
                    return (9999, x)

            level_options = sorted(level_options, key=sort_key)

        except Exception as e:
            st.warning(f"مشكلة في قراءة مجلد المستويات: {e}")

    if not level_options:
        level_options = ["المستوى ١", "المستوى ٢", "المستوى ٣"]  # fallback
        st.info("لم يتم العثور على ملفات مستويات في database/templet")

    # ─── النموذج ───
    with st.form(key="add_student_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            new_username = st.text_input("اسم المستخدم", key="new_un")

        with col2:
            new_password = st.text_input("كلمة المرور", type="password", key="new_pw")

        col3, col4 = st.columns(2)

        with col3:
            role = st.selectbox(
                "الدور",
                ["user", "admin"],
                format_func=lambda x: "طالب" if x == "user" else "أدمن",
                key="role_sel"
            )

        with col4:
            if role == "user":
                selected_level = st.selectbox(
                    "المستوى",
                    options=level_options,
                    key="level_sel_user"
                )
            else:
                selected_level = None
                st.markdown(" ")  # فراغ للتناسق

        submitted = st.form_submit_button("إضافة المستخدم", type="primary", use_container_width=True)

        if submitted:
            if not new_username.strip():
                st.error("اسم المستخدم مطلوب")
                st.stop()

            if not new_password:
                st.error("كلمة المرور مطلوبة")
                st.stop()

            if role == "user" and not selected_level:
                st.error("اختر المستوى من فضلك")
                st.stop()

            # تحميل users الحالي
            try:
                df_users = pd.read_excel("users.xlsx")
            except:
                df_users = pd.DataFrame(columns=["username", "password", "role", "level"])

            if new_username.strip() in df_users["username"].astype(str).values:
                st.error("اسم المستخدم موجود بالفعل")
                st.stop()

            # السجل الجديد
            new_data = {
                "username": new_username.strip(),
                "password": new_password,
                "role": role,
                "level": selected_level if role == "user" else None
            }

            df_users = pd.concat([df_users, pd.DataFrame([new_data])], ignore_index=True)

            try:
                df_users.to_excel("users.xlsx", index=False)
                st.success(f"تم إضافة **{new_username}** بنجاح")
                st.balloons()

                # تحديث الكاش لو موجود
                if "users_df" in globals():
                    global users_df
                    users_df = load_users()

                st.rerun()

            except Exception as e:
                st.error(f"فشل الحفظ: {str(e)}")

    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)

    if st.button("⬅️ رجوع", use_container_width=True):
        st.session_state.page = "admin"
        st.rerun()

# ────────────────────────────────────────────────
# صفحة تعديل بيانات المستخدمين (للأدمن فقط)
# ────────────────────────────────────────────────
def admin_edit_screen():
    st.header("✏️ تعديل بيانات المستخدمين")
    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)

    users_df = load_users()

    if users_df.empty:
        st.warning("لا يوجد مستخدمين مسجلين")
        return

    # اختيار المستخدم
    selected_username = st.selectbox(
        "👤 اختر المستخدم",
        options=users_df["username"].astype(str).tolist()
    )

    user_row = users_df[users_df["username"].astype(str) == selected_username]

    if user_row.empty:
        st.error("المستخدم غير موجود")
        return

    user_index = user_row.index[0]

    current_username = str(user_row.iloc[0]["username"])
    current_password = str(user_row.iloc[0]["password"])
    current_role = str(user_row.iloc[0]["role"])
    current_level = user_row.iloc[0]["level"]

    # استخراج المستويات من templet
    TEMPLATE_PATH = "database/templet"
    level_options = []

    if os.path.exists(TEMPLATE_PATH):
        for f in os.listdir(TEMPLATE_PATH):
            if f.lower().endswith((".xlsx", ".xls")):
                level_options.append(os.path.splitext(f)[0])

    level_options = sorted(level_options)

    with st.form("edit_user_form"):
        col1, col2 = st.columns(2)

        with col1:
            new_username = st.text_input(
                "اسم المستخدم",
                value=current_username
            )

        with col2:
            new_password = st.text_input(
                "كلمة المرور",
                value=current_password
            )

        col3, col4 = st.columns(2)

        with col3:
            new_role = st.selectbox(
                "الدور",
                ["user", "admin"],
                index=0 if current_role == "user" else 1,
                format_func=lambda x: "طالب" if x == "user" else "أدمن"
            )

        with col4:
            if new_role == "user":
                new_level = st.selectbox(
                    "المستوى",
                    options=level_options,
                    index=level_options.index(current_level)
                    if current_level in level_options else 0
                )
            else:
                new_level = None
                st.markdown(" ")

        submitted = st.form_submit_button(
            "💾 حفظ التعديلات",
            type="primary",
            use_container_width=True
        )

    if submitted:
        if not new_username.strip():
            st.error("اسم المستخدم لا يمكن أن يكون فارغًا")
            return

        # منع تكرار اسم المستخدم
        if (
            new_username.strip() != current_username
            and new_username.strip() in users_df["username"].astype(str).values
        ):
            st.error("اسم المستخدم موجود بالفعل")
            return

        users_df.at[user_index, "username"] = new_username.strip()
        users_df.at[user_index, "password"] = new_password
        users_df.at[user_index, "role"] = new_role
        users_df.at[user_index, "level"] = new_level if new_role == "user" else None

        try:
            users_df.to_excel("users.xlsx", index=False)
            st.success("✅ تم تحديث بيانات المستخدم بنجاح")
            st.balloons()
            st.rerun()
        except Exception as e:
            st.error(f"خطأ أثناء الحفظ: {e}")

    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)

    if st.button("⬅️ رجوع", use_container_width=True):
        st.session_state.page = "admin"
        st.rerun()


# ────────────────────────────────────────────────
# التوجيه الرئيسي
# ────────────────────────────────────────────────
match st.session_state.page:
    case "login":
        login_screen()
    case "admin":
        admin_screen()
    case "admin_students":
        admin_students_screen()
    case "admin_student_profile":
        admin_student_profile_screen()
    case "admin_add":
        admin_add_student_screen()
    case "admin_edit":
        admin_edit_screen()
    case "user_home":
        user_home_screen()
    case "daily":
        daily_followup_screen()
    case "records":
        old_records_screen()
    case "evaluations":
        evaluations_screen()
    case _:
        st.session_state.page = "login"
        st.rerun()
