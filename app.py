import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. 프로페셔널 비즈니스 UI 설정
st.set_page_config(page_title="KidsTen Growth Intelligence", layout="wide")

st.markdown("""
    <style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    * { font-family: 'Pretendard', sans-serif !important; }
    .main { background-color: #f8fafc; }
    .stMetric { background-color: white; padding: 20px; border-radius: 12px; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
    h1, h2, h3 { color: #1e293b; }
    </style>
    """, unsafe_allow_html=True)

# 2. 데이터 통합 및 딥 클렌징 엔진 (InvalidIndexError 해결)
URL_1 = "https://docs.google.com/spreadsheets/d/1R4qwQFQxXxL7NO67c8mr08KXMZvU9qkArNFoPFKYJDU/export?format=csv&gid=75240363"
URL_2 = "https://docs.google.com/spreadsheets/d/1R4qwQFQxXxL7NO67c8mr08KXMZvU9qkArNFoPFKYJDU/export?format=csv&gid=481757610"

@st.cache_data
def load_and_deep_clean():
    rename_map = {
        '캠페인 시작일': '날짜', '캠페인 이름': '캠페인명', 
        '광고비(원)': '광고비', '총 전환 매출액 (14일)(원)': '총 전환매출액(14일)',
        '클릭수': '클릭수', '노출수': '노출수'
    }
    
    all_dfs = []
    
    def fetch_strictly(url, name):
        try:
            df = pd.read_csv(url)
            # [단계 1] 이름 없는 유령 컬럼(Unnamed) 제거
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            # [단계 2] 원본 상태에서 중복 이름 제거
            df = df.loc[:, ~df.columns.duplicated()].copy()
            # [단계 3] 항목명 번역
            df = df.rename(columns=rename_map)
            # [단계 4] 번역 후 중복된 이름이 생겼을 경우(예: 비용/광고비 동시 존재) 첫 번째만 남김
            df = df.loc[:, ~df.columns.duplicated()].copy()
            # [단계 5] 인덱스 초기화
            df = df.reset_index(drop=True)
            return df
        except Exception as e:
            st.warning(f"⚠️ {name} 로딩 중 건너뜀: {e}")
            return None

    d1 = fetch_strictly(URL_1, "RawData_1")
    d2 = fetch_strictly(URL_2, "RawData_2")

    if d1 is not None: all_dfs.append(d1)
    if d2 is not None: all_dfs.append(d2)
    
    if not all_dfs: return None
    
    # [단계 6] 수직 통합 시 indexer 에러 방지를 위해 컬럼 합집합만 추출
    full_df = pd.concat(all_dfs, axis=0, ignore_index=True, sort=False)
    # [단계 7] 최종 통합본에서 혹시 모를 중복 컬럼 다시 한 번 체크
    full_df = full_df.loc[:, ~full_df.columns.duplicated()].copy()
    full_df = full_df.reset_index(drop=True)
    
    # 데이터 타입 정제
    full_df['날짜'] = pd.to_datetime(full_df['날짜'], errors='coerce')
    for c in ['광고비', '총 전환매출액(14일)', '클릭수', '노출수']:
        if c in full_df.columns:
            full_df[c] = pd.to_numeric(full_df[c].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
    
    full_df['ROAS'] = (full_df['총 전환매출액(14일)'] / full_df['광고비'] * 100).replace([float('inf')], 0).fillna(0)
    return full_df

# 메인 실행
df = load_and_deep_clean()

if df is not None:
    # --- 사이드바 필터 ---
    with st.sidebar:
        st.header("🏢 KidsTen Filter")
        if '캠페인명' in df.columns:
            camps = sorted([x for x in df['캠페인명'].unique() if pd.notna(x)])
            sel_camps = st.multiselect("캠페인 선택", camps, default=camps)
            f_df = df[df['캠페인명'].isin(sel_camps)]
        else: f_df = df
        
        st.divider()
        st.write(f"**장준영 팀장**")
        st.caption("Growth Lead | 18th Year")

    # --- 메인 대시보드 ---
    st.title("🚀 쿠팡 통합 광고 성과 분석")
    
    # 핵심 지표
    c1, c2, c3 = st.columns(3)
    c1.metric("💰 누적 광고비", f"{f_df['광고비'].sum():,.0f}원")
    c2.metric("📈 누적 매출액", f"{f_df['총 전환매출액(14일)'].sum():,.0f}원")
    total_roas = (f_df['총 전환매출액(14일)'].sum() / f_df['광고비'].sum() * 100) if f_df['광고비'].sum() > 0 else 0
    c3.metric("🎯 평균 ROAS", f"{total_roas:.1f}%")

    st.divider()

    # 트렌드 차트
    st.subheader("🗓️ 일별 광고비 대비 매출 추이")
    trend = f_df.groupby('날짜')[['광고비', '총 전환매출액(14일)']].sum().reset_index()
    fig = go.Figure()
    fig.add_trace(go.Bar(x=trend['날짜'], y=trend['총 전환매출액(14일)'], name='Sales', marker_color='#3b82f6', opacity=0.7))
    fig.add_trace(go.Scatter(x=trend['날짜'], y=trend['광고비'], name='Spend', line=dict(color='#ef4444', width=3)))
    fig.update_layout(template='plotly_white', height=450, margin=dict(l=0,r=0,t=20,b=0))
    st.plotly_chart(fig, use_container_width=True)

    # 데이터 리스트
    st.subheader("📋 실시간 통합 로우데이터")
    st.dataframe(f_df.sort_values('날짜', ascending=False), use_container_width=True)

else:
    st.error("데이터를 합치는 중 오류가 발생했습니다. 구글 시트의 항목명이 중복되지 않았는지 확인해주세요.")
