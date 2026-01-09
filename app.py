import streamlit as st
import pandas as pd
import plotly.express as px

# 1. 앱 설정 및 스타일
st.set_page_config(page_title="KidsTen Growth Cockpit", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #F0F2F6; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #E0E0E0; }
    .insight-card { background-color: #ffffff; padding: 20px; border-radius: 10px; border-left: 5px solid #0056b3; margin-bottom: 20px; box-shadow: 2px 2px 10px rgba(0,0,0,0.05); }
    h1, h2, h3 { color: #003366; font-family: 'Nanum Gothic', sans-serif; }
    </style>
    """, unsafe_allow_html=True)

# 2. 데이터 주소 (팀장님의 주소로 유지!)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1R4qwQFQxXxL7NO67c8mr08KXMZvU9qkArNFoPFKYJDU/export?format=csv"

@st.cache_data
def load_data():
    try:
        df = pd.read_csv(SHEET_URL)
        df['날짜'] = pd.to_datetime(df['날짜'], format='%Y%m%d')
        # 필수 지표 계산 및 예외처리
        df['광고비'] = pd.to_numeric(df['광고비'], errors='coerce').fillna(0)
        df['총 전환매출액(14일)'] = pd.to_numeric(df['총 전환매출액(14일)'], errors='coerce').fillna(0)
        df['클릭수'] = pd.to_numeric(df['클릭수'], errors='coerce').fillna(0)
        df['노출수'] = pd.to_numeric(df['노출수'], errors='coerce').fillna(0)
        
        df['CTR'] = (df['클릭수'] / df['노출수'] * 100).fillna(0)
        df['CVR'] = (df['총 주문수(14일)'] / df['클릭수'] * 100).replace([float('inf'), -float('inf')], 0).fillna(0)
        df['ROAS'] = (df['총 전환매출액(14일)'] / df['광고비'] * 100).replace([float('inf'), -float('inf')], 0).fillna(0)
        return df
    except Exception as e:
        st.error(f"데이터 로드 중 오류 발생: {e}")
        return None

df = load_data()

if df is not None:
    # --- 사이드바 필터 ---
    st.sidebar.header("🔍 분석 필터")
    all_campaigns = df['캠페인명'].unique().tolist()
    selected_campaigns = st.sidebar.multiselect("캠페인을 선택하세요", all_campaigns, default=all_campaigns)
    
    # 필터 적용된 데이터 생성
    f_df = df[df['캠페인명'].isin(selected_campaigns)]

    # --- 타이틀 ---
    st.title("🛡️ KidsTen Ad Management Cockpit")

    # --- 지능형 분석 브리핑 (오류 수정됨) ---
    st.markdown('<div class="insight-card">', unsafe_allow_html=True)
    st.subheader("💡 그로스 리더 전략 브리핑")
    
    if not f_df.empty:
        col_a, col_b = st.columns(2)
        with col_a:
            # ROAS가 가장 높은 키워드 찾기
            best_kw = f_df.groupby('키워드')['ROAS'].mean().idxmax()
            st.write(f"✅ **최고 효율 키워드:** `{best_kw}` (성과 유지 집중)")
        with col_b:
            # 광고비는 많이 쓰는데 ROAS가 낮은 키워드 찾기
            bad_kw_df = f_df[f_df['광고비'] > 5000].groupby('키워드')['ROAS'].mean().sort_values()
            if not bad_kw_df.empty:
                st.write(f"⚠️ **비효율 경고:** `{bad_kw_df.index[0]}` 키워드 (제외 또는 입찰가 하향 검토)")
    st.markdown('</div>', unsafe_allow_html=True)

    # --- KPI 대시보드 ---
    t_spend = f_df['광고비'].sum()
    t_sales = f_df['총 전환매출액(14일)'].sum()
    t_roas = (t_sales / t_spend * 100) if t_spend > 0 else 0
    t_ctr = (f_df['클릭수'].sum() / f_df['노출수'].sum() * 100) if f_df['노출수'].sum() > 0 else 0

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("총 광고 집행비", f"{t_spend:,.0f}원")
    m2.metric("총 광고 매출액", f"{t_sales:,.0f}원")
    m3.metric("평균 ROAS", f"{t_roas:.1f}%")
    m4.metric("평균 클릭률(CTR)", f"{t_ctr:.2f}%")

    st.divider()

    # --- 그래프 분석 ---
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("📈 일별 매출 및 광고비 추이")
        trend = f_df.groupby('날짜')[['광고비', '총 전환매출액(14일)']].sum().reset_index()
        fig1 = px.line(trend, x='날짜', y=['광고비', '총 전환매출액(14일)'], color_discrete_map={'광고비':'#FF4B4B', '총 전환매출액(14일)':'#0056b3'})
        st.plotly_chart(fig1, use_container_width=True)
    
    with c2:
        st.subheader("🎯 키워드별 매출 Top 10")
        top10 = f_df.groupby('키워드')['총 전환매출액(14일)'].sum().sort_values(ascending=False).head(10).reset_index()
        fig2 = px.bar(top10, x='총 전환매출액(14일)', y='키워드', orientation='h', color='총 전환매출액(14일)', color_continuous_scale='Blues')
        st.plotly_chart(fig2, use_container_width=True)

    # --- 상세 데이터 테이블 ---
    st.subheader("📋 실시간 광고 성과 로우데이터")
    st.dataframe(f_df[['날짜', '캠페인명', '키워드', '노출수', '클릭수', 'CTR', '광고비', '총 전환매출액(14일)', 'ROAS']].sort_values(by='날짜', ascending=False), use_container_width=True)

else:
    st.error("데이터를 불러오지 못했습니다. SHEET_URL과 구글 시트 공유 설정을 확인해주세요.")
