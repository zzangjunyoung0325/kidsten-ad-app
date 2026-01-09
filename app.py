import streamlit as st
import pandas as pd

# 1. 디자인 및 G마켓 산스 세팅
st.set_page_config(page_title="KidsTen Growth Cockpit Pro", layout="wide")
st.markdown("""<style>@import url('https://cdn.jsdelivr.net/gh/projectnoonnu/noonfonts_2001@1.1/GmarketSansMedium.woff');* { font-family: 'GmarketSansMedium', sans-serif !important; }</style>""", unsafe_allow_html=True)

# 2. 데이터 주소 설정
URL_1 = "https://docs.google.com/spreadsheets/d/1R4qwQFQxXxL7NO67c8mr08KXMZvU9qkArNFoPFKYJDU/export?format=csv&gid=0"
URL_2 = "https://docs.google.com/spreadsheets/d/1R4qwQFQxXxL7NO67c8mr08KXMZvU9qkArNFoPFKYJDU/export?format=csv&gid=481757610"

@st.cache_data
def load_and_merge_data():
    all_dfs = []
    
    # --- 컬럼 번역기 (중요!) ---
    # 서로 다른 보고서 항목들을 하나의 표준 이름으로 바꿉니다.
    rename_map = {
        '캠페인 시작일': '날짜', 
        '캠페인 이름': '캠페인명',
        '광고비(원)': '광고비',
        '총 전환 매출액 (14일)(원)': '총 전환매출액(14일)',
        '클릭수': '클릭수',
        '노출수': '노출수'
    }

    def fetch_data(url, name):
        try:
            df = pd.read_csv(url)
            # 항목 이름 변경 적용
            df = df.rename(columns=rename_map)
            
            # 필수 항목 체크 (번역 후에도 '날짜'가 없으면 에러)
            if '날짜' not in df.columns:
                st.error(f"❌ {name}에 날짜 관련 항목이 없습니다. 현재 항목: {list(df.columns)}")
                return None
            return df
        except Exception as e:
            st.warning(f"⚠️ {name} 로드 실패: {e}")
            return None

    df1 = fetch_data(URL_1, "RawData_1")
    df2 = fetch_data(URL_2, "RawData_2")

    if df1 is not None: all_dfs.append(df1)
    if df2 is not None: all_dfs.append(df2)
    
    if not all_dfs: return None
    
    # 통합 및 정제
    full_df = pd.concat(all_dfs, ignore_index=True)
    full_df['날짜'] = pd.to_datetime(full_df['날짜'], errors='coerce')
    
    num_cols = ['광고비', '총 전환매출액(14일)', '클릭수', '노출수']
    for col in num_cols:
        if col in full_df.columns:
            full_df[col] = pd.to_numeric(full_df[col], errors='coerce').fillna(0)
    
    # ROAS 계산
    if '광고비' in full_df.columns and '총 전환매출액(14일)' in full_df.columns:
        full_df['ROAS'] = (full_df['총 전환매출액(14일)'] / full_df['광고비'] * 100).fillna(0).replace([float('inf')], 0)
    
    return full_df

df = load_and_merge_data()

if df is not None:
    st.success(f"✅ 통합 완료! (총 {len(df):,}개 데이터 분석 중)")
    
    # --- 사이드바 필터 ---
    st.sidebar.markdown("### 🏛️ 브랜드 필터")
    if '캠페인명' in df.columns:
        # 결측치 제거 후 정렬
        campaigns = sorted([x for x in df['캠페인명'].unique() if pd.notna(x)])
        sel_campaigns = st.sidebar.multiselect("분석 캠페인 선택", campaigns, default=campaigns)
        f_df = df[df['캠페인명'].isin(sel_campaigns)]
    else:
        f_df = df

    # --- 메인 대시보드 ---
    st.title("🛡️ KidsTen Integrated Dashboard")
    
    m1, m2, m3 = st.columns(3)
    m1.metric("💰 총 광고비", f"{f_df['광고비'].sum():,.0f}원")
    m2.metric("📈 총 매출액", f"{f_df['총 전환매출액(14일)'].sum():,.0f}원")
    total_roas = (f_df['총 전환매출액(14일)'].sum() / f_df['광고비'].sum() * 100) if f_df['광고비'].sum() > 0 else 0
    m3.metric("🎯 평균 ROAS", f"{total_roas:.1f}%")

    st.divider()
    st.dataframe(f_df.sort_values('날짜', ascending=False), use_container_width=True)

else:
    st.info("시트 주소 또는 항목명을 확인 중입니다.")
