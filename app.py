import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. 디자인 레이아웃 (HTML 레퍼런스 감성 유지)
st.set_page_config(page_title="KidsTen Growth Cockpit", layout="wide")
st.markdown("""
    <style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #0f172a !important;
        font-family: 'Pretendard', sans-serif !important;
        color: #f8fafc !important;
    }
    .report-card {
        background: rgba(30, 41, 59, 0.7);
        padding: 24px; border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.1); margin-bottom: 20px;
    }
    .m-label { color: #94a3b8; font-size: 14px; margin-bottom: 8px; }
    .m-value { font-size: 30px; font-weight: 700; color: #ffffff; }
    </style>
    """, unsafe_allow_html=True)

# 2. 통합 데이터 로드 엔진 (중복 제거 로직 추가)
URL_1 = "https://docs.google.com/spreadsheets/d/1R4qwQFQxXxL7NO67c8mr08KXMZvU9qkArNFoPFKYJDU/export?format=csv&gid=75240363"
URL_2 = "https://docs.google.com/spreadsheets/d/1R4qwQFQxXxL7NO67c8mr08KXMZvU9qkArNFoPFKYJDU/export?format=csv&gid=481757610"

@st.cache_data
def load_and_merge_data():
    rename_map = {
        '캠페인 시작일': '날짜', '캠페인 이름': '캠페인명', 
        '광고비(원)': '광고비', '총 전환 매출액 (14일)(원)': '총 전환매출액(14일)'
    }
    all_dfs = []
    
    def fetch(url, name):
        try:
            df = pd.read_csv(url)
            # [핵심 수정] 중복된 컬럼명이 있으면 제거 (InvalidIndexError 방지)
            df = df.loc[:, ~df.columns.duplicated()]
            df = df.rename(columns=rename_map)
            return df
        except Exception as e:
            st.error(f"❌ {name} 로드 실패: {e}")
            return None

    d1 = fetch(URL_1, "RawData_1")
    d2 = fetch(URL_2, "RawData_2")

    if d1 is not None: all_dfs.append(d1)
    if d2 is not None: all_dfs.append(d2)
    
    if not all_dfs: return None
    
    # [핵심 수정] 합치기 전 모든 데이터프레임의 컬럼을 유니크하게 재설정
    full_df = pd.concat(all_dfs, axis=0, ignore_index=True)
    full_df = full_df.loc[:, ~full_df.columns.duplicated()] # 최종 중복 제거
    
    # 날짜 및 숫자 변환
    full_df['날짜'] = pd.to_datetime(full_df['날짜'], errors='coerce')
    for col in ['광고비', '총 전환매출액(14일)', '클릭수', '노출수']:
        if col in full_df.columns:
            full_df[col] = pd.to_numeric(full_df[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
    
    full_df['ROAS'] = (full_df['총 전환매출액(14일)'] / full_df['광고비'] * 100).replace([float('inf')], 0).fillna(0)
    return full_df

df = load_and_merge_data()

if df is not None:
    # --- 사이드바 및 필터 ---
    with st.sidebar:
        st.markdown("### 🛰️ KidsTen Insight")
        if '캠페인명' in df.columns:
            camps = sorted([x for x in df['캠페인명'].unique() if pd.notna(x)])
            sel_camps = st.multiselect("분석 캠페인", camps, default=camps)
            f_df = df[df['캠페인명'].isin(sel_camps)]
        else: f_df = df
        st.markdown(f'<div style="margin-top:200px; padding:10px; border:1px solid #334155;"><b>장준영 팀장</b><br><small>Growth Strategy</small></div>', unsafe_allow_html=True)

    # --- 메인 대시보드 ---
    st.markdown("# 📊 KidsTen Ad Cockpit v13.1")
    
    # KPI Grid
    k1, k2, k3 = st.columns(3)
    with k1: st.markdown(f'<div class="report-card"><p class="m-label">총 광고비</p><p class="m-value">{f_df["광고비"].sum():,.0f}</p></div>', unsafe_allow_html=True)
    with k2: st.markdown(f'<div class="report-card"><p class="m-label">총 매출액</p><p class="m-value">{f_df["총 전환매출액(14일)"].sum():,.0f}</p></div>', unsafe_allow_html=True)
    roas = (f_df['총 전환매출액(14일)'].sum() / f_df['광고비'].sum() * 100) if f_df['광고비'].sum() > 0 else 0
    with k3: st.markdown(f'<div class="report-card"><p class="m-label">평균 ROAS</p><p class="m-value" style="color:#3b82f6;">{roas:.1f}%</p></div>', unsafe_allow_html=True)

    # 트렌드 차트
    st.markdown("<div class='report-card'>", unsafe_allow_html=True)
    trend = f_df.groupby('날짜')[['광고비', '총 전환매출액(14일)']].sum().reset_index()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=trend['날짜'], y=trend['총 전환매출액(14일)'], name='Sales', fill='tozeroy', line=dict(color='#3b82f6')))
    fig.add_trace(go.Scatter(x=trend['날짜'], y=trend['광고비'], name='Spend', line=dict(color='#ef4444')))
    fig.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=400)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.dataframe(f_df.sort_values('날짜', ascending=False), use_container_width=True)

else:
    st.warning("데이터 정제 중입니다. 시트 설정을 확인해주세요.")
