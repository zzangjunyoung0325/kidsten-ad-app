import streamlit as st
import pandas as pd
import numpy as np

# 1. 디자인: 아마추어 느낌을 지운 고밀도 프로페셔널 UI
st.set_page_config(page_title="KidsTen Growth Intelligence", layout="wide")
st.markdown("""
    <style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    * { font-family: 'Pretendard', sans-serif !important; }
    .main { background-color: #f8fafc; }
    .report-card { background: white; padding: 20px; border-radius: 12px; border: 1px solid #e2e8f0; margin-bottom: 20px; }
    .stDataFrame { border: 1px solid #e2e8f0; border-radius: 8px; }
    .header-text { font-size: 24px; font-weight: 800; color: #0f172a; border-left: 6px solid #2563eb; padding-left: 15px; margin-bottom: 25px; }
    </style>
    """, unsafe_allow_html=True)

# 2. 데이터 통합 (중복 컬럼 및 인덱스 에러 원천 차단)
URL_1 = "https://docs.google.com/spreadsheets/d/1R4qwQFQxXxL7NO67c8mr08KXMZvU9qkArNFoPFKYJDU/export?format=csv&gid=75240363"
URL_2 = "https://docs.google.com/spreadsheets/d/1R4qwQFQxXxL7NO67c8mr08KXMZvU9qkArNFoPFKYJDU/export?format=csv&gid=481757610"

@st.cache_data
def load_and_analyze_intelligence():
    map_cols = {
        '캠페인 시작일': '날짜', '캠페인 이름': '캠페인명', 
        '광고비(원)': '광고비', '총 전환 매출액 (14일)(원)': '매출액',
        '총 주문수 (14일)': '주문수', '클릭수': '클릭수', '노출수': '노출수'
    }
    
    def fetch_strictly(url):
        try:
            df = pd.read_csv(url)
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')].copy()
            df = df.loc[:, ~df.columns.duplicated()].copy()
            df = df.rename(columns=map_cols)
            df = df.loc[:, ~df.columns.duplicated()].copy()
            return df.reset_index(drop=True)
        except: return None

    d1, d2 = fetch_strictly(URL_1), fetch_strictly(URL_2)
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

df = load_and_analyze_intelligence()

if df is not None:
    # --- 사이드바 ---
    with st.sidebar:
        st.title("🏢 KidsTen Ops")
        st.write(f"**장준영 팀장**")
        st.caption("Growth Strategy Lead | 18th Year")
        st.divider()
        sel_camps = st.multiselect("캠페인 필터", sorted(df['캠페인명'].unique()), default=df['캠페인명'].unique())
        f_df = df[df['캠페인명'].isin(sel_camps)]

    # --- 메인 리포트 (본론) ---
    st.markdown('<div class="header-text">🛰️ Ad Strategic Intelligence Cockpit (Jan 2026)</div>', unsafe_allow_html=True)
    
    # 1. 광고 분석가 전략 제언 (Executive Commentary)
    st.info(f"""
    **[전략 브리핑] 12월 데이터 분석 결과 및 1월 예산 가이드**
    1. **이익 방어**: 12월 하순 CPC 상승이 두드러집니다. CVR 1.5% 미만인 키워드들은 즉시 입찰가를 15% 하향하여 소진을 막으십시오.
    2. **공격적 증액**: CVR 5% 이상인 핵심 품목은 1월 설 기획전 수요를 대비해 예산을 20% 선제적으로 증액하십시오.
    """)

    # 2. 이상 징후 알림 (WoW Comparison)
    st.subheader("🚨 지난 7일 vs 그 전 7일 성과 급락 키워드")
    max_d = f_df['날짜'].max()
    curr_w = f_df[f_df['날짜'] > max_d - pd.Timedelta(days=7)]
    prev_w = f_df[(f_df['날짜'] <= max_d - pd.Timedelta(days=7)) & (f_df['날짜'] > max_d - pd.Timedelta(days=14))]
    
    l_sum = curr_w.groupby('키워드').agg({'ROAS':'mean', '광고비':'sum'}).reset_index()
    p_sum = prev_w.groupby('키워드').agg({'ROAS':'mean'}).reset_index()
    
    diff = pd.merge(l_sum, p_sum, on='키워드', suffixes=('_현재', '_과거'))
    diff['ROAS_변화'] = diff['ROAS_현재'] - diff['ROAS_과거']
    
    alerts = diff[(diff['ROAS_변화'] < -50) & (diff['광고비'] > 30000)].sort_values('ROAS_변화')
    if not alerts.empty:
        st.error(f"⚠️ 성과 급락 감지: {len(alerts)}개 키워드가 관리 범위를 벗어났습니다. (입찰가 하향 검토)")
        st.dataframe(alerts, use_container_width=True)
    else:
        st.success("안전: 급격한 효율 하락을 보이는 핵심 키워드가 없습니다.")

    # 3. 키워드별 전환 품질(CVR) 상세 분석
    st.markdown("---")
    st.subheader("🔍 키워드별 구매 전환율(CVR) 분석 Matrix")
    kw_agg = f_df.groupby('키워드').agg({'클릭수':'sum', '주문수':'sum', 'CVR':'mean', 'ROAS':'mean', '광고비':'sum'}).reset_index()
    
    c1, c2 = st.columns(2)
    with c1:
        st.error("🚫 예산 유실 키워드 (클릭은 높으나 CVR 1% 미만)")
        st.dataframe(kw_agg[(kw_agg['CVR'] < 1) & (kw_agg['클릭수'] > 100)].sort_values('광고비', ascending=False).head(20), use_container_width=True)
    with c2:
        st.success("✨ 효자 키워드 (CVR 5% 이상 고전환)")
        st.dataframe(kw_agg[kw_agg['CVR'] > 5].sort_values('주문수', ascending=False).head(20), use_container_width=True)

    # 4. 캠페인별 1월 의사결정 시트
    st.markdown("---")
    st.subheader("📋 캠페인별 1월 운용 전략 제언 (Action Plan)")
    camp_agg = f_df.groupby('캠페인명').agg({'광고비':'sum', '매출액':'sum', 'ROAS':'mean', 'CVR':'mean'}).reset_index()
    
    def suggest(row):
        if row['ROAS'] >= 400 and row['CVR'] >= 3: return "🚀 공격적 증액 (Scale-up)"
        elif row['ROAS'] < 250: return "⛔ 수익 보호 (감액)"
        else: return "⚖️ 효율 유지 (Optimization)"
        
    camp_agg['1월 권장 액션'] = camp_agg.apply(suggest, axis=1)
    st.dataframe(camp_agg.sort_values('광고비', ascending=False), use_container_width=True)

else:
    st.error("데이터 로드 중입니다. 구글 시트 공유 설정과 GID를 다시 확인해 주세요.")
