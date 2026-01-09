import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. 고품격 다크 UI 디자인 (레퍼런스 HTML 감성 이식)
st.set_page_config(page_title="KidsTen Growth Intelligence", layout="wide")
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
        padding: 24px;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 20px;
    }
    
    .m-label { color: #94a3b8; font-size: 14px; margin-bottom: 8px; font-weight: 500; }
    .m-value { font-size: 32px; font-weight: 700; color: #ffffff; }
    
    h1, h2, h3, p { color: #f8fafc !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. 통합 데이터 로드 엔진 (중복 컬럼 박멸 로직 적용)
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
            # [Fix] 1. 원본 데이터의 중복 컬럼 제거
            df = df.loc[:, ~df.columns.duplicated()]
            # [Fix] 2. 컬럼명 번역(Rename)
            df = df.rename(columns=rename_map)
            # [Fix] 3. 번역 후 이름이 겹치게 된 경우 다시 한 번 중복 제거
            df = df.loc[:, ~df.columns.duplicated()]
            return df
        except Exception as e:
            st.error(f"❌ {name} 로드 실패: {e}")
            return None

    d1 = fetch(URL_1, "RawData_1")
    d2 = fetch(URL_2, "RawData_2")

    if d1 is not None: all_dfs.append(d1)
    if d2 is not None: all_dfs.append(d2)
    
    if not all_dfs: return None
    
    # [Fix] 중복 컬럼이 제거된 상태에서 최종 병합
    full_df = pd.concat(all_dfs, axis=0, ignore_index=True)
    
    # 날짜 처리
    full_df['날짜'] = pd.to_datetime(full_df['날짜'], errors='coerce')
    
    # 숫자 데이터 정제 (콤마 제거 및 숫자 변환)
    num_cols = ['광고비', '총 전환매출액(14일)', '클릭수', '노출수']
    for col in num_cols:
        if col in full_df.columns:
            full_df[col] = pd.to_numeric(full_df[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
    
    full_df['ROAS'] = (full_df['총 전환매출액(14일)'] / full_df['광고비'] * 100).replace([float('inf')], 0).fillna(0)
    return full_df

# 3. 메인 분석 엔진 실행
df = load_and_merge_data()

if df is not None:
    # --- 사이드바 및 필터 ---
    with st.sidebar:
        st.markdown("### 🛰️ KidsTen Strategic Unit")
        if '캠페인명' in df.columns:
            camps = sorted([x for x in df['캠페인명'].unique() if pd.notna(x)])
            sel_camps = st.multiselect("분석 캠페인 선택", camps, default=camps)
            f_df = df[df['캠페인명'].isin(sel_camps)]
        else: f_df = df
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown(f"""
            <div style="padding:15px; border:1px solid rgba(255,255,255,0.1); border-radius:10px;">
                <p style="font-size:12px; color:#94a3b8; margin:0;">Analysis By</p>
                <p style="font-size:15px; font-weight:700; margin:0; color:#ffffff;">장준영 팀장</p>
                <p style="font-size:11px; color:#3b82f6; margin:0;">Growth Strategy Team</p>
            </div>
        """, unsafe_allow_html=True)

    # --- 메인 대시보드 (v13.2) ---
    st.markdown("# 📊 KidsTen Ad Cockpit Pro")
    
    # KPI Grid (HTML 디자인 재현)
    k1, k2, k3 = st.columns(3)
    with k1: st.markdown(f'<div class="report-card"><p class="m-label">누적 집행 광고비</p><p class="m-value">{f_df["광고비"].sum():,.0f}원</p></div>', unsafe_allow_html=True)
    with k2: st.markdown(f'<div class="report-card"><p class="m-label">누적 광고 매출액</p><p class="m-value">{f_df["총 전환매출액(14일)"].sum():,.0f}원</p></div>', unsafe_allow_html=True)
    total_roas = (f_df['총 전환매출액(14일)'].sum() / f_df['광고비'].sum() * 100) if f_df['광고비'].sum() > 0 else 0
    with k3: st.markdown(f'<div class="report-card"><p class="m-label">평균 성과 ROAS</p><p class="m-value" style="color:#3b82f6;">{total_roas:.1f}%</p></div>', unsafe_allow_html=True)

    # 트렌드 차트
    st.markdown("<div class='report-card'>", unsafe_allow_html=True)
    st.subheader("🗓️ 일별 광고 성과 밸런스")
    trend = f_df.groupby('날짜')[['광고비', '총 전환매출액(14일)']].sum().reset_index()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=trend['날짜'], y=trend['총 전환매출액(14일)'], name='Sales', line=dict(color='#3b82f6', width=4), fill='tozeroy'))
    fig.add_trace(go.Scatter(x=trend['날짜'], y=trend['광고비'], name='Spend', line=dict(color='#ef4444', width=2)))
    fig.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=400)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # 데이터 상세 보기
    st.subheader("📋 통합 실시간 로우데이터")
    st.dataframe(f_df.sort_values('날짜', ascending=False), use_container_width=True)

else:
    st.warning("데이터 정제 및 로딩 중입니다. 잠시만 기다려주세요.")
