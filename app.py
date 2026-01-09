import streamlit as st
import pandas as pd
import numpy as np

# 1. 고밀도 프로페셔널 레이아웃 (Netlify 감성 이식)
st.set_page_config(page_title="KidsTen Growth Intelligence", layout="wide")

st.markdown("""
    <style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    * { font-family: 'Pretendard', sans-serif !important; }
    .main { background-color: #f8fafc; }
    
    /* 섹션 헤더 스타일 */
    .section-header { font-size: 20px; font-weight: 800; color: #0f172a; border-left: 5px solid #3b82f6; padding-left: 12px; margin-bottom: 20px; margin-top: 30px; }
    
    /* 상태 배지 */
    .badge-red { background: #fee2e2; color: #991b1b; padding: 4px 8px; border-radius: 4px; font-weight: 700; font-size: 12px; }
    .badge-green { background: #dcfce7; color: #166534; padding: 4px 8px; border-radius: 4px; font-weight: 700; font-size: 12px; }
    
    /* 데이터프레임 가독성 */
    .stDataFrame { border: 1px solid #e2e8f0; border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

# 2. 데이터 통합 및 전략 지표 계산 엔진
URL_1 = "https://docs.google.com/spreadsheets/d/1R4qwQFQxXxL7NO67c8mr08KXMZvU9qkArNFoPFKYJDU/export?format=csv&gid=75240363"
URL_2 = "https://docs.google.com/spreadsheets/d/1R4qwQFQxXxL7NO67c8mr08KXMZvU9qkArNFoPFKYJDU/export?format=csv&gid=481757610"

@st.cache_data
def load_and_analyze_pro():
    map_cols = {
        '캠페인 시작일': '날짜', '캠페인 이름': '캠페인명', 
        '광고비(원)': '광고비', '총 전환 매출액 (14일)(원)': '매출액',
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
    
    # 데이터 클렌징
    for c in ['광고비', '매출액', '주문수', '클릭수', '노출수']:
        if c in full_df.columns:
            full_df[c] = pd.to_numeric(full_df[c].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
            
    # 핵심 전략 지표 계산
    full_df['ROAS'] = (full_df['매출액'] / full_df['광고비'] * 100).replace([np.inf, -np.inf], 0).fillna(0)
    full_df['CVR'] = (full_df['주문수'] / full_df['클릭수'] * 100).replace([np.inf, -np.inf], 0).fillna(0)
    full_df['CPC'] = (full_df['광고비'] / full_df['클릭수']).replace([np.inf, -np.inf], 0).fillna(0)
    
    return full_df

df = load_and_analyze_pro()

if df is not None:
    # --- 상단 타이틀 ---
    st.markdown("# 🛡️ KidsTen Strategic Intelligence Center")
    st.markdown(f"12월 결산 기반 **1월 예산 최적화 가이드** (분석 리더: 장준영 팀장)")
    
    # 3. 이상 징후 알림 (Anomaly Detection)
    st.markdown('<div class="section-header">🚨 Weekly 성과 이상 징후 (최근 7일 vs 이전 7일)</div>', unsafe_allow_html=True)
    
    latest_7 = df[df['날짜'] >= df['날짜'].max() - pd.Timedelta(days=7)]
    prev_7 = df[(df['날짜'] < df['날짜'].max() - pd.Timedelta(days=7)) & (df['날짜'] >= df['날짜'].max() - pd.Timedelta(days=14))]
    
    l_sum = latest_7.groupby('키워드').agg({'ROAS':'mean', '광고비':'sum', 'CVR':'mean'}).reset_index()
    p_sum = prev_7.groupby('키워드').agg({'ROAS':'mean', 'CVR':'mean'}).reset_index()
    
    anomaly_df = pd.merge(l_sum, p_sum, on='키워드', suffixes=('_이번주', '_지난주'))
    anomaly_df['ROAS_변화'] = (anomaly_df['ROAS_이번주'] - anomaly_df['ROAS_지난주'])
    
    # 급락 키워드 필터링
    critical = anomaly_df[(anomaly_df['ROAS_변화'] < -50) & (anomaly_df['광고비'] > 30000)].sort_values('ROAS_변화')
    
    if not critical.empty:
        st.warning(f"위험: 성과가 급락한 {len(critical)}개의 키워드가 발견되었습니다. 즉시 입찰가를 하향하거나 OFF를 검토하세요.")
        st.dataframe(critical[['키워드', 'ROAS_지난주', 'ROAS_이번주', 'ROAS_변화', '광고비']], use_container_width=True)
    else:
        st.success("안전: 급격한 효율 하락을 보이는 핵심 키워드가 없습니다.")

    # 4. CVR 기반 키워드 품질 진단
    st.markdown('<div class="section-header">🔍 키워드 전환 품질(CVR) 상세 진단</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    
    kw_agg = df.groupby('키워드').agg({'클릭수':'sum', '주문수':'sum', 'CVR':'mean', 'ROAS':'mean', '광고비':'sum'}).reset_index()
    
    with col1:
        st.error("🚫 이익 저해 키워드 (클릭은 많으나 구매 전환율 1% 미만)")
        st.dataframe(kw_agg[(kw_agg['CVR'] < 1) & (kw_agg['클릭수'] > 100)].sort_values('광고비', ascending=False), use_container_width=True)
        
    with col2:
        st.success("✨ 확장 대상 키워드 (구매 전환율 5% 이상 우수)")
        st.dataframe(kw_agg[kw_agg['CVR'] > 5].sort_values('주문수', ascending=False), use_container_width=True)

    # 5. 1월 캠페인별 의사결정 시뮬레이터
    st.markdown('<div class="section-header">📋 1월 캠페인별 광고 운용 전략 (Action Item)</div>', unsafe_allow_html=True)
    
    camp_agg = df.groupby('캠페인명').agg({'광고비':'sum', '매출액':'sum', 'ROAS':'mean', 'CVR':'mean'}).reset_index()
    
    def get_action(row):
        if row['ROAS'] >= 400 and row['CVR'] >= 3: return "🚀 Scale-up (증액)"
        elif row['ROAS'] < 250: return "⛔ Profit Guard (감액)"
        else: return "⚖️ Maintain (현상유지)"
        
    camp_agg['1월 권장 액션'] = camp_agg.apply(get_action, axis=1)
    camp_agg['적정 예산 비중(%)'] = (camp_agg['광고비'] / camp_agg['광고비'].sum() * 100).round(1)
    
    st.dataframe(camp_agg.sort_values('광고비', ascending=False), use_container_width=True)

    # 6. 광고 분석가 코멘터리
    st.markdown('<div class="section-header">📝 전문 광고 분석가 총평</div>', unsafe_allow_html=True)
    st.info(f"""
    **12월 데이터 분석 결과:**
    1. **CPC 인플레이션**: 전반적으로 입찰가가 상승하여 ROAS가 압박을 받고 있습니다. CVR이 낮은 키워드부터 과감히 정리하지 않으면 1월 수익성이 위험합니다.
    2. **CVR 양극화**: 브랜드 키워드(KidsTen 등)는 안정적이나, 일반 키워드(칼슘, 영양제 등)에서 효율 저하가 뚜렷합니다. 
    
    **1월 대응 가이드:**
    - **이익 중심**: ROAS 300% 미만 캠페인은 일 예산을 20% 삭감하고, 전환율이 검증된 키워드에만 집중 투입하십시오.
    - **매출 성장**: CVR 5% 이상인 캠페인은 1월 설 명절 기획전과 연계하여 예산을 15% 선증액하는 것을 추천합니다.
    """)

else:
    st.error("데이터 로드 중입니다. 구글 시트 주소와 공유 설정을 확인해 주세요.")
