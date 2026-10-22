"""Dashboard Data Fiskal Kota - Streamlit

Jalankan dengan:
    streamlit run app.py
"""
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

# ----------------------------------------------------------------------------
# Konfigurasi halaman
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="Dashboard Fiskal Kota",
    page_icon="📊",
    layout="wide",
)

DATA_PATH = Path(__file__).parent / "data_fiskal.csv"

# ----------------------------------------------------------------------------
# Definisi kolom
# ----------------------------------------------------------------------------
KOMPONEN_DBH = ["DBH_PAJAK", "DBH_SDA", "DBH_Lainnya"]
KOMPONEN_DAU = ["DAU_Grant", "DAU_Earmark"]
KOMPONEN_DAK = ["DAK_Fisik", "DAK_Nonfisik"]
KOMPONEN_TRANSFER = KOMPONEN_DBH + KOMPONEN_DAU + KOMPONEN_DAK
KOLOM_BM = [
    "bm_pendidikan",
    "bm_kesehatan",
    "bm_perumahan",
    "bm_lingkungan",
    "bm_ekonomi",
    "bm_infrastruktur",
    "bm_pariwisata",
    "bm_perlindungan_sosial",
]
KOLOM_OUTCOME = ["KEMISKINAN", "PENGANGGURAN", "KETIMPANGAN", "IPM", "PE"]

LABEL = {
    "DBH_PAJAK": "DBH Pajak",
    "DBH_SDA": "DBH SDA",
    "DBH_Lainnya": "DBH Lainnya",
    "DAU_Grant": "DAU Grant",
    "DAU_Earmark": "DAU Earmark",
    "DAK_Fisik": "DAK Fisik",
    "DAK_Nonfisik": "DAK Nonfisik",
    "PAD": "PAD",
    "ICT": "ICT",
    "bm_pendidikan": "BM Pendidikan",
    "bm_kesehatan": "BM Kesehatan",
    "bm_perumahan": "BM Perumahan",
    "bm_lingkungan": "BM Lingkungan",
    "bm_ekonomi": "BM Ekonomi",
    "bm_infrastruktur": "BM Infrastruktur",
    "bm_pariwisata": "BM Pariwisata",
    "bm_perlindungan_sosial": "BM Perlindungan Sosial",
    "KEMISKINAN": "Kemiskinan",
    "PENGANGGURAN": "Pengangguran",
    "KETIMPANGAN": "Ketimpangan (Gini)",
    "IPM": "IPM",
    "PE": "Pertumbuhan Ekonomi",
    "Total_DBH": "Total DBH",
    "Total_DAU": "Total DAU",
    "Total_DAK": "Total DAK",
    "Total_Transfer": "Total Transfer",
    "Total_BM": "Total Belanja Modal",
}


def lbl(col: str) -> str:
    return LABEL.get(col, col)


# ----------------------------------------------------------------------------
# Load data
# ----------------------------------------------------------------------------
@st.cache_data(show_spinner="Memuat data...")
def load_data(source) -> pd.DataFrame:
    df = pd.read_csv(source)
    df["Tahun"] = df["Tahun"].astype(int)
    df["Kota_Pendek"] = (
        df["Kota"].str.replace(r"^(Kota|Kabupaten|Kab\.)\s+", "", regex=True).str.strip()
    )
    df["Total_DBH"] = df[KOMPONEN_DBH].sum(axis=1)
    df["Total_DAU"] = df[KOMPONEN_DAU].sum(axis=1)
    df["Total_DAK"] = df[KOMPONEN_DAK].sum(axis=1)
    df["Total_Transfer"] = df[KOMPONEN_TRANSFER].sum(axis=1)
    df["Total_BM"] = df[KOLOM_BM].sum(axis=1)
    return df


if DATA_PATH.exists():
    df_all = load_data(DATA_PATH)
else:
    st.warning(f"File `{DATA_PATH.name}` tidak ditemukan. Silakan upload CSV-nya.")
    up = st.file_uploader("Upload data_fiskal.csv", type="csv")
    if up is None:
        st.stop()
    df_all = load_data(up)

# ----------------------------------------------------------------------------
# Sidebar - filter
# ----------------------------------------------------------------------------
st.sidebar.title("🔎 Filter")

