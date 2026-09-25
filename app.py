import io
import json
import math
import os
import sqlite3
import zipfile
from datetime import datetime, timedelta
import pandas as pd
import streamlit as st


# ---------------------------------------------------------
# SAAT AYARI (UTC+3 TÜRKİYE SAATİ İÇİN YARDIMCI FONKSİYON)
# ---------------------------------------------------------
def get_now():
    return datetime.now() + timedelta(hours=3)


# ---------------------------------------------------------
# SAYFA YAPILANDIRMASI & ÖZEL MODERN CSS REVİZYONU
# ---------------------------------------------------------
st.set_page_config(
    page_title="Eşme Makina MES - Üretim & Fason Yönetimi",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Yüklemeler için klasör oluştur
os.makedirs("uploads", exist_ok=True)

st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [class*="css"]  {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    .main .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
        max-width: 98% !important;
    }

    /* Streamlit Üst Header Saydamlaştırma */
    header[data-testid="stHeader"] {
        background: transparent !important;
    }
    
    [data-testid="stSidebarHeader"] {
        background: transparent !important;
        padding-top: 0.5rem !important;
    }

    /* Sol Menü (Sidebar) Premium Koyu Tema & Gradyan */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #090d16 0%, #111827 100%) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    [data-testid="stSidebar"] > div:first-child {
        background: transparent !important;
    }

    [data-testid="stSidebarContent"] {
        background: transparent !important;
    }

    [data-testid="stSidebar"] * {
        color: #f1f5f9 !important;
    }

    /* Sidebar İçindeki Expander / Açılır Kutular */
    [data-testid="stSidebar"] details {
        background-color: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 10px !important;
        color: #f1f5f9 !important;
        padding: 2px;
    }

    [data-testid="stSidebar"] summary {
        color: #f1f5f9 !important;
        font-weight: 600;
    }

    /* Modern Kart Yapısı */
    .custom-card {
        background: #ffffff;
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.05), 0 2px 6px -1px rgba(0, 0, 0, 0.03);
        border: 1px solid #e2e8f0;
        margin-bottom: 12px;
        transition: all 0.3s ease;
    }
    .custom-card:hover {
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.08);
        border-color: #cbd5e1;
    }
    
    /* Firma Başlık Bandı */
    .firm-header-band {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        color: #ffffff;
        padding: 8px 16px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 0.95rem;
        letter-spacing: 0.4px;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.1);
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 10px;
        margin-bottom: 4px;
        border-left: 4px solid #3b82f6;
    }
    
    .count-badge {
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
        color: #ffffff;
        padding: 2px 8px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 700;
        box-shadow: 0 2px 5px rgba(59, 130, 246, 0.3);
    }

    /* Satır İçi İş Kartı */
    .job-row-card {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 2px 6px !important;
        margin-bottom: 2px !important;
        transition: all 0.2s ease;
    }
    .job-row-card:hover {
        border-color: #94a3b8;
        background-color: #ffffff;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }

    /* =========================================================
       RESPONSIVE TASARIM: MASAÜSTÜ KOMPAKT & MOBİL KART
       ========================================================= */

    /* ----- MASAÜSTÜ GÖRÜNÜMÜ (769px ve üzeri) ----- */
    @media (min-width: 769px) {
        [class*="st-key-job_row_"] {
            gap: 0rem !important;
            row-gap: 0rem !important;
            padding: 2px 4px !important;
            margin: 0 0 2px 0 !important;
            background: #f8fafc !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 6px !important;
        }

        [class*="st-key-job_row_"] div[data-testid="stHorizontalBlock"] {
            gap: 0.18rem !important;
            margin: 0 !important;
            padding: 0 !important;
        }

        [class*="st-key-job_row_"] div[data-testid="stTextInput"],
        [class*="st-key-job_row_"] div[data-testid="stSelectbox"],
        [class*="st-key-job_row_"] div[data-testid="stNumberInput"] {
            margin: 0 !important;
            padding: 0 !important;
        }

        /* Widget label'ı masaüstünde gizle */
        [class*="st-key-job_row_"] div[data-testid="stWidgetLabel"] {
            display: none !important;
            margin: 0 !important;
            padding: 0 !important;
            min-height: 0 !important;
            height: 0 !important;
        }

        [class*="st-key-job_row_"] div[data-baseweb="input"],
        [class*="st-key-job_row_"] div[data-baseweb="select"] {
            min-height: 28px !important;
            height: 28px !important;
            margin: 0 !important;
            font-size: 0.82rem !important;
        }

        [class*="st-key-job_row_"] div[data-baseweb="input"] input {
            height: 26px !important;
            min-height: 26px !important;
            padding-top: 2px !important;
            padding-bottom: 2px !important;
            font-size: 0.82rem !important;
        }

        [class*="st-key-job_row_"] div[data-baseweb="select"] > div {
            min-height: 28px !important;
            height: 28px !important;
            padding-top: 0 !important;
            padding-bottom: 0 !important;
        }

        [class*="st-key-job_row_"] div[data-testid="stButton"] button,
        [class*="st-key-job_row_"] div[data-testid="stDownloadButton"] button,
        [class*="st-key-job_row_"] div[data-testid="stPopover"] > button {
            min-height: 28px !important;
            height: 28px !important;
            padding-top: 0 !important;
            padding-bottom: 0 !important;
            margin: 0 !important;
        }
    }

    /* ----- MOBİL GÖRÜNÜMÜ (768px ve altı) ----- */
    @media (max-width: 768px) {
        .main .block-container {
            padding-top: 15px !important;
            padding-left: 10px !important;
            padding-right: 10px !important;
        }

        /* Masaüstü başlık satırını mobilde gizle */
        [class*="st-key-job_header_row"] {
            display: none !important;
        }

        /* Her bir iş satırını şık bir karta çevir */
        [class*="st-key-job_row_"] {
            background: #ffffff !important;
            border: 1px solid #cbd5e1 !important;
            border-radius: 12px !important;
            padding: 16px !important;
            margin-bottom: 16px !important;
            box-shadow: 0 4px 15px rgba(0,0,0,0.05) !important;
            display: flex !important;
            flex-direction: column !important;
        }

        [class*="st-key-job_row_"] div[data-testid="stHorizontalBlock"] {
            flex-direction: column !important;
            gap: 12px !important;
        }

        /* Etiketleri mobilde göster */
        [class*="st-key-job_row_"] div[data-testid="stWidgetLabel"] {
            display: flex !important;
            margin-bottom: 4px !important;
            min-height: auto !important;
        }
        
        [class*="st-key-job_row_"] div[data-testid="stWidgetLabel"] p {
            font-size: 0.95rem !important;
            font-weight: 700 !important;
            color: #334155 !important;
        }

        /* Input'ları dokunmatik için büyüt */
        [class*="st-key-job_row_"] div[data-baseweb="input"],
        [class*="st-key-job_row_"] div[data-baseweb="select"] {
            min-height: 44px !important;
            height: auto !important;
        }

        [class*="st-key-job_row_"] div[data-baseweb="input"] input {
            height: 42px !important;
            min-height: 42px !important;
            font-size: 1rem !important;
            padding: 0 10px !important;
        }

        [class*="st-key-job_row_"] div[data-baseweb="select"] > div {
            min-height: 44px !important;
            height: auto !important;
        }

        /* Butonları yan yana ve dokunulabilir boyutta tut */
        [class*="st-key-job_actions_"] div[data-testid="stHorizontalBlock"] {
            flex-direction: row !important;
            gap: 8px !important;
        }

        [class*="st-key-job_row_"] div[data-testid="stButton"] button,
        [class*="st-key-job_row_"] div[data-testid="stDownloadButton"] button,
        [class*="st-key-job_row_"] div[data-testid="stPopover"] > button {
            min-height: 44px !important;
            height: 44px !important;
            font-size: 1.2rem !important;
            margin: 0 !important;
            width: 100% !important;
        }
    }

    /* Sol Menü Seçenek Tasarımı */
    [data-testid="stSidebar"] .stRadio > label {
        font-weight: 800 !important;
        color: #64748b !important;
        font-size: 0.78rem !important;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        margin-bottom: 8px;
    }

    [data-testid="stSidebar"] .stRadio > div {
        gap: 6px;
    }

    [data-testid="stSidebar"] .stRadio label {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 10px !important;
        padding: 10px 14px !important;
        color: #cbd5e1 !important;
        font-weight: 500 !important;
        font-size: 0.9rem !important;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
        cursor: pointer;
        display: flex;
        align-items: center;
        margin-bottom: 2px;
    }

    [data-testid="stSidebar"] .stRadio label:hover {
        background: rgba(255, 255, 255, 0.07) !important;
        border-color: rgba(255, 255, 255, 0.15) !important;
        color: #ffffff !important;
        transform: translateX(4px);
    }

    [data-testid="stSidebar"] .stRadio div[data-checked="true"] label {
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%) !important;
        border-color: #60a5fa !important;
        color: #ffffff !important;
        font-weight: 700 !important;
        box-shadow: 0 4px 16px rgba(59, 130, 246, 0.4);
    }

    [data-testid="stMetricValue"] {
        font-size: 1.5rem !important;
        font-weight: 800 !important;
        color: #0f172a;
        letter-spacing: -0.5px;
    }
    
    /* Buton, İndirme ve Popover Görünüm İyileştirmeleri */
    .stButton > button:not([kind="primary"]), 
    div[data-testid="stDownloadButton"] > button:not([kind="primary"]),
    div[data-testid="stDownloadButton"] > a,
    div[data-testid="stPopover"] > button {
        background-color: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        color: #1e293b !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
        padding: 2px 6px !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.02) !important;
        transition: all 0.2s ease-in-out !important;
        min-height: 28px !important;
    }

    .stButton > button:not([kind="primary"]):hover, 
    div[data-testid="stDownloadButton"] > button:not([kind="primary"]):hover,
    div[data-testid="stDownloadButton"] > a:hover,
    div[data-testid="stPopover"] > button:hover {
        background-color: #f8fafc !important;
        border-color: #3b82f6 !important;
        color: #1d4ed8 !important;
        box-shadow: 0 2px 8px rgba(59, 130, 246, 0.12) !important;
        transform: translateY(-1px);
    }
