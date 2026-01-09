import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. 디자인 고도화 (G마켓 산스 폰트 및 HTML 카드 레이아웃 이식)
st.set_page_config(page_title="KidsTen Growth Intelligence v5", layout="wide")

st.markdown("""
    <style>
    @import url('https://cdn.jsdelivr.net/gh/projectnoonnu/noonfonts_2001@1.1/GmarketSansMedium.woff');
    
    * { font-family: 'GmarketSansMedium', sans-serif !important; }
    .main { background-color: #f1f5f9; }
    
    /* HTML 스타일 카드 디자인 */
    .dashboard-card {
        background-color: #ffffff;
        padding: 24px;
        border-radius: 16px;
        box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);
        border: 1px solid #e2e8f0;
        margin-bottom: 24px;
    }
    
    /* 상단 전략 리포트 섹션 */
    .strategy-container {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: white;
        padding: 30px;
        border-radius: 20px;
        margin-bottom: 30px;
        border-left: 10px solid #3b82f6;
    }
    
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 50px;
        font-size: 0.8rem;
        font-weight: bold;
        margin-right: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. 데이터 연동 (팀장님 전용 주소)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1R4qwQFQxXxL7NO67c8mr08KXMZvU9qkArNFoPFKYJDU/export?format=csv"

@st.cache_data
def load_data():
    try:
        df = pd.read_csv(SHEET_URL)
        df['날짜'] = pd.to_datetime(df['날짜'], format='%Y%m%d')
        for col in ['광고비', '총 전환매출액(14일)', '클릭수', '노출수']:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        df['ROAS'] = (df['총 전환매출액(14일)'] / df['광고비'] * 100).fillna(0).replace([float('inf')], 0)
        
        # 성과 상태 분류 로직
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
    st.sidebar.markdown("### 🏢 KidsTen Navigator")
    sel_campaigns = st.sidebar.multiselect("캠페인 필터", df['캠페인명'].unique(), default=df['캠페인명'].unique())
    f_df = df[df['캠페인명'].isin(sel_campaigns)]

    # --- Section 1: 분석 리포트 (수치 기반) ---
    danger_df = f_df[(f_df['ROAS'] <= 200) & (f_df['광고비'] >= 50000)]
    counts = f_df['상태'].value_counts()
    
    st.markdown(f"""
    <div class="strategy-container">
        <h2 style='color:white; margin-top:0;'>🚀 KidsTen Executive Report</h2>
        <div style='display: flex; gap: 40px;'>
            <div style='flex: 1;'>
                <h4 style='color:#60a5fa;'>📊 키워드 관리 현황</h4>
                <p style='font-size:1.1rem;'>
                    <b>총 분석 키워드: {len(f_df['키워드'].unique())}개</b><br>
                    <span style='color:#4ade80;'>✅ 우수: {counts.get('✅ 우수', 0)}개</span> | 
                    <span style='color:#fbbf24;'>🟡 관리: {counts.get('🟡 관리', 0)}개</span> | 
                    <span style='color:#f87171;'>🚨 위험: {counts.get('🚨 위험', 0)}개</span>
                </p>
            </div>
            <div style='flex: 1; border-left: 1px solid rgba(255,255,255,0.2); padding-left: 40px;'>
                <h4 style='color:#f87171;'>⚠️ 즉시 조치 대상 ({len(danger_df['키워드'].unique())}개)</h4>
                <p style='font-size:0.95rem; opacity:0.9;'>
                    ROAS 200% 이하이면서 5만원 이상 소진된 키워드입니다.<br>
                    대상: <b>{', '.join(danger_df['키워드'].unique()[:5])}</b> 등
                </p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- Section 2: 핵심 KPI ---
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💰 광고 집행비", f"{f_df['광고비'].sum():,.0f}원")
    c2.metric("📈 광고 매출", f"{f_df['총 전환매출액(14일)'].sum():,.0f}원")
    total_roas = (f_df['총 전환매출액(14일)'].sum() / f_df['광고비'].sum() * 100)
    c3.metric("🎯 평균 ROAS", f"{total_roas:.1f}%", delta=f"{total_roas-400:.1f}%")
    c4.metric("🖱️ 평균 클릭률", f"{(f_df['클릭수'].sum()/f_df['노출수'].sum()*100):.2f}%")

    # --- Section 3: 키워드 포트폴리오 분석 (4분면 그래프) ---
    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
    st.subheader("📊 키워드 성과 4분면 분석")
    kw_sum = f_df.groupby('키워드').agg({'광고비':'sum', 'ROAS':'mean', '클릭수':'sum'}).reset_index()
    
    fig = px.scatter(kw_sum[kw_sum['광고비']>1000], x='광고비', y='ROAS', size='클릭수', color='ROAS',
                     hover_name='키워드', color_continuous_scale='RdYlGn',
                     labels={'광고비':'총 광고비 소진액', 'ROAS':'수익률(ROAS %)'})
    
    # 4분면 가이드라인 추가
    fig.add_hline(y=400, line_dash="dash", line_color="#10b981", annotation_text="우수 기준 (400%)")
    fig.add_hline(y=200, line_dash="dash", line_color="#ef4444", annotation_text="위험 기준 (200%)")
    fig.add_vline(x=f_df['광고비'].mean(), line_dash="dot", line_color="#64748b", annotation_text="평균 광고비")
    
    fig.update_layout(template="plotly_white", height=500, margin=dict(l=20, r=20, t=20, b=20))
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # --- Section 4: 상세 분석 리스트 ---
    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
    st.subheader("📋 고도화 성과 분석 리스트")
    list_df = f_df[['날짜', '상태', '키워드', '광고비', '총 전환매출액(14일)', 'ROAS']].sort_values(by='광고비', ascending=False)
    st.dataframe(list_df, use_container_width=True, height=400)
    st.markdown('</div>', unsafe_allow_html=True)

else:
    st.error("데이터 연결을 확인해주세요.")
