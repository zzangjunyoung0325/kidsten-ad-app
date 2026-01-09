import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. HTML 레퍼런스(쿠팡11월보고_최종.html) 디자인 완벽 이식
st.set_page_config(page_title="KidsTen Growth Intelligence", layout="wide")

st.markdown("""
    <style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    
    /* 기본 배경 및 폰트 설정 (다크 테마) */
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #0f172a !important;
        font-family: 'Pretendard', sans-serif !important;
        color: #f8fafc !important;
    }
    
    /* 사이드바 다크 스타일 */
    [data-testid="stSidebar"] {
        background-color: #1e293b !important;
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* 카드(패널) 디자인 */
    .report-card {
        background: rgba(30, 41, 59, 0.7);
        padding: 24px;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 20px;
    }
    
    /* 메트릭 텍스트 설정 */
    .m-label { color: #94a3b8; font-size: 14px; margin-bottom: 8px; font-weight: 500; }
    .m-value { font-size: 32px; font-weight: 700; color: #ffffff; }
    .m-sub { font-size: 13px; color: #10b981; margin-top: 5px; }
    
    /* 테이블 스타일 커스텀 */
    .stDataFrame { border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 10px; }
    
    h1, h2, h3, p { color: #f8fafc !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. 데이터 연동 (수정된 GID 반영)
URL_1 = "https://docs.google.com/spreadsheets/d/1R4qwQFQxXxL7NO67c8mr08KXMZvU9qkArNFoPFKYJDU/export?format=csv&gid=75240363"
URL_2 = "https://docs.google.com/spreadsheets/d/1R4qwQFQxXxL7NO67c8mr08KXMZvU9qkArNFoPFKYJDU/export?format=csv&gid=481757610"

@st.cache_data
def load_and_merge_data():
    # 시트마다 다른 항목명 번역기
    rename_map = {
        '캠페인 시작일': '날짜', 
        '캠페인 이름': '캠페인명', 
        '광고비(원)': '광고비', 
        '총 전환 매출액 (14일)(원)': '총 전환매출액(14일)',
        '클릭수': '클릭수',
        '노출수': '노출수'
    }
    
    all_dfs = []
    
    def fetch(url, name):
        try:
            df = pd.read_csv(url)
            df = df.rename(columns=rename_map)
            # 수치 데이터 정제 (쉼표 제거 및 숫자 변환)
            for col in ['광고비', '총 전환매출액(14일)', '클릭수', '노출수']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
            return df
        except Exception as e:
            st.error(f"❌ {name} 로드 실패: {e}")
            return None

    d1 = fetch(URL_1, "RawData_1")
    d2 = fetch(URL_2, "RawData_2")

    if d1 is not None: all_dfs.append(d1)
    if d2 is not None: all_dfs.append(d2)
    
    if not all_dfs: return None
    
    full_df = pd.concat(all_dfs, ignore_index=True)
    full_df['날짜'] = pd.to_datetime(full_df['날짜'], errors='coerce')
    full_df['ROAS'] = (full_df['총 전환매출액(14일)'] / full_df['광고비'] * 100).replace([float('inf')], 0).fillna(0)
    
    return full_df

# 3. 메인 분석 및 출력
df = load_and_merge_data()

if df is not None:
    # --- 사이드바 ---
    with st.sidebar:
        st.markdown("### 🛰️ KidsTen Insight")
        if '캠페인명' in df.columns:
            camps = sorted([x for x in df['캠페인명'].unique() if pd.notna(x)])
            sel_camps = st.multiselect("분석 캠페인", camps, default=camps)
            f_df = df[df['캠페인명'].isin(sel_camps)]
        else:
            f_df = df
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown(f"""
            <div style="padding:15px; border:1px solid rgba(255,255,255,0.1); border-radius:10px;">
                <p style="font-size:12px; color:#94a3b8; margin:0;">Analysis By</p>
                <p style="font-size:15px; font-weight:700; margin:0;">장준영 팀장</p>
                <p style="font-size:11px; color:#3b82f6; margin:0;">Growth Strategy Team</p>
            </div>
        """, unsafe_allow_html=True)

    # --- 메인 대시보드 ---
    st.markdown("# 📊 KidsTen Ad Performance Cockpit")
    st.markdown("<p style='color:#94a3b8;'>통합 데이터 분석 및 전략 보고서</p>", unsafe_allow_html=True)

    # KPI 섹션 (HTML 레이아웃 재현)
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f"""<div class="report-card"><p class="m-label">총 광고비</p><p class="m-value">{f_df['광고비'].sum():,.0f}</p><p class="m-sub">Spend Amount</p></div>""", unsafe_allow_html=True)
    with k2:
        st.markdown(f"""<div class="report-card"><p class="m-label">총 매출액</p><p class="m-value">{f_df['총 전환매출액(14일)'].sum():,.0f}</p><p class="m-sub">Total Sales</p></div>""", unsafe_allow_html=True)
    with k3:
        avg_roas = (f_df['총 전환매출액(14일)'].sum() / f_df['광고비'].sum() * 100) if f_df['광고비'].sum() > 0 else 0
        st.markdown(f"""<div class="report-card"><p class="m-label">평균 ROAS</p><p class="m-value" style="color:#3b82f6;">{avg_roas:.1f}%</p><p class="m-sub">Efficiency Rate</p></div>""", unsafe_allow_html=True)
    with k4:
        st.markdown(f"""<div class="report-card"><p class="m-label">데이터 건수</p><p class="m-value">{len(f_df):,}건</p><p class="m-sub">Total Rows</p></div>""", unsafe_allow_html=True)

    # 메인 차트
    c_left, c_right = st.columns([7, 3])
    with c_left:
        st.markdown("<div class='report-card'>", unsafe_allow_html=True)
        st.subheader("🗓️ 일별 광고비 대비 매출 추이")
        trend = f_df.groupby('날짜')[['광고비', '총 전환매출액(14일)']].sum().reset_index()
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=trend['날짜'], y=trend['총 전환매출액(14일)'], name='Sales', line=dict(color='#3b82f6', width=4), fill='tozeroy'))
        fig.add_trace(go.Scatter(x=trend['날짜'], y=trend['광고비'], name='Spend', line=dict(color='#ef4444', width=2)))
        fig.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=400, margin=dict(l=0,r=0,t=20,b=0))
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with c_right:
        st.markdown("<div class='report-card'>", unsafe_allow_html=True)
        st.subheader("🎯 ROAS 성과 분포")
        # 캠페인별 성과 파이차트
        brand_pie = f_df.groupby('캠페인명')['총 전환매출액(14일)'].sum().reset_index()
        fig_pie = px.pie(brand_pie, values='총 전환매출액(14일)', names='캠페인명', hole=0.5, template='plotly_dark')
        fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=False, height=400, margin=dict(l=0,r=0,t=0,b=0))
        st.plotly_chart(fig_pie, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # 하단 데이터 리스트
    st.subheader("📋 실시간 통합 데이터베이스")
    st.dataframe(f_df.sort_values('날짜', ascending=False), use_container_width=True)

else:
    st.warning("데이터를 불러오는 중입니다. 잠시만 기다려주시거나 구글 시트의 [공유] 설정을 확인해주세요.")
