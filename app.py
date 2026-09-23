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
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 96%;
    }
    
    .custom-card {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 18px 22px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
        border: 1px solid #e2e8f0;
        margin-bottom: 15px;
    }
    
    .firm-header-band {
        background: linear-gradient(135deg, #dc2626 0%, #991b1b 100%);
        color: #ffffff;
        padding: 10px 18px;
        border-radius: 8px;
        font-weight: 700;
        font-size: 1.05rem;
        letter-spacing: 0.5px;
        box-shadow: 0 4px 12px rgba(220, 38, 38, 0.2);
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 22px;
        margin-bottom: 10px;
    }
    
    .count-badge {
        background-color: rgba(255, 255, 255, 0.25);
        color: #ffffff;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.82rem;
        font-weight: 600;
    }

    .file-badge-success {
        background-color: #dcfce7;
        color: #15803d;
        padding: 5px 12px;
        border-radius: 6px;
        font-size: 0.88rem;
        font-weight: 700;
        border: 1px solid #bbf7d0;
        display: inline-block;
        margin-bottom: 6px;
    }

    .file-badge-none {
        background-color: #f1f5f9;
        color: #64748b;
        padding: 5px 12px;
        border-radius: 6px;
        font-size: 0.88rem;
        font-weight: 600;
        border: 1px solid #e2e8f0;
        display: inline-block;
        margin-bottom: 6px;
    }
    
    [data-testid="stSidebar"] {
        background-color: #0f172a;
    }
    [data-testid="stSidebar"] * {
        color: #f8fafc !important;
    }
    
    [data-testid="stMetricValue"] {
        font-size: 1.7rem !important;
        font-weight: 700 !important;
        color: #0f172a;
    }
    
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s ease-in-out;
    }
    .stButton>button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
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

HT_SUPPLIERS = ["ALPHA", "ASTAŞ", "MERSİN ISIL İŞLEM", "DİĞER"]
HT_PROCESSES = ["SUBZERO", "NİTRASYON", "VAKUM ISIL İŞLEM", "SEMENTASYON", "TEMPER", "ISIL İŞLEM"]
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

st.sidebar.markdown("### ⚙️ EŞME MAKİNA MES")
st.sidebar.caption("Üretim Takip & İmalat Yönetimi v6.0")
st.sidebar.divider()

