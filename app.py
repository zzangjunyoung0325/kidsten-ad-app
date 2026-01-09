import streamlit as st
import pandas as pd
import numpy as np

# 1. 고밀도 프로페셔널 레이아웃 (Netlify 스타일 이식)
st.set_page_config(page_title="KidsTen Strategic Intelligence", layout="wide")

st.markdown("""
    <style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    * { font-family: 'Pretendard', sans-serif !important; }
    .main { background-color: #f8fafc; }
    .section-header { font-size: 20px; font-weight: 800; color: #0f172a; border-left: 6px solid #2563eb; padding-left: 12px; margin: 30px 0 15px 0; }
    .alert-box { background-color: #fef2f2; border: 1px solid #fee2e2; padding: 20px; border-radius: 10px; color: #991b1b; }
    .stDataFrame { border: 1px solid #e2e8f0; border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

# 2. 통합 데이터 분석 엔진 (InvalidIndexError 완전 해결)
URL_1 = "https://docs.google.com/spreadsheets/d/1R4qwQFQxXxL7NO67c8mr08KXMZvU9qkArNFoPFKYJDU/export?format=csv&gid=75240363"
URL_2 = "https://docs.google.com/spreadsheets/d/1R4qwQFQxXxL7NO67c8mr08KXMZvU9qkArNFoPFKYJDU/export?format=csv&gid=481757610"

@st.cache_data
def load_and_analyze_intelligence():
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
            # 번역 후 이름이 겹치면(예: 비용/광고비 동시 존재) 첫 번째만 남김
            df = df.loc[:, ~df.columns.duplicated()].copy()
            return df.reset_index(drop=True)
        except: return None

    d1, d2 = fetch_and_clean(URL_1), fetch_and_clean(URL_2)
    dfs = [d for d in [d1, d2] if d is not None]
    if not dfs: return None
    
    # 최종 병합 시 인덱스 무시 (Error Zero)
    full_df = pd.concat(dfs, axis=0, ignore_index=True, sort=False).reset_index(drop=True)
    full_df['날짜'] = pd.to_datetime(full_df['날짜'], errors='coerce')
    
    for c in ['광고비', '매출액', '주문수', '클릭수', '노출수']:
        if c in full_df.columns:
            full_df[c] = pd.to_numeric(full_df[c].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
            
    # 지표 계산
    full_df['ROAS'] = (full_df['매출액'] / full_df['광고비'] * 100).replace([np.inf, -np.inf], 0).fillna(0)
    full_df['CVR'] = (full_df['주문수'] / full_df['클릭수'] * 100).replace([np.inf, -np.inf], 0).fillna(0)
    
    return full_df

df = load_and_analyze_intelligence()

if df is not None:
    # --- 상단 전략 리포트 (분석가 총평) ---
    st.markdown("# 🛰️ Ad Strategic Intelligence Cockpit")
    st.info(f"""
    **12월 결산 기반 1월 운용 가이드 (장준영 팀장)**
    1. **이익 방어**: 12월 하순 CPC 급등이 감지됨. CVR 1.5% 미만 키워드들은 즉시 입찰가를 15% 하향하여 소진을 방어하십시오.
    2. **매출 성장**: CVR 5% 이상인 핵심 품목은 1월 설 기획전 수요에 대비해 예산을 20% 선제적으로 증액하십시오.
    """)

    # 1. WoW 성과 이상 징후 (급락 키워드)
    st.markdown('<div class="section-header">🚨 성과 이상 징후 알림 (지난 7일 vs 이전 7일)</div>', unsafe_allow_html=True)
    max_d = df['날짜'].max()
    curr_w = df[df['날짜'] > max_d - pd.Timedelta(days=7)]
    prev_w = df[(df['날짜'] <= max_d - pd.Timedelta(days=7)) & (df['날짜'] > max_d - pd.Timedelta(days=14))]
    
    l_sum = curr_w.groupby('키워드').agg({'ROAS':'mean', '광고비':'sum'}).reset_index()
    p_sum = prev_w.groupby('키워드').agg({'ROAS':'mean'}).reset_index()
    
    diff = pd.merge(l_sum, p_sum, on='키워드', suffixes=('_현재', '_과거'))
    diff['ROAS_변화'] = diff['ROAS_현재'] - diff['ROAS_과거']
    
    alerts = diff[(diff['ROAS_변화'] < -50) & (diff['광고비'] > 30000)].sort_values('ROAS_변화')
    if not alerts.empty:
        st.error(f"⚠️ 지난주 대비 효율이 급락한 {len(alerts)}개 핵심 키워드를 발견했습니다. (입찰가 하향 검토)")
        st.dataframe(alerts, use_container_width=True)
    else:
        st.success("안전: 급격한 효율 하락을 보이는 키워드가 없습니다.")

    # 2. CVR 기반 전환 품질 심층 진단
    st.markdown('<div class="section-header">🔍 키워드 전환 품질(CVR) 분석 Matrix</div>', unsafe_allow_html=True)
    kw_agg = df.groupby('키워드').agg({'클릭수':'sum', '주문수':'sum', 'CVR':'mean', 'ROAS':'mean', '광고비':'sum'}).reset_index()
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### 🚫 광고비 유실 대상 (CVR 1.5% 미만)")
        st.dataframe(kw_agg[(kw_agg['CVR'] < 1.5) & (kw_agg['클릭수'] > 100)].sort_values('광고비', ascending=False).head(20), use_container_width=True)
    with c2:
        st.markdown("#### ✨ 증액 권장 대상 (CVR 5% 이상)")
        st.dataframe(kw_agg[kw_agg['CVR'] > 5].sort_values('주문수', ascending=False).head(20), use_container_width=True)

    # 3. 1월 캠페인별 의사결정 시트
    st.markdown('<div class="section-header">📋 캠페인별 1월 운용 전략 제언 (Action Plan)</div>', unsafe_allow_html=True)
    camp_agg = df.groupby('캠페인명').agg({'광고비':'sum', '매출액':'sum', 'ROAS':'mean', 'CVR':'mean'}).reset_index()
    
    def suggest(row):
        if row['ROAS'] >= 400 and row['CVR'] >= 3: return "🚀 공격적 증액 (Scale-up)"
        elif row['ROAS'] < 250: return "⛔ 수익 보호 (감액)"
        else: return "⚖️ 효율 유지 (현상유지)"
        
    camp_agg['1월 권장 액션'] = camp_agg.apply(suggest, axis=1)
    st.dataframe(camp_agg.sort_values('광고비', ascending=False), use_container_width=True)

else:
    st.error("데이터 로딩 실패. 시트 공유 설정과 GID를 다시 확인해 주세요.")
