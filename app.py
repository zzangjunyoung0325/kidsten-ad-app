import streamlit as st
import pandas as pd

# 1. 디자인 세팅
st.set_page_config(page_title="KidsTen Growth Cockpit Pro", layout="wide")
st.markdown("""<style>@import url('https://cdn.jsdelivr.net/gh/projectnoonnu/noonfonts_2001@1.1/GmarketSansMedium.woff');* { font-family: 'GmarketSansMedium', sans-serif !important; }</style>""", unsafe_allow_html=True)

# 2. 데이터 주소 설정 (팀장님, 여기서 GID를 다시 한번 확인해주세요!)
URL_1 = "https://docs.google.com/spreadsheets/d/1R4qwQFQxXxL7NO67c8mr08KXMZvU9qkArNFoPFKYJDU/export?format=csv&gid=0"
URL_2 = "https://docs.google.com/spreadsheets/d/1R4qwQFQxXxL7NO67c8mr08KXMZvU9qkArNFoPFKYJDU/export?format=csv&gid=481757610"

@st.cache_data
def load_and_merge_data():
    all_dfs = []
    
    # --- 시트 로드 함수 (중복 제거 및 안전화) ---
    def fetch_data(url, name):
        try:
            temp_df = pd.read_csv(url)
            if '날짜' not in temp_df.columns:
                st.error(f"⚠️ {name} 시트에 '날짜' 컬럼이 없습니다. 현재 컬럼: {list(temp_df.columns)}")
                return None
            return temp_df
        except Exception as e:
            st.error(f"❌ {name} 로드 실패: {e}")
            return None

    # 각 시트에서 데이터 가져오기
    df1 = fetch_data(URL_1, "RawData_1 (기존)")
    df2 = fetch_data(URL_2, "RawData_2 (새로운)")

    if df1 is not None: all_dfs.append(df1)
    if df2 is not None: all_dfs.append(df2)
    
    if not all_dfs:
        st.stop() # 데이터가 하나도 없으면 여기서 멈춤
    
    # 데이터 통합
    full_df = pd.concat(all_dfs, ignore_index=True)
    
    # 데이터 정제 (KeyError 방지 로직)
    if '날짜' in full_df.columns:
        full_df['날짜'] = pd.to_datetime(full_df['날짜'], format='%Y%m%d', errors='coerce')
    
    num_cols = ['광고비', '총 전환매출액(14일)', '클릭수', '노출수']
    for col in num_cols:
        if col in full_df.columns:
            full_df[col] = pd.to_numeric(full_df[col], errors='coerce').fillna(0)
    
    # ROAS 계산: $$ROAS = \frac{\text{총 전환매출액}}{\text{광고비}} \times 100$$
    if '광고비' in full_df.columns and '총 전환매출액(14일)' in full_df.columns:
        full_df['ROAS'] = (full_df['총 전환매출액(14일)'] / full_df['광고비'] * 100).fillna(0).replace([float('inf')], 0)
    
    return full_df

# 메인 실행부
df = load_and_merge_data()

if df is not None:
    st.success(f"✅ 총 {len(df):,}행의 데이터를 성공적으로 로드했습니다!")
    
    # --- 사이드바 필터 ---
    if '캠페인명' in df.columns:
        all_campaigns = sorted(df['캠페인명'].unique().tolist())
        sel_campaigns = st.sidebar.multiselect("분석할 캠페인 선택", all_campaigns, default=all_campaigns)
        f_df = df[df['캠페인명'].isin(sel_campaigns)]
    else:
        st.warning("데이터에 '캠페인명' 컬럼이 없어 필터를 생성할 수 없습니다.")
        f_df = df

    # 대시보드 출력
    st.title("🛡️ KidsTen Integrated Cockpit")
    st.metric("💰 총 집행비", f"{f_df['광고비'].sum():,.0f}원")
    st.dataframe(f_df.head(100), use_container_width=True)
