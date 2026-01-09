import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. 앱 설정 및 키즈텐 스타일 (CSS)
st.set_page_config(page_title="KidsTen Growth Cockpit", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #F0F2F6; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #E0E0E0; }
    .insight-card { background-color: #ffffff; padding: 20px; border-radius: 10px; border-left: 5px solid #0056b3; margin-bottom: 20px; box-shadow: 2px 2px 10px rgba(0,0,0,0.05); }
    h1, h2, h3 { color: #003366; font-family: 'Nanum Gothic', sans-serif; }
    </style>
    """, unsafe_allow_html=True)

# 2. 데이터 로드 (팀장님의 주소로 유지하세요!)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1R4qwQFQxXxL7NO67c8mr08KXMZvU9qkArNFoPFKYJDU/export?format=csv"

@st.cache_data
def load_data():
    df = pd.read_csv(SHEET_URL)
    df['날짜'] = pd.to_datetime(df['날짜'], format='%Y%m%d')
    # 기본 지표 계산
    df['CTR'] = (df['클릭수'] / df['노출수'] * 100).fillna(0)
    df['CPC'] = (df['광고비'] / df['클릭수']).fillna(0)
    df['ROAS'] = (df['총 전환매출액(14일)'] / df['광고비'] * 100).fillna(0)
    return df

try:
    df = load_data()
    
    # --- 사이드바 필터 ---
    st.sidebar.header("🔍 분석 필터")
    campaigns = st.sidebar.multiselect("캠페인 선택", df['캠페인명'].unique(), default=df['캠페인명'].unique())
    filtered_df = df[df['캠페인명'].isin(campaigns)]

    # --- 타이틀 및 요약 분석 ---
    st.title("🛡️ KidsTen Ad Management Cockpit")
    
    # 지능형 분석 코멘트
    st.markdown('<div class="insight-card">', unsafe_allow_html=True)
    st.subheader("💡 그로스 리더 전략 브리핑")
    col_a, col_b = st.columns(2)
    with col_a:
        winner = filtered_df.groupby('키워드')['ROAS'].mean().idxmax()
        st.write(f"✅ **현재 최고 효율 키워드:** `{winner}` (입찰가 유지 및 노출 극대화 권장)")
    with col_b:
        waste = filtered_df[filtered_df['광고비'] > 10000].sort_values(by='ROAS').iloc[0]['키워']
        st.write(f"⚠️ **비효율 경고:** `{waste}` 키워드가 광고비 대비 전환이 매우 낮습니다. (제외 검토 필요)")
    st.markdown('</div>', unsafe_allow_html=True)

    # --- KPI Dashboard ---
    t_spend = filtered_df['광고비'].sum()
    t_sales = filtered_df['총 전환매출액(14일)'].sum()
    t_roas = (t_sales / t_spend * 100) if t_spend > 0 else 0
    t_ctr = (filtered_df['클릭수'].sum() / filtered_df['노출수'].sum() * 100)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("총 광고 집행비", f"{t_spend:,.0f}원")
    m2.metric("총 광고 매출액", f"{t_sales:,.0f}원")
    m3.metric("평균 ROAS", f"{t_roas:.1f}%", delta=f"{t_roas-400:.1f}%")
    m4.metric("평균 CTR", f"{t_ctr:.2f}%")

    st.divider()

    # --- 분석 섹션 1: 매출 vs 광고비 추이 ---
    st.subheader("📈 일별 매출 및 광고비 밸런스")
    trend_df = filtered_df.groupby('날짜')[['광고비', '총 전환매출액(14일)']].sum().reset_index()
    fig_trend = px.line(trend_df, x='날짜', y=['광고비', '총 전환매출액(14일)'], 
                        color_discrete_map={'광고비': '#FF4B4B', '총 전환매출액(14일)': '#0056b3'})
    st.plotly_chart(fig_trend, use_container_width=True)

    # --- 분석 섹션 2: 광고 관리자용 키워드 Lab ---
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🎯 키워드별 ROAS 순위")
        kw_df = filtered_df.groupby('키워드').agg({'광고비':'sum', '총 전환매출액(14일)':'sum', 'ROAS':'mean'}).reset_index()
        kw_df = kw_df[kw_df['광고비'] > 0].sort_values(by='총 전환매출액(14일)', ascending=False).head(15)
        fig_kw = px.bar(kw_df, x='총 전환매출액(14일)', y='키워드', orientation='h', color='ROAS', color_continuous_scale='Blues')
        st.plotly_chart(fig_kw, use_container_width=True)

    with col2:
        st.subheader("📊 노출량 대비 클릭률(CTR) 분석")
        # 노출량은 많으나 클릭이 낮은 상품/키워드 발굴용
        fig_scatter = px.scatter(filtered_df.groupby('키워드').agg({'노출수':'sum', 'CTR':'mean', '광고비':'sum'}).reset_index().head(50), 
                                 x='노출수', y='CTR', size='광고비', hover_name='키워드', color='CTR',
                                 title="버블 크기 = 광고비 소진액")
        st.plotly_chart(fig_scatter, use_container_width=True)

    # --- 데이터 상세 테이블 (광고 관리자용) ---
    st.subheader("📋 광고 성과 상세 데이터 (로우데이터 분석)")
    st.dataframe(filtered_df[['날짜', '캠페인명', '키워드', '노출수', '클릭수', 'CTR', '광고비', 'CPC', '총 전환매출액(14일)', 'ROAS']].sort_values(by='날짜', ascending=False), use_container_width=True)

except Exception as e:
    st.error(f"데이터를 분석하는 중 오류가 발생했습니다. 코드의 SHEET_URL과 따옴표를 확인해주세요. (Error: {e})")
