import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. HTML 레퍼런스 감성 이식 (다크 모드 및 카드 레이아웃)
st.set_page_config(page_title="KidsTen Growth Intelligence", layout="wide")

st.markdown("""
    <style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    
    /* HTML 레퍼런스 테마 적용 (#0f172a) */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: #0f172a !important;
        font-family: 'Pretendard', sans-serif !important;
        color: #f8fafc !important;
    }
    
    [data-testid="stSidebar"] {
        background-color: #1e293b !important;
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* 카드 디자인 (Glassmorphism) */
    .report-card {
        background: rgba(30, 41, 59, 0.7);
        padding: 24px;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    .m-label { color: #94a3b8; font-size: 14px; margin-bottom: 8px; font-weight: 500; }
    .m-value { font-size: 32px; font-weight: 700; color: #ffffff; }
    .m-sub { font-size: 12px; color: #10b981; margin-top: 5px; font-weight: 600; }
    
    h1, h2, h3, h4, p, span { color: #f8fafc !important; }
    .stDataFrame { border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 2. 통합 데이터 로더 (에러 완전 차단 엔진)
URL_1 = "https://docs.google.com/spreadsheets/d/1R4qwQFQxXxL7NO67c8mr08KXMZvU9qkArNFoPFKYJDU/export?format=csv&gid=75240363"
URL_2 = "https://docs.google.com/spreadsheets/d/1R4qwQFQxXxL7NO67c8mr08KXMZvU9qkArNFoPFKYJDU/export?format=csv&gid=481757610"

@st.cache_data
def load_and_merge_data():
    rename_map = {
        '캠페인 시작일': '날짜', '캠페인 이름': '캠페인명', 
        '광고비(원)': '광고비', '총 전환 매출액 (14일)(원)': '총 전환매출액(14일)',
        '클릭수': '클릭수', '노출수': '노출수'
    }
    
    all_dfs = []
    
    def fetch_and_clean(url, name):
        try:
            df = pd.read_csv(url)
            # [핵심] 1. 중복 컬럼 제거 및 인덱스 초기화 (InvalidIndexError 방지)
            df = df.loc[:, ~df.columns.duplicated()].copy()
            df = df.reset_index(drop=True)
            
            # [핵심] 2. 항목명 번역 및 번역 후 중복 다시 체크
            df = df.rename(columns=rename_map)
            df = df.loc[:, ~df.columns.duplicated()].copy()
            
            # [핵심] 3. 숫자 데이터 정제
            num_cols = ['광고비', '총 전환매출액(14일)', '클릭수', '노출수']
            for col in num_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
            return df
        except Exception as e:
            st.error(f"❌ {name} 로드 실패: {e}")
            return None

    d1 = fetch_and_clean(URL_1, "RawData_1")
    d2 = fetch_and_clean(URL_2, "RawData_2")

    if d1 is not None: all_dfs.append(d1)
    if d2 is not None: all_dfs.append(d2)
    
    if not all_dfs: return None
    
    # [핵심] 4. 최종 병합 시 인덱스 무시
    full_df = pd.concat(all_dfs, axis=0, ignore_index=True)
    full_df['날짜'] = pd.to_datetime(full_df['날짜'], errors='coerce')
    full_df['ROAS'] = (full_df['총 전환매출액(14일)'] / full_df['광고비'] * 100).replace([float('inf')], 0).fillna(0)
    
    return full_df

# 3. 메인 분석 엔진 실행
df = load_and_merge_data()

if df is not None:
    # --- 사이드바 및 프로필 ---
    with st.sidebar:
        st.markdown("### 🏢 KidsTen Insight")
        if '캠페인명' in df.columns:
            camps = sorted([x for x in df['캠페인명'].unique() if pd.notna(x)])
            sel_camps = st.multiselect("분석 캠페인 선택", camps, default=camps)
            f_df = df[df['캠페인명'].isin(sel_camps)]
        else: f_df = df
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown(f"""
            <div style="padding:15px; background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.1); border-radius:10px;">
                <p style="font-size:12px; color:#94a3b8; margin:0;">Analysis Specialist</p>
                <p style="font-size:16px; font-weight:700; margin:0; color:#ffffff;">장준영 팀장</p>
                <p style="font-size:11px; color:#3b82f6; margin:0;">KidsTen Growth Lead</p>
            </div>
        """, unsafe_allow_html=True)

    # --- 메인 대시보드 (v14.0) ---
    st.markdown("# 🚀 KidsTen Ad Intelligence Cockpit")
    st.markdown("<p style='color:#94a3b8;'>통합 데이터 분석 및 전략 보고서</p>", unsafe_allow_html=True)
    
    # KPI Grid (HTML 레이아웃 재현)
    k1, k2, k3, k4 = st.columns(4)
    with k1: st.markdown(f'<div class="report-card"><p class="m-label">총 집행 광고비</p><p class="m-value">{f_df["광고비"].sum():,.0f}</p><p class="m-sub">Spend Total</p></div>', unsafe_allow_html=True)
    with k2: st.markdown(f'<div class="report-card"><p class="m-label">총 광고 매출액</p><p class="m-value">{f_df["총 전환매출액(14일)"].sum():,.0f}</p><p class="m-sub">Revenue Total</p></div>', unsafe_allow_html=True)
    roas = (f_df['총 전환매출액(14일)'].sum() / f_df['광고비'].sum() * 100) if f_df['광고비'].sum() > 0 else 0
    with k3: st.markdown(f'<div class="report-card"><p class="m-label">평균 ROAS</p><p class="m-value" style="color:#3b82f6;">{roas:.1f}%</p><p class="m-sub">Efficiency Rate</p></div>', unsafe_allow_html=True)
    with k4: st.markdown(f'<div class="report-card"><p class="m-label">분석 데이터</p><p class="m-value">{len(f_df):,}건</p><p class="m-sub">Raw Records</p></div>', unsafe_allow_html=True)

    # 트렌드 차트
    st.markdown("<div class='report-card'>", unsafe_allow_html=True)
    st.subheader("🗓️ 일별 광고비 및 매출 추이")
    trend = f_df.groupby('날짜')[['광고비', '총 전환매출액(14일)']].sum().reset_index()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=trend['날짜'], y=trend['총 전환매출액(14일)'], name='Sales', fill='tozeroy', line=dict(color='#3b82f6', width=4)))
    fig.add_trace(go.Scatter(x=trend['날짜'], y=trend['광고비'], name='Spend', line=dict(color='#ef4444', width=2)))
    fig.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=400, margin=dict(l=0,r=0,t=20,b=0))
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # 데이터 상세 리스트
    st.subheader("📋 통합 실시간 퍼포먼스 DB")
    st.dataframe(f_df.sort_values('날짜', ascending=False), use_container_width=True)

else:
    st.warning("데이터 정제 및 로딩 중입니다. 구글 시트 공유 설정을 확인해 주세요.")
