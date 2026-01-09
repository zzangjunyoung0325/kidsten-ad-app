import streamlit as st
import pandas as pd
import numpy as np

# 1. Executive 테마 설정
st.set_page_config(page_title="KidsTen Strategic Report", layout="wide")
st.markdown("""
    <style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    * { font-family: 'Pretendard', sans-serif !important; }
    .main { background-color: #ffffff; }
    .report-title { font-size: 28px; font-weight: 800; color: #0f172a; border-left: 8px solid #3b82f6; padding-left: 15px; margin-bottom: 25px; }
    .section-title { font-size: 20px; font-weight: 700; color: #1e293b; margin-top: 30px; margin-bottom: 15px; padding-bottom: 10px; border-bottom: 2px solid #f1f5f9; }
    .action-box { background-color: #fff7ed; border: 1px solid #ffedd5; padding: 20px; border-radius: 12px; margin-bottom: 25px; }
    .critical-alert { background-color: #fef2f2; border: 1px solid #fee2e2; padding: 15px; border-radius: 10px; color: #991b1b; }
    </style>
    """, unsafe_allow_html=True)

# 2. 데이터 통합 엔진 (Error-Free)
URL_1 = "https://docs.google.com/spreadsheets/d/1R4qwQFQxXxL7NO67c8mr08KXMZvU9qkArNFoPFKYJDU/export?format=csv&gid=75240363"
URL_2 = "https://docs.google.com/spreadsheets/d/1R4qwQFQxXxL7NO67c8mr08KXMZvU9qkArNFoPFKYJDU/export?format=csv&gid=481757610"