tahun_min, tahun_max = int(df_all["Tahun"].min()), int(df_all["Tahun"].max())
rentang = st.sidebar.slider(
    "Rentang tahun", tahun_min, tahun_max, (tahun_min, tahun_max)
)

semua_kota = sorted(df_all["Kota"].unique())
kota_dipilih = st.sidebar.multiselect(
    "Kota (kosong = semua)",
    semua_kota,
    default=[],
    help="Biarkan kosong untuk memakai seluruh kota.",
)

df = df_all[df_all["Tahun"].between(*rentang)]
if kota_dipilih:
    df = df[df["Kota"].isin(kota_dipilih)]

if df.empty:
    st.error("Tidak ada data untuk filter yang dipilih.")
    st.stop()

st.sidebar.caption(
    f"{df['Kota'].nunique()} kota · {len(df):,} observasi · "
    f"{rentang[0]}–{rentang[1]}"
)

# ----------------------------------------------------------------------------
# Header & KPI
# ----------------------------------------------------------------------------
st.title("📊 Dashboard Fiskal Kota")
st.caption(
    "Transfer ke daerah (DBH, DAU, DAK), PAD, belanja modal per sektor, "
    "dan indikator kesejahteraan. Nilai ditampilkan sesuai satuan pada data."
)

rata_tahun = df.groupby("Tahun").mean(numeric_only=True)
tahun_akhir = rata_tahun.index.max()
tahun_awal = rata_tahun.index.min()


def kpi(col, nama, kolom, fmt="{:,.1f}", inverse=False):
    nilai = rata_tahun.loc[tahun_akhir, kolom]
    delta = None
    if tahun_akhir != tahun_awal:
        delta = nilai - rata_tahun.loc[tahun_awal, kolom]
    col.metric(
        f"{nama} ({tahun_akhir})",
        fmt.format(nilai),
        None if delta is None else f"{delta:+,.2f} vs {tahun_awal}",
        delta_color="inverse" if inverse else "normal",
    )


c1, c2, c3, c4, c5 = st.columns(5)
kpi(c1, "Rata-rata PAD", "PAD")
kpi(c2, "Rata-rata Total Transfer", "Total_Transfer")
kpi(c3, "Kemiskinan", "KEMISKINAN", "{:.2f}", inverse=True)
kpi(c4, "IPM", "IPM", "{:.2f}")
kpi(c5, "Pertumbuhan Ekonomi", "PE", "{:.2f}")

st.divider()

# ----------------------------------------------------------------------------
# Tabs
# ----------------------------------------------------------------------------
tab_tren, tab_pendapatan, tab_belanja, tab_kota, tab_korelasi, tab_data = st.tabs(
    [
        "📈 Tren",
        "💰 Pendapatan & Transfer",
        "🏗️ Belanja Modal",
        "🏙️ Perbandingan Kota",
        "🔗 Korelasi",
        "🗂️ Data",
    ]
)

SEMUA_INDIKATOR = (
    ["PAD", "Total_Transfer", "Total_DBH", "Total_DAU", "Total_DAK", "Total_BM", "ICT"]
    + KOLOM_OUTCOME
)

# ---- Tab 1: Tren ------------------------------------------------------------
with tab_tren:
    st.subheader("Tren rata-rata per tahun")
    pilih = st.multiselect(
        "Pilih indikator",
        SEMUA_INDIKATOR,
        default=["PAD", "Total_Transfer"],
        format_func=lbl,
    )
    normalisasi = st.checkbox(
        "Normalisasi (indeks, tahun awal = 100) agar skala berbeda bisa dibandingkan",
        value=len(pilih) > 2,
    )
    if pilih:
        tren = rata_tahun[pilih].copy()
        if normalisasi:
            tren = tren / tren.iloc[0] * 100
        tren = tren.rename(columns=LABEL).reset_index()
        tren = tren.melt("Tahun", var_name="Indikator", value_name="Nilai")
        fig = px.line(tren, x="Tahun", y="Nilai", color="Indikator", markers=True)
        fig.update_xaxes(dtick=1)
        fig.update_layout(legend_title_text="", hovermode="x unified")
        st.plotly_chart(fig)
    else:
        st.info("Pilih minimal satu indikator.")

    st.subheader("Sebaran antar kota per tahun")
    ind_box = st.selectbox(
        "Indikator", SEMUA_INDIKATOR, index=SEMUA_INDIKATOR.index("IPM"), format_func=lbl
    )
    fig = px.box(df, x="Tahun", y=ind_box, points="outliers")
    fig.update_layout(yaxis_title=lbl(ind_box))
    st.plotly_chart(fig)

