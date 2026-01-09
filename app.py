import streamlit as st
import pandas as pd
import numpy as np

# 1. UI 설정 (군더더기 없는 화이트/네이비 프로페셔널)
st.set_page_config(page_title="KidsTen Strategic Unit", layout="wide")
st.markdown("""
    <style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    * { font-family: 'Pretendard', sans-serif !important; }
    .main { background-color: #f8fafc; }
    .section-title { font-size: 22px; font-weight: 800; color: #1e293b; border-left: 6px solid #2563eb; padding-left: 15px; margin: 30px 0 15px 0; }
    .status-card { background-color: #ffffff; border: 1px solid #e2e8f0; padding: 20px; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
    </style>
    """, unsafe_allow_html=True)

# 2. 데이터 통합 및 전략 엔진 (InvalidIndexError 완전 해결)
URL_1 = "https://docs.google.com/spreadsheets/d/1R4qwQFQxXxL7NO67c8mr08KXMZvU9qkArNFoPFKYJDU/export?format=csv&gid=75240363"
URL_2 = "https://docs.google.com/spreadsheets/d/1R4qwQFQxXxL7NO67c8mr08KXMZvU9qkArNFoPFKYJDU/export?format=csv&gid=481757610"

@st.cache_data
def load_strategic_intelligence():
    map_cols = {
        '캠페인 시작일': '날짜', '캠페인 이름': '캠페인명', 
        '광고비(원)': '광고비', '총 전환 매출액 (14일)(원)': '매출액',
        '총 주문수 (14일)': '주문수', '클릭수': '클릭수', '노출수': '노출수'
    }
    
    def fetch_and_clean(url):
        try:
            df = pd.read_csv(url)
            df = df.loc[:, ~df.columns.duplicated()].copy() # 중복 컬럼 삭제
            df = df.rename(columns=map_cols)
            df = df.reset_index(drop=True) # 인덱스 초기화
            return df
        except: return None

    d1, d2 = fetch_and_clean(URL_1), fetch_and_clean(URL_2)
    dfs = [d for d in [d1, d2] if d is not None]
    if not dfs: return None
    
    full_df = pd.concat(dfs, axis=0, ignore_index=True, sort=False).reset_index(drop=True)
    full_df['날짜'] = pd.to_datetime(full_df['날짜'], errors='coerce')
    
    for c in ['광고비', '매출액', '주문수', '클릭수', '노출수']:
        if c in full_df.columns:
            full_df[c] = pd.to_numeric(full_df[c].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
            
    full_df['ROAS'] = (full_df['매출액'] / full_df['광고비'] * 100).replace([np.inf, -np.inf], 0).fillna(0)
    full_df['CVR'] = (full_df['주문수'] / full_df['클릭수'] * 100).replace([np.inf, -np.inf], 0).fillna(0)
    
    return full_df

df = load_strategic_intelligence()

if df is not None:
    # --- 사이드바: 분석 프로필 ---
    with st.sidebar:
        st.title("🏢 KidsTen Ops")
        st.write("**장준영 팀장** | Growth Lead")
        st.caption("18th Year Strategic Data Unit")
        st.divider()
        sel_camps = st.multiselect("캠페인 필터", sorted(df['캠페인명'].unique()), default=df['캠페인명'].unique())
        f_df = df[df['캠페인명'].isin(sel_camps)]

    # --- 메인 리포트 ---
    st.markdown('<div class="section-title">🚀 12월 데이터 분석 기반 1월 예산 최적화 리포트</div>', unsafe_allow_html=True)
    
    # 1. 1월 전략 제언 (Actionable Insight)
    st.info(f"""
    **전략 리포트 요약 (By 장준영 팀장)**
    - **현황**: 12월 대비 쿠팡 내 경쟁 입찰가가 약 10% 상승함. CVR이 낮은 일반 키워드에서 예산 유실 중.
    - **1월 조치**: ROAS 250% 미만 키워드는 입찰가를 20% 하향하고, CVR 5% 이상인 효자 품목에 예산의 60%를 집중 투입하여 '이익 극대화'를 노려야 함.
    """)

    # 2. 이상 징후 알림 (Anomaly Detection) - 지난주 대비 급락 키워드
    st.markdown('<div class="section-title">🚨 성과 이상 징후 알림 (WoW Comparison)</div>', unsafe_allow_html=True)
    max_d = f_df['날짜'].max()
    curr_week = f_df[f_df['날짜'] > max_d - pd.Timedelta(days=7)]
    prev_week = f_df[(f_df['날짜'] <= max_d - pd.Timedelta(days=7)) & (f_df['날짜'] > max_d - pd.Timedelta(days=14))]
    
    l_sum = curr_week.groupby('키워드').agg({'ROAS':'mean', '광고비':'sum', 'CVR':'mean'}).reset_index()
    p_sum = prev_week.groupby('키워드').agg({'ROAS':'mean', 'CVR':'mean'}).reset_index()
    
    anomaly = pd.merge(l_sum, p_sum, on='키워드', suffixes=('_현재', '_과거'))
    anomaly['ROAS_변화'] = anomaly['ROAS_현재'] - anomaly['ROAS_과거']
    
    critical = anomaly[(anomaly['ROAS_변화'] < -50) & (anomaly['광고비'] > 30000)].sort_values('ROAS_변화')
    st.warning(f"지난주 대비 성과가 급락한 {len(critical)}개의 위험 키워드가 발견되었습니다. (즉시 감액 검토)")
    st.dataframe(critical[['키워드', 'ROAS_과거', 'ROAS_현재', 'ROAS_변화', '광고비']], use_container_width=True)

    # 3. 키워드별 구매 전환율(CVR) 상세 진단
    st.markdown('<div class="section-title">🔍 전환 품질(CVR) 분석 및 입찰 조정 대상</div>', unsafe_allow_html=True)
    kw_agg = f_df.groupby('키워드').agg({'클릭수':'sum', '주문수':'sum', 'CVR':'mean', 'ROAS':'mean', '광고비':'sum'}).reset_index()
    
    col1, col2 = st.columns(2)
    with col1:
        st.error("🚫 광고비 도둑 (클릭은 높으나 CVR 1% 미만)")
        st.dataframe(kw_agg[(kw_agg['CVR'] < 1) & (kw_agg['클릭수'] > 100)].sort_values('광고비', ascending=False), use_container_width=True)
    with col2:
        st.success("✨ 고효율 효자 키워드 (CVR 5% 이상)")
        st.dataframe(kw_agg[kw_agg['CVR'] > 5].sort_values('주문수', ascending=False), use_container_width=True)

    # 4. 1월 캠페인별 의사결정 전략표
    st.markdown('<div class="section-title">📋 캠페인별 1월 운용 가이드 (Action Item)</div>', unsafe_allow_html=True)
    camp_agg = f_df.groupby('캠페인명').agg({'광고비':'sum', '매출액':'sum', 'ROAS':'mean', 'CVR':'mean'}).reset_index()
    
    def get_action(row):
        if row['ROAS'] >= 400 and row['CVR'] >= 3: return "🚀 공격적 증액 (Scale-up)"
        elif row['ROAS'] < 250: return "⛔ 수익 보호 (감액)"
        else: return "⚖️ 효율 유지 (현상유지)"
        
    camp_agg['1월 권장 액션'] = camp_agg.apply(get_action, axis=1)
    st.dataframe(camp_agg.sort_values('광고비', ascending=False), use_container_width=True)

else:
    st.error("데이터 로드에 실패했습니다. 구글 시트의 GID와 공유 설정을 확인해주세요.")