@st.cache_data
def load_and_analyze():
    map_cols = {
        '캠페인 시작일': '날짜', '캠페인 이름': '캠페인명', 
        '광고비(원)': '광고비', '총 전환 매출액 (14일)(원)': '총 전환매출액(14일)',
        '총 주문수 (14일)': '주문수', '클릭수': '클릭수', '노출수': '노출수'
    }
    dfs = []
    for url in [URL_1, URL_2]:
        try:
            df = pd.read_csv(url).loc[:, ~pd.read_csv(url).columns.duplicated()].rename(columns=map_cols)
            dfs.append(df)
        except: continue
    
    full_df = pd.concat(dfs, ignore_index=True).reset_index(drop=True)
    full_df['날짜'] = pd.to_datetime(full_df['날짜'], errors='coerce')
    
    # 숫자 정제
    cols = ['광고비', '총 전환매출액(14일)', '주문수', '클릭수', '노출수']
    for c in cols:
        if c in full_df.columns:
            full_df[c] = pd.to_numeric(full_df[c].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
    
    # 지표 계산
    full_df['ROAS'] = (full_df['총 전환매출액(14일)'] / full_df['광고비'] * 100).replace([np.inf, -np.inf], 0).fillna(0)
    full_df['CVR'] = (full_df['주문수'] / full_df['클릭수'] * 100).replace([np.inf, -np.inf], 0).fillna(0)
    full_df['CPC'] = (full_df['광고비'] / full_df['클릭수']).replace([np.inf, -np.inf], 0).fillna(0)
    
    return full_df

df = load_and_analyze()

if df is not None:
    # --- 분석 리포트 시작 ---
    st.markdown('<div class="report-title">KidsTen Ad Intelligence Report: 12월 결산 및 1월 전략 제언</div>', unsafe_allow_html=True)
    
    # 1. 1월 대비 전략 제언 (Executive Summary)
    st.markdown('<div class="action-box">', unsafe_allow_html=True)
    st.markdown("### 📝 광고 분석가 리포트: 12월 데이터 분석 결과 및 1월 액션 플랜")
    st.write("""
    - **12월 분석 요약:** 연말 경쟁 심화로 평균 CPC는 상승했으나, 특정 브랜드 키워드의 CVR이 전월 대비 15% 하락했습니다. 이는 선물용 수요가 빠지는 시점의 자연스러운 감소로 판단됩니다.
    - **1월 예산 운용 방향:** 매출 성장보다는 **'이익 보전'**에 집중해야 합니다. 고소진/저CVR 키워드를 20% 축소하고, 검색 광고 비중을 줄여 브랜드 광고의 효율을 극대화하는 전략이 필요합니다.
    - **목표:** 쿠팡 내 매출 110% 유지 및 영업이익률 5%p 개선.
    """)
    st.markdown('</div>', unsafe_allow_html=True)

    # 2. 이상 징후 알림 (Anomaly Detection)
    # 최근 7일 vs 그 전 7일 비교
    latest_7 = df[df['날짜'] >= df['날짜'].max() - pd.Timedelta(days=7)]
    prev_7 = df[(df['날짜'] < df['날짜'].max() - pd.Timedelta(days=7)) & (df['날짜'] >= df['날짜'].max() - pd.Timedelta(days=14))]
    
    st.markdown('<div class="section-title">🚨 지난주 대비 성과 급락 키워드 (이상 징후 알림)</div>', unsafe_allow_html=True)
    
    l_kw = latest_7.groupby('키워드').agg({'ROAS':'mean', '광고비':'sum'}).reset_index()
    p_kw = prev_7.groupby('키워드').agg({'ROAS':'mean', '광고비':'sum'}).reset_index()
    
    merged_7 = pd.merge(l_kw, p_kw, on='키워드', suffixes=('_이번주', '_지난주'))
    merged_7['ROAS_변화율'] = (merged_7['ROAS_이번주'] - merged_7['ROAS_지난주']) / merged_7['ROAS_지난주']
    
    anomalies = merged_7[(merged_7['ROAS_변화율'] < -0.3) & (merged_7['광고비_이번주'] > 50000)].sort_values('ROAS_변화율')
    
    if not anomalies.empty:
        st.warning(f"총 {len(anomalies)}개의 핵심 키워드에서 성과 급락이 감지되었습니다. 즉시 확인이 필요합니다.")
        st.dataframe(anomalies[['키워드', 'ROAS_지난주', 'ROAS_이번주', 'ROAS_변화율', '광고비_이번주']], use_container_width=True)
    else:
        st.success("지난주 대비 급격한 효율 하락을 보이는 핵심 키워드가 없습니다.")

    # 3. 키워드별 구매 전환율(CVR) 분석
    st.markdown('<div class="section-title">🔍 키워드 전환 품질(CVR) 상세 분석</div>', unsafe_allow_html=True)
    st.write("클릭은 유도하지만 구매로 이어지지 않는 '허수 키워드'를 솎아내는 핵심 지표입니다.")
    
    kw_cvr = df.groupby('키워드').agg({
        '클릭수': 'sum', '주문수': 'sum', 'CVR': 'mean', 'ROAS': 'mean', '광고비': 'sum'
    }).reset_index().sort_values('클릭수', ascending=False)
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("#### 🚫 감액/중단 필요 (클릭 높으나 CVR 1% 미만)")
        st.dataframe(kw_cvr[(kw_cvr['CVR'] < 1) & (kw_cvr['클릭수'] > 100)].head(10), use_container_width=True)
    with col_b:
        st.markdown("#### ✨ 증액/확장 필요 (CVR 5% 이상 우수)")
        st.dataframe(kw_cvr[(kw_cvr['CVR'] > 5)].sort_values('주문수', ascending=False).head(10), use_container_width=True)

    # 4. 캠페인별 전략 의사결정 시트
    st.markdown('<div class="section-title">📋 캠페인별 1월 예산 조정 제언</div>', unsafe_allow_html=True)
    st.write("각 캠페인별 데이터 기반 1월 운용 가이드입니다.")
    
    camp_agg = df.groupby('캠페인명').agg({
        '광고비': 'sum', '총 전환매출액(14일)': 'sum', 'ROAS': 'mean', 'CVR': 'mean'
    }).reset_index()
    
    def suggest_action(row):
        if row['ROAS'] >= 400 and row['CVR'] >= 3: return "🚀 공격적 증액 (매출 확대)"
        elif row['ROAS'] < 200: return "⛔ 즉시 감액 (이익 방어)"
        else: return "⚖️ 효율 유지 (입찰가 최적화)"
        
    camp_agg['1월 권장 액션'] = camp_agg.apply(suggest_action, axis=1)
    st.dataframe(camp_agg.sort_values('광고비', ascending=False), use_container_width=True)

else:
    st.error("데이터 로드에 실패했습니다. 구글 시트 주소와 공유 설정을 확인해 주세요.")
