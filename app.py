import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. 앱 설정 및 고급 디자인 커스텀 (HTML/CSS 감성 적용)
st.set_page_config(page_title="KidsTen Growth Intelligence", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@400;600;800&display=swap');
    
    html, body, [class*="css"] { font-family: 'Pretendard', sans-serif; }
    
    .main { background-color: #f4f7f9; }
    
    /* 카드 스타일 디자인 */
    .report-card {
        background-color: #ffffff;
        padding: 25px;
        border-radius: 15px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.05);
        margin-bottom: 25px;
    }
    
    /* 지표(Metric) 스타일 */
    [data-testid="stMetric"] {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 15px 20px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.03);
        border: 1px solid #f0f0f0;
    }
    
    .stHeader { color: #003366; font-weight: 800; }
    .highlight-text { color: #0056b3; font-weight: 600; }
    
    /* 그로스 리더 전용 전략 박스 */
    .strategy-container {
        background: linear-gradient(135deg, #003366 0%, #0056b3 100%);
        color: white;
        padding: 30px;
        border-radius: 20px;
        margin-bottom: 30px;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. 데이터 로드 (팀장님 전용 URL 유지)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1R4qwQFQxXxL7NO67c8mr08KXMZvU9qkArNFoPFKYJDU/export?format=csv"

@st.cache_data
def load_data():
    try:
        df = pd.read_csv(SHEET_URL)
        df['날짜'] = pd.to_datetime(df['날짜'], format='%Y%m%d')
        num_cols = ['광고비', '총 전환매출액(14일)', '클릭수', '노출수', '총 주문수(14일)']
        for col in num_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # 성과 지표 계산
        df['CTR'] = (df['클릭수'] / df['노출수'] * 100).fillna(0)
        df['CVR'] = (df['총 주문수(14일)'] / df['클릭수'] * 100).replace([float('inf')], 0).fillna(0)
        df['ROAS'] = (df['총 전환매출액(14일)'] / df['광고비'] * 100).replace([float('inf')], 0).fillna(0)
        df['CPC'] = (df['광고비'] / df['클릭수']).replace([float('inf')], 0).fillna(0)
        return df
    except Exception as e:
        st.error(f"Data Connection Error: {e}")
        return None

df = load_data()

if df is not None:
    # --- 사이드바: 브랜드/캠페인 필터 ---
    st.sidebar.markdown("### 🏛️ Brand Navigator")
    selected_campaigns = st.sidebar.multiselect("캠페인 필터", df['캠페인명'].unique(), default=df['캠페인명'].unique())
    f_df = df[df['캠페인명'].isin(selected_campaigns)]

    # --- 메인 섹션 1: 전략적 AI 리포트 ---
    st.markdown(f"""
    <div class="strategy-container">
        <h2 style='margin-top:0;'>🚀 KidsTen Growth Intelligence Report</h2>
        <p style='font-size:1.1rem; opacity:0.9;'>18년 경력 그로스 리더를 위한 실시간 데이터 분석 및 전략 제안</p>
        <hr style='opacity:0.3;'>
        <div style='display: flex; gap: 50px;'>
            <div>
                <h4 style='color:#76ff03;'>✅ 성과 요약</h4>
                <p>현재 평균 ROAS는 <b>{f_df['총 전환매출액(14일)'].sum()/f_df['광고비'].sum()*100:.1f}%</b>입니다. 
                매출 기여도가 가장 큰 키워드는 <b>'{f_df.groupby('키워드')['총 전환매출액(14일)'].sum().idxmax()}'</b>입니다.</p>
            </div>
            <div>
                <h4 style='color:#ffea00;'>⚠️ 주의 사항</h4>
                <p>광고비 지출 대비 ROAS가 100% 미만인 키워드가 <b>{len(f_df[f_df['ROAS']<100]['키워드'].unique())}개</b> 발견되었습니다. 
                즉시 입찰가 조정이 필요합니다.</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- 메인 섹션 2: 핵심 KPI (Top Metrics) ---
    m1, m2, m3, m4 = st.columns(4)
    with m1: st.metric("💰 Total Spend", f"{f_df['광고비'].sum():,.0f}원")
    with m2: st.metric("📈 Ad Sales", f"{f_df['총 전환매출액(14일)'].sum():,.0f}원")
    with m3: st.metric("🎯 Avg. ROAS", f"{(f_df['총 전환매출액(14일)'].sum()/f_df['광고비'].sum()*100):.1f}%")
    with m4: st.metric("🖱️ Avg. CTR", f"{(f_df['클릭수'].sum()/f_df['노출수'].sum()*100):.2f}%")

    st.markdown("<br>", unsafe_allow_html=True)

    # --- 메인 섹션 3: 데이터 비주얼라이제이션 (2단 구성) ---
    col_left, col_right = st.columns([6, 4])

    with col_left:
        st.markdown('<div class="report-card">', unsafe_allow_html=True)
        st.subheader("🗓️ 일별 광고 성과 밸런스")
        trend = f_df.groupby('날짜')[['광고비', '총 전환매출액(14일)']].sum().reset_index()
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(x=trend['날짜'], y=trend['광고비'], name='Spend', line=dict(color='#ff4b4b', width=3)))
        fig_trend.add_trace(go.Bar(x=trend['날짜'], y=trend['총 전환매출액(14일)'], name='Sales', marker_color='#0056b3', opacity=0.6))
        fig_trend.update_layout(template='plotly_white', margin=dict(l=20, r=20, t=20, b=20), height=400)
        st.plotly_chart(fig_trend, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_right:
        st.markdown('<div class="report-card">', unsafe_allow_html=True)
        st.subheader("💎 매출 기여도 Top 5 브랜드")
        brand_pie = f_df.groupby('캠페인명')['총 전환매출액(14일)'].sum().reset_index()
        fig_pie = px.pie(brand_pie, values='총 전환매출액(14일)', names='캠페인명', hole=0.5, color_discrete_sequence=px.colors.sequential.RdBu)
        fig_pie.update_layout(showlegend=True, margin=dict(l=0, r=0, t=0, b=0), height=400)
        st.plotly_chart(fig_pie, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # --- 메인 섹션 4: 전문 광고 분석 리포트 (4분면 분석) ---
    st.markdown('<div class="report-card">', unsafe_allow_html=True)
    st.subheader("🎯 키워드 포트폴리오 분석 (Spend vs ROAS)")
    st.write("버블이 우상향(광고비 많이 쓰고 ROAS 높음)할수록 핵심 캐시카우입니다.")
    scatter_df = f_df.groupby('키워드').agg({'광고비':'sum', 'ROAS':'mean', '클릭수':'sum'}).reset_index()
    scatter_df = scatter_df[scatter_df['광고비'] > 0]
    fig_scatter = px.scatter(scatter_df, x='광고비', y='ROAS', size='클릭수', color='ROAS', 
                             hover_name='키워드', color_continuous_scale='RdYlGn',
                             labels={'광고비':'Total Spend', 'ROAS':'Avg ROAS (%)'})
    fig_scatter.add_hline(y=400, line_dash="dash", line_color="red", annotation_text="Target ROAS (400%)")
    fig_scatter.update_layout(template='plotly_white', height=500)
    st.plotly_chart(fig_scatter, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # --- 메인 섹션 5: 로우데이터 상세 테이블 ---
    st.markdown('<div class="report-card">', unsafe_allow_html=True)
    st.subheader("📋 실시간 퍼포먼스 로우데이터")
    st.dataframe(f_df[['날짜', '캠페인명', '키워드', '노출수', '클릭수', 'CTR', '광고비', 'CPC', '총 전환매출액(14일)', 'ROAS']]
                 .sort_values(by='날짜', ascending=False), use_container_width=True, height=400)
    st.markdown('</div>', unsafe_allow_html=True)

else:
    st.error("데이터를 불러오지 못했습니다. SHEET_URL과 구글 시트 공유 설정을 확인해주세요.")
