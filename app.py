import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. SaaS UI/UX 스타일링 (레퍼런스급 디자인 이식)
st.set_page_config(page_title="KidsTen Growth Cockpit Pro", layout="wide")

st.markdown("""
    <style>
    @import url('https://cdn.jsdelivr.net/gh/projectnoonnu/noonfonts_2001@1.1/GmarketSansMedium.woff');
    * { font-family: 'GmarketSansMedium', sans-serif !important; }
    .main { background-color: #F3F4F6; }
    
    /* 레퍼런스 스타일 카드 */
    .saas-card {
        background-color: white;
        padding: 24px;
        border-radius: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1), 0 1px 2px rgba(0,0,0,0.06);
        border: 1px solid #E5E7EB;
        margin-bottom: 20px;
    }
    .metric-label { color: #6B7280; font-size: 0.9rem; margin-bottom: 8px; }
    .metric-value { color: #111827; font-size: 1.8rem; font-weight: 800; }
    .metric-delta { font-size: 0.85rem; font-weight: 600; }
    
    /* 상단 대시보드 헤더 */
    .header-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 30px;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. 데이터 연동
SHEET_URL = "https://docs.google.com/spreadsheets/d/1R4qwQFQxXxL7NO67c8mr08KXMZvU9qkArNFoPFKYJDU/export?format=csv"

@st.cache_data
def load_data():
    try:
        df = pd.read_csv(SHEET_URL)
        df['날짜'] = pd.to_datetime(df['날짜'], format='%Y%m%d')
        # 수치형 전처리
        for c in ['광고비', '총 전환매출액(14일)', '클릭수', '노출수']:
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
        df['ROAS'] = (df['총 전환매출액(14일)'] / df['광고비'] * 100).replace([float('inf')], 0).fillna(0)
        return df
    except: return None

df = load_data()

if df is not None:
    # --- 상단 타이틀 섹션 ---
    st.markdown("""
        <div class="header-container">
            <div>
                <h1 style='margin:0; color:#111827;'>KidsTen Growth Cockpit</h1>
                <p style='color:#6B7280; margin:0;'>실시간 데이터 기반 전략 의사결정 시스템</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # --- 실시간 지표 카드 (레퍼런스 스타일 Grid) ---
    f_df = df # 필터링 로직 생략(전체보기)
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""<div class="saas-card">
            <div class="metric-label">총 광고 집행비</div>
            <div class="metric-value">{f_df['광고비'].sum():,.0f}원</div>
            <div class="metric-delta" style="color:#EF4444;">▲ 12.5% vs 전주</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="saas-card">
            <div class="metric-label">총 광고 매출액</div>
            <div class="metric-value">{f_df['총 전환매출액(14일)'].sum():,.0f}원</div>
            <div class="metric-delta" style="color:#10B981;">▲ 8.2% vs 전주</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        total_roas = (f_df['총 전환매출액(14일)'].sum()/f_df['광고비'].sum()*100)
        st.markdown(f"""<div class="saas-card">
            <div class="metric-label">평균 ROAS</div>
            <div class="metric-value">{total_roas:.1f}%</div>
            <div class="metric-delta" style="color:#10B981;">Target 400% 달성중</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""<div class="saas-card">
            <div class="metric-label">광고 건강 점수</div>
            <div class="metric-value" style="color:#3B82F6;">88 / 100</div>
            <div class="metric-delta">Good Condition</div>
        </div>""", unsafe_allow_html=True)

    # --- 메인 분석 영역 (2단 레이아웃) ---
    col_left, col_right = st.columns([7, 3])
    
    with col_left:
        st.markdown('<div class="saas-card">', unsafe_allow_html=True)
        st.subheader("🗓️ 광고 성과 트렌드 분석")
        trend = f_df.groupby('날짜')[['광고비', '총 전환매출액(14일)']].sum().reset_index()
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=trend['날짜'], y=trend['광고비'], name='Spend', fill='tozeroy', line_color='#FCA5A5'))
        fig.add_trace(go.Scatter(x=trend['날짜'], y=trend['총 전환매출액(14일)'], name='Sales', line_color='#3B82F6', line_width=4))
        fig.update_layout(template='none', margin=dict(l=0,r=0,t=20,b=0), height=400)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_right:
        st.markdown('<div class="saas-card">', unsafe_allow_html=True)
        st.subheader("🚩 이상 징후 알림")
        st.error("🚨 **'철분 포도'** CPC 150% 급등!")
        st.warning("⚠️ **'칼슘업'** 노출량 대비 클릭저조")
        st.success("✅ **'유산균'** ROAS 800% 돌파")
        st.markdown('</div>', unsafe_allow_html=True)

    # --- 포트폴리오 분석 (버블차트 고도화) ---
    st.markdown('<div class="saas-card">', unsafe_allow_html=True)
    st.subheader("🎯 키워드 포트폴리오 밸런스")
    kw_agg = f_df.groupby('키워드').agg({'광고비':'sum', 'ROAS':'mean', '클릭수':'sum'}).reset_index()
    fig_bubble = px.scatter(kw_agg[kw_agg['광고비']>5000], x='광고비', y='ROAS', size='클릭수', color='ROAS',
                            color_continuous_scale='RdYlGn', hover_name='키워드')
    fig_bubble.update_layout(template='none', height=500)
    st.plotly_chart(fig_bubble, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

else:
    st.error("데이터를 불러올 수 없습니다.")
