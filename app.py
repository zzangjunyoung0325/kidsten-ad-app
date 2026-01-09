import streamlit as st
import pandas as pd
import plotly.express as px

# 1. 페이지 설정 및 심플 테마 (Professional Light)
st.set_page_config(page_title="KidsTen Ad Intelligence", layout="wide")

# 최소한의 디자인 포인트만 적용 (가독성 중심)
st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    div[data-testid="stMetric"] {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        padding: 15px;
        border-radius: 10px;
    }
    .stDataFrame { border: 1px solid #e2e8f0; border-radius: 10px; }
    h1, h2, h3 { color: #0f172a; font-weight: 700; }
    </style>
    """, unsafe_allow_html=True)

# 2. 강력한 데이터 통합 엔진 (중복 완전 박멸)
URL_1 = "https://docs.google.com/spreadsheets/d/1R4qwQFQxXxL7NO67c8mr08KXMZvU9qkArNFoPFKYJDU/export?format=csv&gid=75240363"
URL_2 = "https://docs.google.com/spreadsheets/d/1R4qwQFQxXxL7NO67c8mr08KXMZvU9qkArNFoPFKYJDU/export?format=csv&gid=481757610"

@st.cache_data
def load_and_clean_data():
    rename_map = {
        '캠페인 시작일': '날짜', '캠페인 이름': '캠페인명', 
        '광고비(원)': '광고비', '총 전환 매출액 (14일)(원)': '총 전환매출액(14일)'
    }
    
    all_dfs = []
    for url, name in [(URL_1, "RawData_1"), (URL_2, "RawData_2")]:
        try:
            temp_df = pd.read_csv(url)
            # [핵심] 1. 중복 컬럼명 즉시 제거
            temp_df = temp_df.loc[:, ~temp_df.columns.duplicated()].copy()
            # [핵심] 2. 항목명 번역
            temp_df = temp_df.rename(columns=rename_map)
            # [핵심] 3. 번역 후 중복 다시 체크 및 인덱스 초기화
            temp_df = temp_df.loc[:, ~temp_df.columns.duplicated()].copy()
            temp_df = temp_df.reset_index(drop=True)
            all_dfs.append(temp_df)
        except: continue
    
    if not all_dfs: return None
    
    # [핵심] 4. 안전한 병합
    full_df = pd.concat(all_dfs, axis=0, ignore_index=True)
    
    # 날짜 및 숫자 정제
    full_df['날짜'] = pd.to_datetime(full_df['날짜'], errors='coerce')
    num_cols = ['광고비', '총 전환매출액(14일)', '클릭수', '노출수']
    for col in num_cols:
        if col in full_df.columns:
            full_df[col] = pd.to_numeric(full_df[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
    
    return full_df

df = load_and_clean_data()

if df is not None:
    # --- 사이드바: 심플 필터 ---
    with st.sidebar:
        st.title("🏢 KidsTen Dashboard")
        if '캠페인명' in df.columns:
            camps = sorted([x for x in df['캠페인명'].unique() if pd.notna(x)])
            sel_camps = st.multiselect("캠페인 선택", camps, default=camps)
            f_df = df[df['캠페인명'].isin(sel_camps)]
        else: f_df = df
        
        st.divider()
        st.info(f"**장준영 팀장**\nGrowth Strategy Lead")

    # --- 메인 대시보드 (v16.0) ---
    st.title("🚀 쿠팡 통합 광고 성과 분석")
    st.markdown("전체 캠페인 성과 및 일별 추이를 분석합니다.")
    
    # KPI Grid (Simple & Clean)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("💰 총 광고비", f"{f_df['광고비'].sum():,.0f}원")
    m2.metric("📈 총 매출액", f"{f_df['총 전환매출액(14일)'].sum():,.0f}원")
    roas = (f_df['총 전환매출액(14일)'].sum() / f_df['광고비'].sum() * 100) if f_df['광고비'].sum() > 0 else 0
    m3.metric("🎯 평균 ROAS", f"{roas:.1f}%")
    m4.metric("📊 데이터 수", f"{len(f_df):,}건")

    # 성과 차트 (Professional White Theme)
    st.subheader("🗓️ 일별 광고비 및 매출 추이")
    trend = f_df.groupby('날짜')[['광고비', '총 전환매출액(14일)']].sum().reset_index()
    fig = px.line(trend, x='날짜', y=['광고비', '총 전환매출액(14일)'], 
                  labels={'value': '금액(원)', 'variable': '항목'},
                  color_discrete_sequence=['#ef4444', '#1e40af'])
    fig.update_layout(template='plotly_white', height=450)
    st.plotly_chart(fig, use_container_width=True)

    # 데이터 상세 보기
    st.subheader("📋 통합 성과 상세 데이터")
    st.dataframe(f_df.sort_values('날짜', ascending=False), use_container_width=True)

else:
    st.error("데이터를 로드할 수 없습니다. 시트 주소와 공유 설정을 확인해 주세요.")
