import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
import os
from plotly.subplots import make_subplots

# 페이지 설정
st.set_page_config(page_title="육아휴직 통계 대시보드", layout="wide")

# 1. 데이터베이스 연결 확인
DB_PATH = 'parental_leave.db'

def get_connection():
    return sqlite3.connect(DB_PATH)

if not os.path.exists(DB_PATH):
    st.error(f"❌ 데이터베이스 파일('{DB_PATH}')을 찾을 수 없습니다. 파일이 같은 폴더에 있는지 확인해주세요.")
    st.stop()

st.title("📊 육아휴직 및 출산 통계 분석 대시보드")
st.markdown("공공데이터를 활용하여 우리나라의 육아기 지원 현황을 분석합니다.")

# --- 차트 1: 성별에 따른 육아휴직 확산 현황 ---
st.header("1. 성별에 따른 육아휴직 확산 현황 (2021 vs 2024)")

query1 = """
SELECT 연도, 성별, SUM(수급자수) as 총수급자수
FROM 성별현황
GROUP BY 연도, 성별
"""
df1 = pd.read_sql(query1, get_connection())

# 데이터 가공 (남성 비율 계산)
pivot_df1 = df1.pivot(index='연도', columns='성별', values='총수급자수')
pivot_df1['남성비율'] = (pivot_df1['남성'] / (pivot_df1['남성'] + pivot_df1['여성'])) * 100

col1_1, col1_2 = st.columns([2, 1])

with col1_1:
    fig1 = px.bar(df1, x='연도', y='총수급자수', color='성별', barmode='group',
                 text_auto='.s', title="연도별/성별 육아휴직 수급자 수")
    st.plotly_chart(fig1, use_container_width=True)

with col1_2:
    st.write("**[SQL Query]**")
    st.code(query1, language='sql')
    st.write("**[인사이트]**")
    m_ratio_21 = pivot_df1.loc[2021, '남성비율']
    m_ratio_24 = pivot_df1.loc[2024, '남성비율']
    st.info(f"""
    - 남성 수급자 비율이 2021년({m_ratio_21:.1f}%) 대비 2024년({m_ratio_24:.1f}%)로 크게 증가했습니다.
    - 육아휴직이 여성 전유물에서 부모 공동의 영역으로 변화하고 있음을 보여줍니다.
    """)

# --- 차트 2: 수급자수 vs 출생아수 추이 ---
st.header("2. 육아휴직 수급자수 vs 출생아수 추이 (2020~2024)")

query2 = """
SELECT m.연도, SUM(m.육아휴직) as 육아휴직수, SUM(b.출생아수) as 출생아수
FROM 모성보호 m
JOIN 출생등록 b ON m.연도 = b.연도 AND m.월 = b.월
GROUP BY m.연도
"""
df2 = pd.read_sql(query2, get_connection())

col2_1, col2_2 = st.columns([2, 1])

with col2_1:
    fig2 = make_subplots(specs=[[{"secondary_y": True}]])
    fig2.add_trace(go.Scatter(x=df2['연도'], y=df2['육아휴직수'], name="육아휴직 수급자"), secondary_y=False)
    fig2.add_trace(go.Scatter(x=df2['연도'], y=df2['출생아수'], name="출생아 수", line=dict(dash='dash')), secondary_y=True)
    
    fig2.update_layout(title_text="육아휴직 사용자와 출생아 수 비교")
    fig2.update_yaxes(title_text="육아휴직 수급자 (명)", secondary_y=False)
    fig2.update_yaxes(title_text="출생아 수 (명)", secondary_y=True)
    st.plotly_chart(fig2, use_container_width=True)

with col2_2:
    st.write("**[SQL Query]**")
    st.code(query2, language='sql')
    st.write("**[인사이트]**")
    st.info("""
    - 출생아 수는 매년 감소하는 추세이나, 육아휴직 수급자 수는 반대로 증가하거나 유지되고 있습니다.
    - 이는 출산 가구 중 육아휴직을 선택하는 비율(집중도)이 과거보다 높아졌음을 시사합니다.
    """)

# --- 차트 3: 지역별 육아휴직 사용 현황 ---
st.header("3. 지역별 육아휴직 사용 현황 비교 (2021 vs 2024)")

query3 = """
SELECT 연도, 지역, SUM(수급자수) as 수급자수
FROM 지역별현황
WHERE 지역 != '분류불능'
GROUP BY 연도, 지역
"""
df3 = pd.read_sql(query3, get_connection())

# 2024년 기준 내림차순 정렬을 위한 가공
df3_wide = df3.pivot(index='지역', columns='연도', values='수급자수').sort_values(by=2024, ascending=True)
df3_plot = df3_wide.reset_index().melt(id_vars='지역', value_name='수급자수')

col3_1, col3_2 = st.columns([2, 1])

with col3_1:
    fig3 = px.bar(df3_plot, y='지역', x='수급자수', color='연도', barmode='group',
                 orientation='h', title="지역별 육아휴직 수급자 (2024년 순위순)")
    st.plotly_chart(fig3, use_container_width=True)

with col3_2:
    st.write("**[SQL Query]**")
    st.code(query3, language='sql')
    st.write("**[인사이트]**")
    st.info("""
    - 경기, 서울 지역의 수급자 수가 압도적으로 많으며, 이는 인구 밀집도와 일자리 분포의 영향으로 보입니다.
    - 모든 지역에서 2021년 대비 2024년 수급자 수가 증가하여 전국적인 확산세를 확인할 수 있습니다.
    """)
