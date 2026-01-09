import streamlit as st
import pandas as pd
import plotly.express as px

# 1. 앱 설정
st.set_page_config(page_title="KidsTen Growth Cockpit", layout="wide")

# 2. 데이터 주소 (팀장님의 구글 시트 CSV 주소)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1R4qwQFQxXxL7NO67c8mr08KXMZvU9qkArNFoPFKYJDU/export?format=csv"

@st.cache_data
def load_data():
    try:
        df = pd.read_csv(SHEET_URL)
        df['날짜'] = pd.to_datetime(df['날짜'], format='%Y%m%d')
        return df
    except Exception as e:
        st.error(f"데이터 로드 오류: {e}")
        return None

df = load_data()

if df is not None:
    # --- 타이틀 ---
    st.title("📊 KidsTen Ad Growth Cockpit")
    
    # --- 상단 지표 ---
    total_spend = df['광고비'].sum()
    total_sales = df['총 전환매출액(14일)'].sum()
    roas = (total_sales / total_spend * 100) if total_spend > 0 else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("총 광고비", f"{total_spend:,.0f}원")
    col2.metric("총 광고 매출", f"{total_sales:,.0f}원")
    col3.metric("평균 ROAS", f"{roas:.1f}%")

    # --- 그래프 ---
    st.subheader("일별 매출 및 광고비 추이")
    chart_data = df.groupby('날짜')[['광고비', '총 전환매출액(14일)']].sum().reset_index()
    fig = px.line(chart_data, x='날짜', y=['광고비', '총 전환매출액(14일)'], 
                  color_discrete_sequence=['#FF4B4B', '#007BFF'])
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("데이터를 불러올 수 없습니다. 구글 시트 공유 설정을 확인해주세요.")
