import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from babel.numbers import format_number

# ====================
# KONFIGURASI VISUAL
# ====================
sns.set_style("whitegrid", {'grid.linestyle': '--', 'grid.alpha': 0.4})
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial']
plt.rcParams['axes.titlesize'] = 16
plt.rcParams['axes.labelsize'] = 12

# Palette Warna
SEASON_COLORS = ["#FF9AA2", "#FFB7B2", "#FFDAC1", "#E2F0CB"]  # Warna pastel untuk musim
MAIN_COLOR = "#3498db"  # Biru untuk elemen utama
SECONDARY_COLOR = "#e74c3c"  # Merah untuk highlight
WEATHER_COLORS = ["#3498db", "#e74c3c"]  # Untuk cuaca cerah vs berkabut

# Mapping labels
SEASON_LABELS = {1: "Semi", 2: "Panas", 3: "Gugur", 4: "Dingin"}
WEATHER_LABELS = {1: "Cerah", 2: "Berkabut", 3: "Hujan/Salju", 4: "Hujan Lebat"}
DAY_TYPE_LABELS = {0: "Weekend/Holiday", 1: "Weekday"}

# ====================
# FUNGSI UTAMA
# ====================
def load_data():
    df = pd.read_csv("all_data.csv")
    df['dteday'] = pd.to_datetime(df['dteday'])
    df['season_label'] = df['season'].map(SEASON_LABELS)
    df['weather_label'] = df['weathersit'].map(WEATHER_LABELS)
    df['day_type'] = df['workingday'].map(DAY_TYPE_LABELS)
    return df

def create_daily_summary(df):
    return df.resample('D', on='dteday').agg({
        'cnt': ['sum', 'mean', 'max']
    }).reset_index()

# ====================
# LOAD DATA
# ====================
all_df = load_data()

# ====================
# SIDEBAR FILTER
# ====================
min_date = all_df['dteday'].min().date()
max_date = all_df['dteday'].max().date()

with st.sidebar:
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.image("https://camo.githubusercontent.com/e7e99e60ef795eb3ae37545e6a1f84391d462097d74c69d378daaab5660ed444/687474703a2f2f6369747962696b2e65732f66696c65732f707962696b65732e706e67", 
                 width=150)
    
    st.header("Filter Data")
    
    # Date range filter
    start_date, end_date = st.date_input(
        label='Rentang Waktu',
        min_value=min_date,
        max_value=max_date,
        value=[min_date, max_date]
    )
    
    # Additional filters
    selected_seasons = st.multiselect(
        "Pilih Musim",
        options=list(SEASON_LABELS.values()),
        default=list(SEASON_LABELS.values())
    )
    
    selected_day_types = st.multiselect(
        "Pilih Jenis Hari",
        options=list(DAY_TYPE_LABELS.values()),
        default=list(DAY_TYPE_LABELS.values())
    )

# ====================
# PROCESS DATA
# ====================
main_df = all_df[
    (all_df['dteday'].dt.date >= start_date) & 
    (all_df['dteday'].dt.date <= end_date) &
    (all_df['season_label'].isin(selected_seasons)) &
    (all_df['day_type'].isin(selected_day_types))
]

# Cek apakah main_df kosong
if main_df.empty:
    st.warning("Tidak ada data yang bisa kamu lihat, silahkan coba filter lainnya.")
