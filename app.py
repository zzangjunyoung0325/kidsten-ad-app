import streamlit as st
import pandas as pd
import plotly.express as px

# 1. 디자인 및 G마켓 산스 세팅
st.set_page_config(page_title="KidsTen Growth Cockpit Pro", layout="wide")
st.markdown("""<style>@import url('https://cdn.jsdelivr.net/gh/projectnoonnu/noonfonts_2001@1.1/GmarketSansMedium.woff');* { font-family: 'GmarketSansMedium', sans-serif !important; }</style>""", unsafe_allow_html=True)

# 2. 데이터 소스 (팀장님이 주신 정보 반영)
URL_1 = "https://docs.google.com/spreadsheets/d/1R4qwQFQxXxL7NO67c8mr08KXMZvU9qkArNFoPFKYJDU/export?format=csv&gid=0"
URL_2 = "https://docs.google.com/spreadsheets/d/1R4qwQFQxXxL7NO67c8mr08KXMZvU9qkArNFoPFKYJDU/export?format=csv&gid=481757610"

@st.cache_data
def load_and_merge_data():
    all_dfs = []
    
    # --- 시트 1 로드 시도 ---
    try:
        df1 = pd.read_csv(URL_1)
        all_dfs.append(df1)
    except Exception as e:
        st.error(f"❌ RawData_1 (기존 데이터) 로드 실패: {e}")
    
    # --- 시트 2 로드 시도 ---
    try:
        df2 = pd.read_csv(URL_2)
        all_dfs.append(df2)
    except Exception as e:
        st.error(f"❌ RawData_2 (새 데이터) 로드 실패: {e}")
    
    if not all_dfs:
        return None
    
    # 데이터 통합
    full_df = pd.concat(all_dfs, ignore_index=True)
    full_df['날짜'] = pd.to_datetime(full_df['날짜'], format='%Y%m%d', errors='coerce')
    
    # 숫자형 변환
    num_cols = ['광고비', '총 전환매출액(14일)', '클릭수', '노출수']
    for col in num_cols:
        if col in full_df.columns:
            full_df[col] = pd.to_numeric(full_df[col], errors='coerce').fillna(0)
    
    full_df['ROAS'] = (full_df['총 전환매출액(14일)'] / full_df['광고비'] * 100).fillna(0).replace([float('inf')], 0)
    
    def classify(row):
        if row['ROAS'] >= 400: return "✅ 우수"
        elif row['ROAS'] >= 200: return "🟡 관리"
        else: return "🚨 위험"
    full_df['상태'] = full_df.apply(classify, axis=1)
    
    return full_df

df = load_and_merge_data()

if df is not None:
    # --- 사이드바 필터 ---
    st.sidebar.markdown("### 🏢 KidsTen Brand Filter")
    all_campaigns = sorted(df['캠페인명'].unique().tolist())
    sel_campaigns = st.sidebar.multiselect("분석할 캠페인 선택", all_campaigns, default=all_campaigns)
    f_df = df[df['캠페인명'].isin(sel_campaigns)]

    # --- 메인 대시보드 (디자인 유지) ---
    st.title("🛡️ KidsTen Integrated Growth Command")
    
    m1, m2, m3 = st.columns(3)
    m1.metric("💰 통합 광고 집행비", f"{f_df['광고비'].sum():,.0f}원")
    m2.metric("📈 통합 광고 매출", f"{f_df['총 전환매출액(14일)'].sum():,.0f}원")
    total_roas = (f_df['총 전환매출액(14일)'].sum() / f_df['광고비'].sum() * 100) if f_df['광고비'].sum() > 0 else 0
    m3.metric("🎯 평균 ROAS", f"{total_roas:.1f}%")

    # 그래프 및 테이블 코드 생략 (기존 디자인 유지)
    st.dataframe(f_df.sort_values(by='날짜', ascending=False), use_container_width=True)

else:
    st.warning("데이터를 불러올 수 없습니다. 화면 상단의 빨간색 에러 메시지를 확인해 주세요.")
