import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. 전문 SaaS 디자인 설정 (폰트 및 레이아웃)
st.set_page_config(page_title="KidsTen Growth Intelligence v4", layout="wide")

st.markdown("""
    <style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    * { font-family: 'Pretendard', sans-serif; }
    .main { background-color: #f8fafc; }
    
    /* 카드형 UI */
    .st-emotion-cache-12w0qpk { background-color: white; padding: 25px; border-radius: 15px; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1); border: 1px solid #e2e8f0; }
    
    /* 상단 전략 섹션 */
    .strategy-box {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: white;
        padding: 30px;
        border-radius: 20px;
        margin-bottom: 30px;
        border-left: 8px solid #3b82f6;
    }
    .badge { padding: 4px 8px; border-radius: 6px; font-size: 0.75rem; font-weight: 600; margin-right: 5px; }
    .badge-red { background-color: #fee2e2; color: #b91c1c; }
    .badge-green { background-color: #dcfce7; color: #15803d; }
    </style>
    """, unsafe_allow_html=True)

# 2. 데이터 연동 (팀장님 전용 주소)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1R4qwQFQxXxL7NO67c8mr08KXMZvU9qkArNFoPFKYJDU/export?format=csv"

@st.cache_data
def load_data():
    try:
        df = pd.read_csv(SHEET_URL)
        df['날짜'] = pd.to_datetime(df['날짜'], format='%Y%m%d')
        # 숫자형 변환
        for col in ['광고비', '총 전환매출액(14일)', '클릭수', '노출수']:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        df['ROAS'] = (df['총 전환매출액(14일)'] / df['광고비'] * 100).fillna(0).replace([float('inf')], 0)
        df['CTR'] = (df['클릭수'] / df['노출수'] * 100).fillna(0)
        return df
    except: return None

df = load_data()

if df is not None:
    # --- 사이드바 및 필터 ---
    st.sidebar.markdown("### 🔍 Analysis Scope")
    campaign_list = df['캠페인명'].unique().tolist()
    sel_campaigns = st.sidebar.multiselect("캠페인 필터", campaign_list, default=campaign_list)
    f_df = df[df['캠페인명'].isin(sel_campaigns)]

    # --- Section 1: 전략 리포트 (핵심 분석 결과) ---
    st.markdown(f"""
    <div class="strategy-box">
        <h2 style='margin-top:0; color:white;'>🚀 KidsTen Ad Strategy Report</h2>
        <div style='display: flex; gap: 40px;'>
            <div style='flex: 1;'>
                <h4 style='color:#60a5fa;'>✅ 핵심 성과 인사이트</h4>
                <p style='font-size:0.95rem; opacity:0.9;'>
                    현재 선택된 기간의 평균 ROAS는 <b>{f_df['총 전환매출액(14일)'].sum()/f_df['광고비'].sum()*100:.1f}%</b>입니다.<br>
                    매출 1위 키워드는 <b>'{f_df.groupby('키워드')['총 전환매출액(14일)'].sum().idxmax()}'</b>이며 전체 매출의 핵심 기여를 하고 있습니다.
                </p>
            </div>
            <div style='flex: 1; border-left: 1px solid rgba(255,255,255,0.1); padding-left: 40px;'>
                <h4 style='color:#f87171;'>⚠️ 즉시 관리 필요</h4>
                <p style='font-size:0.95rem; opacity:0.9;'>
                    ROAS 200% 미만이면서 광고비 5만원 이상 소진된 키워드가 <b>{len(f_df[(f_df['ROAS']<200) & (f_df['광고비']>50000)])}개</b> 발견되었습니다.<br>
                    해당 키워드들에 대한 입찰가 하향 및 제외 처리를 권장합니다.
                </p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- Section 2: 메인 KPI 대시보드 ---
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("💰 총 집행 광고비", f"{f_df['광고비'].sum():,.0f}원")
    col2.metric("📈 총 광고 매출액", f"{f_df['총 전환매출액(14일)'].sum():,.0f}원")
    total_roas = (f_df['총 전환매출액(14일)'].sum() / f_df['광고비'].sum() * 100)
    col3.metric("🎯 평균 ROAS", f"{total_roas:.1f}%", delta=f"{total_roas-400:.1f}% vs 목표")
    col4.metric("🖱️ 평균 클릭률(CTR)", f"{(f_df['클릭수'].sum()/f_df['노출수'].sum()*100):.2f}%")

    st.markdown("<br>", unsafe_allow_html=True)

    # --- Section 3: 키워드 포트폴리오 분석 (소진액 vs 효율) ---
    st.subheader("📊 키워드 포트폴리오 분석 (Portfolio Analysis)")
    
    kw_agg = f_df.groupby('키워드').agg({'광고비':'sum', 'ROAS':'mean', '클릭수':'sum'}).reset_index()
    # 버블 차트 구현
    fig_scatter = px.scatter(kw_agg[kw_agg['광고비'] > 1000], x='광고비', y='ROAS', size='클릭수', color='ROAS',
                             hover_name='키워드', color_continuous_scale='RdYlGn',
                             title="광고비 소진액 대비 성과 분포 (Target: 400%)",
                             labels={'광고비':'총 광고비', 'ROAS':'수익률(ROAS %)'})
    fig_scatter.add_hline(y=400, line_dash="dash", line_color="red", annotation_text="Target Line")
    fig_scatter.update_layout(template="plotly_white", height=500)
    st.plotly_chart(fig_scatter, use_container_width=True)

    # --- Section 4: 실시간 퍼포먼스 데이터베이스 (분석형 리스트) ---
    st.subheader("📋 고도화 성과 분석 리스트 (Action-Oriented List)")
    
    # 성과 구분을 위한 파생 변수 생성
    def classify_status(row):
        if row['ROAS'] >= 400: return "✅ 우수"
        elif row['ROAS'] >= 200: return "🟡 관리"
        else: return "🚨 위험"
    
    f_df['상태'] = f_df.apply(classify_status, axis=1)
    
    # 분석된 내용을 포함한 테이블
    display_df = f_df[['날짜', '상태', '키워드', '노출수', '클릭수', '광고비', '총 전환매출액(14일)', 'ROAS']].sort_values(by='광고비', ascending=False)
    
    st.dataframe(display_df, use_container_width=True, height=500, column_config={
        "ROAS": st.column_config.NumberColumn("ROAS (%)", format="%.1f%%"),
        "광고비": st.column_config.NumberColumn("소진액", format="%d원"),
        "총 전환매출액(14일)": st.column_config.NumberColumn("매출액", format="%d원")
    })

else:
    st.error("데이터 연결을 확인해주세요.")