</style>
""",
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# VERİTABANI BAĞLANTISI VE OTOMATİK MİGRASYON
# ---------------------------------------------------------
def get_db_connection():
    conn = sqlite3.connect("esme_makina_uretim.db")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS work_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer TEXT,
            job_name TEXT,
            material TEXT,
            dimensions TEXT,
            supplier TEXT,
            quantity INTEGER,
            heat_treatment TEXT,
            status TEXT,
            machine_name TEXT,
            deadline TEXT,
            notes TEXT,
            start_time TEXT,
            end_time TEXT,
            duration_str TEXT,
            price REAL,
            dik_time REAL DEFAULT 0,
            torna_time REAL DEFAULT 0,
            tel_time REAL DEFAULT 0,
            uni_time REAL DEFAULT 0,
            drawing_path TEXT,
            drawing_name TEXT,
            created_at TEXT,
            is_archived INTEGER DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_name TEXT,
            message TEXT,
            created_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS heat_treatment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sent_date TEXT,
            supplier_firm TEXT,
            customer TEXT,
            product_code_name TEXT,
            quantity INTEGER,
            material TEXT,
            hardness TEXT,
            weight_kg REAL,
            process_type TEXT,
            status TEXT,
            invoice_info TEXT,
            notes TEXT,
            created_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS wjg_waterjet (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sent_date TEXT,
            customer TEXT,
            part_name TEXT,
            part_code TEXT,
            dimensions TEXT,
            order_qty INTEGER,
            received_qty INTEGER,
            unit_price REAL,
            invoice_info TEXT,
            status TEXT,
            notes TEXT,
            created_at TEXT
        )
    """)

    cursor.execute("PRAGMA table_info(work_orders)")
    cols = [row[1] for row in cursor.fetchall()]

    columns_to_add = [
        ("supplier", "TEXT"),
        ("machine_name", "TEXT"),
        ("notes", "TEXT"),
        ("start_time", "TEXT"),
        ("end_time", "TEXT"),
        ("duration_str", "TEXT"),
        ("price", "REAL"),
        ("dik_time", "REAL DEFAULT 0"),
        ("torna_time", "REAL DEFAULT 0"),
        ("tel_time", "REAL DEFAULT 0"),
        ("uni_time", "REAL DEFAULT 0"),
        ("drawing_path", "TEXT"),
        ("drawing_name", "TEXT"),
        ("is_archived", "INTEGER DEFAULT 0"),
    ]

    for col_name, col_type in columns_to_add:
        if col_name not in cols:
            cursor.execute(
                f"ALTER TABLE work_orders ADD COLUMN {col_name} {col_type}"
            )

    conn.commit()
    conn.close()


init_db()


# ---------------------------------------------------------
# EXCEL YEDEKLEME VE GERİ YÜKLEME FONKSİYONLARI
# ---------------------------------------------------------
def export_all_to_excel():
    output = io.BytesIO()
    conn = get_db_connection()

    df_active = pd.read_sql_query(
        "SELECT * FROM work_orders WHERE is_archived = 0 ORDER BY id ASC", conn
    )
    df_archived = pd.read_sql_query(
        "SELECT * FROM work_orders WHERE is_archived = 1 ORDER BY id DESC", conn
    )
    df_ht = pd.read_sql_query(
        "SELECT * FROM heat_treatment ORDER BY id DESC", conn
    )
    df_wjg = pd.read_sql_query(
        "SELECT * FROM wjg_waterjet ORDER BY id DESC", conn
    )
    df_chat = pd.read_sql_query(
        "SELECT * FROM chat_messages ORDER BY id DESC", conn
    )

    conn.close()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_active.to_excel(writer, sheet_name="Aktif İş Planı", index=False)
        df_archived.to_excel(
            writer, sheet_name="İmalat Hafızası (Arşiv)", index=False
        )
        df_ht.to_excel(writer, sheet_name="Isıl İşlem Takip", index=False)
        df_wjg.to_excel(writer, sheet_name="Su Jeti (WJG) Takip", index=False)
        df_chat.to_excel(writer, sheet_name="Atölye Sohbeti", index=False)

    return output.getvalue()


def restore_db_from_excel(uploaded_file):
    try:
        xls = pd.ExcelFile(uploaded_file)
        conn = get_db_connection()
        cursor = conn.cursor()

        dfs_wo = []
        if "Aktif İş Planı" in xls.sheet_names:
            dfs_wo.append(pd.read_excel(xls, "Aktif İş Planı"))
        if "İmalat Hafızası (Arşiv)" in xls.sheet_names:
            dfs_wo.append(pd.read_excel(xls, "İmalat Hafızası (Arşiv)"))

        if dfs_wo:
            df_all_wo = pd.concat(dfs_wo, ignore_index=True)
            cursor.execute("DELETE FROM work_orders")
            df_all_wo.to_sql("work_orders", conn, if_exists="append", index=False)

        if "Isıl İşlem Takip" in xls.sheet_names:
            df_ht = pd.read_excel(xls, "Isıl İşlem Takip")
            cursor.execute("DELETE FROM heat_treatment")
            df_ht.to_sql("heat_treatment", conn, if_exists="append", index=False)

        if "Su Jeti (WJG) Takip" in xls.sheet_names:
            df_wjg = pd.read_excel(xls, "Su Jeti (WJG) Takip")
            cursor.execute("DELETE FROM wjg_waterjet")
            df_wjg.to_sql("wjg_waterjet", conn, if_exists="append", index=False)

        if "Atölye Sohbeti" in xls.sheet_names:
            df_chat = pd.read_excel(xls, "Atölye Sohbeti")
            cursor.execute("DELETE FROM chat_messages")
            df_chat.to_sql("chat_messages", conn, if_exists="append", index=False)

        conn.commit()
        conn.close()
        return True, "Yedek verileri başarıyla sisteme geri yüklendi!"
    except Exception as e:
        return False, f"Geri yükleme sırasında hata oluştu: {str(e)}"


def parse_drawing_files(path_str, name_str):
    if not path_str:
        return [], []
    try:
        paths = json.loads(path_str)
        names = json.loads(name_str)
        return paths, names
    except Exception:
        if ";" in str(path_str):
            return str(path_str).split(";"), str(name_str).split(";")
        return [str(path_str)], [str(name_str)]


def format_drawing_files(paths, names):
    return json.dumps(paths), json.dumps(names)


def create_zip_archive(paths, names):
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for p, n in zip(paths, names):
            if os.path.exists(p):
                zip_file.write(p, arcname=n)
    zip_buffer.seek(0)
    return zip_buffer.getvalue()


