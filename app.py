import streamlit as st
import pandas as pd
import sqlite3
import math
import os
from datetime import datetime

# ---------------------------------------------------------
# SAYFA YAPILANDIRMASI & ÖZEL MODERN CSS
# ---------------------------------------------------------
st.set_page_config(
    page_title="Eşme Makina MES - Üretim & Fason Yönetimi",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Yüklemeler için klasör oluştur
os.makedirs("uploads", exist_ok=True)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"]  {
        font-family: 'Inter', sans-serif;
    }
    
    .main .block-container {
        padding-top: 1.2rem;
        padding-bottom: 2rem;
        max-width: 98%;
    }

    /* Üst Logo ve Başlık Alanı */
    .brand-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: #ffffff;
        padding: 12px 24px;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.04);
        border: 1px solid #e2e8f0;
        margin-bottom: 20px;
    }
    
    /* Modern Kart Yapısı */
    .custom-card {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 18px 22px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.04);
        border: 1px solid #e2e8f0;
        margin-bottom: 15px;
    }
    
    /* Firma Başlık Bandı */
    .firm-header-band {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        color: #ffffff;
        padding: 10px 18px;
        border-radius: 8px;
        font-weight: 700;
        font-size: 1.05rem;
        letter-spacing: 0.5px;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.15);
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 18px;
        margin-bottom: 12px;
    }
    
    .count-badge {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
        color: #ffffff;
        padding: 3px 12px;
        border-radius: 12px;
        font-size: 0.82rem;
        font-weight: 600;
    }

    /* Satır İçi İş Kartı */
    .job-row-card {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 10px 14px;
        margin-bottom: 8px;
        transition: all 0.2s ease;
    }
    .job-row-card:hover {
        border-color: #cbd5e1;
        background-color: #ffffff;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }

    /* Sol Menü (Sidebar) Modernizasyonu */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%) !important;
        padding-top: 1rem;
    }
    
    [data-testid="stSidebar"] * {
        color: #f8fafc !important;
    }

    [data-testid="stSidebar"] .stRadio > label {
        font-weight: 700 !important;
        color: #94a3b8 !important;
        font-size: 0.85rem !important;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 8px;
    }

    /* Radio Seçeneklerini Buton/Kart Şekline Getirme */
    [data-testid="stSidebar"] .stRadio > div {
        gap: 6px;
    }

    [data-testid="stSidebar"] .stRadio label {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 10px !important;
        padding: 10px 14px !important;
        color: #e2e8f0 !important;
        font-weight: 500 !important;
        font-size: 0.92rem !important;
        transition: all 0.25s ease-in-out !important;
        cursor: pointer;
        display: flex;
        align-items: center;
        margin-bottom: 2px;
    }

    [data-testid="stSidebar"] .stRadio label:hover {
        background: rgba(255, 255, 255, 0.1) !important;
        border-color: rgba(255, 255, 255, 0.2) !important;
        transform: translateX(4px);
    }

    [data-testid="stSidebar"] .stRadio div[data-checked="true"] label {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
        border-color: #60a5fa !important;
        color: #ffffff !important;
        font-weight: 700 !important;
        box-shadow: 0 4px 14px rgba(37, 99, 235, 0.35);
    }

    [data-testid="stMetricValue"] {
        font-size: 1.6rem !important;
        font-weight: 700 !important;
        color: #0f172a;
    }
    
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s ease-in-out;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# VERİTABANI BAĞLANTISI VE OTOMATİK MİGRASYON
# ---------------------------------------------------------
def get_db_connection():
    conn = sqlite3.connect('esme_makina_uretim.db')
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
        ('machine_name', 'TEXT'),
        ('notes', 'TEXT'),
        ('start_time', 'TEXT'),
        ('end_time', 'TEXT'),
        ('duration_str', 'TEXT'),
        ('price', 'REAL'),
        ('dik_time', 'REAL DEFAULT 0'),
        ('torna_time', 'REAL DEFAULT 0'),
        ('tel_time', 'REAL DEFAULT 0'),
        ('uni_time', 'REAL DEFAULT 0'),
        ('drawing_path', 'TEXT'),
        ('drawing_name', 'TEXT'),
        ('is_archived', 'INTEGER DEFAULT 0')
    ]
    
    for col_name, col_type in columns_to_add:
        if col_name not in cols:
            cursor.execute(f"ALTER TABLE work_orders ADD COLUMN {col_name} {col_type}")
            
    conn.commit()
    conn.close()

init_db()

# SABİT LİSTELER
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
    "ELOKSAL KAPLAMA",
    "WJG SU JETİ",
    "ASM LAZER",
    "HAZIR"
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
    "Tel Erezyon 3"
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
    "KURŞUN": 11.34
}

# GÜNCELLENEN ISIL İŞLEM LİSTELERİ
HT_SUPPLIERS = [
    "ALPHA ISIL İŞLEM", 
    "ASTAŞ ISIL İŞLEM", 
    "ÇUKUROVA ISIL İŞLEM", 
    "VOESTALPİNE ISIL İŞLEM"
]

HT_PROCESSES = [
    "SUBZERO+VAKUM", 
    "VAKUM", 
    "NİTRASYON", 
    "İNDÜKSİYON", 
    "SEMENTASYON"
]

HT_STATUSES = ["ISIL İŞLEMDE", "GELDİ / TAMAMLANDI", "FATURALANDI"]
WJG_STATUSES = ["KESİMDE / GÖNDERİLDİ", "GELDİ / TAMAMLANDI", "FATURA ALINDI"]

def parse_date(date_str):
    if not date_str:
        return None
    for fmt in ("%d.%m.%Y %H:%M:%S", "%d.%m.%Y %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%d.%m.%Y"):
        try:
            return datetime.strptime(str(date_str).strip(), fmt)
        except ValueError:
            pass
    return None

# ---------------------------------------------------------
# SOL MENÜ & LOGO
# ---------------------------------------------------------
if os.path.exists("LOGO VE İSİM.JPG"):
    st.sidebar.image("LOGO VE İSİM.JPG", use_container_width=True)

st.sidebar.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

