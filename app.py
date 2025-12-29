import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# -----------------------------------------------------------------------------
# 1. 기본 설정
# -----------------------------------------------------------------------------
st.set_page_config(page_title="서울 부동산 심층 분석 보고서", layout="wide")

# -----------------------------------------------------------------------------
# 2. 내장 데이터 (2024년 기준 추정치)
# -----------------------------------------------------------------------------

# A. 부동산 평당 가격 (단위: 만원)
PRICE_DATA_2024 = {
    '강남구': 8150, '서초구': 7720, '용산구': 6250, '송파구': 5980, '성동구': 5250,
    '마포구': 4700, '광진구': 4450, '양천구': 4400, '영등포구': 4150, '강동구': 4100,
    '동작구': 4000, '중구': 3850, '종로구': 3700, '서대문구': 3500, '동대문구': 3350,
    '성북구': 3150, '강서구': 3100, '관악구': 3000, '은평구': 2950, '구로구': 2850,
    '노원구': 2800, '중랑구': 2650, '강북구': 2600, '금천구': 2550, '도봉구': 2450
}

# B. 사설학원 수 (단위: 개소, 2023-2024 서울열린데이터광장 및 교육통계 기반 추정)
ACADEMY_DATA = {
    '강남구': 2578, '양천구': 1050, '송파구': 1155, '서초구': 1187, '노원구': 739,
    '강동구': 680, '성북구': 550, '마포구': 520, '강서구': 600, '은평구': 538,
    '동작구': 450, '영등포구': 430, '서대문구': 370, '광진구': 390, '동대문구': 350,
    '관악구': 380, '성동구': 320, '구로구': 340, '중랑구': 300, '도봉구': 290,
    '강북구': 220, '금천구': 200, '용산구': 180, '종로구': 230, '중구': 150
}


# -----------------------------------------------------------------------------
# 3. 데이터 로드 및 가공 함수
# -----------------------------------------------------------------------------
@st.cache_data
def load_and_process_data():
    try:
        # 1. 인구 데이터 로드
        df_pop_raw = pd.read_excel('data/population_2023.xlsx', engine='openpyxl')
        df_pop = df_pop_raw[df_pop_raw['성별'] == '계'].copy()

        target_year = '2024' if '2024' in [str(c) for c in df_pop.columns] else '2023'
        if target_year not in df_pop.columns: target_year = int(target_year)

        df_pivot = df_pop.pivot(index='행정구역(시군구)별', columns='연령별', values=target_year)
        df_pivot.index = df_pivot.index.str.strip()

        # 2. 연령대별 세분화 (핵심 로직)
        # 영유아(0-6), 초등(7-12), 중고등(13-18)
        cols = [str(c) for c in df_pivot.columns]

        # 컬럼 매핑 (데이터 컬럼명에 따라 유연하게 처리)
        def get_sum(keyword_list):
            target_cols = [c for c in df_pivot.columns if any(k in str(c) for k in keyword_list)]
            return df_pivot[target_cols].sum(axis=1)

        # 5세 단위 데이터를 활용한 근사치 계산
        # 0-4세 + 5-9세의 절반 -> 영유아(0~6)
        # 5-9세의 절반 + 10-14세의 절반 -> 초등(7~12)
        # 10-14세의 절반 + 15-19세의 80% -> 중고등(13~18)
        # *정확한 나이별 데이터가 없으므로 구간 비율로 추정

        col_0_4 = get_sum(['0 - 4세'])
        col_5_9 = get_sum(['5 - 9세'])
        col_10_14 = get_sum(['10 - 14세'])
        col_15_19 = get_sum(['15 - 19세'])

        df_pivot['infant'] = col_0_4 + (col_5_9 * 0.4)  # 0~6세
        df_pivot['elementary'] = (col_5_9 * 0.6) + (col_10_14 * 0.6)  # 7~12세
        df_pivot['adolescent'] = (col_10_14 * 0.4) + (col_15_19 * 0.8)  # 13~18세 (입시생)

        df_pivot['total_pop'] = df_pivot['계']

        # 비율 계산
        df_pivot['ratio_infant'] = (df_pivot['infant'] / df_pivot['total_pop']) * 100
        df_pivot['ratio_elem'] = (df_pivot['elementary'] / df_pivot['total_pop']) * 100
        df_pivot['ratio_adol'] = (df_pivot['adolescent'] / df_pivot['total_pop']) * 100
        df_pivot['ratio_total_youth'] = df_pivot['ratio_infant'] + df_pivot['ratio_elem'] + df_pivot['ratio_adol']

        # 3. 외부 데이터 병합 (가격, 학원)
        df_price = pd.DataFrame(list(PRICE_DATA_2024.items()), columns=['region', 'price'])
        df_academy = pd.DataFrame(list(ACADEMY_DATA.items()), columns=['region', 'academy_count'])

        merged = pd.merge(df_price, df_pivot, left_on='region', right_index=True, how='inner')
        merged = pd.merge(merged, df_academy, on='region', how='inner')

        return merged

    except Exception as e:
        st.error(f"데이터 처리 중 오류 발생: {e}")
        return pd.DataFrame()


# -----------------------------------------------------------------------------
# 4. 메인 대시보드 UI
# -----------------------------------------------------------------------------
st.title("🏙️ 서울 부동산 딥다이브: 입시와 집값의 연결고리")
st.markdown("""
> **가설 확장:단순한 학령인구가 아니라, '입시생(중고등학생)'과 '학원 인프라'가 집값에 미치는 영향을 심층 분석합니다.  
> 인구 구조를 영유아/초등/중고등으로 쪼개어 어떤 계층이 부동산 가치를 견인하는지 파헤칩니다.
""")