else:
    daily_summary = create_daily_summary(main_df)
    max_day = main_df.loc[main_df['cnt'].idxmax()]
    min_day = main_df.loc[main_df['cnt'].idxmin()]

    # ====================
    # DASHBOARD LAYOUT
    # ====================
    st.title('Bike Sharing Analytics 🚲')
    st.markdown("""
    Dashboard ini menampilkan analisis pola penyewaan sepeda berdasarkan berbagai faktor seperti musim, 
    cuaca, dan jenis hari. Gunakan filter di sidebar untuk menyesuaikan tampilan data.
    """)

    # SECTION 1: METRIC UTAMA
    st.header("📊 Ringkasan Utama")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Penyewaan", 
                 value=f"{daily_summary['cnt']['sum'].sum():,}",
                 help="Total sepeda yang disewa dalam periode terpilih")
        
    with col2:
        st.metric("Rata-rata Harian", 
                 value=f"{daily_summary['cnt']['mean'].mean():.0f}",
                 help="Rata-rata penyewaan per hari")
        
    with col3:
        st.metric("Puncak Tertinggi", 
                 value=f"{daily_summary['cnt']['max'].max():,}",
                 help="Penyewaan tertinggi dalam satu hari")

    # SECTION 2: TREN HARIAN
    st.header("📈 Tren Harian Penyewaan")
    fig, ax = plt.subplots(figsize=(16, 6))
    sns.lineplot(
        data=daily_summary,
        x='dteday',
        y=('cnt', 'sum'),
        color=MAIN_COLOR,
        linewidth=2.5,
        marker='o',
        markersize=8
    )

    ax.set_title("Perkembangan Jumlah Penyewaan Harian", pad=20)
    ax.set_xlabel("Tanggal")
    ax.set_ylabel("Jumlah Penyewaan")
    ax.grid(True, alpha=0.3)

    # Highlight puncak tertinggi
    max_point = daily_summary.loc[daily_summary[('cnt', 'sum')].idxmax()]
    ax.annotate(f'Puncak: {max_point[("cnt", "sum")]:,}',
                xy=(max_point['dteday'], max_point[('cnt', 'sum')]),
                xytext=(max_point['dteday'], max_point[('cnt', 'sum')] + 500),
                arrowprops=dict(facecolor=SECONDARY_COLOR, shrink=0.05),
                ha='center')

    st.pyplot(fig)

    # SECTION 3: ANALISIS MUSIMAN (Pertanyaan 1)
    st.header("🍂 Analisis Musiman")
    st.markdown("**Bagaimana distribusi penyewaan tertinggi dan terendah dalam satu musim bila diukur dengan jam serta hari?**")

    season_summary = main_df.groupby(['season', 'season_label']).agg({
        'cnt': ['max', 'min'],
        'dteday': ['first', 'last'],
        'hr': ['first', 'last']
    }).reset_index()

    # Rename columns for easier access
    season_summary.columns = ['season', 'season_label', 'cnt_max', 'cnt_min', 
                             'dteday_first', 'dteday_last', 'hr_first', 'hr_last']

    # Find the actual days with max/min counts
    max_days = main_df.loc[main_df.groupby('season')['cnt'].idxmax()]
    min_days = main_df.loc[main_df.groupby('season')['cnt'].idxmin()]

    season_summary = season_summary.merge(
        max_days[['season', 'dteday', 'hr', 'cnt']].rename(columns={
            'dteday': 'dteday_max',
            'hr': 'hr_max',
            'cnt': 'cnt_max_actual'
        }),
        on='season'
    ).merge(
        min_days[['season', 'dteday', 'hr', 'cnt']].rename(columns={
            'dteday': 'dteday_min',
            'hr': 'hr_min',
            'cnt': 'cnt_min_actual'
        }),
        on='season'
    )

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(24, 8))
    fig.suptitle('Analisis Penyewaan Sepeda per Musim', y=1.02, fontsize=18, fontweight='bold')

    # Plot penyewaan TERTINGGI per musim
    sns.barplot(
        data=season_summary,
        x="season_label",
        y="cnt_max_actual",
        hue="season_label",
        palette=SEASON_COLORS,
        ax=ax1,
        edgecolor='black',
        linewidth=1,
        legend=False
    )
    ax1.set_title("Jumlah Penyewaan Tertinggi per Musim", fontsize=16, pad=20)
    ax1.set_xlabel("Musim", fontsize=14, labelpad=10)
    ax1.set_ylabel("Jumlah Penyewaan", fontsize=14, labelpad=10)

    # Tambahkan label detail
    for i, row in season_summary.iterrows():
        ax1.text(
            i, 
            row["cnt_max_actual"] * 0.05,
            f'Hari: {row["dteday_max"].strftime("%d %b %Y")}\nJam: {int(row["hr_max"])}:00\nTotal: {row["cnt_max_actual"]:,}',
            ha='center', 
            va='bottom', 
            fontsize=11,
            bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', boxstyle='round,pad=0.3')
        )

    # Plot penyewaan TERENDAH per musim
    sns.barplot(
        data=season_summary,
        x="season_label",
        y="cnt_min_actual",
        hue="season_label",
        palette=SEASON_COLORS,
        ax=ax2,
        edgecolor='black',
        linewidth=1,
        legend=False
    )
    ax2.set_title("Jumlah Penyewaan Terendah per Musim", fontsize=16, pad=20)
    ax2.set_xlabel("Musim", fontsize=14, labelpad=10)
    ax2.set_ylabel("Jumlah Penyewaan", fontsize=14, labelpad=10)

    # Tambahkan label detail
    for i, row in season_summary.iterrows():
        ax2.text(
            i, 
            row["cnt_min_actual"] * 1.2,
            f'Hari: {row["dteday_min"].strftime("%d %b %Y")}\nJam: {int(row["hr_min"])}:00\nTotal: {row["cnt_min_actual"]:,}',
            ha='center', 
            va='bottom', 
            fontsize=11,
            bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', boxstyle='round,pad=0.3')
        )

    # Adjust ylim
    ax1.set_ylim(0, season_summary["cnt_max_actual"].max() * 1.15)
    ax2.set_ylim(0, season_summary["cnt_min_actual"].max() * 2.5)

    # Tambahkan legenda
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor=SEASON_COLORS[0], edgecolor='black', label='Musim Semi'),
        Patch(facecolor=SEASON_COLORS[1], edgecolor='black', label='Musim Panas'),
        Patch(facecolor=SEASON_COLORS[2], edgecolor='black', label='Musim Gugur'),
        Patch(facecolor=SEASON_COLORS[3], edgecolor='black', label='Musim Dingin')
    ]

    fig.legend(
        handles=legend_elements,
        title='Keterangan Musim:',
        bbox_to_anchor=(0.5, -0.05),
        loc='lower center',
        ncol=4,
        fontsize=12,
        title_fontsize=13
    )

    st.pyplot(fig)

    # SECTION 4: POLA WEEKDAY VS WEEKEND (Pertanyaan 2)
    st.header("📅 Pola Penyewaan: Weekday vs Weekend")
    st.markdown("**Bagaimana distribusi penyewaan sepeda antara weekdays dan weekend?**")

    # Create summary data
    weekday_summary = main_df.groupby("day_type").agg({
        'cnt': ['sum', 'mean', 'count']
    }).reset_index()
    weekday_summary.columns = ['day_type', 'total', 'average', 'count']

    hourly_pattern = main_df.groupby(["hr", "day_type"])["cnt"].mean().reset_index()

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 7), gridspec_kw={'width_ratios': [1, 2]})
    fig.suptitle('Analisis Pola Penyewaan Sepeda: Weekday vs Weekend', y=1.05, fontsize=18, fontweight='bold')

    # Chart 1: Total Penyewaan
    sns.barplot(
        data=weekday_summary,
        x="day_type",
        y="total",
        palette=["#e74c3c", "#3498db"],  # Merah untuk weekend, Biru untuk weekday
        ax=ax1,
        edgecolor='black',
        linewidth=1,
        hue="day_type",
        legend=False
    )
    ax1.set_title("Total Penyewaan", pad=15)
    ax1.set_xlabel("")
    ax1.set_ylabel("Total Penyewaan", labelpad=10)

    # Format angka
    for i, row in weekday_summary.iterrows():
        ax1.text(
            i, 
            row["total"] * 0.05,
            f'{row["total"]/1e6:.2f}M',
            ha='center', 
            va='bottom', 
            fontsize=12,
            fontweight='bold',
            bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', boxstyle='round,pad=0.3')
        )

    # Chart 2: Pola per Jam
    sns.lineplot(
        data=hourly_pattern,
        x="hr",
        y="cnt",
        hue="day_type",
        style="day_type",
        markers=True,
        dashes=False,
        markersize=8,
        palette=["#3498db", "#e74c3c"],  # Biru untuk Weekday, Merah untuk Weekend
        ax=ax2,
        linewidth=2.5
    )
    ax2.set_title("Rata-rata Penyewaan per Jam", pad=15)
    ax2.set_xlabel("Jam (0-23)", labelpad=10)
    ax2.set_ylabel("Rata-rata Penyewaan", labelpad=10)
    ax2.set_xticks(range(0, 24))
    ax2.legend(title="Jenis Hari", loc="upper left")

    # Highlight peak hours
    weekday_peak = hourly_pattern[hourly_pattern['day_type'] == 'Weekday']
    weekend_peak = hourly_pattern[hourly_pattern['day_type'] == 'Weekend']

    if not weekday_peak.empty:
        weekday_peak_data = weekday_peak.loc[weekday_peak['cnt'].idxmax()]
        ax2.scatter(weekday_peak_data['hr'], weekday_peak_data['cnt'], color="#3498db", s=200, zorder=5, edgecolor='black')
        ax2.annotate(f'Puncak Weekday\nJam {int(weekday_peak_data["hr"])}:00\n{int(weekday_peak_data["cnt"])} penyewaan',
                      xy=(weekday_peak_data['hr'], weekday_peak_data['cnt']),
                      xytext=(weekday_peak_data['hr'] + 1, weekday_peak_data['cnt'] + 50),
                      arrowprops=dict(facecolor='black', shrink=0.05),
                      bbox=dict(boxstyle='round,pad=0.5', fc='white', alpha=0.8))

    if not weekend_peak.empty:
        weekend_peak_data = weekend_peak.loc[weekend_peak['cnt'].idxmax()]
        ax2.scatter(weekend_peak_data['hr'], weekend_peak_data['cnt'], color="#e74c3c", s=200, zorder=5, edgecolor='black')
        ax2.annotate(f'Puncak Weekend\nJam {int(weekend_peak_data["hr"])}:00\n{int(weekend_peak_data["cnt"])} penyewaan',
                      xy=(weekend_peak_data['hr'], weekend_peak_data['cnt']),
                      xytext=(weekend_peak_data['hr'] + 1, weekend_peak_data['cnt'] - 100),
                      arrowprops=dict(facecolor='black', shrink=0.05),
                      bbox=dict(boxstyle='round,pad=0.5', fc='white', alpha=0.8))

    st.pyplot(fig)

    # SECTION 5: PENGARUH CUACA (Pertanyaan 3)
    st.header("☀️ Pengaruh Kondisi Cuaca")
    st.markdown("**Bagaimana perbedaan pola penyewaan sepeda per jam antara kondisi cuaca cerah dan berkabut?**")

    weather_comparison = main_df[main_df['weathersit'].isin([1, 2])].groupby(['hr', 'weather_label'])['cnt'].mean().unstack()

    fig, ax = plt.subplots(figsize=(16, 6))
    sns.lineplot(
        data=weather_comparison,
        markers=True,
        palette=WEATHER_COLORS,
        linewidth=2.5,
        ax=ax
    )
    ax.set_title("Perbandingan Pola Penyewaan: Cuaca Cerah vs Berkabut", pad=20)
    ax.set_xlabel("Jam (0-23)")
    ax.set_ylabel("Rata-rata Penyewaan")
    ax.legend(title="Kondisi Cuaca")
    ax.set_xticks(range(0, 24))

    st.pyplot(fig)

    # SECTION 6: REKOR PENYEWAAN
    st.header("🏆 Rekor Penyewaan")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Hari Terbaik")
        st.metric(
            label=max_day['dteday'].strftime('%d %b %Y'),
            value=f"{max_day['cnt']:,} penyewaan",
            help=f"Musim: {max_day['season_label']} | Jam puncak: {int(max_day['hr'])}:00 | Cuaca: {max_day['weather_label']}"
        )
        
    with col2:
        st.subheader("Hari Terburuk")
        st.metric(
            label=min_day['dteday'].strftime('%d %b %Y'),
            value=f"{min_day['cnt']:,} penyewaan",
            help=f"Musim: {min_day['season_label']} | Jam terendah: {int(min_day['hr'])}:00 | Cuaca: {min_day['weather_label']}"
        )

    # FOOTER
    st.markdown("---")
    st.caption('© 2025 Bike Sharing Analytics | Dibuat dengan Streamlit')