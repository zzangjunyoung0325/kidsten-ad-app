import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. 디자인 마스터 세팅 (G마켓 산스 및 전문 SaaS 레이아웃)
st.set_page_config(page_title="KidsTen Growth Intelligence Pro", layout="wide")

st.markdown("""
    <style>
    @import url('https://cdn.jsdelivr.net/gh/projectnoonnu/noonfonts_2001@1.1/GmarketSansMedium.woff');
    * { font-family: 'GmarketSansMedium', sans-serif !important; }
    .main { background-color: #f8fafc; }
    
    /* 카드 디자인 (HTML/SaaS 감성) */
    .st-emotion-cache-12w0qpk { background-color: white !important; border-radius: 20px !important; padding: 30px !important; box-shadow: 0 4px 20px rgba(0,0,0,0.05) !important; border: 1px solid #edf2f7 !important; }
    
    /* 상단 전략 섹션 디자인 */
    .strategy-card {
        background: linear-gradient(135deg, #003366 0%, #0056b3 100%);
        color: white;
        padding: 40px;
        border-radius: 24px;
        margin-bottom: 35px;
        box-shadow: 0 12px 24px rgba(0,51,102,0.2);
    }
    
    /* 요약 배지 스타일 */
    .summary-badge {
        display: inline-block;
        padding: 8px 16px;
        border-radius: 12px;
        font-weight: 800;
        font-size: 1.1rem;
        margin-right: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .badge-red { background-color: #ff4b4b; color: white; }
    .badge-yellow { background-color: #facc15; color: #1e293b; }
    .badge-green { background-color: #10b981; color: white; }
    </style>
    """, unsafe_allow_html=True)

# 2. 데이터 연동
SHEET_URL = "https://docs.google.com/spreadsheets/d/1R4qwQFQxXxL7NO67c8mr08KXMZvU9qkArNFoPFKYJDU/export?format=csv"

@st.cache_data
def load_data():
    try:
        df = pd.read_csv(SHEET_URL)
        df['날짜'] = pd.to_datetime(df['날짜'], format='%Y%m%d')
        for col in ['광고비', '총 전환매출액(14일)', '클릭수', '노출수']:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        df['ROAS'] = (df['총 전환매출액(14일)'] / df['광고비'] * 100).fillna(0).replace([float('inf')], 0)
        
        def classify(row):
            if row['ROAS'] >= 400: return "✅ 우수"
            elif row['ROAS'] >= 200: return "🟡 관리"
            else: return "🚨 위험"
        df['상태'] = df.apply(classify, axis=1)
        return df
    except: return None

df = load_data()

if df is not None:
    # --- 사이드바 필터 ---
    st.sidebar.markdown("## 🏢 브랜드 네비게이터")
    sel_campaigns = st.sidebar.multiselect("캠페인 필터", df['캠페인명'].unique(), default=df['캠페인명'].unique())
    f_df = df[df['캠페인명'].isin(sel_campaigns)]

    # --- Section 1: 전문 전략 리포트 (Badge UI 적용) ---
    danger_df = f_df[(f_df['ROAS'] <= 200) & (f_df['광고비'] >= 50000)]
    counts = f_df['상태'].value_counts()
    
    st.markdown(f"""
    <div class="strategy-card">
        <h1 style='color:white; margin-top:0;'>🛡️ KidsTen Ad Growth Strategy Center</h1>
        <p style='font-size:1.2rem; opacity:0.8;'>성과 기반 지능형 광고 관리 시스템</p>
        <div style='display: flex; gap: 20px; margin-top: 25px;'>
            <div class="summary-badge badge-red">🚨 위험 키워드: {counts.get('🚨 위험', 0)}개</div>
            <div class="summary-badge badge-yellow">🟡 관리 키워드: {counts.get('🟡 관리', 0)}개</div>
            <div class="summary-badge badge-green">✅ 우수 키워드: {counts.get('✅ 우수', 0)}개</div>
        </div>
        <div style='margin-top: 25px; background: rgba(255,255,255,0.1); padding: 20px; border-radius: 15px;'>
            <h4 style='color:#60a5fa; margin-top:0;'>⚠️ 즉시 관리 대상 키워드 리스트</h4>
            <p style='font-size:1.1rem;'>{', '.join(danger_df['키워드'].unique()[:8]) if not danger_df.empty else '현재 즉시 조치 대상이 없습니다.'}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- Section 2: 핵심 KPI 메트릭 ---
    k1, k2, k3, k4 = st.columns(4)
    with k1: st.metric("💰 집행 광고비", f"{f_df['광고비'].sum():,.0f}원")
    with k2: st.metric("📈 광고 매출", f"{f_df['총 전환매출액(14일)'].sum():,.0f}원")
    total_roas = (f_df['총 전환매출액(14일)'].sum() / f_df['광고비'].sum() * 100)
    with k3: st.metric("🎯 평균 ROAS", f"{total_roas:.1f}%", delta=f"{total_roas-400:.1f}%")
    with k4: st.metric("🖱️ 평균 클릭률(CTR)", f"{(f_df['클릭수'].sum()/f_df['노출수'].sum()*100):.2f}%")

    st.markdown("<br>", unsafe_allow_html=True)

    # --- Section 3: 키워드 포트폴리오 분석 (그래프 고도화) ---
    st.subheader("🎯 키워드 성과 4분면 분석 (Action-Oriented Graph)")
    kw_sum = f_df.groupby('키워드').agg({'광고비':'sum', 'ROAS':'mean', '클릭수':'sum'}).reset_index()
    # 그래프 데이터 필터링 (의미 있는 데이터만)
    kw_sum = kw_sum[kw_sum['광고비'] > 1000].sort_values(by='광고비', ascending=False).head(50)

    fig = px.scatter(kw_sum, x='광고비', y='ROAS', size='광고비', color='ROAS',
                     hover_name='키워드', color_continuous_scale='RdYlGn',
                     labels={'광고비':'총 소진액', 'ROAS':'수익률(ROAS %)'})
    
    # 4분면 가이드라인
    fig.add_hline(y=400, line_dash="dash", line_color="#10b981", annotation_text="Cash Cow Zone")
    fig.add_hline(y=200, line_dash="dash", line_color="#ef4444", annotation_text="Danger Zone")
    fig.update_layout(template="plotly_white", height=600, plot_bgcolor='rgba(248, 250, 252, 1)')
    st.plotly_chart(fig, use_container_width=True)

    # --- Section 4: 실시간 분석 리스트 ---
    st.subheader("📋 성과 분석 데이터베이스")
    # 정렬 및 필터링이 쉬운 인터랙티브 테이블
    st.dataframe(
        f_df[['날짜', '상태', '키워드', '광고비', '총 전환매출액(14일)', 'ROAS']].sort_values(by='광고비', ascending=False),
        use_container_width=True,
        height=500,
        column_config={
            "ROAS": st.column_config.NumberColumn("ROAS (%)", format="%.1f%%"),
            "광고비": st.column_config.NumberColumn("집행비", format="%d원"),
            "총 전환매출액(14일)": st.column_config.NumberColumn("매출액", format="%d원")
        }
    )
else:
    st.error("데이터 연결을 확인해주세요.")
