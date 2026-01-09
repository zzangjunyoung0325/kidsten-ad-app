import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# 1. 앱 설정 및 SaaS 스타일링 (HTML/CSS 고도화)
st.set_page_config(page_title="KidsTen Growth Command Center", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Pretendard', sans-serif; }
    .main { background-color: #F8FAFC; }
    
    /* SaaS 카드 디자인 */
    .metric-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 16px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06);
        border: 1px solid #E2E8F0;
    }
    .strategy-card {
        background: linear-gradient(135deg, #1E293B 0%, #334155 100%);
        color: white;
        padding: 25px;
        border-radius: 20px;
        margin-bottom: 25px;
        box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);
    }
    .alert-badge {
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        background-color: #FEE2E2;
        color: #B91C1C;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. 데이터 엔진 (매뉴얼 기준 지표 계산)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1R4qwQFQxXxL7NO67c8mr08KXMZvU9qkArNFoPFKYJDU/export?format=csv"

@st.cache_data
def load_data():
    try:
        df = pd.read_csv(SHEET_URL)
        df['날짜'] = pd.to_datetime(df['날짜'], format='%Y%m%d')
        # 숫자형 변환 및 결측치 처리
        cols = ['광고비', '총 전환매출액(14일)', '클릭수', '노출수', '직접 전환매출액(14일)', '간접 전환매출액(14일)']
        for col in cols:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # 핵심 지표 계산 (사내 기준 적용)
        df['ROAS'] = (df['총 전환매출액(14일)'] / df['광고비'] * 100).replace([float('inf')], 0).fillna(0)
        df['CPC'] = (df['광고비'] / df['클릭수']).replace([float('inf')], 0).fillna(0)
        df['CTR'] = (df['클릭수'] / df['노출수'] * 100).fillna(0)
        return df
    except: return None

df = load_data()

if df is not None:
    # --- 사이드바: Growth Leader 전용 필터 ---
    st.sidebar.markdown("### 🏛️ Command Filter")
    all_c = df['캠페인명'].unique().tolist()
    sel_c = st.sidebar.multiselect("캠페인 선택", all_c, default=all_c)
    f_df = df[df['캠페인명'].isin(sel_c)]

    # --- 상단: 전략적 Insight 섹션 ---
    st.markdown('<div class="strategy-card">', unsafe_allow_html=True)
    st.markdown("## 🛰️ Growth Strategy Insight")
    
    col_st1, col_st2 = st.columns(2)
    with col_st1:
        # 매뉴얼 기반 제외 대상 추천 (5클릭 & 2만원 & ROAS 300% 미만)
        bad_kws = f_df[(f_df['클릭수'] >= 5) & (f_df['광고비'] >= 20000) & (f_df['ROAS'] < 300)]['키워드'].unique()
        st.markdown(f"**🚫 사내 기준 비효율 키워드 ({len(bad_kws)}개)**")
        if len(bad_kws) > 0:
            st.warning(f"제외 검토: {', '.join(bad_kws[:3])} 등")
        else: st.success("현재 사내 기준을 벗어난 비효율 키워드가 없습니다.")
        
    with col_st2:
        # CPC 폭등 탐지 (평균 대비 150% 이상)
        avg_cpc = f_df['CPC'].mean()
        high_cpc_kw = f_df[f_df['CPC'] > avg_cpc * 1.5].groupby('키워드')['CPC'].mean().sort_values(ascending=False)
        st.markdown(f"**⚠️ CPC 폭등 주의 (평균: {avg_cpc:,.0f}원)**")
        if not high_cpc_kw.empty:
            st.error(f"경고: '{high_cpc_kw.index[0]}' ({high_cpc_kw.values[0]:,.0f}원)")
        else: st.success("비정상적인 CPC 폭등이 감지되지 않았습니다.")
    st.markdown('</div>', unsafe_allow_html=True)

    # --- 메인: KPI 스코어보드 ---
    k1, k2, k3, k4 = st.columns(4)
    with k1: st.metric("총 집행 광고비", f"{f_df['광고비'].sum():,.0f}원")
    with k2: st.metric("총 광고 매출액", f"{f_df['총 전환매출액(14일)'].sum():,.0f}원")
    with k3: 
        final_roas = (f_df['총 전환매출액(14일)'].sum() / f_df['광고비'].sum() * 100)
        st.metric("평균 ROAS", f"{final_roas:.1f}%", delta=f"{final_roas-350:.1f}% (vs Target)")
    with k4: st.metric("평균 클릭률", f"{(f_df['클릭수'].sum() / f_df['노출수'].sum() * 100):.2f}%")

    st.markdown("<br>", unsafe_allow_html=True)

    # --- 중단: 고차원 분석 차트 ---
    col_l, col_r = st.columns([7, 3])
    
    with col_l:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.subheader("📊 일별 매출 밸런스 및 직접/간접 전환 비중")
        # 직접 vs 간접 매출 비중 차트
        attrib_df = f_df.groupby('날짜')[['직접 전환매출액(14일)', '간접 전환매출액(14일)']].sum().reset_index()
        fig_attr = px.bar(attrib_df, x='날짜', y=['직접 전환매출액(14일)', '간접 전환매출액(14일)'], 
                          title="광고 기여도 분석 (직접 vs 간접)", barmode='stack',
                          color_discrete_sequence=['#003366', '#94A3B8'])
        st.plotly_chart(fig_attr, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_r:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.subheader("🎯 ROAS 성과 분포")
        # 캠페인별 ROAS 파이 차트
        brand_roas = f_df.groupby('캠페인명')['총 전환매출액(14일)'].sum().reset_index()
        fig_pie = px.pie(brand_roas, values='총 전환매출액(14일)', names='캠페인명', hole=0.6,
                         color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig_pie, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # --- 하단: 키워드 4분면 전략 차트 ---
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.subheader("💡 키워드 포트폴리오 분석 (소진액 vs 효율)")
    scatter_data = f_df.groupby('키워드').agg({'광고비':'sum', 'ROAS':'mean', '클릭수':'sum'}).reset_index()
    fig_scatter = px.scatter(scatter_data[scatter_data['광고비']>0], x='광고비', y='ROAS', size='클릭수', 
                             hover_name='키워드', color='ROAS', color_continuous_scale='RdYlGn',
                             labels={'광고비':'총 광고비', 'ROAS':'평균 ROAS (%)'})
    fig_scatter.add_hline(y=350, line_dash="dash", line_color="red", annotation_text="목표 ROAS (350%)")
    st.plotly_chart(fig_scatter, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # --- 상세 테이블 ---
    st.subheader("📋 실시간 퍼포먼스 데이터베이스")
    st.dataframe(f_df[['날짜', '캠페인명', '키워드', '노출수', '클릭수', '광고비', '총 전환매출액(14일)', 'ROAS']]
                 .sort_values(by='날짜', ascending=False), use_container_width=True)

else:
    st.error("데이터 연결을 확인해주세요. SHEET_URL 주소가 정확한지 확인이 필요합니다.")
