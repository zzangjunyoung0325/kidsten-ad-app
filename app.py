import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. 하이엔드 비즈니스 UI 디자인 (CSS)
st.set_page_config(page_title="KidsTen Growth Intelligence", layout="wide")

st.markdown("""
    <style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    * { font-family: 'Pretendard', sans-serif !important; }
    
    /* 배경 및 레이아웃 */
    .main { background-color: #f1f5f9; }
    
    /* 상단 전략 헤더 */
    .strategy-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: white;
        padding: 40px;
        border-radius: 20px;
        margin-bottom: 30px;
        box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);
    }
    
    /* 프리미엄 카드 디자인 */
    .stat-card {
        background: white;
        padding: 25px;
        border-radius: 15px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
    }
    .stat-label { color: #64748b; font-size: 14px; font-weight: 600; margin-bottom: 10px; }
    .stat-value { color: #0f172a; font-size: 28px; font-weight: 800; }
    
    /* 배지 스타일 */
    .badge {
        padding: 4px 12px;
        border-radius: 50px;
        font-size: 12px;
        font-weight: 700;
        margin-top: 10px;
        display: inline-block;
    }
    .badge-success { background: #dcfce7; color: #166534; }
    .badge-danger { background: #fee2e2; color: #991b1b; }
    </style>
    """, unsafe_allow_html=True)

# 2. 강력한 데이터 통합 엔진 (Error-Free)
URL_1 = "https://docs.google.com/spreadsheets/d/1R4qwQFQxXxL7NO67c8mr08KXMZvU9qkArNFoPFKYJDU/export?format=csv&gid=75240363"
URL_2 = "https://docs.google.com/spreadsheets/d/1R4qwQFQxXxL7NO67c8mr08KXMZvU9qkArNFoPFKYJDU/export?format=csv&gid=481757610"

