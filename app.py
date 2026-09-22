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

# Premium Modern CSS Stilleri
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
# VERİTABANI BAĞLANTISI VE ŞEMA YÖNETİMİ
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
            created_at TEXT,
            is_archived INTEGER DEFAULT 0
        )
    ''')
    
    # Eksik Sütun Otomatik Kontrolü (machine_name vb.)
    cursor.execute("PRAGMA table_info(work_orders)")
    cols = [row[1] for row in cursor.fetchall()]
    if 'machine_name' not in cols:
        cursor.execute("ALTER TABLE work_orders ADD COLUMN machine_name TEXT")
        
    conn.commit()
    conn.close()

init_db()

# İŞLEMLER SEKMESİ SEÇENEKLERİ
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

# TEZGAH SEÇENEKLERİ LISTESI
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

# MALZEME SINIFLARI & ÖZGÜL AĞIRLIKLARI (g/cm3)
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
# SOL NAVİGASYON MENÜSÜ
# ---------------------------------------------------------
st.sidebar.markdown("### ⚙️ EŞME MAKİNA MES")
st.sidebar.caption("Üretim Takip & İmalat Yönetimi v3.0")
st.sidebar.divider()

menu = st.sidebar.radio(
    "Sistem Menüsü:",
    ["📊 İş Planı (Canlı Tablo)", "🛠️ Tezgah Parkı Durumu", "📚 İmalat Hafızası (Arşiv)", "💰 Akıllı Maliyet Hesabı"]
)

# ---------------------------------------------------------
# 1. İŞ PLANINI GÖRÜNTÜLE VE YÖNET (EXCEL MANTIĞI)
# ---------------------------------------------------------
if menu == "📊 İş Planı (Canlı Tablo)":
    st.markdown("## 📊 İŞ PLANI")
    st.caption("Aktif müşteri siparişleri ve canlı imalat durumları tablosu.")

    # Üst Kısım: Yeni İş Ekleme Formu
    with st.expander("➕ **Yeni İş / Parça Siparişi Ekle**", expanded=False):
        with st.form("add_job_form", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                cust = st.text_input("Firma / Müşteri Adı *", placeholder="Ör: PHILSA A.Ş.")
                job = st.text_input("İş / Parça Adı *", placeholder="Ör: OKP4746.M PLATE")
                mat = st.selectbox("Malzeme Türü", list(MATERIAL_DENSITIES.keys()))
            with col2:
                dims = st.text_input("Malzeme Ölçüleri", placeholder="Ör: 30x45x85 mm")
                supp = st.text_input("Malzeme Siparişi / Tedarikçi", placeholder="Ör: ATLAS METAL")
                qty = st.number_input("Adet", min_value=1, value=10)
            with col3:
                heat = st.text_input("Isıl İşlem - Kaplama", placeholder="Ör: 56-58 HRC")
                stt = st.selectbox("İlk Durum / İşlem", STATUS_OPTIONS)
                mac = st.selectbox("Bağlı Tezgah", MACHINE_OPTIONS)
                ddl = st.text_input("Termin Tarihi", placeholder="Ör: 15.09.2026 veya STOK")

            submitted = st.form_submit_button("🚀 Siparişi Veritabanına Ekle", type="primary")
            if submitted and cust and job:
                conn = get_db_connection()
                conn.execute('''
                    INSERT INTO work_orders (customer, job_name, material, dimensions, supplier, quantity, heat_treatment, status, machine_name, deadline, is_archived)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                ''', (cust.upper().strip(), job.strip(), mat, dims, supp, qty, heat, stt, mac, ddl))
                conn.commit()
                conn.close()
                st.success("İş başarıyla eklendi!")
                st.rerun()

    # Veritabanından Aktif İşleri Çek
    conn = get_db_connection()
    df_active = pd.read_sql_query("SELECT * FROM work_orders WHERE is_archived = 0 ORDER BY id ASC", conn)
    conn.close()

    if not df_active.empty:
        customers = df_active['customer'].unique()
        
        # FIRMA BAZLI TABLO GÖSTERİMİ (MODERN EXCEL BANTLARI)
        for customer in customers:
            cust_df = df_active[df_active['customer'] == customer].copy()
            
            # Tezgah sütunu eksikse varsayılan doldur
            if 'machine_name' not in cust_df.columns:
                cust_df['machine_name'] = "YOK / ATANMADI"
            cust_df['machine_name'] = cust_df['machine_name'].fillna("YOK / ATANMADI")
            
            # Modern Şerit Başlık
            st.markdown(f"""
                <div class="firm-header-band">
                    <span>🏢 {customer}</span>
                    <span class="count-badge">{len(cust_df)} Kalem İş</span>
                </div>
            """, unsafe_allow_html=True)
            
            # Tablo Sütun Düzenlemesi
            display_df = cust_df[['id', 'job_name', 'material', 'dimensions', 'supplier', 'quantity', 'heat_treatment', 'status', 'machine_name', 'deadline']].copy()
            display_df.columns = ['ID', 'İŞ', 'MALZEME', 'MALZEME ÖLÇÜLERİ', 'MALZEME SİPARİŞİ', 'ADET', 'ISIL İŞLEM- KAPLAMA', 'İŞLEMLER', 'BAĞLI TEZGAH', 'TERMİN TARİHİ']

            # İnteraktif Tablo (Doğrudan Hücreden Düzenleme)
            edited_df = st.data_editor(
                display_df,
                key=f"editor_{customer}",
                use_container_width=True,
                hide_index=True,
                column_config={
                    "ID": st.column_config.NumberColumn("ID", disabled=True, width="small"),
                    "İŞ": st.column_config.TextColumn("İŞ"),
                    "MALZEME": st.column_config.TextColumn("MALZEME"),
                    "MALZEME ÖLÇÜLERİ": st.column_config.TextColumn("MALZEME ÖLÇÜLERİ"),
                    "MALZEME SİPARİŞİ": st.column_config.TextColumn("MALZEME SİPARİŞİ"),
                    "ADET": st.column_config.NumberColumn("ADET"),
                    "ISIL İŞLEM- KAPLAMA": st.column_config.TextColumn("ISIL İŞLEM- KAPLAMA"),
                    "İŞLEMLER": st.column_config.SelectboxColumn("İŞLEMLER", options=STATUS_OPTIONS, required=True),
                    "BAĞLI TEZGAH": st.column_config.SelectboxColumn("BAĞLI TEZGAH", options=MACHINE_OPTIONS, required=True),
                    "TERMİN TARİHİ": st.column_config.TextColumn("TERMİN TARİHİ")
                }
            )

            # Tablo Altı İşlem Çubuğu (Kaydet, İş Bitir, Sil)
            col_save, col_select, col_finish, col_delete = st.columns([2, 3, 2, 2])
            
            with col_save:
                if st.button(f"💾 {customer} Değişiklikleri Kaydet", key=f"save_{customer}"):
                    conn = get_db_connection()
                    for _, row in edited_df.iterrows():
                        conn.execute('''
                            UPDATE work_orders
                            SET job_name=?, material=?, dimensions=?, supplier=?, quantity=?, heat_treatment=?, status=?, machine_name=?, deadline=?
                            WHERE id=?
                        ''', (row['İŞ'], row['MALZEME'], row['MALZEME ÖLÇÜLERİ'], row['MALZEME SİPARİŞİ'], row['ADET'], row['ISIL İŞLEM- KAPLAMA'], row['İŞLEMLER'], row['BAĞLI TEZGAH'], row['TERMİN TARİHİ'], row['ID']))
                    conn.commit()
                    conn.close()
                    st.toast("Tablo ve tezgah seçimleri kaydedildi!", icon="✅")
                    st.rerun()

            with col_select:
                job_list = [f"{r['id']} - {r['job_name']}" for _, r in cust_df.iterrows()]
                selected_job_str = st.selectbox("İş Seç:", job_list, key=f"sel_{customer}", label_visibility="collapsed")

            with col_finish:
                if st.button("🏁 İŞİ BİTİR (ARŞİVLE)", key=f"fin_{customer}", type="primary"):
                    if selected_job_str:
                        job_id = int(selected_job_str.split(" - ")[0])
                        conn = get_db_connection()
                        conn.execute("UPDATE work_orders SET is_archived = 1, status = 'TAMAMLANDI', machine_name = 'YOK / ATANMADI' WHERE id = ?", (job_id,))
                        conn.commit()
                        conn.close()
                        st.toast("İş tamamlandı ve arşive kaldırıldı!", icon="🎉")
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
# 2. TEZGAH PARKI DURUMU (CANLI TABLODAN BESLENİR)
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

    # Bağlı tezgahların eşleşmesi
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
# 3. İMALAT HAFIZASI (ARŞİV)
# ---------------------------------------------------------
elif menu == "📚 İmalat Hafızası (Arşiv)":
    st.markdown("## 📚 İmalat Hafızası & Biten İşler Arşivi")
    st.caption("Tamamlanıp arşive kaldırılan geçmiş işlerinizin detaylı dökümü.")
    
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
            col_text, col_del = st.columns([5, 1])
            with col_text:
                st.markdown(f"#### ✅ {row['job_name']}")
                st.write(f"• **Malzeme:** {row['material']} ({row['dimensions']})")
                st.write(f"• **Adet:** {row['quantity']} | **Tedarikçi:** {row['supplier']}")
                st.write(f"• **Isıl İşlem:** {row['heat_treatment']}")
            with col_del:
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
# 4. AKILLI MALİYET HESABI (TL BAZLI & MALZEME SINIFLARI)
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
        st.subheader("2. İşleme Süreleri & Kar Marjı")
        dik_süre = st.number_input("Dik İşleme Süresi (Dk):", value=30)
        torna_süre = st.number_input("CNC Torna Süresi (Dk):", value=15)
        rate_dik = st.number_input("Dik İşleme Saat Ücreti (TL/Saat):", value=1200.0)
        rate_torna = st.number_input("Torna Saat Ücreti (TL/Saat):", value=1000.0)
        heat_cost = st.number_input("Isıl İşlem / Kaplama Maliyeti (TL):", value=350.0)
        profit_margin = st.slider("Hedef Kar Marjı (%):", 0, 200, 35)
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