menu = st.sidebar.radio(
    "SİSTEM KATEGORİLERİ",
    [
        "📊 İş Planı (Canlı Tablo)",
        "🛠️ Tezgah Parkı Durumu",
        "🔥 Isıl İşlem Takip",
        "🌊 Su Jeti (WJG) Takip",
        "📚 İmalat Hafızası (Arşiv)",
        "💰 Akıllı Maliyet Hesabı",
        "💬 Atölye Sohbeti"
    ]
)

st.sidebar.caption("Eşme Makina MES v6.5 • 2026")

# ---------------------------------------------------------
# ÜST LOGO & BAŞLIK ALANI (ANA SAYFA)
# ---------------------------------------------------------
col_header_logo, col_header_title = st.columns([1, 4])
with col_header_logo:
    if os.path.exists("LOGO VE İSİM.JPG"):
        st.image("LOGO VE İSİM.JPG", width=220)
with col_header_title:
    st.markdown("### ⚙️ EŞME MAKİNA MES - ÜRETİM & FASON YÖNETİM SİSTEMİ")
    st.caption("Canlı İş Planlama, Tezgah Takibi, Isıl İşlem ve Otomatik Kayıtlı İmalat Hafızası")

st.divider()

# ---------------------------------------------------------
# 1. İŞ PLANINI GÖRÜNTÜLE VE YÖNET (OTOMATİK KAYITLI & SAĞDA DOSYA YÜKLE/İNDİR)
# ---------------------------------------------------------
if menu == "📊 İş Planı (Canlı Tablo)":
    st.markdown("## 📊 İŞ PLANI")
    st.caption("Aktif müşteri siparişleri ve canlı imalat durumları. Yapılan tüm değişiklikler anında otomatik kaydedilir.")

    with st.expander("➕ **Yeni İş / Parça Siparişi Ekle**", expanded=False):
        with st.form("add_job_form", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                cust = st.text_input("Firma / Müşteri Adı *", placeholder="Ör: PHILSA A.Ş.")
                job = st.text_input("İş / Parça Adı *", placeholder="Ör: OKP4746.M PLATE")
                mat = st.text_input("Malzeme Türü", placeholder="Ör: Ç.2379, 7075 Alüminyum")
            with col2:
                dims = st.text_input("Malzeme Ölçüleri", placeholder="Ör: 30x45x85 mm")
                supp = st.text_input("Malzeme Siparişi / Tedarikçi", placeholder="Ör: ATLAS METAL")
                qty = st.number_input("Adet", min_value=1, value=10)
            with col3:
                heat = st.text_input("Isıl İşlem - Kaplama", placeholder="Ör: 56-58 HRC")
                stt = st.selectbox("İlk Durum / İşlem", STATUS_OPTIONS)
                mac = st.selectbox("Bağlı Tezgah", MACHINE_OPTIONS)
                ddl = st.text_input("Termin Tarihi", placeholder="Ör: 15.09.2026 veya STOK")

            initial_note = st.text_area("İş Notları (Opsiyonel)", placeholder="İşle ilgili özel notlar...")

            submitted = st.form_submit_button("🚀 Siparişi Ekle ve Süreyi Başlat", type="primary")
            if submitted and cust and job:
                now_str = datetime.now().strftime("%d.%m.%Y %H:%M")
                conn = get_db_connection()
                conn.execute('''
                    INSERT INTO work_orders 
                    (customer, job_name, material, dimensions, supplier, quantity, heat_treatment, status, machine_name, deadline, notes, start_time, created_at, is_archived)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                ''', (cust.upper().strip(), job.strip(), mat.strip(), dims.strip(), supp.strip(), qty, heat.strip(), stt, mac, ddl.strip(), initial_note.strip(), now_str, now_str))
                conn.commit()
                conn.close()
                st.toast("İş sipariş planına eklendi!", icon="🚀")
                st.rerun()

    conn = get_db_connection()
    df_active = pd.read_sql_query("SELECT * FROM work_orders WHERE is_archived = 0 ORDER BY id ASC", conn)
    conn.close()

    if not df_active.empty:
        df_active['drawing_path'] = df_active['drawing_path'].fillna("")
        df_active['drawing_name'] = df_active['drawing_name'].fillna("")
        df_active['notes'] = df_active['notes'].fillna("")
        df_active['machine_name'] = df_active['machine_name'].fillna("YOK / ATANMADI")

        customers = df_active['customer'].unique()
        
        for customer in customers:
            cust_df = df_active[df_active['customer'] == customer].copy()
            
            st.markdown(f"""
                <div class="firm-header-band">
                    <span>🏢 {customer}</span>
                    <span class="count-badge">{len(cust_df)} Kalem İş</span>
                </div>
            """, unsafe_allow_html=True)

            # TABLO BAŞLIKLARI (SATIR İÇİ DOSYA BÖLÜMÜ EN SAĞDA)
            h1, h2, h3, h4, h5, h6, h7, h8 = st.columns([2, 1.2, 1, 1.5, 1.5, 1.5, 1.8, 2.2])
            with h1: st.caption("**İŞ / PARÇA ADI**")
            with h2: st.caption("**MALZEME / ÖLÇÜ**")
            with h3: st.caption("**ADET**")
            with h4: st.caption("**ISIL İŞLEM**")
            with h5: st.caption("**İŞLEM / DURUM**")
            with h6: st.caption("**TEZGAH**")
            with h7: st.caption("**NOT / TERMİN**")
            with h8: st.caption("**📂 DOSYA İŞLEMLERİ (EN SAĞ)**")

            for _, row in cust_df.iterrows():
                j_id = int(row['id'])
                
                st.markdown("<div class='job-row-card'>", unsafe_allow_html=True)
                c1, c2, c3, c4, c5, c6, c7, c8 = st.columns([2, 1.2, 1, 1.5, 1.5, 1.5, 1.8, 2.2])
                
                with c1:
                    new_job = st.text_input("İş Adı", value=row['job_name'], key=f"job_{j_id}", label_visibility="collapsed")
                with c2:
                    new_mat = st.text_input("Malzeme", value=row['material'], key=f"mat_{j_id}", label_visibility="collapsed", placeholder="Malzeme")
                    new_dim = st.text_input("Ölçü", value=row['dimensions'], key=f"dim_{j_id}", label_visibility="collapsed", placeholder="Ölçü")
                with c3:
                    new_qty = st.number_input("Adet", value=int(row['quantity']), min_value=1, key=f"qty_{j_id}", label_visibility="collapsed")
                with c4:
                    new_heat = st.text_input("Isıl İşlem", value=row['heat_treatment'], key=f"heat_{j_id}", label_visibility="collapsed", placeholder="Sertlik/Kaplama")
                with c5:
                    idx_st = STATUS_OPTIONS.index(row['status']) if row['status'] in STATUS_OPTIONS else 0
                    new_st = st.selectbox("Durum", STATUS_OPTIONS, index=idx_st, key=f"st_{j_id}", label_visibility="collapsed")
                with c6:
                    idx_m = MACHINE_OPTIONS.index(row['machine_name']) if row['machine_name'] in MACHINE_OPTIONS else 0
                    new_mac = st.selectbox("Tezgah", MACHINE_OPTIONS, index=idx_m, key=f"mac_{j_id}", label_visibility="collapsed")
                with c7:
                    new_ddl = st.text_input("Termin", value=row['deadline'], key=f"ddl_{j_id}", label_visibility="collapsed", placeholder="Termin")
                    new_note = st.text_input("Not", value=row['notes'], key=f"note_{j_id}", label_visibility="collapsed", placeholder="Notlar")
                
                # EN SAĞ BÖLÜM: DOSYA YÜKLE / İNDİR & SİL
                with c8:
                    d_path = str(row['drawing_path'])
                    d_name = str(row['drawing_name'])
                    has_file = bool(d_path and os.path.exists(d_path))
                    
                    f_col1, f_col2, f_col3 = st.columns([1.5, 1, 0.5])
                    with f_col1:
                        up_file = st.file_uploader("Dosya", type=None, key=f"up_{j_id}", label_visibility="collapsed")
                        if up_file is not None:
                            original_filename = str(up_file.name)
                            save_filename = f"job_{j_id}_{original_filename}"
                            save_path = os.path.join("uploads", save_filename)
                            with open(save_path, "wb") as f:
                                f.write(up_file.getbuffer())
                            
                            conn = get_db_connection()
                            conn.execute("UPDATE work_orders SET drawing_path = ?, drawing_name = ? WHERE id = ?", (save_path, original_filename, j_id))
                            conn.commit()
                            conn.close()
                            st.toast("Dosya yüklendi!", icon="🟢")
                            st.rerun()

                    with f_col2:
                        if has_file:
                            with open(d_path, "rb") as f_bytes:
                                st.download_button("📥 İndir", f_bytes.read(), file_name=d_name, key=f"dl_{j_id}")
                        else:
                            st.caption("Yok")

                    with f_col3:
                        if st.button("🗑️", key=f"del_{j_id}", help="İşi Sil"):
                            conn = get_db_connection()
                            conn.execute("DELETE FROM work_orders WHERE id = ?", (j_id,))
                            conn.commit()
                            conn.close()
                            st.toast("İş silindi!", icon="🗑️")
                            st.rerun()

                st.markdown("</div>", unsafe_allow_html=True)

                # OTOMATİK KAYIT VE "HAZIR" DURUMU KONTROLÜ
                if (new_job != row['job_name'] or new_mat != row['material'] or new_dim != row['dimensions'] or 
                    new_qty != row['quantity'] or new_heat != row['heat_treatment'] or new_st != row['status'] or 
                    new_mac != row['machine_name'] or new_ddl != row['deadline'] or new_note != row['notes']):
                    
                    conn = get_db_connection()
                    if new_st == "HAZIR":
                        end_now_dt = datetime.now()
                        end_now_str = end_now_dt.strftime("%d.%m.%Y %H:%M")
                        duration_calc_str = "Belirtilmedi"
                        if row['start_time']:
                            start_dt = parse_date(row['start_time'])
                            if start_dt:
                                diff = end_now_dt - start_dt
                                days = diff.days
                                hours, remainder = divmod(diff.seconds, 3600)
                                minutes, _ = divmod(remainder, 60)
                                duration_calc_str = f"{days} Gün {hours} Saat {minutes} Dk" if days > 0 else f"{hours} Saat {minutes} Dk"

                        conn.execute('''
                            UPDATE work_orders 
                            SET job_name=?, material=?, dimensions=?, quantity=?, heat_treatment=?, status='HAZIR / TAMAMLANDI', machine_name='YOK / ATANMADI', deadline=?, notes=?, is_archived=1, end_time=?, duration_str=?
                            WHERE id=?
                        ''', (new_job, new_mat, new_dim, new_qty, new_heat, new_ddl, new_note, end_now_str, duration_calc_str, j_id))
                        conn.commit()
                        conn.close()
                        st.toast("🎉 Parça 'HAZIR' durumuna getirildi ve arşive aktarıldı!", icon="🎉")
                        st.rerun()
                    else:
                        conn.execute('''
                            UPDATE work_orders
                            SET job_name=?, material=?, dimensions=?, quantity=?, heat_treatment=?, status=?, machine_name=?, deadline=?, notes=?
                            WHERE id=?
                        ''', (new_job, new_mat, new_dim, new_qty, new_heat, new_st, new_mac, new_ddl, new_note, j_id))
                        conn.commit()
                        conn.close()
                        st.toast("Değişiklikler otomatik kaydedildi", icon="💾")
                        st.rerun()

    else:
        st.info("İş planında henüz aktif iş bulunmuyor. Yukarıdaki formdan yeni iş ekleyebilirsiniz.")

# ---------------------------------------------------------
# 2. TEZGAH PARKI DURUMU
# ---------------------------------------------------------
elif menu == "🛠️ Tezgah Parkı Durumu":
    st.markdown("## 🛠️ Tezgah Parkı Anlık Durum Panosu")
    st.caption("İş planında 'BAĞLI TEZGAH' olarak atadığınız makinelerin canlı yük durumu.")

    MACHINES = {
        "CNC Dik İşleme": [f"CNC Dik İşleme {i}" for i in range(1, 6)],
        "CNC Torna": [f"CNC Torna {i}" for i in range(1, 5)],
        "Tel Erezyon": [f"Tel Erezyon {i}" for i in range(1, 4)]
    }

    conn = get_db_connection()
    df_active = pd.read_sql_query("SELECT * FROM work_orders WHERE is_archived = 0", conn)
    conn.close()

    assigned_jobs = {}
    if not df_active.empty and 'machine_name' in df_active.columns:
        for _, r in df_active.iterrows():
            m_name = r['machine_name']
            if m_name and m_name != "YOK / ATANMADI":
                assigned_jobs[m_name] = f"🏢 **{r['customer']}** - {r['job_name']}"

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
        st.markdown("<div class='custom-card'><h4>CNC Dik İşleme (5 Adet)</h4>", unsafe_allow_html=True)
        for m in MACHINES["CNC Dik İşleme"]:
            if m in assigned_jobs:
                st.markdown(f"**{m}**: 🔴 **ÇALIŞIYOR**")
                st.caption(f"Bağlı İş: {assigned_jobs[m]}")
            else:
                st.markdown(f"**{m}**: 🟢 **BOŞ / HAZIR**")
            st.write("---")
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown("<div class='custom-card'><h4>CNC Torna (4 Adet)</h4>", unsafe_allow_html=True)
        for m in MACHINES["CNC Torna"]:
            if m in assigned_jobs:
                st.markdown(f"**{m}**: 🔴 **ÇALIŞIYOR**")
                st.caption(f"Bağlı İş: {assigned_jobs[m]}")
            else:
                st.markdown(f"**{m}**: 🟢 **BOŞ / HAZIR**")
            st.write("---")
        st.markdown("</div>", unsafe_allow_html=True)

    with c3:
        st.markdown("<div class='custom-card'><h4>Tel Erezyon (3 Adet)</h4>", unsafe_allow_html=True)
        for m in MACHINES["Tel Erezyon"]:
            if m in assigned_jobs:
                st.markdown(f"**{m}**: 🔴 **ÇALIŞIYOR**")
                st.caption(f"Bağlı İş: {assigned_jobs[m]}")
            else:
                st.markdown(f"**{m}**: 🟢 **BOŞ / HAZIR**")
            st.write("---")
        st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------
# 3. ISIL İŞLEM TAKİP MODÜLÜ (GÜNCELLENMİŞ FİRMALAR & OTOMATİK KAYIT)
# ---------------------------------------------------------
elif menu == "🔥 Isıl İşlem Takip":
    st.markdown("## 🔥 Isıl İşlem Takip Modülü")
    st.caption("Fason ısıl işleme gönderilen malzemelerin firma, sertlik, kg ve fatura durum takibi. Tablodaki değişiklikler otomatik kaydedilir.")

    with st.expander("➕ **Yeni Isıl İşlem Gönderim Kaydı Ekle**", expanded=False):
        with st.form("add_ht_form", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                ht_date = st.text_input("Tarih *", value=datetime.now().strftime("%d.%m.%Y"))
                ht_supplier = st.selectbox("Isıl İşlem Firması *", HT_SUPPLIERS)
                ht_customer = st.text_input("Müşteri Firma Adı *", placeholder="Ör: PROFACE, DENTAŞ")
            with col2:
                ht_prod = st.text_input("Ürün Kodu ve Adı *", placeholder="Ör: CUTTER BIÇAĞI MALAFASI")
                ht_qty = st.number_input("Adet", min_value=1, value=1)
                ht_mat = st.text_input("Malzeme Cinsi", value="Ç.2379")
            with col3:
                ht_hard = st.text_input("Hedef Sertlik", value="60-62 HRC")
                ht_weight = st.number_input("Ağırlık (KG)", min_value=0.0, value=5.0, step=0.5)
                ht_process = st.selectbox("İşlem Türü", HT_PROCESSES)

            col_a, col_b = st.columns(2)
            with col_a:
                ht_status = st.selectbox("İşlem Durumu", HT_STATUSES)
            with col_b:
                ht_inv = st.text_input("Fatura Kontrolü / Not", placeholder="Ör: 3770+KDV veya Bekliyor")

            submitted = st.form_submit_button("🔥 Isıl İşlem Kaydını Ekle", type="primary")
            if submitted and ht_customer and ht_prod:
                now_s = datetime.now().strftime("%d.%m.%Y %H:%M")
                conn = get_db_connection()
                conn.execute('''
                    INSERT INTO heat_treatment
                    (sent_date, supplier_firm, customer, product_code_name, quantity, material, hardness, weight_kg, process_type, status, invoice_info, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (ht_date.strip(), ht_supplier, ht_customer.upper().strip(), ht_prod.strip(), ht_qty, ht_mat.strip(), ht_hard.strip(), ht_weight, ht_process, ht_status, ht_inv.strip(), now_s))
                conn.commit()
                conn.close()
                st.toast("Isıl işlem kaydı başarıyla eklendi!", icon="🔥")
                st.rerun()

    conn = get_db_connection()
    df_ht = pd.read_sql_query("SELECT * FROM heat_treatment ORDER BY id DESC", conn)
    conn.close()

    if not df_ht.empty:
        st.subheader("📋 Isıl İşlem Kayıtları Tablosu")
        
        display_ht = df_ht[['id', 'sent_date', 'supplier_firm', 'customer', 'product_code_name', 'quantity', 'material', 'hardness', 'weight_kg', 'process_type', 'status', 'invoice_info']].copy()

        edited_ht = st.data_editor(
            display_ht,
            key="ht_editor",
            use_container_width=True,
            hide_index=True,
            column_order=["sent_date", "supplier_firm", "customer", "product_code_name", "quantity", "material", "hardness", "weight_kg", "process_type", "status", "invoice_info"],
            column_config={
                "sent_date": st.column_config.TextColumn("TARİH", width="small"),
                "supplier_firm": st.column_config.SelectboxColumn("ISIL İŞLEM FİRMASI", options=HT_SUPPLIERS, required=True, width="medium"),
                "customer": st.column_config.TextColumn("FİRMA ADI", width="medium"),
                "product_code_name": st.column_config.TextColumn("ÜRÜN KODU VE ADI", width="large"),
                "quantity": st.column_config.NumberColumn("ADET", width="small"),
                "material": st.column_config.TextColumn("MALZEME", width="small"),
                "hardness": st.column_config.TextColumn("SERTLİK", width="small"),
                "weight_kg": st.column_config.NumberColumn("KG", width="small"),
                "process_type": st.column_config.SelectboxColumn("İŞLEM", options=HT_PROCESSES, width="medium"),
                "status": st.column_config.SelectboxColumn("DURUM", options=HT_STATUSES, width="medium"),
                "invoice_info": st.column_config.TextColumn("FATURA KONTROLÜ", width="medium")
            }
        )

        # OTOMATİK KAYIT KONTROLÜ
        if not edited_ht.equals(display_ht):
            conn = get_db_connection()
            for _, row in edited_ht.iterrows():
                conn.execute('''
                    UPDATE heat_treatment
                    SET sent_date=?, supplier_firm=?, customer=?, product_code_name=?, quantity=?, material=?, hardness=?, weight_kg=?, process_type=?, status=?, invoice_info=?
                    WHERE id=?
                ''', (row['sent_date'], row['supplier_firm'], row['customer'], row['product_code_name'], row['quantity'], row['material'], row['hardness'], row['weight_kg'], row['process_type'], row['status'], row['invoice_info'], row['id']))
            conn.commit()
            conn.close()
            st.toast("Isıl işlem tablosu otomatik kaydedildi", icon="💾")
            st.rerun()

        ht_list = [f"{r['id']} - {r['customer']} ({r['product_code_name']})" for _, r in df_ht.iterrows()]
        sel_ht_del = st.selectbox("Silinecek Isıl İşlem Kaydını Seçin:", ["Seçiniz..."] + ht_list, key="sel_ht_del")
        if st.button("🗑️ Seçili Isıl İşlem Kaydını Sil") and sel_ht_del != "Seçiniz...":
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
# 4. SU JETİ (WJG) TAKİP MODÜLÜ (OTOMATİK KAYIT)
# ---------------------------------------------------------
elif menu == "🌊 Su Jeti (WJG) Takip":
    st.markdown("## 🌊 Su Jeti (WJG) Takip Modülü")
    st.caption("Su jetinde kesilen parçaların adet, ölçü, birim fiyat ve fatura durum takibi. Tablo otomatik kaydedilir.")

    with st.expander("➕ **Yeni Su Jeti (WJG) Kesim Kaydı Ekle**", expanded=False):
        with st.form("add_wjg_form", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                wjg_date = st.text_input("Kesim Tarihi *", value=datetime.now().strftime("%d.%m.%Y"))
                wjg_customer = st.text_input("Firma Adı *", placeholder="Ör: ANKUTSAN, OMKAR")
                wjg_part = st.text_input("Parça Tanımı *", placeholder="Ör: GAGALI SLOT BIÇAĞI")
            with col2:
                wjg_code = st.text_input("Parça Kodu", placeholder="Ör: LMC231")
                wjg_dims = st.text_input("Ölçu (mm)", placeholder="Ör: 231x48x10")
                wjg_ord_qty = st.number_input("Sipariş Adedi", min_value=1, value=10)
            with col3:
                wjg_rec_qty = st.number_input("Gelen Adet", min_value=0, value=10)
                wjg_price = st.number_input("Birim Fiyat (TL)", min_value=0.0, value=0.0, step=10.0)
                wjg_inv = st.text_input("Fatura Bilgisi", placeholder="Ör: 9100+KDV")

            wjg_status = st.selectbox("Kesim Durumu", WJG_STATUSES)

            submitted = st.form_submit_button("🌊 Su Jeti Kaydını Ekle", type="primary")
            if submitted and wjg_customer and wjg_part:
                now_s = datetime.now().strftime("%d.%m.%Y %H:%M")
                conn = get_db_connection()
                conn.execute('''
                    INSERT INTO wjg_waterjet
                    (sent_date, customer, part_name, part_code, dimensions, order_qty, received_qty, unit_price, invoice_info, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (wjg_date.strip(), wjg_customer.upper().strip(), wjg_part.strip(), wjg_code.strip(), wjg_dims.strip(), wjg_ord_qty, wjg_rec_qty, wjg_price, wjg_inv.strip(), wjg_status, now_s))
                conn.commit()
                conn.close()
                st.toast("Su jeti kesim kaydı eklendi!", icon="🌊")
                st.rerun()

    conn = get_db_connection()
    df_wjg = pd.read_sql_query("SELECT * FROM wjg_waterjet ORDER BY id DESC", conn)
    conn.close()

    if not df_wjg.empty:
        st.subheader("📋 Su Jeti (WJG) Kesim Kayıtları Tablosu")
        
        display_wjg = df_wjg[['id', 'sent_date', 'customer', 'part_name', 'part_code', 'dimensions', 'order_qty', 'received_qty', 'unit_price', 'invoice_info', 'status']].copy()

        edited_wjg = st.data_editor(
            display_wjg,
            key="wjg_editor",
            use_container_width=True,
            hide_index=True,
            column_order=["sent_date", "customer", "part_name", "part_code", "dimensions", "order_qty", "received_qty", "unit_price", "invoice_info", "status"],
            column_config={
                "sent_date": st.column_config.TextColumn("TARİH", width="small"),
                "customer": st.column_config.TextColumn("FİRMA", width="medium"),
                "part_name": st.column_config.TextColumn("PARÇA", width="large"),
                "part_code": st.column_config.TextColumn("PARÇA KODU", width="small"),
                "dimensions": st.column_config.TextColumn("ÖLÇÜ (mm)", width="medium"),
                "order_qty": st.column_config.NumberColumn("SİP. ADEDİ", width="small"),
                "received_qty": st.column_config.NumberColumn("GELEN ADET", width="small"),
                "unit_price": st.column_config.NumberColumn("BİRİM FİYAT", width="small"),
                "invoice_info": st.column_config.TextColumn("FATURA", width="medium"),
                "status": st.column_config.SelectboxColumn("DURUM", options=WJG_STATUSES, width="medium")
            }
        )

        # OTOMATİK KAYIT KONTROLÜ
        if not edited_wjg.equals(display_wjg):
            conn = get_db_connection()
            for _, row in edited_wjg.iterrows():
                conn.execute('''
                    UPDATE wjg_waterjet
                    SET sent_date=?, customer=?, part_name=?, part_code=?, dimensions=?, order_qty=?, received_qty=?, unit_price=?, invoice_info=?, status=?
                    WHERE id=?
                ''', (row['sent_date'], row['customer'], row['part_name'], row['part_code'], row['dimensions'], row['order_qty'], row['received_qty'], row['unit_price'], row['invoice_info'], row['status'], row['id']))
            conn.commit()
            conn.close()
            st.toast("Su jeti tablosu otomatik kaydedildi", icon="💾")
            st.rerun()

        wjg_list = [f"{r['id']} - {r['customer']} ({r['part_name']})" for _, r in df_wjg.iterrows()]
        sel_wjg_del = st.selectbox("Silinecek Su Jeti Kaydını Seçin:", ["Seçiniz..."] + wjg_list, key="sel_wjg_del")
        if st.button("🗑️ Seçili Su Jeti Kaydını Sil") and sel_wjg_del != "Seçiniz...":
            del_id = int(sel_wjg_del.split(" - ")[0])
            conn = get_db_connection()
            conn.execute("DELETE FROM wjg_waterjet WHERE id = ?", (del_id,))
            conn.commit()
            conn.close()
            st.toast("Su jeti kaydı silindi!", icon="🗑️")
            st.rerun()
    else:
        st.info("Henüz eklenmiş su jeti kaydı bulunmuyor.")

# ---------------------------------------------------------
# 5. İMALAT HAFIZASI (ARŞİV)
# ---------------------------------------------------------
elif menu == "📚 İmalat Hafızası (Arşiv)":
    st.markdown("## 📚 İmalat Hafızası & Biten İşler Arşivi")
    st.caption("Tamamlanıp arşive kaldırılan geçmiş işlerinizin detaylı dökümü, dosyaları, imalat süreleri ve tezgah bazlı süre kayıtları.")
    
    conn = get_db_connection()
    df_arch = pd.read_sql_query("SELECT * FROM work_orders WHERE is_archived = 1 ORDER BY id DESC", conn)
    conn.close()

    if not df_arch.empty:
        df_arch['drawing_path'] = df_arch['drawing_path'].fillna("")
        df_arch['drawing_name'] = df_arch['drawing_name'].fillna("")
        df_arch['notes'] = df_arch['notes'].fillna("")
        df_arch['customer'] = df_arch['customer'].fillna("")
        df_arch['job_name'] = df_arch['job_name'].fillna("")
        df_arch['material'] = df_arch['material'].fillna("")
        df_arch['supplier'] = df_arch['supplier'].fillna("")
        df_arch['dimensions'] = df_arch['dimensions'].fillna("")

        col_search, col_cust_filt = st.columns([3, 1])
        with col_search:
            search_q = st.text_input("🔍 Arşivde Arama Yap (Parça Kodu / Adı, Malzeme, Firma, Tedarikçi veya Not):", placeholder="Ör: OKP4746, PLATE, 2379, ATLAS...")
        with col_cust_filt:
            all_custs = ["TÜM FİRMALAR"] + list(df_arch['customer'].unique())
            selected_cust = st.selectbox("📁 Firma Filtrele:", all_custs)

        filtered_df = df_arch.copy()
        if selected_cust != "TÜM FİRMALAR":
            filtered_df = filtered_df[filtered_df['customer'] == selected_cust]

        if search_q.strip():
            q = search_q.strip()
            mask = (
                filtered_df['job_name'].str.contains(q, case=False, na=False) |
                filtered_df['material'].str.contains(q, case=False, na=False) |
                filtered_df['customer'].str.contains(q, case=False, na=False) |
                filtered_df['notes'].str.contains(q, case=False, na=False) |
                filtered_df['supplier'].str.contains(q, case=False, na=False) |
                filtered_df['dimensions'].str.contains(q, case=False, na=False)
            )
            filtered_df = filtered_df[mask]

        st.caption(f"Arama kriterlerinize uygun **{len(filtered_df)}** adet arşiv kaydı bulundu.")

        for _, row in filtered_df.iterrows():
            st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
            
            arch_path = str(row['drawing_path']) if pd.notna(row['drawing_path']) and row['drawing_path'] else ""
            arch_name = str(row['drawing_name']) if pd.notna(row['drawing_name']) and row['drawing_name'] else "teknik_resim"
            has_arch_file = bool(arch_path and os.path.exists(arch_path))

            c1, c2, c3, c4 = st.columns([2.5, 2.5, 3, 2])
            
            with c1:
                st.markdown(f"#### ✅ {row['job_name']}")
                st.write(f"🏢 **Firma:** {row['customer']}")
                st.write(f"• **Malzeme:** {row['material'] or '-'} ({row['dimensions'] or '-'})")
                st.write(f"• **Adet:** {row['quantity']} | **Tedarikçi:** {row['supplier'] or '-'}")
                st.write(f"• **Isıl İşlem:** {row['heat_treatment'] or '-'}")

                if has_arch_file:
                    st.caption(f"🟢 **Yüklü Dosya:** {arch_name}")
                    with open(arch_path, "rb") as f_bytes:
                        file_data = f_bytes.read()
                    st.download_button(
                        label="📥 Dosyayı İndir",
                        data=file_data,
                        file_name=arch_name,
                        key=f"arch_dl_{row['id']}"
                    )
                else:
                    st.caption("⚪ Dosya Yüklenmemiş")

            with c2:
                st.markdown("##### ⏱️ İmalat Geçen Süre")
                st.write(f"• **Başlama Tarihi:** {row['start_time'] or '-'}")
                st.write(f"• **Bitiş Tarihi:** {row['end_time'] or '-'}")
                st.info(f"⏳ **Geçen Toplam Süre:** {row['duration_str'] or 'Belirtilmedi'}")

            with c3:
                st.markdown("##### 🛠️ Tezgah İşleme Süreleri (Dk)")
                dik_val = float(row['dik_time']) if pd.notna(row['dik_time']) else 0.0
                torna_val = float(row['torna_time']) if pd.notna(row['torna_time']) else 0.0
                tel_val = float(row['tel_time']) if pd.notna(row['tel_time']) else 0.0
                uni_val = float(row['uni_time']) if pd.notna(row['uni_time']) else 0.0

                ca, cb = st.columns(2)
                with ca:
                    in_dik = st.number_input("Dik İşleme (Dk):", min_value=0.0, value=dik_val, key=f"dik_{row['id']}")
                    in_torna = st.number_input("CNC Torna (Dk):", min_value=0.0, value=torna_val, key=f"torna_{row['id']}")
                with cb:
                    in_tel = st.number_input("Tel Erezyon (Dk):", min_value=0.0, value=tel_val, key=f"tel_{row['id']}")
                    in_uni = st.number_input("Üniversal (Dk):", min_value=0.0, value=uni_val, key=f"uni_{row['id']}")

            with c4:
                st.markdown("##### 💵 Fiyat & Not Düzenle")
                current_price = float(row['price']) if pd.notna(row['price']) else 0.0
                price_val = st.number_input("İmalat Fiyatı (TL):", min_value=0.0, value=current_price, step=100.0, key=f"p_{row['id']}")
                note_val = st.text_area("Arşiv Notu:", value=row['notes'] or "", key=f"n_{row['id']}", height=80)
                
                b1, b2 = st.columns(2)
                with b1:
                    if st.button("💾 Kaydet", key=f"arch_save_{row['id']}"):
                        conn = get_db_connection()
                        conn.execute('''
                            UPDATE work_orders 
                            SET price = ?, notes = ?, dik_time = ?, torna_time = ?, tel_time = ?, uni_time = ? 
                            WHERE id = ?
                        ''', (price_val, note_val, in_dik, in_torna, in_tel, in_uni, row['id']))
                        conn.commit()
                        conn.close()
                        st.toast("Fiyat ve süreler kaydedildi!", icon="✅")
                        st.rerun()
                with b2:
                    if st.button("🗑️ Sil", key=f"arch_del_{row['id']}"):
                        conn = get_db_connection()
                        conn.execute("DELETE FROM work_orders WHERE id = ?", (row['id'],))
                        conn.commit()
                        conn.close()
                        st.toast("İş arşivden silindi!", icon="🗑️")
                        st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("Arşivde henüz tamamlanmış iş bulunmuyor.")

# ---------------------------------------------------------
# 6. AKILLI MALİYET HESABI
# ---------------------------------------------------------
elif menu == "💰 Akıllı Maliyet Hesabı":
    st.markdown("## 💰 Akıllı Malzeme Ağırlığı & Maliyet Hesabı (TL)")
    st.caption("Ölçüleri girerek parçanın teorik kg ağırlığını ve tüm tezgahların işleme süreleriyle maliyetini hesaplayın.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
        st.subheader("1. Malzeme Sınıfı ve Ölçüler")
        mat_choice = st.selectbox("Malzeme Türü Seçiniz:", list(MATERIAL_DENSITIES.keys()))
        density = MATERIAL_DENSITIES[mat_choice]
        st.caption(f"Malzeme Özgül Ağırlığı: **{density} g/cm³**")
        
        shape = st.radio("Malzeme Formu:", ["Dolu Kütük / Dikdörtgen", "Dolu Mil / Çap", "Boru / Tüp"])
        calculated_weight = 0.0
        
        if shape == "Dolu Kütük / Dikdörtgen":
            t_mm = st.number_input("Kalınlık (mm):", min_value=1.0, value=20.0)
            w_mm = st.number_input("Genişlik (mm):", min_value=1.0, value=100.0)
            l_mm = st.number_input("Boy (mm):", min_value=1.0, value=150.0)
            vol_cm3 = (t_mm * w_mm * l_mm) / 1000.0
            calculated_weight = (vol_cm3 * density) / 1000.0

        elif shape == "Dolu Mil / Çap":
            d_mm = st.number_input("Dış Çap (Ø mm):", min_value=1.0, value=50.0)
            l_mm = st.number_input("Boy (mm):", min_value=1.0, value=200.0)
            r_cm = (d_mm / 10.0) / 2.0
            l_cm = l_mm / 10.0
            vol_cm3 = math.pi * (r_cm ** 2) * l_cm
            calculated_weight = (vol_cm3 * density) / 1000.0

        elif shape == "Boru / Tüp":
            d_out = st.number_input("Dış Çap (Dış Ø mm):", min_value=2.0, value=60.0)
            d_in = st.number_input("İç Çap (İç Ø mm):", min_value=1.0, value=40.0)
            l_mm = st.number_input("Boy (mm):", min_value=1.0, value=100.0)
            r_out_cm = (d_out / 10.0) / 2.0
            r_in_cm = (d_in / 10.0) / 2.0
            l_cm = l_mm / 10.0
            vol_cm3 = math.pi * ((r_out_cm ** 2) - (r_in_cm ** 2)) * l_cm
            calculated_weight = (vol_cm3 * density) / 1000.0 if d_out > d_in else 0.0

        st.success(f"⚖️ **Hesaplanan Net Ağırlık:** {round(calculated_weight, 3)} Kg")
        unit_mat_price = st.number_input("Hammadde Kg Fiyatı (TL):", min_value=1.0, value=250.0, step=10.0)
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
        st.subheader("2. Tezgah Süreleri & Saat Ücretleri")
        
        ca, cb = st.columns(2)
        with ca:
            dik_süre = st.number_input("CNC Dik İşleme Süresi (Dk):", value=30)
            torna_süre = st.number_input("CNC Torna Süresi (Dk):", value=15)
            tel_süre = st.number_input("Tel Erezyon Süresi (Dk):", value=20)
            uni_süre = st.number_input("Üniversal Tezgah Süresi (Dk):", value=10)
        with cb:
            rate_dik = st.number_input("Dik İşleme (TL/Saat):", value=1200.0)
            rate_torna = st.number_input("Torna (TL/Saat):", value=1000.0)
            rate_tel = st.number_input("Tel Erezyon (TL/Saat):", value=800.0)
            rate_uni = st.number_input("Üniversal Tezgah (TL/Saat):", value=600.0)

        heat_cost = st.number_input("Isıl İşlem / Kaplama Maliyeti (TL):", value=350.0)
        profit_margin = st.number_input("Hedef Kar Marjı (%):", min_value=0.0, value=35.0, step=5.0)
        st.markdown("</div>", unsafe_allow_html=True)

    raw_cost = calculated_weight * unit_mat_price
    machining_cost = ((dik_süre/60)*rate_dik) + ((torna_süre/60)*rate_torna) + ((tel_süre/60)*rate_tel) + ((uni_süre/60)*rate_uni)
    total_cost = raw_cost + machining_cost + heat_cost
    final_price = total_cost * (1 + (profit_margin / 100))

    st.divider()
    st.subheader("📊 Finansal Özet Metrikleri (TL)")
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Hammadde Tutarı", f"{round(raw_cost, 2):,} TL".replace(",", "."))
    m2.metric("Tezgah İşleme Tutarı", f"{round(machining_cost, 2):,} TL".replace(",", "."))
    m3.metric("Net Yalın İmalat Maliyeti", f"{round(total_cost, 2):,} TL".replace(",", "."))
    m4.metric("Önerilen Birim Satış Fiyatı", f"{round(final_price, 2):,} TL".replace(",", "."), delta=f"%{profit_margin} Kar")

# ---------------------------------------------------------
# 7. ATÖLYE SOHBETİ
# ---------------------------------------------------------
elif menu == "💬 Atölye Sohbeti":
    st.markdown("## 💬 Atölye İçi Dijital Mesajlaşma & Not Panosu")
    st.caption("Atölye ekibi, mühendisler ve ustalar arası anlık haberleşme panosu.")
    
    col_user, col_msg = st.columns([1, 3])
    
    with col_user:
        st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
        st.subheader("👤 Kullanıcı Profili")
        user_name = st.text_input("Adınız / Unvanınız:", placeholder="Ör: Barış Usta, Ahmet Bey")
        st.caption("Mesaj göndermek için adınızı giriniz.")
        st.markdown("</div>", unsafe_allow_html=True)

    with col_msg:
        st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
        st.subheader("✍️ Yeni Mesaj Yaz")
        msg_text = st.text_area("Mesajınız:", placeholder="Ör: Philsa imalatı bitti, ısıl işleme gönderildi.", height=90)
        
        if st.button("💬 Mesajı Gönder", type="primary"):
            if user_name and msg_text:
                now_s = datetime.now().strftime("%d.%m.%Y %H:%M")
                conn = get_db_connection()
                conn.execute("INSERT INTO chat_messages (user_name, message, created_at) VALUES (?, ?, ?)", (user_name.strip(), msg_text.strip(), now_s))
                conn.commit()
                conn.close()
                st.toast("Mesajınız panoya gönderildi!", icon="💬")
                st.rerun()
            else:
                st.error("Lütfen hem adınızı hem de mesajınızı giriniz.")
        st.markdown("</div>", unsafe_allow_html=True)

    st.divider()
    st.subheader("📜 Geçmiş Mesajlar & Pano")
    
    conn = get_db_connection()
    df_chat = pd.read_sql_query("SELECT * FROM chat_messages ORDER BY id DESC", conn)
    conn.close()

    if not df_chat.empty:
        for _, r in df_chat.iterrows():
            msg_id = int(r['id'])
            
            st.markdown("<div class='custom-card' style='border-left: 5px solid #2563eb;'>", unsafe_allow_html=True)
            
            c_m_main, c_m_act = st.columns([4, 1])
            
            with c_m_main:
                st.markdown(f"**👤 {r['user_name']}** &nbsp;&nbsp; `<small style='color:#64748b;'>🕒 {r['created_at']}</small>`", unsafe_allow_html=True)
                st.write(r['message'])

            with c_m_act:
                btn_e, btn_d = st.columns(2)
                with btn_e:
                    if st.button("✏️", key=f"c_edit_btn_{msg_id}", help="Mesajı Düzenle"):
                        st.session_state[f"editing_msg_{msg_id}"] = True
                with btn_d:
                    if st.button("🗑️", key=f"c_del_btn_{msg_id}", help="Mesajı Sil"):
                        conn = get_db_connection()
                        conn.execute("DELETE FROM chat_messages WHERE id = ?", (msg_id,))
                        conn.commit()
                        conn.close()
                        st.toast("Mesaj silindi!", icon="🗑️")
                        st.rerun()

            if st.session_state.get(f"editing_msg_{msg_id}", False):
                with st.form(f"form_edit_msg_{msg_id}"):
                    new_u = st.text_input("Kullanıcı Adı:", value=r['user_name'])
                    new_m = st.text_area("Mesaj Metni:", value=r['message'])
                    
                    ce1, ce2 = st.columns(2)
                    with ce1:
                        if st.form_submit_button("💾 Güncelle", type="primary"):
                            conn = get_db_connection()
                            conn.execute("UPDATE chat_messages SET user_name = ?, message = ? WHERE id = ?", (new_u.strip(), new_m.strip(), msg_id))
                            conn.commit()
                            conn.close()
                            st.session_state[f"editing_msg_{msg_id}"] = False
                            st.toast("Mesaj güncellendi!", icon="✅")
                            st.rerun()
                    with ce2:
                        if st.form_submit_button("❌ İptal"):
                            st.session_state[f"editing_msg_{msg_id}"] = False
                            st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("Henüz sohbet panosunda mesaj bulunmuyor. İlk mesajı siz gönderebilirsiniz!")