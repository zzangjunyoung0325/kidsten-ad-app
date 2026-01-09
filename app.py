import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. 고도화된 SaaS UI/UX 디자인 (G마켓 산스 및 카드 레이아웃)
st.set_page_config(page_title="KidsTen Growth Cockpit Pro", layout="wide")

st.markdown("""
    <style>
    @import url('https://cdn.jsdelivr.net/gh/projectnoonnu/noonfonts_2001@1.1/GmarketSansMedium.woff');
    * { font-family: 'GmarketSansMedium', sans-serif !important; }
    .main { background-color: #f1f5f9; }
    
    /* 카드 디자인 */
    .dashboard-card {
        background-color: #ffffff;
        padding: 24px;
        border-radius: 16px;
        box-shadow: 0 10px 15px -3px rgba(0,0,0,0.05);
        border: 1px solid #e2e8f0;
        margin-bottom: 24px;
    }
    
    /* 상단 전략 리포트 섹션 */
    .strategy-container {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: white;
        padding: 30px;
        border-radius: 20px;
        margin-bottom: 30px;
        border-left: 10px solid #3b82f6;
    }
    
    .status-badge {
        display: inline-block;
        padding: 6px 14px;
        border-radius: 50px;
        font-weight: bold;
        font-size: 0.9rem;
        margin-right: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .badge-red { background-color: #ef4444; color: white; }
    .badge-yellow { background-color: #fbbf24; color: #1e293b; }
    .badge-green { background-color: #10b981; color: white; }
    </style>
    """, unsafe_allow_html=True)

# 2. 멀티 데이터 소스 엔진 (RawData_1 + RawData_2)
# 팀장님이 주신 시트 ID와 GID를 정확히 매핑했습니다.
URL_1 = "https://docs.google.com/spreadsheets/d/1R4qwQFQxXxL7NO67c8mr08KXMZvU9qkArNFoPFKYJDU/export?format=csv&gid=0"
URL_2 = "https://docs.google.com/spreadsheets/d/1R4qwQFQxXxL7NO67c8mr08KXMZvU9qkArNFoPFKYJDU/export?format=csv&gid=481757610"

@st.cache_data
def load_and_merge_data():
    try:
        # 데이터 로드
        df1 = pd.read_csv(URL_1)
        df2 = pd.read_csv(URL_2)
        
        # 데이터 통합 (위아래로 붙이기)
        full_df = pd.concat([df1, df2], ignore_index=True)
        
        # 날짜 형식 및 숫자 형식 전처리
        full_df['날짜'] = pd.to_datetime(full_df['날짜'], format='%Y%m%d', errors='coerce')
        num_cols = ['광고비', '총 전환매출액(14일)', '클릭수', '노출수']
        for col in num_cols:
            if col in full_df.columns:
                full_df[col] = pd.to_numeric(full_df[col], errors='coerce').fillna(0)
        
        # 성과 지표 계산
        full_df['ROAS'] = (full_df['총 전환매출액(14일)'] / full_df['광고비'] * 100).fillna(0).replace([float('inf')], 0)
        full_df['CTR'] = (full_df['클릭수'] / full_df['노출수'] * 100).fillna(0)
        
        # 성과 상태 분류 (팀장님 요청 로직: 200% 이하는 위험)
        def classify(row):
            if row['ROAS'] >= 400: return "✅ 우수"
            elif row['ROAS'] >= 200: return "🟡 관리"
            else: return "🚨 위험"
        full_df['상태'] = full_df.apply(classify, axis=1)
        
        return full_df
    except Exception as e:
        st.error(f"데이터 로드 오류: {e}")
        return None

df = load_and_merge_data()

if df is not None:
    # --- 사이드바 필터 (복구 완료!) ---
    st.sidebar.markdown("### 🏢 KidsTen Brand Filter")
    all_campaigns = sorted(df['캠페인명'].unique().tolist())
    sel_campaigns = st.sidebar.multiselect("분석할 캠페인을 선택하세요", all_campaigns, default=all_campaigns)
    
    # 필터 적용 데이터
    f_df = df[df['캠페인명'].isin(sel_campaigns)]

    # --- Section 1: 전략 리포트 (상태별 카운트 포함) ---
    counts = f_df['상태'].value_counts()
    danger_df = f_df[(f_df['ROAS'] <= 200) & (f_df['광고비'] >= 50000)]
    
    st.markdown(f"""
    <div class="strategy-container">
        <h2 style='color:white; margin-top:0;'>🛡️ KidsTen Integrated Growth Command</h2>
        <div style='display: flex; gap: 20px; margin-bottom: 25px;'>
            <div class="status-badge badge-red">🚨 위험: {counts.get('🚨 위험', 0)}개</div>
            <div class="status-badge badge-yellow">🟡 관리: {counts.get('🟡 관리', 0)}개</div>
            <div class="status-badge badge-green">✅ 우수: {counts.get('✅ 우수', 0)}개</div>
        </div>
        <div style='background: rgba(255,255,255,0.1); padding: 20px; border-radius: 15px;'>
            <h4 style='color:#60a5fa; margin-top:0;'>⚠️ 즉시 조치 필요 키워드 (ROAS 200% 이하 & 5만원 이상)</h4>
            <p style='font-size:1.1rem; margin:0;'>{', '.join(danger_df['키워드'].unique()[:10]) if not danger_df.empty else '현재 조치 대상이 없습니다.'}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- Section 2: 핵심 KPI 메트릭 ---
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("💰 통합 광고 집행비", f"{f_df['광고비'].sum():,.0f}원")
    m2.metric("📈 통합 광고 매출", f"{f_df['총 전환매출액(14일)'].sum():,.0f}원")
    total_roas = (f_df['총 전환매출액(14일)'].sum() / f_df['광고비'].sum() * 100) if f_df['광고비'].sum() > 0 else 0
    m3.metric("🎯 평균 ROAS", f"{total_roas:.1f}%", delta=f"{total_roas-400:.1f}% vs 목표")
    m4.metric("🖱️ 평균 클릭률(CTR)", f"{(f_df['클릭수'].sum()/f_df['노출수'].sum()*100):.2f}%")

    # --- Section 3: 4분면 분석 그래프 (G마켓 산스 적용) ---
    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
    st.subheader("🎯 키워드 성과 4분면 분석 (소진액 vs 효율)")
    kw_agg = f_df.groupby('키워드').agg({'광고비':'sum', 'ROAS':'mean', '클릭수':'sum'}).reset_index()
    fig = px.scatter(kw_agg[kw_agg['광고비']>1000], x='광고비', y='ROAS', size='광고비', color='ROAS',
                     hover_name='키워드', color_continuous_scale='RdYlGn',
                     labels={'광고비':'총 광고비 소진액', 'ROAS':'수익률(ROAS %)'})
    fig.add_hline(y=400, line_dash="dash", line_color="#10b981", annotation_text="Target")
    fig.add_hline(y=200, line_dash="dash", line_color="#ef4444", annotation_text="Danger")
    fig.update_layout(template="plotly_white", height=550)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # --- Section 4: 실시간 성과 상세 리스트 ---
    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
    st.subheader("📋 고도화 성과 분석 리스트")
    st.dataframe(
        f_df[['날짜', '상태', '키워드', '광고비', '총 전환매출액(14일)', 'ROAS']].sort_values(by='광고비', ascending=False),
        use_container_width=True, height=450
    )
    st.markdown('</div>', unsafe_allow_html=True)

else:
    st.error("데이터 소스를 찾을 수 없습니다. 구글 시트 공유 설정과 GID를 확인해 주세요.")
