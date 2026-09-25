import io
import json
import math
import os
import psycopg
from psycopg import sql
from pathlib import Path
from uuid import uuid4
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
    initial_sidebar_state="auto",
)

# Yüklemeler için klasör oluştur
# Dosyalar kalıcı veritabanında saklanır.

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

    /* Satır İçi İş Kartı - Neredeyse Bitişik ve Kompakt */
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
       SADECE İŞ PLANI SATIRLARINI KOMPAKTLAŞTIR
       Diğer sayfalardaki Streamlit elemanlarının boşluklarına
       kesinlikle müdahale edilmez.
       st.container(key=...) tarafından oluşturulan sınıf kullanılır.
       ========================================================= */

    /* İş satırı container'ı */
    [class*="st-key-job_row_"] {
        gap: 0rem !important;
        row-gap: 0rem !important;
        padding: 2px 4px !important;
        margin: 0 0 2px 0 !important;
        background: #f8fafc !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 6px !important;
    }

    /* Satırın kendi kolonları */
    [class*="st-key-job_row_"] div[data-testid="stHorizontalBlock"] {
        gap: 0.18rem !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    /* Sadece iş satırındaki widget dış boşlukları */
    [class*="st-key-job_row_"] div[data-testid="stTextInput"],
    [class*="st-key-job_row_"] div[data-testid="stSelectbox"],
    [class*="st-key-job_row_"] div[data-testid="stNumberInput"] {
        margin: 0 !important;
        padding: 0 !important;
    }

    /* Widget label'ı zaten collapsed; dikey yer kaplamasın */
    [class*="st-key-job_row_"] div[data-testid="stWidgetLabel"] {
        margin: 0 !important;
        padding: 0 !important;
        min-height: 0 !important;
        height: 0 !important;
    }

    [class*="st-key-job_row_"] div[data-testid="stWidgetLabel"] > div {
        margin: 0 !important;
        padding: 0 !important;
    }

    /* Text / select / number input kontrol yüksekliği */
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

    /* İşlem butonları */
    [class*="st-key-job_row_"] div[data-testid="stButton"] button,
    [class*="st-key-job_row_"] div[data-testid="stDownloadButton"] button,
    [class*="st-key-job_row_"] div[data-testid="stPopover"] > button {
        min-height: 28px !important;
        height: 28px !important;
        padding-top: 0 !important;
        padding-bottom: 0 !important;
        margin: 0 !important;
    }

    [data-testid="stSidebar"] .stRadio > label {
        font-weight: 800 !important;
        color: #64748b !important;
        font-size: 0.78rem !important;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        margin-bottom: 8px;
    }

    /* Radio Seçeneklerini Şık Buton/Kart Tasarımına Dönüştürme */
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


    /* =========================================================
       GÜVENLİ RESPONSIVE TASARIM - TELEFON / TABLET / PC
       Streamlit'in kendi kolon/flex hesaplamasına müdahale edilmez.
       Bu özellikle mobilde "hata oluştu / yeniden bağlanıyor" sorunlarını
       önlemek için önemlidir.
       ========================================================= */

    /* Tablet */
    @media only screen and (min-width: 769px) and (max-width: 1200px) {
        .main .block-container {
            max-width: 100% !important;
            padding-left: 0.75rem !important;
            padding-right: 0.75rem !important;
        }

        .custom-card {
            padding: 14px !important;
        }

        .firm-header-band {
            padding: 7px 10px !important;
        }
    }

    /* Telefon */
    @media only screen and (max-width: 768px) {
        .main .block-container {
            width: 100% !important;
            max-width: 100% !important;
            padding: 0.5rem 0.55rem 1rem 0.55rem !important;
            box-sizing: border-box !important;
        }

        /* Streamlit'in native kolon/flex yapısını BOZMAYIN.
           Mobilde bunları column'a zorlamak bazı sürümlerde frontend
           render/reconnect sorunlarına yol açabilir. */
        [data-testid="stHorizontalBlock"] {
            max-width: 100% !important;
        }

        /* Ana başlık */
        h1 { font-size: 1.35rem !important; }
        h2 { font-size: 1.15rem !important; }
        h3 { font-size: 1rem !important; }

        /* Firma başlığı */
        .firm-header-band {
            font-size: 0.78rem !important;
            padding: 6px 8px !important;
            margin-top: 6px !important;
            margin-bottom: 3px !important;
        }

        .count-badge {
            font-size: 0.68rem !important;
            padding: 2px 6px !important;
        }

        /* Kartlar */
        .custom-card {
            width: 100% !important;
            box-sizing: border-box !important;
            padding: 12px !important;
            margin-bottom: 8px !important;
        }

        /* Form alanları: okunabilir ve dokunulabilir */
        .stTextInput input,
        .stNumberInput input,
        .stTextArea textarea {
            font-size: 14px !important;
        }

        .stButton > button,
        div[data-testid="stDownloadButton"] > button,
        div[data-testid="stPopover"] > button {
            min-height: 38px !important;
        }

        /* İş planı satırı: sadece dış kutu yatay kaydırılır.
           İçerideki Streamlit kolonlarının flex yapısı değiştirilmez. */
        [class*="st-key-job_row_"] {
            width: 100% !important;
            max-width: 100% !important;
            overflow-x: auto !important;
            overflow-y: hidden !important;
            -webkit-overflow-scrolling: touch !important;
            scrollbar-width: thin;
            box-sizing: border-box !important;
        }

        [class*="st-key-job_row_"] > div {
            min-width: 1040px !important;
        }

        [class*="st-key-job_row_"] div[data-testid="stHorizontalBlock"] {
            min-width: 1030px !important;
            flex-wrap: nowrap !important;
        }

        /* Data editor */
        [data-testid="stDataEditor"] {
            max-width: 100% !important;
        }

        /* Metrikler */
        [data-testid="stMetricValue"] {
            font-size: 1.25rem !important;
        }

        /* Sidebar: yalnızca genişlik ayarı; iç flex yapısına dokunulmaz */
        [data-testid="stSidebar"] {
            width: min(86vw, 340px) !important;
        }
    }

    /* Çok küçük telefonlar */
    @media only screen and (max-width: 420px) {
        .main .block-container {
            padding-left: 0.35rem !important;
            padding-right: 0.35rem !important;
        }

        .firm-header-band {
            font-size: 0.72rem !important;
        }

        .stButton > button {
            font-size: 0.82rem !important;
        }
    }

    /* Bu revizyon yalnızca iş satırları ve sol menü Excel düğmesine uygulanır. */
    [class*="st-key-job_table_"] { gap: 3px !important; }
    [class*="st-key-job_row_"] { margin: 0 !important; padding: 1px 3px !important; }
    [class*="st-key-job_row_"] [data-testid="stVerticalBlock"] { gap: 0 !important; }
    [class*="st-key-job_row_"] [data-testid="stButton"] button,
    [class*="st-key-job_row_"] [data-testid="stDownloadButton"] button,
    [class*="st-key-job_row_"] [data-testid="stDownloadButton"] a,
    [class*="st-key-job_row_"] [data-testid="stPopover"] button[data-testid="stPopoverButton"] {
        box-sizing: border-box !important;
        width: 100% !important; min-width: 0 !important;
        height: 28px !important; min-height: 28px !important; max-height: 28px !important;
        padding: 0 !important; display: flex !important;
        align-items: center !important; justify-content: center !important;
    }
    [class*="st-key-job_row_"] [data-testid="stPopoverButton"] > div {
        justify-content: center !important; gap: 0 !important;
    }
    [class*="st-key-job_row_"] [data-testid="stPopoverButton"] svg { display: none !important; }
    [data-testid="stSidebar"] .st-key-excel_backup_button button,
    [data-testid="stSidebar"] .st-key-excel_backup_button a {
        background: rgba(255,255,255,0.03) !important;
        color: #f1f5f9 !important; border: 1px solid rgba(255,255,255,0.10) !important;
        border-radius: 10px !important; min-height: 40px !important;
    }
    [data-testid="stSidebar"] .st-key-excel_backup_button button p,
    [data-testid="stSidebar"] .st-key-excel_backup_button a p { color: #f1f5f9 !important; }
    [data-testid="stSidebar"] .st-key-excel_backup_button button:hover,
    [data-testid="stSidebar"] .st-key-excel_backup_button a:hover {
        background: rgba(255,255,255,0.07) !important; color: #ffffff !important;
        border-color: rgba(255,255,255,0.15) !important;
    }

</style>
""",
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# VERİTABANI BAĞLANTISI VE OTOMATİK MİGRASYON
# ---------------------------------------------------------
def get_db_connection():
  try:
    cfg = st.secrets["database"]
    return psycopg.connect(
        host=cfg["host"], port=int(cfg.get("port", 5432)),
        dbname=cfg.get("dbname", "postgres"), user=cfg["user"],
        password=cfg["password"], sslmode="require", connect_timeout=15,
        options="-c search_path=esme_mes,public -c statement_timeout=60000",
        prepare_threshold=None,
    )
  except Exception:
    st.error("Kalıcı kayıt sistemine bağlanılamadı. Streamlit Settings → Secrets "
             "bölümündeki bağlantı bilgilerini ve Supabase projesinin açık olduğunu "
             "kontrol edin. Güvenlik için yeni kayıt girişi durduruldu.")
    st.stop()


def read_sql_query(query, conn, params=None):
  with conn.cursor() as cur:
    cur.execute(query, params)
    return pd.DataFrame(cur.fetchall(), columns=[c.name for c in cur.description])


@st.cache_resource(show_spinner=False)
def init_db():
  with get_db_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT pg_advisory_xact_lock(73519024)")
    cursor.execute("CREATE SCHEMA IF NOT EXISTS esme_mes")
  
    cursor.execute("""
          CREATE TABLE IF NOT EXISTS work_orders (
              id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
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
              id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
              user_name TEXT,
              message TEXT,
              created_at TEXT
          )
      """)
  
    cursor.execute("""
          CREATE TABLE IF NOT EXISTS heat_treatment (
              id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
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
              id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
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
  
    cursor.execute("""SELECT column_name FROM information_schema.columns
                      WHERE table_schema='esme_mes' AND table_name='work_orders'""")
    cols = [row[0] for row in cursor.fetchall()]
  
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
  
    cursor.execute("""CREATE TABLE IF NOT EXISTS drawing_files (
        path TEXT PRIMARY KEY, name TEXT NOT NULL, content BYTEA NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now())""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS restore_snapshots (
        id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(), content BYTEA NOT NULL)""")
  


init_db()


# ---------------------------------------------------------
# EXCEL YEDEKLEME VE GERİ YÜKLEME FONKSİYONLARI
# ---------------------------------------------------------
def export_all_to_excel():
  output = io.BytesIO()
  conn = get_db_connection()

  df_active = read_sql_query(
      "SELECT * FROM work_orders WHERE is_archived = 0 ORDER BY id ASC", conn
  )
  df_archived = read_sql_query(
      "SELECT * FROM work_orders WHERE is_archived = 1 ORDER BY id DESC", conn
  )
  df_ht = read_sql_query(
      "SELECT * FROM heat_treatment ORDER BY id DESC", conn
  )
  df_wjg = read_sql_query(
      "SELECT * FROM wjg_waterjet ORDER BY id DESC", conn
  )
  df_chat = read_sql_query(
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
  # Tüm sayfalar doğrulanır; tek işlemde yüklenir. Hata varsa geri alınır.
  try:
    sheets = {
        "work_orders": ["Aktif İş Planı", "İmalat Hafızası (Arşiv)"],
        "heat_treatment": ["Isıl İşlem Takip"],
        "wjg_waterjet": ["Su Jeti (WJG) Takip"],
        "chat_messages": ["Atölye Sohbeti"],
    }
    with pd.ExcelFile(uploaded_file) as xls:
      required = [name for names in sheets.values() for name in names]
      if any(name not in xls.sheet_names for name in required):
        return False, "Tam program yedeğini seçin. Eksik sayfalı dosya yüklenmedi; mevcut kayıtlar korundu."
      frames = {table: pd.concat([pd.read_excel(xls, name) for name in names],
                                 ignore_index=True) for table, names in sheets.items()}
    with get_db_connection() as conn:
      for table in sorted(sheets):
        conn.execute(sql.SQL("LOCK TABLE {} IN ACCESS EXCLUSIVE MODE").format(sql.Identifier(table)))
      snapshot = io.BytesIO()
      with pd.ExcelWriter(snapshot, engine="openpyxl") as writer:
        for table, names in sheets.items():
          previous = read_sql_query(sql.SQL("SELECT * FROM {} ORDER BY id").format(sql.Identifier(table)), conn)
          if table == "work_orders":
            previous[previous.is_archived == 0].to_excel(writer, sheet_name=names[0], index=False)
            previous[previous.is_archived == 1].to_excel(writer, sheet_name=names[1], index=False)
          else:
            previous.to_excel(writer, sheet_name=names[0], index=False)
      conn.execute("INSERT INTO restore_snapshots(content) VALUES (%s)", (snapshot.getvalue(),))
      for table, frame in frames.items():
        schema = dict(conn.execute("""SELECT column_name, data_type FROM information_schema.columns
          WHERE table_schema='esme_mes' AND table_name=%s""", (table,)).fetchall())
        if 'id' not in frame or any(c not in schema for c in frame.columns):
          raise ValueError("Yedek sütunları uyumsuz")
        if frame['id'].isna().any() or frame['id'].duplicated().any():
          raise ValueError("Geçersiz kayıt numaraları")
        values = []
        for row in frame.itertuples(index=False, name=None):
          converted = []
          for col, value in zip(frame.columns, row):
            if pd.isna(value):
              value = None
            elif schema[col] in ('integer', 'bigint'):
              if float(value) != int(value):
                raise ValueError("Tam sayı bekleniyor")
              value = int(value)
            elif schema[col] in ('real', 'double precision', 'numeric'):
              value = float(value)
            else:
              value = str(value)
            converted.append(value)
          values.append(converted)
        conn.execute(sql.SQL("DELETE FROM {}").format(sql.Identifier(table)))
        if values:
          statement = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
              sql.Identifier(table), sql.SQL(',').join(map(sql.Identifier, frame.columns)),
              sql.SQL(',').join(sql.Placeholder() for _ in frame.columns))
          with conn.cursor() as cur:
            cur.executemany(statement, values)
        # RESTART işlemi geri alınabilir; geri yükleme sonrası yeni numara çakışmaz.
        next_id = int(frame['id'].max()) + 1 if len(frame) else 1
        conn.execute(sql.SQL("ALTER TABLE {} ALTER COLUMN id RESTART WITH {}").format(
            sql.Identifier(table), sql.Literal(max(1, next_id))))
    return True, "Yedek kalıcı sisteme yüklendi. Önceki kayıtların güvenlik kopyası da saklandı."
  except Exception:
    return False, "Yedek yüklenemedi. Mevcut kayıtlar değiştirilmedi. Tam program yedeğini seçip tekrar deneyin."


def drawing_exists(path):
  return path in st.session_state.get("_drawing_paths", set())


def read_drawing(path):
  with get_db_connection() as conn:
    row = conn.execute("SELECT content FROM drawing_files WHERE path=%s", (path,)).fetchone()
  if row is None:
    raise FileNotFoundError("Teknik resim bulunamadı")
  return bytes(row[0])


def refresh_drawing_index():
  with get_db_connection() as conn:
    st.session_state["_drawing_paths"] = {r[0] for r in conn.execute("SELECT path FROM drawing_files").fetchall()}


refresh_drawing_index()


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
      if drawing_exists(p):
        zip_file.writestr(n, read_drawing(p))
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
# TEL EREZYON: ÖN PLANLAMA MODELİ (25.09.2026)
# Kaynak noktaları tezgâh teknolojisi değildir. Kalınlığa genelleme ve
# finiş katsayısı açıkça belirtilmiş planlama varsayımlarıdır.
# ---------------------------------------------------------
EDM_MATERIALS = {
    "Çelik": (100.0, "50 mm çelik için tedarikçi başlangıç değeri; kaliteye özel doğrulanmış tablo değildir."),
    "Tungsten karbür (WC / sert metal)": (40.0, "Tedarikçinin 30–50 mm²/dk aralığının ortası. Bağlayıcı oranı ve tezgâha göre büyük fark olabilir."),
    "Pirinç": (None, "ELCUT 234 deneyinin 5–80 mm kalınlık bağıntısı; tezgâhınıza göre kalibre edilmelidir."),
    "Alüminyum": (200.0, "İmalat hizmeti sağlayıcısının rehberindeki 60 mm alüminyum için 200–220 mm²/dk aralığının alt sınırı."),
    "Krom / Paslanmaz çelik": (120.0, "İmalat hizmeti sağlayıcısının rehberindeki 40 mm paslanmaz için 120–140 mm²/dk aralığının alt sınırı; 304/316 ayrı doğrulanmamıştır."),
}


def edm_reference_rate(material, thickness):
  if material not in EDM_MATERIALS or not math.isfinite(thickness) or thickness <= 0:
    raise ValueError("Geçerli malzeme ve kalınlık girin.")
  if material == "Pirinç":
    if not 5 <= thickness <= 80:
      return None
    # Rao & Sarcar (2009), Cs [mm/min], T [mm], experimental fit.
    feed = 1.0356 + 22542.18 / (1 + math.exp((thickness + 101.54) / 13.06))
    return feed * thickness
  if not 5 <= thickness <= 100:
    return None
  return EDM_MATERIALS[material][0]


def calculate_edm(length, thickness, quantity, area_rate, skim_count,
                  skim_time_ratio, time_allowance, setup_minutes,
                  handling_minutes, hourly_rate, extra_cost):
  inputs = (length, thickness, quantity, area_rate, skim_count, skim_time_ratio,
            time_allowance, setup_minutes, handling_minutes, hourly_rate, extra_cost)
  if not all(math.isfinite(float(v)) for v in inputs):
    raise ValueError("Sayılar sonlu olmalıdır.")
  if min(length, thickness, area_rate) <= 0 or quantity < 1 or int(quantity) != quantity:
    raise ValueError("Kesim yolu, kalınlık, hız ve adet sıfırdan büyük olmalıdır.")
  if int(skim_count) != skim_count or not 0 <= skim_count <= 6:
    raise ValueError("Finiş paso sayısı 0–6 olmalıdır.")
  if min(skim_time_ratio, time_allowance, setup_minutes, handling_minutes, hourly_rate, extra_cost) < 0:
    raise ValueError("Negatif değer kullanılamaz.")
  area = length * thickness
  rough = area / area_rate
  skim = rough * skim_time_ratio * skim_count
  net = (rough + skim) * quantity
  reserve = net * time_allowance / 100
  fixed = setup_minutes + handling_minutes * quantity
  total = net + reserve + fixed
  # ±%40 hız senaryosu: istatistiksel güven aralığı değildir.
  lower = (net + reserve) / 1.4 + fixed
  upper = (net + reserve) / 0.6 + fixed
  return dict(area=area, feed=area_rate / thickness, rough=rough, skim=skim,
              net=net, reserve=reserve, fixed=fixed, total=total,
              lower=lower, upper=upper,
              cost=total / 60 * hourly_rate + extra_cost,
              cost_lower=lower / 60 * hourly_rate + extra_cost,
              cost_upper=upper / 60 * hourly_rate + extra_cost)


def edm_duration(minutes):
  rounded = max(1, math.ceil(minutes)) if minutes > 0 else 0
  hours, mins = divmod(rounded, 60)
  return f"{hours} sa {mins} dk" if hours else f"{mins} dk"


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
        "⚡ Tel Erezyon Maliyet Hesabı",
        "💬 Atölye Sohbeti",
    ],
)

st.sidebar.markdown("---")

# Excel yalnızca kullanıcının açık isteğiyle hazırlanır.
# Hazırlanan dosya sonraki işlemlerde saklanmaz; eski yedek indirilmesini önler.
if st.sidebar.button(
    "📊 Tüm Verileri Excel'e Aktar",
    key="excel_backup_button",
    use_container_width=True,
    help="Güncel kayıtların Excel yedeğini hazırlar. Ardından indirme düğmesine basın.",
):
  with st.spinner("Excel yedeği hazırlanıyor…"):
    excel_backup = export_all_to_excel()
  backup_filename = f"Esme_Makina_Yedek_{get_now().strftime('%Y%m%d_%H%M%S')}.xlsx"
  st.sidebar.download_button(
      label="📥 Hazırlanan Excel Yedeğini İndir",
      key="excel_backup_download",
      data=excel_backup,
      file_name=backup_filename,
      mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      use_container_width=True,
      on_click="ignore",
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

st.sidebar.caption("☁️ Kalıcı kayıt sistemi • Eşme Makina MES")
st.sidebar.caption("Excel yedeği teknik resimlerin içeriğini kapsamaz.")

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
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 0)
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
  df_active = read_sql_query(
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

    col_search, col_filter = st.columns([2, 1])
    with col_search:
      search_query = st.text_input(
          "🔍 İş Planında Arama Yap (Parça Adı, Müşteri, Malzeme)",
          placeholder="Ör: OKP4746, PHILSA...", key="job_search")
    with col_filter:
      cust_filter = st.selectbox(
          "Müşteri Filtresi", ["TÜMÜ"] + sorted(df_active["customer"].dropna().unique().tolist()),
          key="job_customer_filter")
    if search_query.strip():
      q = search_query.strip().translate(str.maketrans("İI", "ii")).casefold()
      mask = pd.Series(False, index=df_active.index)
      for field in ("job_name", "customer", "material"):
        values = df_active[field].fillna("").astype(str).str.translate(str.maketrans("İI", "ii")).str.casefold()
        mask |= values.str.contains(q, regex=False, na=False)
      df_active = df_active[mask]
    if cust_filter != "TÜMÜ":
      df_active = df_active[df_active["customer"] == cust_filter]
    st.caption(f"Bulunan iş: {len(df_active)} adet")
    if df_active.empty:
      st.info("Aramanıza uygun iş bulunamadı. Aramayı veya müşteri filtresini değiştirin.")

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

      with st.container(key=f"job_header_{str(customer).replace(' ', '_')}"):
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

      with st.container(key=f"job_table_{str(customer)}"):
        for _, row in cust_df.iterrows():
          j_id = int(row["id"])
  
          with st.container(key=f"job_row_{j_id}"):
            c1, c2, c3, c4, c5, c6, c7, c8, c9, c10, c11 = st.columns(col_widths)
  
            with c1:
              new_job = st.text_input(
                  "İş Adı",
                  value=row["job_name"],
                  key=f"job_{j_id}",
                  label_visibility="collapsed",
              )
            with c2:
              new_mat = st.text_input(
                  "Malzeme",
                  value=row["material"],
                  max_chars=20,
                  key=f"mat_{j_id}",
                  label_visibility="collapsed",
                  placeholder="Malzeme",
              )
            with c3:
              new_supp = st.text_input(
                  "Tedarikçi",
                  value=row["supplier"],
                  key=f"supp_{j_id}",
                  label_visibility="collapsed",
                  placeholder="Atlas, Altek vb.",
              )
            with c4:
              new_dim = st.text_input(
                  "Ölçü",
                  value=row["dimensions"],
                  max_chars=15,
                  key=f"dim_{j_id}",
                  label_visibility="collapsed",
                  placeholder="Ölçü",
              )
            with c5:
              new_qty = st.number_input(
                  "Adet",
                  value=int(row["quantity"]),
                  min_value=1,
                  key=f"qty_{j_id}",
                  label_visibility="collapsed",
              )
            with c6:
              new_heat = st.text_input(
                  "Isıl İşlem",
                  value=row["heat_treatment"],
                  key=f"heat_{j_id}",
                  label_visibility="collapsed",
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
                  label_visibility="collapsed",
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
                  label_visibility="collapsed",
              )
            with c9:
              new_ddl = st.text_input(
                  "Termin",
                  value=row["deadline"],
                  key=f"ddl_{j_id}",
                  label_visibility="collapsed",
                  placeholder="STOK / Tarih",
              )
            with c10:
              new_note = st.text_input(
                  "Not",
                  value=row["notes"],
                  key=f"note_{j_id}",
                  label_visibility="collapsed",
                  placeholder="Not",
              )
  
            with c11:
              paths, names = parse_drawing_files(
                  row["drawing_path"], row["drawing_name"]
              )
              has_files = len(paths) > 0 and any(drawing_exists(p) for p in paths)
  
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
                    with get_db_connection() as conn:
                      for up_file in up_files:
                        orig_name = Path(up_file.name).name
                        s_path = "db:" + uuid4().hex
                        conn.execute("INSERT INTO drawing_files(path,name,content) VALUES (%s,%s,%s)",
                                     (s_path, orig_name, up_file.getvalue()))
                        new_paths.append(s_path)
                        new_names.append(orig_name)
                      path_json, name_json = format_drawing_files(new_paths, new_names)
                      conn.execute("UPDATE work_orders SET drawing_path=%s, drawing_name=%s WHERE id=%s",
                                   (path_json, name_json, int(j_id)))
                    st.toast(
                        f"{len(new_paths)} dosya başarıyla yüklendi!", icon="🟢"
                    )
                    st.rerun()
  
              with ic2:
                if has_files:
                  valid_paths = [p for p in paths if drawing_exists(p)]
                  valid_names = [
                      n for p, n in zip(paths, names) if drawing_exists(p)
                  ]
  
                  if len(valid_paths) == 1:
                    with io.BytesIO(read_drawing(valid_paths[0])) as f_bytes:
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
                  conn.execute("DELETE FROM work_orders WHERE id = %s", (j_id,))
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
                              SET job_name=%s, material=%s, supplier=%s, dimensions=%s, quantity=%s, heat_treatment=%s, status='HAZIR / TAMAMLANDI', machine_name='YOK / ATANMADI', deadline=%s, notes=%s, is_archived=1, end_time=%s, duration_str=%s
                              WHERE id=%s
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
                              SET job_name=%s, material=%s, supplier=%s, dimensions=%s, quantity=%s, heat_treatment=%s, status=%s, machine_name=%s, deadline=%s, notes=%s
                              WHERE id=%s
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
  df_active = read_sql_query(
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
        assigned_jobs.setdefault(m_name, []).append({
            "text": f"🏢 **{r['customer']}** - {r['job_name']}",
            "time": conn_time,
        })

  total_machines = 12
  known_machines = {m for group in MACHINES.values() for m in group}
  busy_count = len(known_machines.intersection(assigned_jobs))
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
        st.caption(f"Bağlı iş sayısı: {len(assigned_jobs[m])}")
        for job in assigned_jobs[m]:
          st.caption(f"Bağlı İş: {job['text']}")
          st.caption(f"🕒 **Bağlanma Zamanı:** {job['time']}")
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
        st.caption(f"Bağlı iş sayısı: {len(assigned_jobs[m])}")
        for job in assigned_jobs[m]:
          st.caption(f"Bağlı İş: {job['text']}")
          st.caption(f"🕒 **Bağlanma Zamanı:** {job['time']}")
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
        st.caption(f"Bağlı iş sayısı: {len(assigned_jobs[m])}")
        for job in assigned_jobs[m]:
          st.caption(f"Bağlı İş: {job['text']}")
          st.caption(f"🕒 **Bağlanma Zamanı:** {job['time']}")
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
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
  df_ht = read_sql_query(
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
                    SET sent_date=%s, supplier_firm=%s, customer=%s, product_code_name=%s, quantity=%s, material=%s, hardness=%s, weight_kg=%s, process_type=%s, status=%s, invoice_info=%s
                    WHERE id=%s
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
      conn.execute("DELETE FROM heat_treatment WHERE id = %s", (del_id,))
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
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, '', %s)
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
  df_wjg = read_sql_query(
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
                    SET sent_date=%s, customer=%s, part_name=%s, part_code=%s, dimensions=%s, order_qty=%s, received_qty=%s, unit_price=%s, status=%s, invoice_info=%s
                    WHERE id=%s
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
      conn.execute("DELETE FROM wjg_waterjet WHERE id = %s", (del_id,))
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
  df_arch = read_sql_query(
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
                            SET dik_time=%s, torna_time=%s, tel_time=%s, uni_time=%s, price=%s, notes=%s
                            WHERE id=%s
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
        valid_paths = [p for p in paths if drawing_exists(p)]
        valid_names = [n for p, n in zip(paths, names) if drawing_exists(p)]

        if valid_paths:
          if len(valid_paths) == 1:
            with io.BytesIO(read_drawing(valid_paths[0])) as f_bytes:
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
                " SIRADA' WHERE id = %s",
                (arch_id,),
            )
            conn.commit()
            conn.close()
            st.toast("İş tekrar canlı plana aktarıldı!", icon="🔄")
            st.rerun()
        with col_b2:
          if st.button("🗑️ Arşivden Kalıcı Sil", key=f"arch_del_{arch_id}"):
            conn = get_db_connection()
            conn.execute("DELETE FROM work_orders WHERE id = %s", (arch_id,))
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
      weight_kg = (vol_cm3 * density) / 1000 if out_d > in_d else 0.0

    unit_price_kg = st.number_input(
        "Malzeme KG Birim Fiyatı (₺)",
        min_value=0.0,
        value=120.0,
        step=1.0,
        key="cost_unit_price",
    )
    total_mat_cost = weight_kg * unit_price_kg

    st.divider()
    st.metric("Hesaplanan Parça Ağırlığı", f"{weight_kg:.3f} KG")
    st.metric("Tahmini Hammadde Maliyeti", f"{total_mat_cost:.2f} ₺")
    st.markdown("</div>", unsafe_allow_html=True)

  with col_mach:
    st.markdown(
        "<div class='custom-card'><h3>⚙️ 2. İşleme & Teklif Maliyeti</h3>",
        unsafe_allow_html=True,
    )

    c_time, c_rate = st.columns(2)
    with c_time:
      st.markdown("**⏱️ İşleme Süreleri (Dk)**")
      t_dik = st.number_input(
          "CNC Dik İsl. (Dk)",
          min_value=0.0,
          value=30.0,
          step=1.0,
          key="cost_t_dik",
      )
      t_torna = st.number_input(
          "CNC Torna (Dk)",
          min_value=0.0,
          value=15.0,
          step=1.0,
          key="cost_t_torna",
      )
      t_tel = st.number_input(
          "Tel Erezyon (Dk)",
          min_value=0.0,
          value=45.0,
          step=1.0,
          key="cost_t_tel",
      )
      t_uni = st.number_input(
          "Üniversal (Dk)",
          min_value=0.0,
          value=10.0,
          step=1.0,
          key="cost_t_uni",
      )

    with c_rate:
      st.markdown("**💳 Saat Ücretleri (₺/Saat)**")
      r_dik = st.number_input(
          "Dik İşleme Ücreti",
          min_value=0.0,
          value=1200.0,
          step=1.0,
          key="cost_r_dik",
      )
      r_torna = st.number_input(
          "Torna Saat Ücreti",
          min_value=0.0,
          value=1000.0,
          step=1.0,
          key="cost_r_torna",
      )
      r_tel = st.number_input(
          "Tel Erezyon Ücreti",
          min_value=0.0,
          value=800.0,
          step=1.0,
          key="cost_r_tel",
      )
      r_uni = st.number_input(
          "Üniversal Ücreti",
          min_value=0.0,
          value=600.0,
          step=1.0,
          key="cost_r_uni",
      )

    st.markdown("---")
    c_fason1, c_fason2 = st.columns(2)

    with c_fason1:
      fason_ht = st.number_input(
          "ISIL İŞLEM MALİYETİ (₺)",
          min_value=0.0,
          value=150.0,
          step=1.0,
          key="cost_fason_ht",
      )
      fason_coat = st.number_input(
          "KAPLAMA/SU JETİ MALİYETİ (₺)",
          min_value=0.0,
          value=0.0,
          step=1.0,
          key="cost_fason_coat",
      )

    with c_fason2:
      st.metric(
          "Eklenen Hammadde Maliyeti",
          f"{total_mat_cost:.2f} ₺",
          help=(
              "Sol tarafta hesaplanan hammadde maliyeti doğrudan hesaba"
              " katılır."
          ),
      )
      profit_margin = st.slider(
          "Kâr Marjı (%)",
          min_value=0,
          max_value=100,
          value=30,
          key="cost_profit",
      )

    cost_machining = (
        ((t_dik / 60) * r_dik)
        + ((t_torna / 60) * r_torna)
        + ((t_tel / 60) * r_tel)
        + ((t_uni / 60) * r_uni)
    )
    total_base_cost = cost_machining + total_mat_cost + fason_ht + fason_coat
    final_price = total_base_cost * (1 + (profit_margin / 100))

    st.markdown("</div>", unsafe_allow_html=True)

  st.divider()
  st.markdown("### 📊 HESAPLANAN TEKLİF VE MALİYET ÖZETİ")
  m1, m2, m3 = st.columns(3)
  m1.metric("İşleme İşçilik Maliyeti", f"{cost_machining:.2f} ₺")
  m2.metric("Toplam İmalat Maliyeti", f"{total_base_cost:.2f} ₺")
  m3.metric(
      "Önerilen Teklif Fiyatı",
      f"{final_price:.2f} ₺",
      delta=f"%{profit_margin} Kâr Marjı",
  )

# ---------------------------------------------------------
# 7. ATÖLYE SOHBETİ
# ---------------------------------------------------------
elif menu == "⚡ Tel Erezyon Maliyet Hesabı":
  st.markdown("## ⚡ Tel Erezyon Maliyet Hesabı")
  st.caption("Kesim yolunu ve parça bilgilerini girin; yaklaşık süreyi ve işleme maliyetini görün.")
  edm_machine = st.selectbox("Tezgâh", ["FANUC ROBOCUT α-1iD (2009)", "FANUC ROBOCUT α-C400iB"], key="edm_machine")
  st.caption("Kullanılan tel: EDM Teknik EW • Ø0,25 mm • Her iki tezgâhta aynı tel.")
  st.info("Yaklaşık planlama hesabı: su içinde düz kesim ve iyi yıkama varsayılır. "
          "EW telin alaşım/kaplaması doğrulanmadı; başlangıç hesabı pirinç tel referanslarına dayanır. "
          "Bu iki FANUC için doğrulanmış hız tablosu bulunmadığından model seçimi otomatik hız farkı uygulamaz.")
  left, right = st.columns(2)
  with left:
    edm_material = st.selectbox("Malzeme cinsi", list(EDM_MATERIALS), key="edm_material")
    edm_grade = st.text_input("Malzeme kalitesi / kodu (isteğe bağlı)", key="edm_grade",
                             placeholder="Ör: 1.2379, 1.2738, Sulubant, AISI 304, AISI 316")
    edm_length = st.number_input("Bir parçanın toplam kesim yolu (mm)", min_value=0.1,
                                 value=100.0, step=10.0, key="edm_length",
                                 help="Tüm konturları ve malzeme içindeki giriş yolunu bir kez toplayın. Finiş pasolarını tekrar eklemeyin.")
    edm_height = st.number_input("Parça kalınlığı / kesim yüksekliği (mm)", min_value=0.1,
                                 max_value=500.0, value=30.0, step=1.0, key="edm_height")
    edm_quantity = st.number_input("Parça adedi (ayrı ayrı kesilecek)", min_value=1,
                                  max_value=100000, value=1, step=1, key="edm_quantity")
  with right:
    edm_mode = st.radio("Kesim tercihi", ["Hızlı — 1 kaba paso", "Hassas — kaba + finiş pasoları"],
                        key="edm_mode")
    edm_skims = 0
    if edm_mode.startswith("Hassas"):
      edm_skims = st.number_input("Finiş paso sayısı", min_value=1, max_value=6,
                                  value=2, step=1, key="edm_skims")
      st.caption("Hassas seçim varsayılan olarak 1 kaba + 2 finiş pasosudur. Belirli bir tolerans veya yüzey kalitesi garantisi değildir.")
    edm_hourly = st.number_input("Tezgâh saatlik maliyeti (₺/saat)", min_value=0.0,
                                 value=0.0, step=100.0, key=f"edm_hourly_{edm_machine}",
                                 help="Tel, elektrik, işçilik ve genel giderler dahil saatlik maliyetinizi yazın.")
    edm_setup = st.number_input("İşin tamamı için hazırlık süresi (dk)", min_value=0.0,
                                value=15.0, step=5.0, key="edm_setup")
    edm_allowance = st.number_input("Kesim süresine eklenecek pay (%)", min_value=0.0,
                                    max_value=200.0, value=15.0, step=5.0, key="edm_allowance",
                                    help="Kısa duruşlar, köşeler ve yıkama farklılıkları için seçtiğiniz planlama payı.")
  reference = edm_reference_rate(edm_material, edm_height)
  with st.expander("⚙️ Tezgâha göre ayarla / ek giderler", expanded=reference is None):
    st.caption(EDM_MATERIALS[edm_material][1])
    manual = st.checkbox("Tezgâhımdan bildiğim kaba kesim hızını kullan", key="edm_manual")
    manual_feed = st.number_input("Bilinen kaba kesim ilerlemesi (mm/dk)", min_value=0.001,
                                  value=2.0, step=0.1, format="%.3f", key=f"edm_manual_feed_{edm_machine}_{edm_material}_{edm_height}",
                                  disabled=not manual,
                                  help="Aynı malzeme, kalınlık ve tel için ölçülen ilerleme. Tel makarasının m/dk hızı değildir.")
    skim_ratio = st.number_input("Bir finiş pasosu / kaba paso süre oranı", min_value=0.05,
                                 max_value=5.0, value=0.50, step=0.05, key="edm_skim_ratio",
                                 disabled=edm_skims == 0,
                                 help="0,50: her finiş pasosu kaba pasonun yarısı kadar sürer. Bu bir planlama varsayımıdır; tezgâhınıza göre değiştirin.")
    handling = st.number_input("Parça başına ek bağlama / tel geçirme süresi (dk)",
                               min_value=0.0, value=0.0, step=1.0, key="edm_handling")
    extra = st.number_input("İşin tamamı için ek gider (₺)", min_value=0.0, value=0.0,
                            step=50.0, key="edm_extra",
                            help="Saat ücretine dahil etmediğiniz giderler. Dahil olan tel/elektrik giderini tekrar eklemeyin.")
    st.caption("Bu ekrandaki girişler hesaplama içindir; kalıcı bir teklif kaydı oluşturmaz.")
  area_rate = manual_feed * edm_height if manual else reference
  if area_rate is None:
    st.warning("Bu kalınlık için otomatik tahmin sınırının dışındasınız. "
               "Tezgâhınızdan bildiğiniz kaba kesim hızını yukarıdan girin. "
               "Pirinç araştırması 5–80 mm; diğer malzemeler için geçici model sınırı 5–100 mm'dir.")
  else:
    result = calculate_edm(edm_length, edm_height, edm_quantity, area_rate, edm_skims,
                           skim_ratio, edm_allowance, edm_setup, handling, edm_hourly, extra)
    st.divider()
    st.markdown("### Tahmini süre ve maliyet")
    a, b, c = st.columns(3)
    a.metric("Toplam planlanan süre", edm_duration(result['total']))
    b.metric("Kaba kesim ilerlemesi", f"{result['feed']:.2f} mm/dk")
    c.metric("Toplam işleme maliyeti", f"{result['cost']:,.2f} ₺" if edm_hourly > 0 else "Saat ücreti girin")
    st.caption(f"Süre senaryosu: {edm_duration(result['lower'])} – {edm_duration(result['upper'])}. "
               "Hızın tahminden %40 yüksek/düşük olmasıyla hesaplanır; güven aralığı veya garanti değildir.")
    if edm_hourly > 0:
      st.caption(f"Parça başına: {result['cost'] / edm_quantity:,.2f} ₺ • "
                 f"Maliyet senaryosu: {result['cost_lower']:,.2f} – {result['cost_upper']:,.2f} ₺ • Kâr ve KDV dahil değil.")
    st.dataframe(pd.DataFrame([
        {"Süre kalemi": "Kaba kesim — tüm parçalar", "Dakika": round(result['rough'] * edm_quantity, 1)},
        {"Süre kalemi": f"Finiş — parça başına {edm_skims} paso", "Dakika": round(result['skim'] * edm_quantity, 1)},
        {"Süre kalemi": "Kesim süresi payı", "Dakika": round(result['reserve'], 1)},
        {"Süre kalemi": "Hazırlık + ek bağlama / tel geçirme", "Dakika": round(result['fixed'], 1)},
        {"Süre kalemi": "TOPLAM", "Dakika": round(result['total'], 1)},
    ]), hide_index=True, use_container_width=True)
    if not manual:
      st.caption("Kaynaklar farklı tezgâhlara aittir. Çelik, karbür, alüminyum ve paslanmazda "
                 "alan kesme hızı sabit kabul edilip kalınlığa bölünür; bu, doğrulanmış bir kalınlık tablosu değildir. "
                 "Malzeme kodu not olarak tutulur; farklı kodlara kanıtsız ayrı hız verilmez.")
    st.caption("Üst üste kesimde toplam paket kalınlığını ve paket adedini kullanın. "
               "Konik kesim, çok küçük köşeler, kötü yıkama ve tel kopmaları süreyi bu aralığın dışına taşıyabilir.")
  with st.expander("📖 Araştırma kaynakları ve hesap esasları"):
    st.markdown("[FANUC α-CiB üretici kataloğu](https://www.fanuc.com/fin/id/product/catalog/RCUT-CiB(E)-07.pdf)")
    st.write("FANUC kataloğu Ø0,25 mm pirinç telle 25/75 mm kalıp çeliğinde üç pasolu örnek verir; "
             "tüm malzemeleri kapsayan ilerleme tablosu vermez. α-1iD ile α-C400iB arasında "
             "kanıtsız hız katsayısı uygulanmamıştır. Hassas seçimi yüzey/tolerans taahhüdü değildir.")
    st.markdown("**Başlangıç değerleri — farklı tezgâhlar ve genel rehberler; FANUC teknoloji tablosu değildir:**")
    st.dataframe(pd.DataFrame([
        {"Malzeme": "Çelik", "Kaynak": "Lemhunter", "Referans": "50 mm: yaklaşık 100 mm²/dk", "Model": "100 mm²/dk; kalite farkı tanımlanmadı"},
        {"Malzeme": "Tungsten karbür", "Kaynak": "Lemhunter", "Referans": "30–50 mm²/dk; kalınlık belirtilmemiş", "Model": "40 mm²/dk; düşük güvenli başlangıç"},
        {"Malzeme": "Alüminyum", "Kaynak": "MHAOCNC", "Referans": "60 mm: 200–220 mm²/dk", "Model": "200 mm²/dk"},
        {"Malzeme": "Paslanmaz", "Kaynak": "MHAOCNC", "Referans": "40 mm: 120–140 mm²/dk", "Model": "120 mm²/dk; 304/316 ortak ön tahmin"},
        {"Malzeme": "Pirinç", "Kaynak": "Rao & Sarcar, 2009", "Referans": "ELCUT 234; Ø0,25 mm tel; 5–80 mm", "Model": "Yayımlanmış kalınlık–ilerleme bağıntısı"},
    ]), hide_index=True, use_container_width=True)
    st.markdown("[Lemhunter — çelik ve karbür başlangıç değerleri](https://m.lemhunter.com/news/understanding-wire-edm-costs-and-machining-time/)  \n"
                "[MHAOCNC — malzeme, kalınlık ve süre hesabı](https://www.mhaocnc.com/How-To-Calculate-Wire-Edm-Machining-Time-id49158555.html)  \n"
                "[Rao & Sarcar — pirinç kesim deneyleri, 2009](https://www.researchgate.net/publication/242128421_Evaluation_of_optimal_parameters_for_machining_brass_with_wire_cut_EDM)  \n"
                "[Electronica Ecocut — 50 mm çelikte Ø0,25 mm düz pirinç tel ile 60 mm²/dk azami hız örneği](https://electronicagroup.com/products/wire-edm/ecocut/)")
    st.write("Temel hesap: kaba süre = kesim yolu × kalınlık ÷ alan kesme hızı. "
             "Hassas kesimde her finiş pasosunun süresi ayrıca eklenir. "
             "Varsayılan 0,50 finiş oranı, %15 süre payı ve ±%40 hız senaryosu kaynak standardı değil, "
             "değiştirilebilir planlama kabulleridir. Saat maliyeti hazırlık süresine de uygulanır.")
    st.caption("Pirinç bağıntısı: v = 1,0356 + 22542,18 / (1 + exp((H + 101,54) / 13,06)); "
               "H: mm, v: mm/dk. Tel sarım hızı ile kesim ilerlemesi farklıdır. Araştırma: 25.09.2026.")


elif menu == "💬 Atölye Sohbeti":
  st.markdown("## 💬 Atölye İçi Anlık Mesajlaşma")
  st.caption(
      "Vardiyalar arası notlar, tezgah durum bildirimleri ve atölye iletişimi."
  )

  conn = get_db_connection()
  df_chat = read_sql_query(
      "SELECT * FROM chat_messages ORDER BY id DESC LIMIT 50", conn
  )
  conn.close()

  with st.form("chat_form", clear_on_submit=True):
    col_u, col_m, col_b = st.columns([1.5, 4, 1])
    with col_u:
      user_n = st.text_input("Adınız / Vardiya", placeholder="Ör: Ahmet Usta")
    with col_m:
      msg_t = st.text_input(
          "Mesajınız", placeholder="Ör: Dik 2 tezgahının takımı değiştirildi."
      )
    with col_b:
      st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
      sent = st.form_submit_button("Gönder 💬", type="primary")

    if sent and user_n and msg_t:
      now_c = get_now().strftime("%d.%m.%Y %H:%M")
      conn = get_db_connection()
      conn.execute(
          "INSERT INTO chat_messages (user_name, message, created_at) VALUES"
          " (%s, %s, %s)",
          (user_n.strip(), msg_t.strip(), now_c),
      )
      conn.commit()
      conn.close()
      st.rerun()

  st.subheader("📜 Son Mesajlar")
  if not df_chat.empty:
    for _, r in df_chat.iterrows():
      st.markdown(
          f"**👤 {r['user_name']}** ({r['created_at']}): {r['message']}"
      )
      st.divider()
  else:
    st.info("Henüz sohbet mesajı yok.")