import streamlit as st
import pandas as pd
import plotly.express as px

# 1. UI 설정
st.set_page_config(page_title="KidsTen Growth Intelligence", layout="wide")
st.markdown("<style>.main { background-color: #f8fafc; } .stMetric { background-color: white; border: 1px solid #e2e8f0; padding: 15px; border-radius: 10px; }</style>", unsafe_allow_html=True)

# 2. 데이터 통합 (강력한 에러 방지 로직 유지)
URL_1 = "https://docs.google.com/spreadsheets/d/1R4qwQFQxXxL7NO67c8mr08KXMZvU9qkArNFoPFKYJDU/export?format=csv&gid=75240363"
URL_2 = "https://docs.google.com/spreadsheets/d/1R4qwQFQxXxL7NO67c8mr08KXMZvU9qkArNFoPFKYJDU/export?format=csv&gid=481757610"

@st.cache_data
def load_strategic_data():
    map_cols = {'캠페인 시작일': '날짜', '캠페인 이름': '캠페인명', '광고비(원)': '광고비', '총 전환 매출액 (14일)(원)': '총 전환매출액(14일)'}
    dfs = []
    for url in [URL_1, URL_2]:
        try:
            temp = pd.read_csv(url).loc[:, ~pd.read_csv(url).columns.duplicated()].rename(columns=map_cols)
            dfs.append(temp)
        except: continue
    
    full_df = pd.concat(dfs, ignore_index=True).reset_index(drop=True)
    full_df['날짜'] = pd.to_datetime(full_df['날짜'], errors='coerce')
    for c in ['광고비', '총 전환매출액(14일)', '클릭수', '노출수']:
        if c in full_df.columns:
            full_df[c] = pd.to_numeric(full_df[c].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
    
    full_df['ROAS'] = (full_df['총 전환매출액(14일)'] / full_df['광고비'] * 100).fillna(0).replace(float('inf'), 0)
    return full_df

df = load_strategic_data()

if df is not None:
    # --- 사이드바 필터 ---
    st.sidebar.title("🏢 KidsTen Ops")
    sel_camps = st.sidebar.multiselect("캠페인 필터", sorted(df['캠페인명'].unique()), default=df['캠페인명'].unique())
    f_df = df[df['캠페인명'].isin(sel_camps)]

    # --- [본론] Section 1: 전략적 판단 브리핑 (Action Items) ---
    st.title("🛡️ Growth Strategy Cockpit")
    
    # 전략적 추출
    money_pits = f_df[(f_df['ROAS'] < 200) & (f_df['광고비'] > f_df['광고비'].mean())].sort_values('광고비', ascending=False)
    hidden_gems = f_df[(f_df['ROAS'] > 500) & (f_df['광고비'] < f_df['광고비'].mean())].sort_values('ROAS', ascending=False)

    st.info(f"💡 **오늘의 전략 조치 사항**\n\n"
            f"1. **예산 낭비 경고:** 효율 200% 미만인 '{money_pits['키워드'].iloc[0] if not money_pits.empty else '없음'}' 외 {len(money_pits)}개 키워드 감액 검토 필요.\n"
            f"2. **증액 기회 포착:** ROAS 500% 이상인 '{hidden_gems['키워드'].iloc[0] if not hidden_gems.empty else '없음'}' 외 {len(hidden_gems)}개 키워드 증액 시 매출 확대 가능.")

    # KPI Metrics
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💰 누적 광고비", f"{f_df['광고비'].sum():,.0f}원")
    c2.metric("📈 누적 매출액", f"{f_df['총 전환매출액(14일)'].sum():,.0f}원")
    c3.metric("🎯 평균 ROAS", f"{(f_df['총 전환매출액(14일)'].sum()/f_df['광고비'].sum()*100):.1f}%")
    c4.metric("🖱️ 평균 CTR", f"{(f_df['클릭수'].sum()/f_df['노출수'].sum()*100):.2f}%")

    # --- [본론] Section 2: 판단을 위한 시각화 (4분면 분석) ---
    st.divider()
    st.subheader("📊 키워드 포트폴리오 진단 (소진액 vs 효율)")
    
    # 키워드별 집계
    kw_df = f_df.groupby('키워드').agg({'광고비':'sum', '총 전환매출액(14일)':'sum', 'ROAS':'mean'}).reset_index()
    
    fig = px.scatter(kw_df[kw_df['광고비'] > 10000], x='광고비', y='ROAS', 
                     size='총 전환매출액(14일)', color='ROAS', hover_name='키워드',
                     color_continuous_scale='RdYlGn', template='plotly_white')
    
    # 기준선 추가 (판단의 근거)
    fig.add_hline(y=400, line_dash="dash", line_color="green", annotation_text="목표 수익률(400%)")
    fig.add_hline(y=200, line_dash="dash", line_color="red", annotation_text="손익 분기점(200%)")
    st.plotly_chart(fig, use_container_width=True)

    # --- [본론] Section 3: 데이터 테이블 (판단 우선순위 정렬) ---
    st.subheader("📋 성과 하위(위험) 키워드 TOP 20")
    st.write("광고비 소진은 많으나 효율이 낮은 순서로 보여줍니다. (즉시 조치 대상)")
    st.dataframe(money_pits[['날짜', '키워드', '광고비', 'ROAS', '캠페인명']].head(20), use_container_width=True)

else:
    st.error("데이터를 불러올 수 없습니다. 시트 주소를 확인해주세요.")
