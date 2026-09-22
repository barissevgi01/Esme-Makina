import streamlit as st
import pandas as pd
import sqlite3
import math
from datetime import datetime

# ---------------------------------------------------------
# SAYFA YAPILANDIRMASI & ÖZEL MODERN CSS
# ---------------------------------------------------------
st.set_page_config(
    page_title="Eşme Makina MES - İş Planı",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
# VERİTABANI VE ŞEMA MİGRASYONU
# ---------------------------------------------------------
def get_db_connection():
    conn = sqlite3.connect('esme_makina_uretim.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
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
            created_at TEXT,
            is_archived INTEGER DEFAULT 0
        )
    ''')
    
    # Eksik Sütun Otomatik Ekleme
    cursor.execute("PRAGMA table_info(work_orders)")
    cols = [row[1] for row in cursor.fetchall()]
    
    columns_to_add = [
        ('machine_name', 'TEXT'),
        ('notes', 'TEXT'),
        ('start_time', 'TEXT'),
        ('end_time', 'TEXT'),
        ('duration_str', 'TEXT'),
        ('price', 'REAL'),
        ('is_archived', 'INTEGER DEFAULT 0')
    ]
    
    for col_name, col_type in columns_to_add:
        if col_name not in cols:
            cursor.execute(f"ALTER TABLE work_orders ADD COLUMN {col_name} {col_type}")
            
    conn.commit()
    conn.close()

init_db()

# İŞLEMLER LISTESI
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
    "ASM LAZER"
]

# TEZGAH SEÇENEKLERİ
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

# MALZEME ÖZGÜL AĞIRLIKLARI (g/cm3)
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

# ---------------------------------------------------------
# TARIH HESAPLAMA YARDIMCI FONKSİYONU
# ---------------------------------------------------------
def parse_date(date_str):
    if not date_str:
        return None
    for fmt in ("%d.%m.%Y %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%d.%m.%Y"):
        try:
            return datetime.strptime(str(date_str).strip(), fmt)
        except ValueError:
            pass
    return None

# ---------------------------------------------------------
# SOL NAVİGASYON MENÜSÜ
# ---------------------------------------------------------
st.sidebar.markdown("### ⚙️ EŞME MAKİNA MES")
st.sidebar.caption("Üretim Takip & İmalat Yönetimi v3.6")
st.sidebar.divider()

menu = st.sidebar.radio(
    "Sistem Menüsü:",
    ["📊 İş Planı (Canlı Tablo)", "🛠️ Tezgah Parkı Durumu", "📚 İmalat Hafızası (Arşiv)", "💰 Akıllı Maliyet Hesabı"]
)

# ---------------------------------------------------------
# 1. İŞ PLANINI GÖRÜNTÜLE VE YÖNET
# ---------------------------------------------------------
if menu == "📊 İş Planı (Canlı Tablo)":
    st.markdown("## 📊 İŞ PLANI")
    st.caption("Aktif müşteri siparişleri ve canlı imalat durumları tablosu.")

    # Yeni İş Ekleme Formu
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

            initial_note = st.text_area("İş Notları (Opsiyonel)", placeholder="İşle ilgili özel notlar veya talimatlar...")

            submitted = st.form_submit_button("🚀 Siparişi Ekle ve Süreyi Başlat", type="primary")
            if submitted and cust and job:
                start_now = datetime.now().strftime("%d.%m.%Y %H:%M")
                conn = get_db_connection()
                conn.execute('''
                    INSERT INTO work_orders 
                    (customer, job_name, material, dimensions, supplier, quantity, heat_treatment, status, machine_name, deadline, notes, start_time, created_at, is_archived)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                ''', (cust.upper().strip(), job.strip(), mat.strip(), dims.strip(), supp.strip(), qty, heat.strip(), stt, mac, ddl.strip(), initial_note.strip(), start_now, start_now))
                conn.commit()
                conn.close()
                st.success("İş eklendi ve süre takibi başlatıldı!")
                st.rerun()

    # Veritabanından Aktif İşleri Çek
    conn = get_db_connection()
    df_active = pd.read_sql_query("SELECT * FROM work_orders WHERE is_archived = 0 ORDER BY id ASC", conn)
    conn.close()

    if not df_active.empty:
        customers = df_active['customer'].unique()
        
        for customer in customers:
            cust_df = df_active[df_active['customer'] == customer].copy()
            
            if 'machine_name' not in cust_df.columns:
                cust_df['machine_name'] = "YOK / ATANMADI"
            cust_df['machine_name'] = cust_df['machine_name'].fillna("YOK / ATANMADI")
            cust_df['notes'] = cust_df['notes'].fillna("")
            
            # Modern Şerit Başlık
            st.markdown(f"""
                <div class="firm-header-band">
                    <span>🏢 {customer}</span>
                    <span class="count-badge">{len(cust_df)} Kalem İş</span>
                </div>
            """, unsafe_allow_html=True)
            
            # Tablo Sütun Düzenlemesi
            display_df = cust_df[['id', 'job_name', 'material', 'dimensions', 'supplier', 'quantity', 'heat_treatment', 'status', 'machine_name', 'deadline', 'notes']].copy()

            # İnteraktif Tablo (column_order ile ID gizleniyor)
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

            # Tablo Altı İşlem Çubuğu
            col_save, col_select, col_finish, col_delete = st.columns([2, 3, 2, 2])
            
            with col_save:
                if st.button(f"💾 {customer} Kaydet", key=f"save_{customer}"):
                    conn = get_db_connection()
                    for _, row in edited_df.iterrows():
                        conn.execute('''
                            UPDATE work_orders
                            SET job_name=?, material=?, dimensions=?, supplier=?, quantity=?, heat_treatment=?, status=?, machine_name=?, deadline=?, notes=?
                            WHERE id=?
                        ''', (row['job_name'], row['material'], row['dimensions'], row['supplier'], row['quantity'], row['heat_treatment'], row['status'], row['machine_name'], row['deadline'], row['notes'], row['id']))
                    conn.commit()
                    conn.close()
                    st.toast("Tablo ve notlar kaydedildi!", icon="✅")
                    st.rerun()

            with col_select:
                job_list = [f"{r['id']} - {r['job_name']}" for _, r in cust_df.iterrows()]
                selected_job_str = st.selectbox("İş Seç:", job_list, key=f"sel_{customer}", label_visibility="collapsed")

            with col_finish:
                if st.button("🏁 İŞİ BİTİR (ARŞİVLE)", key=f"fin_{customer}", type="primary"):
                    if selected_job_str:
                        job_id = int(selected_job_str.split(" - ")[0])
                        
                        # Bitiş zamanı ve Süre Hesaplama
                        end_now_dt = datetime.now()
                        end_now_str = end_now_dt.strftime("%d.%m.%Y %H:%M")
                        
                        conn = get_db_connection()
                        job_row = conn.execute("SELECT start_time FROM work_orders WHERE id = ?", (job_id,)).fetchone()
                        
                        duration_calc_str = "Belirtilmedi"
                        if job_row and job_row['start_time']:
                            start_dt = parse_date(job_row['start_time'])
                            if start_dt:
                                diff = end_now_dt - start_dt
                                days = diff.days
                                hours, remainder = divmod(diff.seconds, 3600)
                                minutes, _ = divmod(remainder, 60)
                                
                                parts = []
                                if days > 0:
                                    parts.append(f"{days} Gün")
                                if hours > 0:
                                    parts.append(f"{hours} Saat")
                                parts.append(f"{minutes} Dk")
                                duration_calc_str = " ".join(parts)

                        conn.execute('''
                            UPDATE work_orders 
                            SET is_archived = 1, status = 'TAMAMLANDI', machine_name = 'YOK / ATANMADI', end_time = ?, duration_str = ? 
                            WHERE id = ?
                        ''', (end_now_str, duration_calc_str, job_id))
                        conn.commit()
                        conn.close()
                        st.toast(f"İş tamamlandı! Geçen Süre: {duration_calc_str}", icon="🎉")
                        st.rerun()

            with col_delete:
                if st.button("🗑️ İŞİ SİL", key=f"del_{customer}"):
                    if selected_job_str:
                        job_id = int(selected_job_str.split(" - ")[0])
                        conn = get_db_connection()
                        conn.execute("DELETE FROM work_orders WHERE id = ?", (job_id,))
                        conn.commit()
                        conn.close()
                        st.warning("İş silindi!")
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
# 3. İMALAT HAFIZASI (ARŞİV, SÜRE, NOT & FİYAT DÜZENLEME)
# ---------------------------------------------------------
elif menu == "📚 İmalat Hafızası (Arşiv)":
    st.markdown("## 📚 İmalat Hafızası & Biten İşler Arşivi")
    st.caption("Tamamlanıp arşive kaldırılan geçmiş işlerinizin detaylı dökümü, imalat süreleri ve fiyat kayıtları.")
    
    conn = get_db_connection()
    df_arch = pd.read_sql_query("SELECT * FROM work_orders WHERE is_archived = 1 ORDER BY id DESC", conn)
    conn.close()

    if not df_arch.empty:
        customers = df_arch['customer'].unique()
        selected_cust = st.selectbox("📁 Firma Filtrele:", customers)
        
        cust_df = df_arch[df_arch['customer'] == selected_cust]
        st.subheader(f"🏢 {selected_cust} Firmasına Ait Arşiv Kayıtları")

        for _, row in cust_df.iterrows():
            st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
            
            c1, c2, c3 = st.columns([3, 3, 2])
            
            with c1:
                st.markdown(f"#### ✅ {row['job_name']}")
                st.write(f"• **Malzeme:** {row['material'] or '-'} ({row['dimensions'] or '-'})")
                st.write(f"• **Adet:** {row['quantity']} | **Tedarikçi:** {row['supplier'] or '-'}")
                st.write(f"• **Isıl İşlem:** {row['heat_treatment'] or '-'}")

            with c2:
                st.markdown("##### ⏱️ İmalat Süre Bilgileri")
                st.write(f"• **Başlama Tarihi:** {row['start_time'] or '-'}")
                st.write(f"• **Bitiş Tarihi:** {row['end_time'] or '-'}")
                st.info(f"⏳ **Geçen Toplam Süre:** {row['duration_str'] or 'Belirtilmedi'}")

            with c3:
                st.markdown("##### 💵 Fiyat & Not Düzenle")
                current_price = float(row['price']) if row['price'] is not None else 0.0
                price_val = st.number_input("İmalat Fiyatı (TL):", min_value=0.0, value=current_price, step=100.0, key=f"p_{row['id']}")
                note_val = st.text_area("Arşiv Notu:", value=row['notes'] or "", key=f"n_{row['id']}", height=80)
                
                b1, b2 = st.columns(2)
                with b1:
                    if st.button("💾 Kaydet", key=f"arch_save_{row['id']}"):
                        conn = get_db_connection()
                        conn.execute("UPDATE work_orders SET price = ?, notes = ? WHERE id = ?", (price_val, note_val, row['id']))
                        conn.commit()
                        conn.close()
                        st.toast("Fiyat ve not güncellendi!", icon="✅")
                        st.rerun()
                with b2:
                    if st.button("🗑️ Sil", key=f"arch_del_{row['id']}"):
                        conn = get_db_connection()
                        conn.execute("DELETE FROM work_orders WHERE id = ?", (row['id'],))
                        conn.commit()
                        conn.close()
                        st.toast("İş arşivden tamamen silindi!", icon="🗑️")
                        st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("Arşivde henüz tamamlanmış iş bulunmuyor.")

# ---------------------------------------------------------
# 4. AKILLI MALİYET HESABI
# ---------------------------------------------------------
elif menu == "💰 Akıllı Maliyet Hesabı":
    st.markdown("## 💰 Akıllı Malzeme Ağırlığı & Maliyet Hesabı (TL)")
    st.caption("Ölçüleri girerek parçanın teorik kg ağırlığını ve TL cinsinden birim imalat fiyatını hesaplayın.")
    
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
        st.subheader("2. İşleme Süreleri & Manuel Kar Marjı")
        dik_süre = st.number_input("Dik İşleme Süresi (Dk):", value=30)
        torna_süre = st.number_input("CNC Torna Süresi (Dk):", value=15)
        rate_dik = st.number_input("Dik İşleme Saat Ücreti (TL/Saat):", value=1200.0)
        rate_torna = st.number_input("Torna Saat Ücreti (TL/Saat):", value=1000.0)
        heat_cost = st.number_input("Isıl İşlem / Kaplama Maliyeti (TL):", value=350.0)
        
        # MANUEL KAR MARJI GİRİŞİ (%666 vb. yazılabilir)
        profit_margin = st.number_input("Hedef Kar Marjı (%):", min_value=0.0, value=35.0, step=5.0)
        st.markdown("</div>", unsafe_allow_html=True)

    # Maliyet Hesaplama
    raw_cost = calculated_weight * unit_mat_price
    machining_cost = ((dik_süre/60)*rate_dik) + ((torna_süre/60)*rate_torna)
    total_cost = raw_cost + machining_cost + heat_cost
    final_price = total_cost * (1 + (profit_margin / 100))

    st.divider()
    st.subheader("📊 Finansal Özet Metrikleri (TL)")
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Hammadde Tutarı", f"{round(raw_cost, 2):,} TL".replace(",", "."))
    m2.metric("Net Yalın İmalat Maliyeti", f"{round(total_cost, 2):,} TL".replace(",", "."))
    m3.metric("Önerilen Birim Satış Fiyatı", f"{round(final_price, 2):,} TL".replace(",", "."), delta=f"%{profit_margin} Kar")