@st.cache_data
def load_and_sync_data():
    map_cols = {'캠페인 시작일': '날짜', '캠페인 이름': '캠페인명', '광고비(원)': '광고비', '총 전환 매출액 (14일)(원)': '총 전환매출액(14일)'}
    dfs = []
    for url, name in [(URL_1, "S1"), (URL_2, "S2")]:
        try:
            df = pd.read_csv(url)
            # 중복 제거 및 인덱스 초기화 (InvalidIndexError 원천 차단)
            df = df.loc[:, ~df.columns.duplicated()].copy()
            df = df.rename(columns=map_cols)
            df = df.reset_index(drop=True)
            dfs.append(df)
        except: continue
    
    if not dfs: return None
    
    # 통합 병합
    full_df = pd.concat(dfs, axis=0, ignore_index=True).reset_index(drop=True)
    full_df['날짜'] = pd.to_datetime(full_df['날짜'], errors='coerce')
    
    # 숫자 정제
    for c in ['광고비', '총 전환매출액(14일)', '클릭수', '노출수']:
        if c in full_df.columns:
            full_df[c] = pd.to_numeric(full_df[c].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
    
    full_df['ROAS'] = (full_df['총 전환매출액(14일)'] / full_df['광고비'] * 100).replace([float('inf')], 0).fillna(0)
    return full_df

df = load_and_sync_data()

if df is not None:
    # --- 사이드바: 전문가 프로필 ---
    with st.sidebar:
        st.markdown("### 🏢 KidsTen Growth Cockpit")
        camps = sorted([x for x in df['캠페인명'].unique() if pd.notna(x)])
        sel_camps = st.multiselect("캠페인 필터링", camps, default=camps)
        f_df = df[df['캠페인명'].isin(sel_camps)]
        
        st.markdown("<br>"*10, unsafe_allow_html=True)
        st.markdown(f"""
            <div style="background:white; padding:20px; border-radius:15px; border:1px solid #e2e8f0;">
                <p style="font-size:12px; color:#64748b; margin:0;">Lead Strategist</p>
                <p style="font-size:16px; font-weight:800; color:#0f172a; margin:0;">장준영 팀장</p>
                <p style="font-size:11px; color:#3b82f6; margin:0;">Growth Lead | 18th Year</p>
            </div>
        """, unsafe_allow_html=True)

    # --- 메인 헤더 섹션 (HTML 감성 이식) ---
    st.markdown(f"""
        <div class="strategy-header">
            <h1 style="color:white; margin:0;">🚀 KidsTen Ad Intelligence Cockpit</h1>
            <p style="color:#94a3b8; font-size:18px; margin-top:10px;">
                현재 <b>{len(f_df):,}건</b>의 광고 데이터를 기반으로 성과를 실시간 분석 중입니다.
            </p>
        </div>
    """, unsafe_allow_html=True)

    # --- 성과 메트릭 (고급 카드 레이아웃) ---
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f'<div class="stat-card"><div class="stat-label">💰 누적 집행비</div><div class="stat-value">{f_df["광고비"].sum():,.0f}</div><div class="badge badge-success">Budget Sync OK</div></div>', unsafe_allow_html=True)
    with m2:
        st.markdown(f'<div class="stat-card"><div class="stat-label">📈 누적 매출액</div><div class="stat-value">{f_df["총 전환매출액(14일)"].sum():,.0f}</div><div class="badge badge-success">Revenue Sync OK</div></div>', unsafe_allow_html=True)
    with m3:
        roas = (f_df['총 전환매출액(14일)'].sum() / f_df['광고비'].sum() * 100) if f_df['광고비'].sum() > 0 else 0
        status = "✅ 최적" if roas >= 400 else "🚨 관리"
        b_class = "badge-success" if roas >= 400 else "badge-danger"
        st.markdown(f'<div class="stat-card"><div class="stat-label">🎯 평균 ROAS</div><div class="stat-value" style="color:#3b82f6;">{roas:.1f}%</div><div class="badge {b_class}">{status}</div></div>', unsafe_allow_html=True)
    with m4:
        st.markdown(f'<div class="stat-card"><div class="stat-label">🖱️ 평균 클릭률</div><div class="stat-value">{(f_df["클릭수"].sum()/f_df["노출수"].sum()*100):.2f}%</div><div class="badge badge-success">CTR Monitor</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- 차트 섹션 (SaaS 감성) ---
    c_left, c_right = st.columns([7, 3])
    with c_left:
        st.subheader("🗓️ 일별 광고비 대비 매출 추이")
        trend = f_df.groupby('날짜')[['광고비', '총 전환매출액(14일)']].sum().reset_index()
        fig = go.Figure()
        fig.add_trace(go.Bar(x=trend['날짜'], y=trend['총 전환매출액(14일)'], name='Sales', marker_color='#3b82f6', opacity=0.8))
        fig.add_trace(go.Scatter(x=trend['날짜'], y=trend['광고비'], name='Spend', line=dict(color='#ef4444', width=3)))
        fig.update_layout(template='plotly_white', height=450, margin=dict(l=0,r=0,t=20,b=0))
        st.plotly_chart(fig, use_container_width=True)

    with c_right:
        st.subheader("🎯 브랜드별 매출 비중")
        brand_pie = f_df.groupby('캠페인명')['총 전환매출액(14일)'].sum().reset_index()
        fig_pie = px.pie(brand_pie, values='총 전환매출액(14일)', names='캠페인명', hole=0.6, color_discrete_sequence=px.colors.qualitative.Pastel)
        fig_pie.update_layout(showlegend=False, height=450, margin=dict(l=0,r=0,t=0,b=0))
        st.plotly_chart(fig_pie, use_container_width=True)

    # --- 상세 테이블 ---
    st.subheader("📋 실시간 통합 데이터베이스")
    st.dataframe(f_df.sort_values('날짜', ascending=False), use_container_width=True)

else:
    st.error("데이터 로드 중입니다. 구글 시트 주소와 공유 설정을 다시 확인해 주세요.")