STATUS_OPTIONS = [
    "MALZEME SİPARİŞİ VERİLDİ",
    "DİK İŞLEME SIRADA",
    "DİK İŞLEMEDE",
    "CNC TORNA SIRADA",
    "CNC TORNADA",
    "TEL EREZYON SIRADA",
    "TEL EREZYONDA",
    "TAŞLAMA SIRADA",
    "TAŞLAMADA",
    "FREZE SIRADA",
    "FREZEDE",
    "TORNA SIRADA",
    "TORNADA",
    "ISIL İŞLEM ASTAŞ",
    "ISIL İŞLEM ALPHA",
    "ISIL İŞLEM VOESTALPINE",
    "KAPLAYAMA GİDECEK",
    "KAPLAMADA",
    "ELOKSAL KAPLAMA",
    "WJG SU JETİ",
    "ASM LAZER",
    "HAZIR",
]

MACHINE_OPTIONS = [
    "YOK / ATANMADI",
    "CNC Dik İşleme 1",
    "CNC Dik İşleme 2",
    "CNC Dik İşleme 3",
    "CNC Dik İşleme 4",
    "CNC Dik İşleme 5",
    "CNC Torna 1",
    "CNC Torna 2",
    "CNC Torna 3",
    "CNC Torna 4",
    "Tel Erezyon 1",
    "Tel Erezyon 2",
    "Tel Erezyon 3",
]

MATERIAL_DENSITIES = {
    "ÇELİK": 7.85,
    "KROM": 8.00,
    "ALÜMİNYUM": 2.70,
    "TUNGSTEN CARBIDE": 14.50,
    "DELRİN": 1.41,
    "TEFLON": 2.20,
    "KESTAMİD": 1.15,
    "ERTALYTE": 1.39,
    "PİRİNÇ": 8.50,
    "BRONZ": 8.80,
    "BAKIR": 8.96,
    "KURŞUN": 11.34,
}

HT_SUPPLIERS = [
    "ALPHA ISIL İŞLEM",
    "ASTAŞ ISIL İŞLEM",
    "ÇUKUROVA ISIL İŞLEM",
    "VOESTALPİNE ISIL İŞLEM",
]

HT_PROCESSES = [
    "SUBZERO+VAKUM",
    "VAKUM",
    "NİTRASYON",
    "İNDÜKSİYON",
    "SEMENTASYON",
]

HT_STATUSES = ["ISIL İŞLEMDE", "GELDİ / TAMAMLANDI", "FATURALANDI"]
WJG_STATUSES = ["KESİMDE / GÖNDERİLDİ", "GELDİ / TAMAMLANDI", "FATURA ALINDI"]


def parse_date(date_str):
    if not date_str:
        return None
    for fmt in (
        "%d.%m.%Y %H:%M:%S",
        "%d.%m.%Y %H:%M",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%d.%m.%Y",
    ):
        try:
            return datetime.strptime(str(date_str).strip(), fmt)
        except ValueError:
            pass
    return None


# ---------------------------------------------------------
# SOL MENÜ & LOGO & YEDEKLEME & GERİ YÜKLEME
# ---------------------------------------------------------
if os.path.exists("LOGO VE İSİM.JPG"):
    st.sidebar.image("LOGO VE İSİM.JPG", use_container_width=True)

st.sidebar.markdown("<div style='height: 5px;'></div>", unsafe_allow_html=True)

menu = st.sidebar.radio(
    "SİSTEM KATEGORİLERİ",
    [
        "📊 İş Planı (Canlı Tablo)",
        "🛠️ Tezgah Parkı Durumu",
        "🔥 Isıl İşlem Takip",
        "🌊 Su Jeti (WJG) Takip",
        "📚 İmalat Hafızası (Arşiv)",
        "💰 Akıllı Maliyet Hesabı",
        "💬 Atölye Sohbeti",
    ],
)

st.sidebar.markdown("---")

excel_backup = export_all_to_excel()
backup_filename = f"Esme_Makina_Yedek_{get_now().strftime('%Y%m%d_%H%M')}.xlsx"

st.sidebar.download_button(
    label="📊 Tüm Verileri Excel'e Aktar",
    data=excel_backup,
    file_name=backup_filename,
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    use_container_width=True,
    help=(
        "Tüm aktif işler, arşiv, ısıl işlem, su jeti ve sohbet geçmişini Excel"
        " dosyası olarak indirir."
    ),
)

with st.sidebar.expander("📥 Excel Yedeğinden Geri Yükle", expanded=False):
    uploaded_restore_file = st.file_uploader(
        "Geri yüklenecek Excel yedeğini seçin (.xlsx)",
        type=["xlsx"],
        key="restore_file_uploader",
    )
    if uploaded_restore_file is not None:
        if st.button(
            "⚠️ Yedeği Programa Yükle", type="primary", use_container_width=True
        ):
            success, msg = restore_db_from_excel(uploaded_restore_file)
            if success:
                st.success(msg)
                st.toast(msg, icon="🟢")
                st.rerun()
            else:
                st.error(msg)

st.sidebar.caption("Eşme Makina MES v6.8 • 2026")

# ---------------------------------------------------------
# ÜST LOGO & BAŞLIK ALANI (ANA SAYFA)
# ---------------------------------------------------------
col_header_logo, col_header_title = st.columns([1, 5])
with col_header_logo:
    if os.path.exists("LOGO VE İSİM.JPG"):
        st.image("LOGO VE İSİM.JPG", width=180)
with col_header_title:
    st.markdown("### ⚙️ EŞME MAKİNA MES - ÜRETİM & FASON YÖNETİM SİSTEMİ")
    st.caption(
        "Canlı İş Planlama, Tezgah Takibi, Isıl İşlem ve Otomatik Kayıtlı İmalat"
        " Hafızası"
    )

st.divider()

