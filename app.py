import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. 디자인: 팀장님이 만드신 HTML의 감성을 SaaS 앱 형태로 이식
st.set_page_config(page_title="KidsTen Growth Cockpit", layout="wide")

st.markdown("""
    <style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    * { font-family: 'Pretendard', sans-serif !important; }
    
    .main { background-color: #f1f5f9; }
    .stMetric { background-color: white; padding: 20px; border-radius: 12px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }
    
    /* 상단 앱 바 스타일 */
    .app-bar {
        background: #ffffff;
        padding: 20px 30px;
        border-bottom: 1px solid #e2e8f0;
        margin-bottom: 30px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. 데이터 통합 엔진 (InvalidIndexError 완전 해결 버전)
URL_1 = "https://docs.google.com/spreadsheets/d/1R4qwQFQxXxL7NO67c8mr08KXMZvU9qkArNFoPFKYJDU/export?format=csv&gid=75240363"
URL_2 = "https://docs.google.com/spreadsheets/d/1R4qwQFQxXxL7NO67c8mr08KXMZvU9qkArNFoPFKYJDU/export?format=csv&gid=481757610"

@st.cache_data
def load_data_final():
    rename_map = {
        '캠페인 시작일': '날짜', '캠페인 이름': '캠페인명', 
        '광고비(원)': '광고비', '총 전환 매출액 (14일)(원)': '총 전환매출액(14일)'
    }
    
    def clean_sheet(url):
        try:
            df = pd.read_csv(url)
            # [단계 1] 컬럼 중복 제거 (InvalidIndexError 예방 핵심)
            df = df.loc[:, ~df.columns.duplicated()].copy()
            # [단계 2] 인덱스 완전 초기화
            df = df.reset_index(drop=True)
            # [단계 3] 이름 변경
            df = df.rename(columns=rename_map)
            # [단계 4] 변경 후 중복 다시 체크
            df = df.loc[:, ~df.columns.duplicated()].copy()
            return df
        except: return None

    d1 = clean_sheet(URL_1)
    d2 = clean_sheet(URL_2)
    
    dfs = [d for d in [d1, d2] if d is not None]
    if not dfs: return None
    
    # [단계 5] 합칠 때 발생할 수 있는 모든 인덱스 충돌 방지 (axis=0, ignore_index=True)
    full_df = pd.concat(dfs, axis=0, ignore_index=True, sort=False)
    
    # [단계 6] 최종 통합본의 중복 컬럼 및 인덱스 마지막 점검
    full_df = full_df.loc[:, ~full_df.columns.duplicated()].copy()
    full_df = full_df.reset_index(drop=True)
    
    # 데이터 정제
    full_df['날짜'] = pd.to_datetime(full_df['날짜'], errors='coerce')
    for c in ['광고비', '총 전환매출액(14일)', '클릭수', '노출수']:
        if c in full_df.columns:
            full_df[c] = pd.to_numeric(full_df[c].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
    
    full_df['ROAS'] = (full_df['총 전환매출액(14일)'] / full_df['광고비'] * 100).replace([float('inf')], 0).fillna(0)
    return full_df

df = load_data_final()

if df is not None:
    # --- 사이드바 ---
    with st.sidebar:
        st.title("🏢 KidsTen Ops")
        camps = sorted([x for x in df['캠페인명'].unique() if pd.notna(x)])
        sel_camps = st.multiselect("캠페인 필터", camps, default=camps)
        f_df = df[df['캠페인명'].isin(sel_camps)]
        
        st.divider()
        st.write(f"**Jun-young Jang**")
        st.caption("Growth Team Leader | 18th Year")

    # --- 메인 화면 (SaaS 앱 바 스타일) ---
    st.markdown(f"""
        <div class="app-bar">
            <h2 style="margin:0;">🚀 Ad Strategy Cockpit</h2>
            <span style="color:#64748b;">Data Updated: {pd.Timestamp.now().strftime('%Y-%m-%d')}</span>
        </div>
    """, unsafe_allow_html=True)
    
    # KPI 카드
    c1, c2, c3 = st.columns(3)
    c1.metric("💰 누적 광고비", f"{f_df['광고비'].sum():,.0f}원")
    c2.metric("📈 누적 매출액", f"{f_df['총 전환매출액(14일)'].sum():,.0f}원")
    roas = (f_df['총 전환매출액(14일)'].sum() / f_df['광고비'].sum() * 100) if f_df['광고비'].sum() > 0 else 0
    c3.metric("🎯 평균 ROAS", f"{roas:.1f}%")

    st.divider()

    # 트렌드 그래프
    st.subheader("🗓️ 일별 광고 성과 트렌드")
    trend = f_df.groupby('날짜')[['광고비', '총 전환매출액(14일)']].sum().reset_index()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=trend['날짜'], y=trend['총 전환매출액(14일)'], name='Sales', line=dict(color='#3b82f6', width=4), fill='tozeroy'))
    fig.add_trace(go.Scatter(x=trend['날짜'], y=trend['광고비'], name='Spend', line=dict(color='#ef4444', width=2)))
    fig.update_layout(template='plotly_white', height=450, margin=dict(l=0,r=0,t=20,b=0))
    st.plotly_chart(fig, use_container_width=True)

    # 테이블
    st.subheader("📋 실시간 통합 성과 데이터베이스")
    st.dataframe(f_df.sort_values('날짜', ascending=False), use_container_width=True)

else:
    st.error("데이터 통합 중 오류가 발생했습니다. 구글 시트의 공유 설정이나 시트 형식을 확인해 주세요.")