st.divider()

df = load_and_process_data()

if not df.empty:
    # 탭 구성
    tab1, tab2, tab3 = st.tabs(["👶 연령별 상관분석", "🏫 학원 인프라 효과", "📊 종합 데이터"])

    # [TAB 1] 연령대별 집값 상관관계 비교
    with tab1:
        st.subheader("어떤 아이들이 집값을 올리는가?")
        st.markdown("전체 학령인구를 영유아(0-6세), 초등(7-12세), 입시생(13-18세)로 나누어 집값과의 상관관계를 비교합니다.")

        col_c1, col_c2 = st.columns([3, 1])

        with col_c1:
            # 상관계수 계산
            corr_infant = df['ratio_infant'].corr(df['price'])
            corr_elem = df['ratio_elem'].corr(df['price'])
            corr_adol = df['ratio_adol'].corr(df['price'])

            # 막대 차트로 상관계수 비교
            corr_data = pd.DataFrame({
                '연령대': ['영유아 (0~6세)', '초등학생 (7~12세)', '중고등학생 (13~18세)'],
                '상관계수': [corr_infant, corr_elem, corr_adol],
                '설명': ['보육 중심', '학군 형성기', '본격 입시 학군']
            })

            fig_bar = px.bar(corr_data, x='연령대', y='상관계수', color='상관계수',
                             color_continuous_scale='Bluered', text_auto='.2f',
                             title="연령대별 집값과의 상관계수 비교")
            fig_bar.update_layout(height=400)
            st.plotly_chart(fig_bar, use_container_width=True)

        with col_c2:
            st.info("💡 **분석 결과**")
            max_corr = corr_data.loc[corr_data['상관계수'].idxmax()]
            st.write(f"가장 강력한 요인: **{max_corr['연령대']}**")

            if max_corr['연령대'] == '중고등학생 (13~18세)':
                st.write("""
                **"입시가 집값이다"**
                영유아보다 중고등학생 비율이 높은 곳이 집값이 훨씬 비쌉니다. 
                이는 실거주 수요가 **고등학교 학군**을 따라 이동함을 보여줍니다.
                """)
            else:
                st.write("연령대별 차이가 크지 않거나 다른 요인이 작용하고 있습니다.")

        # 산점도: 중고등학생 비율 vs 집값
        fig_scatter = px.scatter(df, x='ratio_adol', y='price', size='total_pop',
                                 color='price', hover_name='region', trendline='ols',
                                 labels={'ratio_adol': '중고등학생(입시생) 인구 비율(%)', 'price': '평당 가격(만원)'},
                                 title="입시생(13~18세) 비율과 집값의 상관관계")
        st.plotly_chart(fig_scatter, use_container_width=True)

    # [TAB 2] 학원 수와 집값
    with tab2:
        st.subheader("사교육의 힘: 학원이 많은 곳이 비쌀까?")
        col_a1, col_a2 = st.columns([3, 1])

        with col_a1:
            fig_academy = px.scatter(df, x='academy_count', y='price', size='ratio_adol',
                                     color='price', hover_name='region', trendline='ols',
                                     color_continuous_scale='Viridis',
                                     labels={'academy_count': '사설학원 수 (개)', 'price': '평당 가격(만원)',
                                             'ratio_adol': '입시생 비율'},
                                     title="서울시 자치구별 학원 수 vs 아파트 평당 가격")
            # 주요 구 텍스트 추가
            for i, row in df.iterrows():
                if row['academy_count'] > 500 or row['price'] > 5000:  # 특징적인 구만 표시
                    fig_academy.add_annotation(x=row['academy_count'], y=row['price'], text=row['region'],
                                               showarrow=False, yshift=10)

            st.plotly_chart(fig_academy, use_container_width=True)

        with col_a2:
            st.success("🏫 **인프라 분석**")
            corr_academy = df['academy_count'].corr(df['price'])
            st.metric("상관계수 (학원-집값)", f"{corr_academy:.2f}")

            st.markdown("""
            - 강남구의 독주: 학원 수 2,500여 개로 압도적 1위이며 집값도 1위입니다.
            - 양천구(목동) & 노원구(중계): 집값 대비 학원 수가 매우 많습니다. 전형적인'교육 특구'**의 모습을 보입니다.
            - 상관계수: 인구 비율보다 학원 수와의 상관계수가 더 높게 나올 수 있습니다.* 이는 '교육 인프라'가 집값 방어의 핵심임을 시사합니다.
            """)

    # [TAB 3] 데이터 상세
    with tab3:
        st.dataframe(
            df[['region', 'price', 'academy_count', 'ratio_infant', 'ratio_elem', 'ratio_adol']]
            .sort_values(by='price', ascending=False)
            .style.format({
                'price': '{:,.0f} 만원',
                'academy_count': '{:,.0f} 개',
                'ratio_infant': '{:.2f}%',
                'ratio_elem': '{:.2f}%',
                'ratio_adol': '{:.2f}%'
            })
            .background_gradient(subset=['price', 'academy_count', 'ratio_adol'], cmap='Reds')
        )
else:

    st.error("데이터 로드 실패. data 폴더를 확인해주세요.")