# ---------------------------------------------------------
# 1. İŞ PLANINI GÖRÜNTÜLE VE YÖNET
# ---------------------------------------------------------
if menu == "📊 İş Planı (Canlı Tablo)":
    st.markdown("## 📊 İŞ PLANI")
    st.caption(
        "Aktif müşteri siparişleri ve canlı imalat durumları. Yapılan tüm"
        " değişiklikler anında otomatik kaydedilir."
    )

    with st.expander("➕ **Yeni İş / Parça Siparişi Ekle**", expanded=False):
        with st.form("add_job_form", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                cust = st.text_input(
                    "Firma / Müşteri Adı *", placeholder="Ör: PHILSA A.Ş."
                )
                job = st.text_input(
                    "İş / Parça Adı *", placeholder="Ör: OKP4746.M PLATE"
                )
                mat = st.text_input(
                    "Malzeme Türü", placeholder="Ör: Ç.2379, 7075 Alüminyum", max_chars=20
                )
            with col2:
                dims = st.text_input(
                    "Malzeme Ölçüleri", placeholder="Ör: 30x45x85 mm", max_chars=15
                )
                supp = st.text_input(
                    "Malzeme Siparişi / Tedarikçi",
                    placeholder="Ör: ATLAS METAL, ALTEK METAL",
                )
                qty = st.number_input("Adet", min_value=1, value=10)
            with col3:
                heat = st.text_input(
                    "Isıl İşlem - Kaplama", placeholder="Ör: 56-58 HRC"
                )
                stt = st.selectbox("İlk Durum / İşlem", STATUS_OPTIONS)
                mac = st.selectbox("Bağlı Tezgah", MACHINE_OPTIONS)
                ddl = st.text_input(
                    "Termin Tarihi", placeholder="Ör: 15.09.2026 veya STOK"
                )

            initial_note = st.text_area(
                "İş Notları (Opsiyonel)", placeholder="İşle ilgili özel notlar..."
            )

            submitted = st.form_submit_button(
                "🚀 Siparişi Ekle ve Süreyi Başlat", type="primary"
            )
            if submitted and cust and job:
                now_str = get_now().strftime("%d.%m.%Y %H:%M")
                conn = get_db_connection()
                conn.execute(
                    """
                    INSERT INTO work_orders 
                    (customer, job_name, material, dimensions, supplier, quantity, heat_treatment, status, machine_name, deadline, notes, start_time, created_at, is_archived)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                """,
                    (
                        cust.upper().strip(),
                        job.strip(),
                        mat.strip(),
                        dims.strip(),
                        supp.strip(),
                        qty,
                        heat.strip(),
                        stt,
                        mac,
                        ddl.strip(),
                        initial_note.strip(),
                        now_str,
                        now_str,
                    ),
                )
                conn.commit()
                conn.close()
                st.toast("İş sipariş planına eklendi!", icon="🚀")
                st.rerun()

    conn = get_db_connection()
    df_active = pd.read_sql_query(
        "SELECT * FROM work_orders WHERE is_archived = 0 ORDER BY id ASC", conn
    )
    conn.close()

    if not df_active.empty:
        df_active["drawing_path"] = df_active["drawing_path"].fillna("")
        df_active["drawing_name"] = df_active["drawing_name"].fillna("")
        df_active["notes"] = df_active["notes"].fillna("")
        df_active["supplier"] = df_active["supplier"].fillna("")
        df_active["machine_name"] = df_active["machine_name"].fillna(
            "YOK / ATANMADI"
        )

        customers = df_active["customer"].unique()

        for customer in customers:
            cust_df = df_active[df_active["customer"] == customer].copy()

            st.markdown(
                f"""
                <div class="firm-header-band">
                    <span>🏢 {customer}</span>
                    <span class="count-badge">{len(cust_df)} Kalem İş</span>
                </div>
            """,
                unsafe_allow_html=True,
            )

            col_widths = [1.4, 0.9, 0.9, 0.6, 0.4, 0.9, 1.2, 0.9, 0.7, 1.3, 0.8]

            # Mobilde gizlenmesi için masaüstü başlıklarını container içine alıyoruz
            with st.container(key="job_header_row"):
                h1, h2, h3, h4, h5, h6, h7, h8, h9, h10, h11 = st.columns(col_widths)
                with h1:
                    st.caption("**İŞ / PARÇA ADI**")
                with h2:
                    st.caption("**MALZEME**")
                with h3:
                    st.caption("**TEDARİKÇİ**")
                with h4:
                    st.caption("**ÖLÇÜ**")
                with h5:
                    st.caption("**ADET**")
                with h6:
                    st.caption("**ISIL İŞLEM**")
                with h7:
                    st.caption("**DURUM**")
                with h8:
                    st.caption("**TEZGAH**")
                with h9:
                    st.caption("**TERMİN**")
                with h10:
                    st.caption("**NOT**")
                with h11:
                    st.caption("**İŞLEM**")

            for _, row in cust_df.iterrows():
                j_id = int(row["id"])

                with st.container(key=f"job_row_{j_id}"):
                    c1, c2, c3, c4, c5, c6, c7, c8, c9, c10, c11 = st.columns(col_widths)

                    # label_visibility="collapsed" KULLANMIYORUZ! Masaüstünde CSS ile gizlenecek, mobilde kart başlığı olacak.
                    with c1:
                        new_job = st.text_input(
                            "İş Adı",
                            value=row["job_name"],
                            key=f"job_{j_id}",
                        )
                    with c2:
                        new_mat = st.text_input(
                            "Malzeme",
                            value=row["material"],
                            max_chars=20,
                            key=f"mat_{j_id}",
                            placeholder="Malzeme",
                        )
                    with c3:
                        new_supp = st.text_input(
                            "Tedarikçi",
                            value=row["supplier"],
                            key=f"supp_{j_id}",
                            placeholder="Atlas, Altek vb.",
                        )
                    with c4:
                        new_dim = st.text_input(
                            "Ölçü",
                            value=row["dimensions"],
                            max_chars=15,
                            key=f"dim_{j_id}",
                            placeholder="Ölçü",
                        )
                    with c5:
                        new_qty = st.number_input(
                            "Adet",
                            value=int(row["quantity"]),
                            min_value=1,
                            key=f"qty_{j_id}",
                        )
                    with c6:
                        new_heat = st.text_input(
                            "Isıl İşlem",
                            value=row["heat_treatment"],
                            key=f"heat_{j_id}",
                            placeholder="Sertlik/Kaplama",
                        )
                    with c7:
                        idx_st = (
                            STATUS_OPTIONS.index(row["status"])
                            if row["status"] in STATUS_OPTIONS
                            else 0
                        )
                        new_st = st.selectbox(
                            "Durum",
                            STATUS_OPTIONS,
                            index=idx_st,
                            key=f"st_{j_id}",
                        )
                    with c8:
                        idx_m = (
                            MACHINE_OPTIONS.index(row["machine_name"])
                            if row["machine_name"] in MACHINE_OPTIONS
                            else 0
                        )
                        new_mac = st.selectbox(
                            "Tezgah",
                            MACHINE_OPTIONS,
                            index=idx_m,
                            key=f"mac_{j_id}",
                        )
                    with c9:
                        new_ddl = st.text_input(
                            "Termin",
                            value=row["deadline"],
                            key=f"ddl_{j_id}",
                            placeholder="STOK / Tarih",
                        )
                    with c10:
                        new_note = st.text_input(
                            "Not",
                            value=row["notes"],
                            key=f"note_{j_id}",
                            placeholder="Not",
                        )

                    with c11:
                        paths, names = parse_drawing_files(
                            row["drawing_path"], row["drawing_name"]
                        )
                        has_files = len(paths) > 0 and any(os.path.exists(p) for p in paths)

                        # İşlem butonlarını mobilde hizalamak için container kullanıyoruz
                        with st.container(key=f"job_actions_{j_id}"):
                            ic1, ic2, ic3 = st.columns(3)

                            with ic1:
                                with st.popover("📤", help="Teknik Resim / Dosyalar Yükle"):
                                    up_files = st.file_uploader(
                                        "Dosyaları Seçin",
                                        type=None,
                                        accept_multiple_files=True,
                                        key=f"up_{j_id}",
                                        label_visibility="collapsed",
                                    )
                                    if up_files:
                                        new_paths, new_names = [], []
                                        for up_file in up_files:
                                            orig_name = str(up_file.name)
                                            s_filename = f"job_{j_id}_{orig_name}"
                                            s_path = os.path.join("uploads", s_filename)
                                            with open(s_path, "wb") as f:
                                                f.write(up_file.getbuffer())
                                            new_paths.append(s_path)
                                            new_names.append(orig_name)

                                        path_json, name_json = format_drawing_files(
                                            new_paths, new_names
                                        )
                                        conn = get_db_connection()
                                        conn.execute(
                                            "UPDATE work_orders SET drawing_path = ?, drawing_name = ?"
                                            " WHERE id = ?",
                                            (path_json, name_json, j_id),
                                        )
                                        conn.commit()
                                        conn.close()
                                        st.toast(
                                            f"{len(new_paths)} dosya başarıyla yüklendi!", icon="🟢"
                                        )
                                        st.rerun()

                            with ic2:
                                if has_files:
                                    valid_paths = [p for p in paths if os.path.exists(p)]
                                    valid_names = [
                                        n for p, n in zip(paths, names) if os.path.exists(p)
                                    ]

                                    if len(valid_paths) == 1:
                                        with open(valid_paths[0], "rb") as f_bytes:
                                            st.download_button(
                                                "📥",
                                                f_bytes.read(),
                                                file_name=valid_names[0],
                                                key=f"dl_{j_id}",
                                                help=f"İndir ({valid_names[0]})",
                                            )
                                    else:
                                        zip_bytes = create_zip_archive(valid_paths, valid_names)
                                        zip_file_name = f"{row['job_name']}_dosyalar.zip"
                                        st.download_button(
                                            "📥",
                                            zip_bytes,
                                            file_name=zip_file_name,
                                            mime="application/zip",
                                            key=f"dl_{j_id}",
                                            help=(
                                                f"Tüm {len(valid_paths)} dosyayı ZIP olarak indir"
                                            ),
                                        )
                                else:
                                    if st.button("📥", key=f"nodl_{j_id}", help="Yüklü dosya yok"):
                                        st.toast(
                                            "Bu iş için yüklü teknik resim/dosya bulunmuyor.", icon="ℹ️"
                                        )

                            with ic3:
                                if st.button("🗑️", key=f"del_{j_id}", help="Bu işi sil"):
                                    conn = get_db_connection()
                                    conn.execute("DELETE FROM work_orders WHERE id = ?", (j_id,))
                                    conn.commit()
                                    conn.close()
                                    st.toast("İş silindi!", icon="🗑️")
                                    st.rerun()

                if (
                    new_job != row["job_name"]
                    or new_mat != row["material"]
                    or new_supp != row["supplier"]
                    or new_dim != row["dimensions"]
                    or new_qty != row["quantity"]
                    or new_heat != row["heat_treatment"]
                    or new_st != row["status"]
                    or new_mac != row["machine_name"]
                    or new_ddl != row["deadline"]
                    or new_note != row["notes"]
                ):

                    conn = get_db_connection()
                    if new_st == "HAZIR":
                        end_now_dt = get_now()
                        end_now_str = end_now_dt.strftime("%d.%m.%Y %H:%M")
                        duration_calc_str = "Belirtilmedi"
                        if row["start_time"]:
                            start_dt = parse_date(row["start_time"])
                            if start_dt:
                                diff = end_now_dt - start_dt
                                days = diff.days
                                hours, remainder = divmod(diff.seconds, 3600)
                                minutes, _ = divmod(remainder, 60)
                                duration_calc_str = (
                                    f"{days} Gün {hours} Saat {minutes} Dk"
                                    if days > 0
                                    else f"{hours} Saat {minutes} Dk"
                                )

                        conn.execute(
                            """
                            UPDATE work_orders 
                            SET job_name=?, material=?, supplier=?, dimensions=?, quantity=?, heat_treatment=?, status='HAZIR / TAMAMLANDI', machine_name='YOK / ATANMADI', deadline=?, notes=?, is_archived=1, end_time=?, duration_str=?
                            WHERE id=?
                        """,
                            (
                                new_job,
                                new_mat,
                                new_supp,
                                new_dim,
                                new_qty,
                                new_heat,
                                new_ddl,
                                new_note,
                                end_now_str,
                                duration_calc_str,
                                j_id,
                            ),
                        )
                        conn.commit()
                        conn.close()
                        st.toast(
                            "🎉 Parça 'HAZIR' durumuna getirildi ve arşive aktarıldı!",
                            icon="🎉",
                        )
                        st.rerun()
                    else:
                        conn.execute(
                            """
                            UPDATE work_orders
                            SET job_name=?, material=?, supplier=?, dimensions=?, quantity=?, heat_treatment=?, status=?, machine_name=?, deadline=?, notes=?
                            WHERE id=?
                        """,
                            (
                                new_job,
                                new_mat,
                                new_supp,
                                new_dim,
                                new_qty,
                                new_heat,
                                new_st,
                                new_mac,
                                new_ddl,
                                new_note,
                                j_id,
                            ),
                        )
                        conn.commit()
                        conn.close()
                        st.toast("Değişiklikler otomatik kaydedildi", icon="💾")
                        st.rerun()

    else:
        st.info(
            "İş planında henüz aktif iş bulunmuyor. Yukarıdaki formdan yeni iş"
            " ekleyebilirsiniz."
        )

# ---------------------------------------------------------
# 2. TEZGAH PARKI DURUMU
# ---------------------------------------------------------
elif menu == "🛠️ Tezgah Parkı Durumu":
    st.markdown("## 🛠️ Tezgah Parkı Anlık Durum Panosu")
    st.caption(
        "İş planında 'BAĞLI TEZGAH' olarak atadığınız makinelerin canlı yük"
        " durumu ve iş bağlanma zamanları."
    )

    MACHINES = {
        "CNC Dik İşleme": [f"CNC Dik İşleme {i}" for i in range(1, 6)],
        "CNC Torna": [f"CNC Torna {i}" for i in range(1, 5)],
        "Tel Erezyon": [f"Tel Erezyon {i}" for i in range(1, 4)],
    }

    conn = get_db_connection()
    df_active = pd.read_sql_query(
        "SELECT * FROM work_orders WHERE is_archived = 0", conn
    )
    conn.close()

    assigned_jobs = {}
    if not df_active.empty and "machine_name" in df_active.columns:
        for _, r in df_active.iterrows():
            m_name = r["machine_name"]
            if m_name and m_name != "YOK / ATANMADI":
                conn_time = (
                    r["start_time"] or r["created_at"] or "Tarih Belirtilmedi"
                )
                assigned_jobs[m_name] = {
                    "text": f"🏢 **{r['customer']}** - {r['job_name']}",
                    "time": conn_time,
                }

    total_machines = 12
    busy_count = len(assigned_jobs)
    occupancy_rate = int((busy_count / total_machines) * 100)

    m1, m2, m3 = st.columns(3)
    m1.metric("Toplam Tezgah Parkı", f"{total_machines} Adet")
    m2.metric("Bağlı Çalışan Tezgah", f"{busy_count} Adet")
    m3.metric("Atölye Anlık Yükü", f"%{occupancy_rate}")

    st.progress(occupancy_rate / 100)
    st.divider()

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            "<div class='custom-card'><h4>CNC Dik İşleme (5 Adet)</h4>",
            unsafe_allow_html=True,
        )
        for m in MACHINES["CNC Dik İşleme"]:
            if m in assigned_jobs:
                st.markdown(f"**{m}**: 🔴 **ÇALIŞIYOR**")
                st.caption(f"Bağlı İş: {assigned_jobs[m]['text']}")
                st.caption(f"🕒 **Bağlanma Zamanı:** {assigned_jobs[m]['time']}")
            else:
                st.markdown(f"**{m}**: 🟢 **BOŞ / HAZIR**")
            st.write("---")
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown(
            "<div class='custom-card'><h4>CNC Torna (4 Adet)</h4>",
            unsafe_allow_html=True,
        )
        for m in MACHINES["CNC Torna"]:
            if m in assigned_jobs:
                st.markdown(f"**{m}**: 🔴 **ÇALIŞIYOR**")
                st.caption(f"Bağlı İş: {assigned_jobs[m]['text']}")
                st.caption(f"🕒 **Bağlanma Zamanı:** {assigned_jobs[m]['time']}")
            else:
                st.markdown(f"**{m}**: 🟢 **BOŞ / HAZIR**")
            st.write("---")
        st.markdown("</div>", unsafe_allow_html=True)

    with c3:
        st.markdown(
            "<div class='custom-card'><h4>Tel Erezyon (3 Adet)</h4>",
            unsafe_allow_html=True,
        )
        for m in MACHINES["Tel Erezyon"]:
            if m in assigned_jobs:
                st.markdown(f"**{m}**: 🔴 **ÇALIŞIYOR**")
                st.caption(f"Bağlı İş: {assigned_jobs[m]['text']}")
                st.caption(f"🕒 **Bağlanma Zamanı:** {assigned_jobs[m]['time']}")
            else:
                st.markdown(f"**{m}**: 🟢 **BOŞ / HAZIR**")
            st.write("---")
        st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------