menu = st.sidebar.radio(
    "Sistem Menüsü:",
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

# ---------------------------------------------------------
# 1. İŞ PLANINI GÖRÜNTÜLE VE YÖNET
# ---------------------------------------------------------
if menu == "📊 İş Planı (Canlı Tablo)":
    st.markdown("## 📊 İŞ PLANI")
    st.caption("Aktif müşteri siparişleri ve canlı imalat durumları tablosu.")

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
                st.success(f"İş sipariş planına eklendi! İmalat süresi başlatıldı: {now_str}")
                st.rerun()

    conn = get_db_connection()
    df_active = pd.read_sql_query("SELECT * FROM work_orders WHERE is_archived = 0 ORDER BY id ASC", conn)
    conn.close()

    if not df_active.empty:
        df_active['drawing_path'] = df_active['drawing_path'].fillna("")
        df_active['drawing_name'] = df_active['drawing_name'].fillna("")
        df_active['notes'] = df_active['notes'].fillna("")
        df_active['machine_name'] = df_active['machine_name'].fillna("YOK / ATANMADI")
        df_active['material'] = df_active['material'].fillna("")
        df_active['dimensions'] = df_active['dimensions'].fillna("")
        df_active['supplier'] = df_active['supplier'].fillna("")
        df_active['heat_treatment'] = df_active['heat_treatment'].fillna("")
        df_active['deadline'] = df_active['deadline'].fillna("")

        customers = df_active['customer'].unique()
        
        for customer in customers:
            cust_df = df_active[df_active['customer'] == customer].copy()
            
            st.markdown(f"""
                <div class="firm-header-band">
                    <span>🏢 {customer}</span>
                    <span class="count-badge">{len(cust_df)} Kalem İş</span>
                </div>
            """, unsafe_allow_html=True)
            
            display_df = cust_df[['id', 'job_name', 'material', 'dimensions', 'supplier', 'quantity', 'heat_treatment', 'status', 'machine_name', 'deadline', 'notes']].copy()

            edited_df = st.data_editor(
                display_df,
                key=f"editor_{customer}",
                use_container_width=True,
                hide_index=True,
                column_order=["job_name", "material", "dimensions", "supplier", "quantity", "heat_treatment", "status", "machine_name", "deadline", "notes"],
                column_config={
                    "job_name": st.column_config.TextColumn("İŞ", width="medium"),
                    "material": st.column_config.TextColumn("MALZEME", width="small"),
                    "dimensions": st.column_config.TextColumn("MALZEME ÖLÇÜLERİ", width="medium"),
                    "supplier": st.column_config.TextColumn("MALZEME SİPARİŞİ", width="small"),
                    "quantity": st.column_config.NumberColumn("ADET", width="small"),
                    "heat_treatment": st.column_config.TextColumn("ISIL İŞLEM- KAPLAMA", width="small"),
                    "status": st.column_config.SelectboxColumn("İŞLEMLER", options=STATUS_OPTIONS, required=True, width="medium"),
                    "machine_name": st.column_config.SelectboxColumn("BAĞLI TEZGAH", options=MACHINE_OPTIONS, required=True, width="medium"),
                    "deadline": st.column_config.TextColumn("TERMİN TARİHİ", width="small"),
                    "notes": st.column_config.TextColumn("NOTLAR", width="large")
                }
            )

            if st.button(f"💾 {customer} Tablo Değişikliklerini Kaydet", key=f"save_{customer}", type="primary"):
                conn = get_db_connection()
                archived_count = 0
                
                for _, row in edited_df.iterrows():
                    j_id = int(row['id'])
                    new_status = str(row['status'])
                    
                    if new_status == "HAZIR":
                        end_now_dt = datetime.now()
                        end_now_str = end_now_dt.strftime("%d.%m.%Y %H:%M")
                        
                        orig_row = cust_df[cust_df['id'] == j_id].iloc[0]
                        duration_calc_str = "Belirtilmedi"
                        if orig_row['start_time']:
                            start_dt = parse_date(orig_row['start_time'])
                            if start_dt:
                                diff = end_now_dt - start_dt
                                days = diff.days
                                hours, remainder = divmod(diff.seconds, 3600)
                                minutes, _ = divmod(remainder, 60)
                                
                                parts = []
                                if days > 0: parts.append(f"{days} Gün")
                                if hours > 0: parts.append(f"{hours} Saat")
                                parts.append(f"{minutes} Dk")
                                duration_calc_str = " ".join(parts)

                        conn.execute('''
                            UPDATE work_orders 
                            SET job_name=?, material=?, dimensions=?, supplier=?, quantity=?, heat_treatment=?, status='HAZIR / TAMAMLANDI', machine_name='YOK / ATANMADI', deadline=?, notes=?, is_archived=1, end_time=?, duration_str=?
                            WHERE id=?
                        ''', (row['job_name'], row['material'], row['dimensions'], row['supplier'], row['quantity'], row['heat_treatment'], row['deadline'], row['notes'], end_now_str, duration_calc_str, j_id))
                        archived_count += 1
                    else:
                        conn.execute('''
                            UPDATE work_orders
                            SET job_name=?, material=?, dimensions=?, supplier=?, quantity=?, heat_treatment=?, status=?, machine_name=?, deadline=?, notes=?
                            WHERE id=?
                        ''', (row['job_name'], row['material'], row['dimensions'], row['supplier'], row['quantity'], row['heat_treatment'], new_status, row['machine_name'], row['deadline'], row['notes'], j_id))
                
                conn.commit()
                conn.close()
                
                if archived_count > 0:
                    st.toast(f"🎉 {archived_count} adet parça 'HAZIR' durumuna getirildi ve arşive aktarıldı!", icon="🎉")
                else:
                    st.toast(f"{customer} tablosu güncellendi!", icon="✅")
                st.rerun()

            with st.expander(f"📂 {customer} - Dosya Yükle / İndir & İşlem Yönetimi", expanded=False):
                for _, r in cust_df.iterrows():
                    j_id = int(r['id'])
                    
                    d_path = str(r['drawing_path']) if pd.notna(r['drawing_path']) and r['drawing_path'] else ""
                    d_name = str(r['drawing_name']) if pd.notna(r['drawing_name']) and r['drawing_name'] else "teknik_resim"
                    has_file = bool(d_path and os.path.exists(d_path))

                    c_info, c_badge, c_up, c_down, c_del = st.columns([3, 2.5, 3, 2, 1.5])
                    
                    with c_info:
                        st.write(f"**{r['job_name']}**")
                        st.caption(f"Başlangıç: {r['start_time'] or 'Kayıtlı değil'}")

                    with c_badge:
                        if has_file:
                            st.markdown(f"<div class='file-badge-success'>🟢 ✅ DOSYA YÜKLÜ<br><small style='color:#166534;'>{d_name}</small></div>", unsafe_allow_html=True)
                        else:
                            st.markdown("<div class='file-badge-none'>⚪ ❌ Dosya Yüklenmedi</div>", unsafe_allow_html=True)

                    with c_up:
                        up_f = st.file_uploader("Dosya Yükle", type=None, key=f"up_{j_id}", label_visibility="collapsed")
                        if up_f is not None:
                            original_filename = str(up_f.name)
                            save_filename = f"job_{j_id}_{original_filename}"
                            save_path = os.path.join("uploads", save_filename)
                            with open(save_path, "wb") as f:
                                f.write(up_f.getbuffer())
                            
                            conn = get_db_connection()
                            conn.execute("UPDATE work_orders SET drawing_path = ?, drawing_name = ? WHERE id = ?", (save_path, original_filename, j_id))
                            conn.commit()
                            conn.close()
                            st.toast(f"'{original_filename}' başarıyla yüklendi!", icon="📤")
                            st.rerun()

                    with c_down:
                        if has_file:
                            with open(d_path, "rb") as f_bytes:
                                file_data = f_bytes.read()
                            st.download_button(
                                label="📥 İndir",
                                data=file_data,
                                file_name=d_name,
                                key=f"dl_{j_id}"
                            )
                        else:
                            st.caption("-")

                    with c_del:
                        if st.button("🗑️ Sil", key=f"del_{j_id}"):
                            conn = get_db_connection()
                            conn.execute("DELETE FROM work_orders WHERE id = ?", (j_id,))
                            conn.commit()
                            conn.close()
                            st.warning("İş silindi!")
                            st.rerun()
                    st.divider()

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
# 3. ISIL İŞLEM TAKİP MODÜLÜ
# ---------------------------------------------------------
elif menu == "🔥 Isıl İşlem Takip":
    st.markdown("## 🔥 Isıl İşlem Takip Modülü")
    st.caption("Fason ısıl işleme gönderilen malzemelerin firma, sertlik, kg ve fatura durum takibi.")

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
                st.success("Isıl işlem gönderim kaydı başarıyla eklendi!")
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

        c_save, c_del_sel = st.columns([3, 2])
        with c_save:
            if st.button("💾 Isıl İşlem Tablo Değişikliklerini Kaydet", type="primary"):
                conn = get_db_connection()
                for _, row in edited_ht.iterrows():
                    conn.execute('''
                        UPDATE heat_treatment
                        SET sent_date=?, supplier_firm=?, customer=?, product_code_name=?, quantity=?, material=?, hardness=?, weight_kg=?, process_type=?, status=?, invoice_info=?
                        WHERE id=?
                    ''', (row['sent_date'], row['supplier_firm'], row['customer'], row['product_code_name'], row['quantity'], row['material'], row['hardness'], row['weight_kg'], row['process_type'], row['status'], row['invoice_info'], row['id']))
                conn.commit()
                conn.close()
                st.toast("Isıl işlem tablosu güncellendi!", icon="✅")
                st.rerun()

        with c_del_sel:
            ht_list = [f"{r['id']} - {r['customer']} ({r['product_code_name']})" for _, r in df_ht.iterrows()]
            sel_ht_del = st.selectbox("Silinecek Isıl İşlem Kaydını Seçin:", ht_list, key="sel_ht_del")
            if st.button("🗑️ Seçili Kaydı Sil"):
                if sel_ht_del:
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
    st.caption("Su jetinde kesilen parçaların adet, ölçü, birim fiyat ve fatura durum takibi.")

    with st.expander("➕ **Yeni Su Jeti (WJG) Kesim Kaydı Ekle**", expanded=False):
        with st.form("add_wjg_form", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                wjg_date = st.text_input("Kesim Tarihi *", value=datetime.now().strftime("%d.%m.%Y"))
                wjg_customer = st.text_input("Firma Adı *", placeholder="Ör: ANKUTSAN, OMKAR")
                wjg_part = st.text_input("Parça Tanımı *", placeholder="Ör: GAGALI SLOT BIÇAĞI")
            with col2:
                wjg_code = st.text_input("Parça Kodu", placeholder="Ör: LMC231")
                wjg_dims = st.text_input("Ölçü (mm)", placeholder="Ör: 231x48x10")
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
                st.success("Su jeti kesim kaydı eklendi!")
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

        c_save, c_del_sel = st.columns([3, 2])
        with c_save:
            if st.button("💾 Su Jeti Tablo Değişikliklerini Kaydet", type="primary"):
                conn = get_db_connection()
                for _, row in edited_wjg.iterrows():
                    conn.execute('''
                        UPDATE wjg_waterjet
                        SET sent_date=?, customer=?, part_name=?, part_code=?, dimensions=?, order_qty=?, received_qty=?, unit_price=?, invoice_info=?, status=?
                        WHERE id=?
                    ''', (row['sent_date'], row['customer'], row['part_name'], row['part_code'], row['dimensions'], row['order_qty'], row['received_qty'], row['unit_price'], row['invoice_info'], row['status'], row['id']))
                conn.commit()
                conn.close()
                st.toast("Su jeti tablosu güncellendi!", icon="✅")
                st.rerun()

        with c_del_sel:
            wjg_list = [f"{r['id']} - {r['customer']} ({r['part_name']})" for _, r in df_wjg.iterrows()]
            sel_wjg_del = st.selectbox("Silinecek Su Jeti Kaydını Seçin:", wjg_list, key="sel_wjg_del")
            if st.button("🗑️ Seçili Kaydı Sil ", key="btn_del_wjg"):
                if sel_wjg_del:
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
                    st.markdown(f"<div class='file-badge-success'>🟢 ✅ {arch_name}</div>", unsafe_allow_html=True)
                    with open(arch_path, "rb") as f_bytes:
                        file_data = f_bytes.read()
                    st.download_button(
                        label="📥 Yüklü Dosyayı İndir",
                        data=file_data,
                        file_name=arch_name,
                        key=f"arch_dl_{row['id']}"
                    )
                else:
                    st.markdown("<div class='file-badge-none'>⚪ Dosya Yüklenmemiş</div>", unsafe_allow_html=True)

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
                        st.toast("Fiyat, tezgah süreleri ve not kaydedildi!", icon="✅")
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
# 7. ATÖLYE SOHBETİ (MESAJ DÜZENLEME & SİLME BUTONLARI SAĞDA)
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
            
            st.markdown("<div class='custom-card' style='border-left: 5px solid #dc2626;'>", unsafe_allow_html=True)
            
            c_m_main, c_m_act = st.columns([4, 1])
            
            with c_m_main:
                st.markdown(f"**👤 {r['user_name']}** &nbsp;&nbsp; `<small style='color:#64748b;'>🕒 {r['created_at']}</small>`", unsafe_allow_html=True)
                st.write(r['message'])

            with c_m_act:
                # MESAJLARIN SAĞ TARAFINDAKİ DÜZENLE VE SİL BUTONLARI
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

            # DÜZENLEME FORMU AÇILDIĞINDA
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