# ---- Tab 2: Pendapatan & Transfer -------------------------------------------
with tab_pendapatan:
    st.subheader("Struktur transfer ke daerah (rata-rata per kota)")
    struktur = rata_tahun[KOMPONEN_TRANSFER].rename(columns=LABEL).reset_index()
    struktur = struktur.melt("Tahun", var_name="Komponen", value_name="Nilai")
    fig = px.bar(struktur, x="Tahun", y="Nilai", color="Komponen", barmode="stack")
    fig.update_xaxes(dtick=1)
    fig.update_layout(legend_title_text="")
    st.plotly_chart(fig)

    col_a, col_b = st.columns(2)
    with col_a:
        thn = st.selectbox(
            "Komposisi pada tahun",
            sorted(df["Tahun"].unique(), reverse=True),
            key="thn_pie",
        )
        kom = (
            df[df["Tahun"] == thn][KOMPONEN_TRANSFER + ["PAD"]]
            .mean()
            .rename(index=LABEL)
            .reset_index()
        )
        kom.columns = ["Komponen", "Nilai"]
        fig = px.pie(kom, names="Komponen", values="Nilai", hole=0.45)
        fig.update_layout(title=f"Komposisi pendapatan rata-rata ({thn})")
        st.plotly_chart(fig)
    with col_b:
        st.markdown("**Ketergantungan fiskal** (Total Transfer ÷ (Transfer + PAD))")
        tmp = df.copy()
        tmp["Rasio_Ketergantungan"] = tmp["Total_Transfer"] / (
            tmp["Total_Transfer"] + tmp["PAD"]
        )
        rasio = tmp.groupby("Tahun")["Rasio_Ketergantungan"].mean().reset_index()
        fig = px.line(rasio, x="Tahun", y="Rasio_Ketergantungan", markers=True)
        fig.update_yaxes(tickformat=".0%", title="Rasio ketergantungan")
        fig.update_xaxes(dtick=1)
        st.plotly_chart(fig)

# ---- Tab 3: Belanja Modal ---------------------------------------------------
with tab_belanja:
    st.subheader("Belanja modal per sektor (rata-rata per kota)")
    bm = rata_tahun[KOLOM_BM].rename(columns=LABEL).reset_index()
    bm = bm.melt("Tahun", var_name="Sektor", value_name="Nilai")
    fig = px.area(bm, x="Tahun", y="Nilai", color="Sektor")
    fig.update_xaxes(dtick=1)
    fig.update_layout(legend_title_text="")
    st.plotly_chart(fig)

    st.subheader("Peta panas belanja modal: kota × sektor")
    thn_bm = st.selectbox(
        "Tahun",
        sorted(df["Tahun"].unique(), reverse=True),
        key="thn_bm",
    )
    n_kota = st.slider("Tampilkan N kota teratas (berdasar total BM)", 5, 50, 20)
    d = df[df["Tahun"] == thn_bm].nlargest(n_kota, "Total_BM")
    heat = d.set_index("Kota_Pendek")[KOLOM_BM].rename(columns=LABEL)
    fig = px.imshow(
        heat,
        aspect="auto",
        color_continuous_scale="YlGnBu",
        labels=dict(color="Nilai"),
    )
    fig.update_layout(height=max(400, 22 * len(heat)))
    st.plotly_chart(fig)

