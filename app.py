import streamlit as st
import pandas as pd
import numpy as np

# 1. 고밀도 프로페셔널 레이아웃 설정
st.set_page_config(page_title="KidsTen Growth Cockpit", layout="wide")
st.markdown("""
    <style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    * { font-family: 'Pretendard', sans-serif !important; }
    .main { background-color: #f8fafc; }
    .stMetric { background-color: white; border: 1px solid #e2e8f0; padding: 15px; border-radius: 8px; }
    .section-title { font-size: 20px; font-weight: 800; color: #0f172a; border-left: 6px solid #2563eb; padding-left: 12px; margin: 30px 0 15px 0; }
    .strategy-box { background-color: #eff6ff; border: 1px solid #dbeafe; padding: 20px; border-radius: 10px; margin-bottom: 25px; }
    </style>
    """, unsafe_allow_html=True)

# 2. 데이터 통합 및 전략 지표 엔진 (InvalidIndexError 완전 해결)
URL_1 = "https://docs.google.com/spreadsheets/d/1R4qwQFQxXxL7NO67c8mr08KXMZvU9qkArNFoPFKYJDU/export?format=csv&gid=75240363"
URL_2 = "https://docs.google.com/spreadsheets/d/1R4qwQFQxXxL7NO67c8mr08KXMZvU9qkArNFoPFKYJDU/export?format=csv&gid=481757610"

@st.cache_data
def load_strategic_data():
    map_cols = {
        '캠페인 시작일': '날짜', '캠페인 이름': '캠페인명', 
        '광고비(원)': '광고비', '총 전환 매출액 (14일)(원)': '매출액',
        '총 주문수 (14일)': '주문수', '클릭수': '클릭수', '노출수': '노출수'
    }
    
    def fetch_and_clean(url):
        try:
            df = pd.read_csv(url)
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')].copy() # 유령 컬럼 삭제
            df = df.loc[:, ~df.columns.duplicated()].copy() # 중복 컬럼 삭제
            df = df.rename(columns=map_cols)
            df = df.loc[:, ~df.columns.duplicated()].copy() # 번역 후 중복 재삭제
            return df.reset_index(drop=True)
        except: return None

    d1, d2 = fetch_and_clean(URL_1), fetch_and_clean(URL_2)
    dfs = [d for d in [d1, d2] if d is not None]
    if not dfs: return None
    
    full_df = pd.concat(dfs, axis=0, ignore_index=True, sort=False).reset_index(drop=True)
    full_df['날짜'] = pd.to_datetime(full_df['날짜'], errors='coerce')
    
    # 지표 정제 및 계산
    for c in ['광고비', '매출액', '주문수', '클릭수', '노출수']:
        if c in full_df.columns:
            full_df[c] = pd.to_numeric(full_df[c].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
            
    full_df['ROAS'] = (full_df['매출액'] / full_df['광고비'] * 100).replace([np.inf, -np.inf], 0).fillna(0)
    full_df['CVR'] = (full_df['주문수'] / full_df['클릭수'] * 100).replace([np.inf, -np.inf], 0).fillna(0)
    
    return full_df

df = load_strategic_data()

if df is not None:
    # --- 상단 전략 리포트 ---
    st.markdown('<div class="section-title">🚀 1월 매출 성장 및 이익 방어 전략 리포트</div>', unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="strategy-box">', unsafe_allow_html=True)
        st.write(f"**분석 리더: 장준영 팀장** | **데이터 범위:** {df['날짜'].min().strftime('%Y-%m-%d')} ~ {df['날짜'].max().strftime('%Y-%m-%d')}")
        st.write("""
        - **12월 총평:** 연말 광고비 경쟁 심화로 평균 CPC가 상승 추세임. 전환율(CVR)이 낮은 키워드의 예산 낭비가 심각함.
        - **1월 액션:** ROAS 250% 미만 키워드 15% 감액, CVR 5% 이상 우수 캠페인 20% 증액으로 '이익 중심' 운용 권장.
        """)
        st.markdown('</div>', unsafe_allow_html=True)

    # 1. 이상 징후 알림 (Anomaly Detection)
    st.markdown('<div class="section-header">🚨 주간 성과 이상 징후 (최근 7일 vs 이전 7일)</div>', unsafe_allow_html=True)
    max_d = df['날짜'].max()
    curr_week = df[df['날짜'] > max_d - pd.Timedelta(days=7)]
    prev_week = df[(df['날짜'] <= max_d - pd.Timedelta(days=7)) & (df['날짜'] > max_d - pd.Timedelta(days=14))]
    
    l_sum = curr_week.groupby('키워드').agg({'ROAS':'mean', '광고비':'sum'}).reset_index()
    p_sum = prev_week.groupby('키워드').agg({'ROAS':'mean'}).reset_index()
    
    compare = pd.merge(l_sum, p_sum, on='키워드', suffixes=('_이번주', '_지난주'))
    compare['변화율'] = (compare['ROAS_이번주'] - compare['ROAS_지난주'])
    
    critical = compare[(compare['변화율'] < -50) & (compare['광고비'] > 30000)].sort_values('변화율')
    st.write("지난주 대비 성과가 급락한 요주의 키워드입니다. (즉시 조치 필요)")
    st.dataframe(critical, use_container_width=True)

    # 2. 키워드별 구매 전환율(CVR) 상세 비교
    st.markdown('<div class="section-header">🔍 키워드 전환 품질(CVR) 심층 분석</div>', unsafe_allow_html=True)
    kw_agg = df.groupby('키워드').agg({'클릭수':'sum', '주문수':'sum', 'CVR':'mean', 'ROAS':'mean', '광고비':'sum'}).reset_index()
    
    col1, col2 = st.columns(2)
    with col1:
        st.error("🚫 광고비 도둑 (클릭은 많으나 CVR 1% 미만)")
        st.dataframe(kw_agg[(kw_agg['CVR'] < 1) & (kw_agg['클릭수'] > 100)].sort_values('광고비', ascending=False).head(20), use_container_width=True)
    with col2:
        st.success("✨ 효자 키워드 (CVR 5% 이상 고효율)")
        st.dataframe(kw_agg[kw_agg['CVR'] > 5].sort_values('주문수', ascending=False).head(20), use_container_width=True)

    # 3. 1월 캠페인별 예산 조정 가이드
    st.markdown('<div class="section-header">📋 캠페인별 1월 운용 의사결정 시트</div>', unsafe_allow_html=True)
    camp_agg = df.groupby('캠페인명').agg({'광고비':'sum', '매출액':'sum', 'ROAS':'mean', 'CVR':'mean'}).reset_index()
    
    def set_strategy(row):
        if row['ROAS'] >= 400 and row['CVR'] >= 3: return "🚀 공격적 증액 (Scale-up)"
        elif row['ROAS'] < 200: return "⛔ 즉시 감액 (Profit-Cut)"
        else: return "⚖️ 효율 유지 (Optimization)"
        
    camp_agg['1월 권장 전략'] = camp_agg.apply(set_strategy, axis=1)
    st.dataframe(camp_agg.sort_values('광고비', ascending=False), use_container_width=True)

else:
    st.error("데이터 로딩 실패. 시트 공유 설정과 GID를 확인해 주세요.")