# 3. ISIL İŞLEM TAKİP MODÜLÜ
# ---------------------------------------------------------
elif menu == "🔥 Isıl İşlem Takip":
    st.markdown("## 🔥 Isıl İşlem Takip Modülü")
    st.caption(
        "Fason ısıl işleme gönderilen malzemelerin firma, sertlik, kg ve fatura"
        " durum takibi."
    )

    with st.expander("➕ **Yeni Isıl İşlem Gönderim Kaydı Ekle**", expanded=False):
        with st.form("add_ht_form", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                ht_date = st.text_input(
                    "Tarih *", value=get_now().strftime("%d.%m.%Y")
                )
                ht_supplier = st.selectbox("Isıl İşlem Firması *", HT_SUPPLIERS)
                ht_customer = st.text_input(
                    "Müşteri Firma Adı *", placeholder="Ör: PROFACE, DENTAŞ"
                )
            with col2:
                ht_prod = st.text_input(
                    "Ürün Kodu ve Adı *", placeholder="Ör: CUTTER BIÇAĞI MALAFASI"
                )
                ht_qty = st.number_input("Adet", min_value=1, value=1)
                ht_mat = st.text_input("Malzeme Cinsi", value="Ç.2379")
            with col3:
                ht_hard = st.text_input("Hedef Sertlik", value="60-62 HRC")
                ht_weight = st.number_input(
                    "Ağırlık (KG)", min_value=0.0, value=5.0, step=0.5
                )
                ht_process = st.selectbox("İşlem Türü", HT_PROCESSES)

            col_a, col_b = st.columns(2)
            with col_a:
                ht_status = st.selectbox("İşlem Durumu", HT_STATUSES)
            with col_b:
                ht_inv = st.text_input(
                    "Fatura Kontrolü / Not", placeholder="Ör: 3770+KDV veya Bekliyor"
                )

            submitted = st.form_submit_button(
                "🔥 Isıl İşlem Kaydını Ekle", type="primary"
            )
            if submitted and ht_customer and ht_prod:
                now_s = get_now().strftime("%d.%m.%Y %H:%M")
                conn = get_db_connection()
                conn.execute(
                    """
                    INSERT INTO heat_treatment
                    (sent_date, supplier_firm, customer, product_code_name, quantity, material, hardness, weight_kg, process_type, status, invoice_info, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        ht_date.strip(),
                        ht_supplier,
                        ht_customer.upper().strip(),
                        ht_prod.strip(),
                        ht_qty,
                        ht_mat.strip(),
                        ht_hard.strip(),
                        ht_weight,
                        ht_process,
                        ht_status,
                        ht_inv.strip(),
                        now_s,
                    ),
                )
                conn.commit()
                conn.close()
                st.toast("Isıl işlem kaydı başarıyla eklendi!", icon="🔥")
                st.rerun()

    conn = get_db_connection()
    df_ht = pd.read_sql_query(
        "SELECT * FROM heat_treatment ORDER BY id DESC", conn
    )
    conn.close()

    if not df_ht.empty:
        st.subheader("📋 Isıl İşlem Kayıtları Tablosu")

        display_ht = df_ht[[
            "id",
            "sent_date",
            "supplier_firm",
            "customer",
            "product_code_name",
            "quantity",
            "material",
            "hardness",
            "weight_kg",
            "process_type",
            "status",
            "invoice_info",
        ]].copy()

        edited_ht = st.data_editor(
            display_ht,
            key="ht_editor",
            use_container_width=True,
            hide_index=True,
            column_order=[
                "sent_date",
                "supplier_firm",
                "customer",
                "product_code_name",
                "quantity",
                "material",
                "hardness",
                "weight_kg",
                "process_type",
                "status",
                "invoice_info",
            ],
            column_config={
                "sent_date": st.column_config.TextColumn("TARİH", width="small"),
                "supplier_firm": st.column_config.SelectboxColumn(
                    "ISIL İŞLEM FİRMASI",
                    options=HT_SUPPLIERS,
                    required=True,
                    width="medium",
                ),
                "customer": st.column_config.TextColumn(
                    "FİRMA ADI", width="medium"
                ),
                "product_code_name": st.column_config.TextColumn(
                    "ÜRÜN KODU VE ADI", width="large"
                ),
                "quantity": st.column_config.NumberColumn("ADET", width="small"),
                "material": st.column_config.TextColumn("MALZEME", width="small"),
                "hardness": st.column_config.TextColumn("SERTLİK", width="small"),
                "weight_kg": st.column_config.NumberColumn("KG", width="small"),
                "process_type": st.column_config.SelectboxColumn(
                    "İŞLEM", options=HT_PROCESSES, width="medium"
                ),
                "status": st.column_config.SelectboxColumn(
                    "DURUM", options=HT_STATUSES, width="medium"
                ),
                "invoice_info": st.column_config.TextColumn(
                    "FATURA KONTROLÜ", width="medium"
                ),
            },
        )

        if not edited_ht.equals(display_ht):
            conn = get_db_connection()
            for _, row in edited_ht.iterrows():
                conn.execute(
                    """
                    UPDATE heat_treatment
                    SET sent_date=?, supplier_firm=?, customer=?, product_code_name=?, quantity=?, material=?, hardness=?, weight_kg=?, process_type=?, status=?, invoice_info=?
                    WHERE id=?
                """,
                    (
                        row["sent_date"],
                        row["supplier_firm"],
                        row["customer"],
                        row["product_code_name"],
                        row["quantity"],
                        row["material"],
                        row["hardness"],
                        row["weight_kg"],
                        row["process_type"],
                        row["status"],
                        row["invoice_info"],
                        row["id"],
                    ),
                )
            conn.commit()
            conn.close()
            st.toast("Isıl işlem tablosu otomatik kaydedildi", icon="💾")
            st.rerun()

        ht_list = [
            f"{r['id']} - {r['customer']} ({r['product_code_name']})"
            for _, r in df_ht.iterrows()
        ]
        sel_ht_del = st.selectbox(
            "Silinecek Isıl İşlem Kaydını Seçin:",
            ["Seçiniz..."] + ht_list,
            key="sel_ht_del",
        )
        if (
            st.button("🗑️ Seçili Isıl İşlem Kaydını Sil")
            and sel_ht_del != "Seçiniz..."
        ):
            del_id = int(sel_ht_del.split(" - ")[0])
            conn = get_db_connection()
            conn.execute("DELETE FROM heat_treatment WHERE id = ?", (del_id,))
            conn.commit()
            conn.close()
            st.toast("Isıl işlem kaydı silindi!", icon="🗑️")
            st.rerun()
    else:
        st.info("Henüz eklenmiş ısıl işlem kaydı bulunmuyor.")

# ---------------------------------------------------------
# 4. SU JETİ (WJG) TAKİP MODÜLÜ
# ---------------------------------------------------------
elif menu == "🌊 Su Jeti (WJG) Takip":
    st.markdown("## 🌊 Su Jeti (WJG) Takip Modülü")
    st.caption(
        "Su jetinde kesilen parçaların adet, ölçü, birim fiyat ve fatura durum"
        " takibi."
    )

    with st.expander("➕ **Yeni Su Jeti (WJG) Kesim Kaydı Ekle**", expanded=False):
        with st.form("add_wjg_form", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                wjg_date = st.text_input(
                    "Kesim Tarihi *", value=get_now().strftime("%d.%m.%Y")
                )
                wjg_customer = st.text_input(
                    "Firma Adı *", placeholder="Ör: ANKUTSAN, OMKAR"
                )
                wjg_part = st.text_input(
                    "Parça Tanımı *", placeholder="Ör: GAGALI SLOT BIÇAĞI"
                )
            with col2:
                wjg_code = st.text_input("Parça Kodu", placeholder="Ör: LMC231")
                wjg_dims = st.text_input("Ölçü (mm)", placeholder="Ör: 231x48x10")
                wjg_ord_qty = st.number_input("Sipariş Adedi", min_value=1, value=10)
            with col3:
                wjg_rec_qty = st.number_input("Gelen Adet", min_value=0, value=10)
                wjg_price = st.number_input(
                    "Birim Fiyat (TL)", min_value=0.0, value=150.0, step=10.0
                )
                wjg_st = st.selectbox("Kesim Durumu", WJG_STATUSES)

            wjg_inv = st.text_input(
                "Fatura / Açıklama Notu", placeholder="Ör: Fatura Bekleniyor"
            )

            submitted_wjg = st.form_submit_button(
                "🌊 Su Jeti Kesim Kaydını Ekle", type="primary"
            )
            if submitted_wjg and wjg_customer and wjg_part:
                now_s = get_now().strftime("%d.%m.%Y %H:%M")
                conn = get_db_connection()
                conn.execute(
                    """
                    INSERT INTO wjg_waterjet
                    (sent_date, customer, part_name, part_code, dimensions, order_qty, received_qty, unit_price, invoice_info, status, notes, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '', ?)
                """,
                    (
                        wjg_date.strip(),
                        wjg_customer.upper().strip(),
                        wjg_part.strip(),
                        wjg_code.strip(),
                        wjg_dims.strip(),
                        wjg_ord_qty,
                        wjg_rec_qty,
                        wjg_price,
                        wjg_inv.strip(),
                        wjg_st,
                        now_s,
                    ),
                )
                conn.commit()
                conn.close()
                st.toast("Su Jeti kesim kaydı eklendi!", icon="🌊")
                st.rerun()

    conn = get_db_connection()
    df_wjg = pd.read_sql_query(
        "SELECT * FROM wjg_waterjet ORDER BY id DESC", conn
    )
    conn.close()

    if not df_wjg.empty:
        st.subheader("📋 Su Jeti (WJG) Kesim Kayıtları Tablosu")

        display_wjg = df_wjg[[
            "id",
            "sent_date",
            "customer",
            "part_name",
            "part_code",
            "dimensions",
            "order_qty",
            "received_qty",
            "unit_price",
            "status",
            "invoice_info",
        ]].copy()

        edited_wjg = st.data_editor(
            display_wjg,
            key="wjg_editor",
            use_container_width=True,
            hide_index=True,
            column_order=[
                "sent_date",
                "customer",
                "part_name",
                "part_code",
                "dimensions",
                "order_qty",
                "received_qty",
                "unit_price",
                "status",
                "invoice_info",
            ],
            column_config={
                "sent_date": st.column_config.TextColumn("TARİH", width="small"),
                "customer": st.column_config.TextColumn(
                    "FİRMA ADI", width="medium"
                ),
                "part_name": st.column_config.TextColumn(
                    "PARÇA TANIMI", width="medium"
                ),
                "part_code": st.column_config.TextColumn("KODU", width="small"),
                "dimensions": st.column_config.TextColumn("ÖLÇÜ", width="small"),
                "order_qty": st.column_config.NumberColumn(
                    "SİP. ADET", width="small"
                ),
                "received_qty": st.column_config.NumberColumn(
                    "GELEN ADET", width="small"
                ),
                "unit_price": st.column_config.NumberColumn(
                    "BİRİM FİYAT (₺)", width="small", format="%.2f ₺"
                ),
                "status": st.column_config.SelectboxColumn(
                    "DURUM", options=WJG_STATUSES, width="medium"
                ),
                "invoice_info": st.column_config.TextColumn(
                    "FATURA / NOT", width="medium"
                ),
            },
        )

        if not edited_wjg.equals(display_wjg):
            conn = get_db_connection()
            for _, row in edited_wjg.iterrows():
                conn.execute(
                    """
                    UPDATE wjg_waterjet
                    SET sent_date=?, customer=?, part_name=?, part_code=?, dimensions=?, order_qty=?, received_qty=?, unit_price=?, status=?, invoice_info=?
                    WHERE id=?
                """,
                    (
                        row["sent_date"],
                        row["customer"],
                        row["part_name"],
                        row["part_code"],
                        row["dimensions"],
                        row["order_qty"],
                        row["received_qty"],
                        row["unit_price"],
                        row["status"],
                        row["invoice_info"],
                        row["id"],
                    ),
                )
            conn.commit()
            conn.close()
            st.toast("Su jeti tablosu otomatik kaydedildi", icon="💾")
            st.rerun()

        wjg_list = [
            f"{r['id']} - {r['customer']} ({r['part_name']})"
            for _, r in df_wjg.iterrows()
        ]
        sel_wjg_del = st.selectbox(
            "Silinecek Kesim Kaydını Seçin:",
            ["Seçiniz..."] + wjg_list,
            key="sel_wjg_del",
        )
        if (
            st.button("🗑️ Seçili Su Jeti Kaydını Sil")
            and sel_wjg_del != "Seçiniz..."
        ):
            del_id = int(sel_wjg_del.split(" - ")[0])
            conn = get_db_connection()
            conn.execute("DELETE FROM wjg_waterjet WHERE id = ?", (del_id,))
            conn.commit()
            conn.close()
            st.toast("Su jeti kaydı silindi!", icon="🗑️")
            st.rerun()
    else:
        st.info("Henüz eklenmiş su jeti kesim kaydı bulunmuyor.")

# ---------------------------------------------------------
# 5. İMALAT HAFIZASI (ARŞİV) MODÜLÜ
# ---------------------------------------------------------
elif menu == "📚 İmalat Hafızası (Arşiv)":
    st.markdown("## 📚 İMALAT HAFIZASI (GEÇMİŞ SİPARİŞ ARŞİVİ)")
    st.caption(
        "Tamamlanan işlerin imalat süreleri, fiyatları, notları ve teknik resim"
        " hafızası."
    )

    conn = get_db_connection()
    df_arch = pd.read_sql_query(
        "SELECT * FROM work_orders WHERE is_archived = 1 ORDER BY id DESC", conn
    )
    conn.close()

    if not df_arch.empty:
        col_search, col_filter = st.columns([2, 1])
        with col_search:
            search_query = st.text_input(
                "🔍 Arşivde Arama Yap (Parça Adı, Müşteri, Malzeme)",
                placeholder="Ör: OKP4746, PHILSA...",
            )
        with col_filter:
            cust_filter = st.selectbox(
                "Müşteri Filtresi", ["TÜMÜ"] + list(df_arch["customer"].unique())
            )

        filtered_df = df_arch.copy()
        if search_query:
            q = search_query.lower()
            filtered_df = filtered_df[
                filtered_df["job_name"].str.lower().str.contains(q, na=False)
                | filtered_df["customer"].str.lower().str.contains(q, na=False)
                | filtered_df["material"].str.lower().str.contains(q, na=False)
            ]
        if cust_filter != "TÜMÜ":
            filtered_df = filtered_df[filtered_df["customer"] == cust_filter]

        st.subheader(f"🗂️ Bulunan Arşiv Kaydı: {len(filtered_df)} Adet")

        for _, r in filtered_df.iterrows():
            arch_id = int(r["id"])
            with st.expander(
                f"📦 **{r['customer']}** | {r['job_name']} - ({r['quantity']} Adet) -"
                f" Tamamlanma: {r['end_time'] or 'Belirtilmedi'}"
            ):
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.write(f"**Malzeme:** {r['material']}")
                    st.write(f"**Tedarikçi:** {r['supplier'] or 'Belirtilmedi'}")
                    st.write(f"**Ölçü:** {r['dimensions']}")
                with c2:
                    st.write(f"**Isıl İşlem:** {r['heat_treatment']}")
                    st.write(f"**Başlangıç:** {r['start_time']}")
                    st.write(f"**Bitiş:** {r['end_time']}")
                with c3:
                    st.write(f"**Geçen Toplam Süre:** {r['duration_str']}")
                    st.write(f"**Kayıtlı Fiyat:** {r['price'] or 0.0:.2f} ₺")

                st.markdown("---")

                st.markdown("##### ⏱️ İmalat Süreleri, Fiyat & Not Düzenleme")
                with st.form(key=f"edit_arch_form_{arch_id}"):
                    ac1, ac2, ac3, ac4, ac5 = st.columns(5)
                    with ac1:
                        u_dik = st.number_input(
                            "Dik İşleme Süresi (Dk)",
                            min_value=0.0,
                            value=float(r["dik_time"] or 0.0),
                            step=1.0,
                            key=f"arch_dik_{arch_id}",
                        )
                    with ac2:
                        u_torna = st.number_input(
                            "CNC Torna Süresi (Dk)",
                            min_value=0.0,
                            value=float(r["torna_time"] or 0.0),
                            step=1.0,
                            key=f"arch_torna_{arch_id}",
                        )
                    with ac3:
                        u_tel = st.number_input(
                            "Tel Erezyon Süresi (Dk)",
                            min_value=0.0,
                            value=float(r["tel_time"] or 0.0),
                            step=1.0,
                            key=f"arch_tel_{arch_id}",
                        )
                    with ac4:
                        u_uni = st.number_input(
                            "Üniversal Tezgah (Dk)",
                            min_value=0.0,
                            value=float(r["uni_time"] or 0.0),
                            step=1.0,
                            key=f"arch_uni_{arch_id}",
                        )
                    with ac5:
                        u_price = st.number_input(
                            "Mevcut İş Fiyatı (₺)",
                            min_value=0.0,
                            value=float(r["price"] or 0.0),
                            step=1.0,
                            key=f"arch_price_{arch_id}",
                        )

                    u_notes = st.text_area(
                        "İş / İmalat Notları",
                        value=str(r["notes"] or ""),
                        key=f"arch_notes_{arch_id}",
                    )

                    save_arch_btn = st.form_submit_button(
                        "💾 Arşiv Bilgilerini Güncelle ve Kaydet", type="primary"
                    )
                    if save_arch_btn:
                        conn = get_db_connection()
                        conn.execute(
                            """
                            UPDATE work_orders
                            SET dik_time=?, torna_time=?, tel_time=?, uni_time=?, price=?, notes=?
                            WHERE id=?
                        """,
                            (
                                u_dik,
                                u_torna,
                                u_tel,
                                u_uni,
                                u_price,
                                u_notes.strip(),
                                arch_id,
                            ),
                        )
                        conn.commit()
                        conn.close()
                        st.toast("Arşiv bilgileri başarıyla güncellendi!", icon="💾")
                        st.rerun()

                st.markdown("---")

                paths, names = parse_drawing_files(r["drawing_path"], r["drawing_name"])
                valid_paths = [p for p in paths if os.path.exists(p)]
                valid_names = [n for p, n in zip(paths, names) if os.path.exists(p)]

                if valid_paths:
                    if len(valid_paths) == 1:
                        with open(valid_paths[0], "rb") as f_bytes:
                            st.download_button(
                                f"📥 Teknik Resim İndir ({valid_names[0]})",
                                f_bytes.read(),
                                file_name=valid_names[0],
                                key=f"arch_dl_{arch_id}",
                            )
                    else:
                        zip_bytes = create_zip_archive(valid_paths, valid_names)
                        st.download_button(
                            "📥 Tüm Teknik Resimleri ZIP Olarak İndir"
                            f" ({len(valid_paths)} Dosya)",
                            zip_bytes,
                            file_name=f"{r['job_name']}_arhiv_dosyalar.zip",
                            mime="application/zip",
                            key=f"arch_dl_{arch_id}",
                        )

                col_b1, col_b2 = st.columns([1, 1])
                with col_b1:
                    if st.button("🔄 İş Planına Geri Taşı", key=f"restore_{arch_id}"):
                        conn = get_db_connection()
                        conn.execute(
                            "UPDATE work_orders SET is_archived = 0, status = 'DİK İŞLEME"
                            " SIRADA' WHERE id = ?",
                            (arch_id,),
                        )
                        conn.commit()
                        conn.close()
                        st.toast("İş tekrar canlı plana aktarıldı!", icon="🔄")
                        st.rerun()
                with col_b2:
                    if st.button("🗑️ Arşivden Kalıcı Sil", key=f"arch_del_{arch_id}"):
                        conn = get_db_connection()
                        conn.execute("DELETE FROM work_orders WHERE id = ?", (arch_id,))
                        conn.commit()
                        conn.close()
                        st.toast("Arşiv kaydı silindi!", icon="🗑️")
                        st.rerun()
    else:
        st.info("Arşivde henüz tamamlanmış iş bulunmuyor.")

# ---------------------------------------------------------
# 6. AKILLI MALİYET HESABI
# ---------------------------------------------------------
elif menu == "💰 Akıllı Maliyet Hesabı":
    st.markdown("## 💰 Akıllı Parça & İşleme Maliyet Hesaplayıcı")
    st.caption(
        "Hammadde ağırlığı, tezgah saat ücretleri ve fason giderleri ile hızlı"
        " teklif maliyeti oluşturun."
    )

    col_mat, col_mach = st.columns([1, 1], gap="large")

    with col_mat:
        st.markdown(
            "<div class='custom-card'><h3>⚖️ 1. Hammadde & Ağırlık Hesabı</h3>",
            unsafe_allow_html=True,
        )

        shape = st.selectbox(
            "Geometri / Kesit Türü",
            [
                "Dolu Mil (Silindir)",
                "Lama / Blok (L x W x H)",
                "Boru (Dış D - İç D - Boy)",
            ],
        )
        mat_type = st.selectbox("Malzeme Türü", list(MATERIAL_DENSITIES.keys()))
        density = MATERIAL_DENSITIES[mat_type]
        st.info(f"Seçilen Malzeme Özkütlesi: **{density} g/cm³**")

        weight_kg = 0.0

        if shape == "Dolu Mil (Silindir)":
            dia = st.number_input(
                "Çap (mm)", min_value=1.0, value=50.0, step=1.0, key="cost_dia"
            )
            length = st.number_input(
                "Boy (mm)", min_value=1.0, value=100.0, step=1.0, key="cost_len"
            )
            vol_cm3 = (math.pi * ((dia / 2) ** 2) * length) / 1000
            weight_kg = (vol_cm3 * density) / 1000

        elif shape == "Lama / Blok (L x W x H)":
            l = st.number_input(
                "Uzunluk - L (mm)",
                min_value=1.0,
                value=100.0,
                step=1.0,
                key="cost_l",
            )
            w = st.number_input(
                "Genişlik - W (mm)", min_value=1.0, value=50.0, step=1.0, key="cost_w"
            )
            h = st.number_input(
                "Yükseklik/Kalınlık - H (mm)",
                min_value=1.0,
                value=20.0,
                step=1.0,
                key="cost_h",
            )
            vol_cm3 = (l * w * h) / 1000
            weight_kg = (vol_cm3 * density) / 1000

        elif shape == "Boru (Dış D - İç D - Boy)":
            out_d = st.number_input(
                "Dış Çap (mm)", min_value=1.0, value=60.0, step=1.0, key="cost_out_d"
            )
            in_d = st.number_input(
                "İç Çap (mm)", min_value=0.0, value=40.0, step=1.0, key="cost_in_d"
            )
            l = st.number_input(
                "Boy (mm)", min_value=1.0, value=100.0, step=1.0, key="cost_pipe_l"
            )
            vol_cm3 = (
                math.pi * (((out_d / 2) ** 2) - ((in_d / 2) ** 2)) * l
            ) / 1000
            weight_kg = (vol_cm3 * density) / 1000
        
        st.success(f"Hesaplanan Ağırlık: **{weight_kg:.3f} KG**")
        
        kg_price = st.number_input("Malzeme KG Fiyatı (₺)", min_value=0.0, value=150.0, step=10.0)
        total_mat_cost = weight_kg * kg_price
        st.info(f"Hammadde Maliyeti: **{total_mat_cost:.2f} ₺**")

    with col_mach:
        st.markdown(
            "<div class='custom-card'><h3>⚙️ 2. İşçilik & Operasyon Maliyeti</h3>",
            unsafe_allow_html=True,
        )
        
        dik_saat = st.number_input("Dik İşleme Süresi (Saat)", min_value=0.0, value=0.0, step=0.5)
        dik_ucret = st.number_input("Dik İşleme Saat Ücreti (₺)", min_value=0.0, value=1500.0, step=100.0)
        
        torna_saat = st.number_input("CNC Torna Süresi (Saat)", min_value=0.0, value=0.0, step=0.5)
        torna_ucret = st.number_input("CNC Torna Saat Ücreti (₺)", min_value=0.0, value=1200.0, step=100.0)
        
        tel_saat = st.number_input("Tel Erezyon Süresi (Saat)", min_value=0.0, value=0.0, step=0.5)
        tel_ucret = st.number_input("Tel Erezyon Saat Ücreti (₺)", min_value=0.0, value=800.0, step=50.0)
        
        fason_gider = st.number_input("Isıl İşlem / Kaplama Fason Gideri (₺)", min_value=0.0, value=0.0, step=100.0)
        
        total_mach_cost = (dik_saat * dik_ucret) + (torna_saat * torna_ucret) + (tel_saat * tel_ucret) + fason_gider
        st.info(f"Toplam İşçilik/Fason Maliyeti: **{total_mach_cost:.2f} ₺**")
        
    st.divider()
    
    grand_total = total_mat_cost + total_mach_cost
    st.markdown(f"<h2 style='text-align: center; color: #1e293b;'>Genel Toplam Maliyet: <span style='color: #16a34a;'>{grand_total:.2f} ₺</span></h2>", unsafe_allow_html=True)
    
    kar_marji = st.slider("Hedef Kar Marjı (%)", min_value=0, max_value=200, value=40, step=5)
    satis_fiyati = grand_total * (1 + (kar_marji / 100))
    st.markdown(f"<h1 style='text-align: center; color: #0f172a;'>Önerilen Satış Fiyatı: <span style='color: #2563eb;'>{satis_fiyati:.2f} ₺</span></h1>", unsafe_allow_html=True)

# ---------------------------------------------------------
# 7. ATÖLYE SOHBETİ
# ---------------------------------------------------------
elif menu == "💬 Atölye Sohbeti":
    st.markdown("## 💬 Atölye İçi İletişim Panosu")
    st.caption("Personel arası hızlı notlar, vardiya devir mesajları ve hatırlatmalar.")
    
    conn = get_db_connection()
    
    with st.form("chat_form", clear_on_submit=True):
        c_user, c_msg = st.columns([1, 4])
        with c_user:
            user_name = st.text_input("Adınız", placeholder="Ör: Barış", max_chars=20)
        with c_msg:
            message = st.text_input("Mesajınız", placeholder="Vardiya notu, malzeme eksiği vb...")
        
        submit_chat = st.form_submit_button("Mesajı Gönder 🚀", type="primary")
        
        if submit_chat and user_name and message:
            now_str = get_now().strftime("%d.%m.%Y %H:%M")
            conn.execute(
                "INSERT INTO chat_messages (user_name, message, created_at) VALUES (?, ?, ?)",
                (user_name.strip(), message.strip(), now_str)
            )
            conn.commit()
            st.rerun()
            
    st.divider()
    
    df_chat = pd.read_sql_query("SELECT * FROM chat_messages ORDER BY id DESC LIMIT 50", conn)
    conn.close()
    
    if not df_chat.empty:
        for _, row in df_chat.iterrows():
            st.markdown(
                f"""
                <div style="background-color: #f1f5f9; padding: 10px 15px; border-radius: 8px; margin-bottom: 8px; border-left: 4px solid #3b82f6;">
                    <small style="color: #64748b;"><b>{row['user_name']}</b> • {row['created_at']}</small>
                    <div style="margin-top: 4px; color: #0f172a;">{row['message']}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
    else:
        st.info("Henüz mesaj bulunmuyor. İlk mesajı siz gönderin!")