# ---- Tab 4: Perbandingan Kota -----------------------------------------------
with tab_kota:
    st.subheader("Peringkat kota")
    c1, c2, c3 = st.columns([2, 1, 1])
    ind_rank = c1.selectbox(
        "Indikator", SEMUA_INDIKATOR, format_func=lbl, key="ind_rank"
    )
    thn_rank = c2.selectbox(
        "Tahun",
        sorted(df["Tahun"].unique(), reverse=True),
        key="thn_rank",
    )
    top_n = c3.slider("Jumlah kota", 5, 30, 10, key="top_n")
    urut = st.radio(
        "Urutan", ["Tertinggi", "Terendah"], horizontal=True, key="urut_rank"
    )

    d = df[df["Tahun"] == thn_rank]
    d = d.nlargest(top_n, ind_rank) if urut == "Tertinggi" else d.nsmallest(top_n, ind_rank)
    d = d.sort_values(ind_rank, ascending=(urut == "Tertinggi"))
    fig = px.bar(d, x=ind_rank, y="Kota", orientation="h", text_auto=".2f")
    fig.update_layout(xaxis_title=lbl(ind_rank), yaxis_title="")
    st.plotly_chart(fig)

    st.subheader("Bandingkan kota dari waktu ke waktu")
    default_kota = list(df["Kota"].unique()[:3])
    banding = st.multiselect(
        "Pilih kota (maks. 8 disarankan)",
        sorted(df["Kota"].unique()),
        default=default_kota,
        key="kota_banding",
    )
    ind_banding = st.selectbox(
        "Indikator", SEMUA_INDIKATOR, format_func=lbl, key="ind_banding"
    )
    if banding:
        d = df[df["Kota"].isin(banding)]
        fig = px.line(d, x="Tahun", y=ind_banding, color="Kota", markers=True)
        fig.update_xaxes(dtick=1)
        fig.update_layout(yaxis_title=lbl(ind_banding), legend_title_text="")
        st.plotly_chart(fig)
    else:
        st.info("Pilih minimal satu kota.")

# ---- Tab 5: Korelasi --------------------------------------------------------
with tab_korelasi:
    st.subheader("Matriks korelasi")
    kolom_korelasi = st.multiselect(
        "Variabel",
        [c for c in LABEL if c in df.columns],
        default=["PAD", "Total_DBH", "Total_DAU", "Total_DAK", "Total_BM"] + KOLOM_OUTCOME,
        format_func=lbl,
    )
    if len(kolom_korelasi) >= 2:
        corr = df[kolom_korelasi].corr().rename(index=LABEL, columns=LABEL)
        fig = px.imshow(
            corr,
            text_auto=".2f",
            zmin=-1,
            zmax=1,
            color_continuous_scale="RdBu_r",
            aspect="auto",
        )
        st.plotly_chart(fig)
        st.caption(
            "Korelasi tidak menunjukkan hubungan sebab-akibat; "
            "gunakan sebagai petunjuk awal untuk analisis lebih lanjut."
        )
    else:
        st.info("Pilih minimal dua variabel.")

    st.subheader("Scatter plot")
    c1, c2, c3 = st.columns(3)
    x_var = c1.selectbox(
        "Sumbu X", SEMUA_INDIKATOR, format_func=lbl, key="x_var"
    )
    y_var = c2.selectbox(
        "Sumbu Y",
        SEMUA_INDIKATOR,
        index=SEMUA_INDIKATOR.index("IPM"),
        format_func=lbl,
        key="y_var",
    )
    warna = c3.selectbox("Warna", ["Tahun", "Tidak ada"], key="warna_sc")
    fig = px.scatter(
        df,
        x=x_var,
        y=y_var,
        color="Tahun" if warna == "Tahun" else None,
        hover_name="Kota",
        trendline="ols",
        trendline_scope="overall",
        opacity=0.65,
    )
    fig.update_layout(xaxis_title=lbl(x_var), yaxis_title=lbl(y_var))
    st.plotly_chart(fig)

# ---- Tab 6: Data ------------------------------------------------------------
with tab_data:
    st.subheader("Data terfilter")
    tampil = df.drop(columns=["Kota_Pendek"])
    st.dataframe(tampil, hide_index=True)
    st.download_button(
        "⬇️ Unduh CSV (terfilter)",
        tampil.to_csv(index=False).encode("utf-8"),
        file_name="data_fiskal_terfilter.csv",
        mime="text/csv",
    )
    with st.expander("Statistik deskriptif"):
        st.dataframe(tampil.describe().T)
