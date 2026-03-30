import pandas as pd
import json

# 기존 데이터
PRICE_DATA_2024 = {'강남구': 8150, '서초구': 7720, '용산구': 6250, '송파구': 5980, '성동구': 5250, '마포구': 4700, '광진구': 4450,
                   '양천구': 4400, '영등포구': 4150, '강동구': 4100, '동작구': 4000, '중구': 3850, '종로구': 3700, '서대문구': 3500,
                   '동대문구': 3350, '성북구': 3150, '강서구': 3100, '관악구': 3000, '은평구': 2950, '구로구': 2850, '노원구': 2800,
                   '중랑구': 2650, '강북구': 2600, '금천구': 2550, '도봉구': 2450}
ACADEMY_DATA = {'강남구': 2578, '양천구': 1050, '송파구': 1155, '서초구': 1187, '노원구': 739, '강동구': 680, '성북구': 550, '마포구': 520,
                '강서구': 600, '은평구': 538, '동작구': 450, '영등포구': 430, '서대문구': 370, '광진구': 390, '동대문구': 350, '관악구': 380,
                '성동구': 320, '구로구': 340, '중랑구': 300, '도봉구': 290, '강북구': 220, '금천구': 200, '용산구': 180, '종로구': 230,
                '중구': 150}


def export_real_data():
    # 1. 엑셀 로드 및 가공 (원래 코드 그대로)
    df_pop_raw = pd.read_excel('data/population_2023.xlsx', engine='openpyxl')
    df_pop = df_pop_raw[df_pop_raw['성별'] == '계'].copy()

    target_year = '2024' if '2024' in [str(c) for c in df_pop.columns] else '2023'
    if target_year not in df_pop.columns: target_year = int(target_year)

    df_pivot = df_pop.pivot(index='행정구역(시군구)별', columns='연령별', values=target_year)
    df_pivot.index = df_pivot.index.str.strip()

    def get_sum(keyword_list):
        target_cols = [c for c in df_pivot.columns if any(k in str(c) for k in keyword_list)]
        return df_pivot[target_cols].sum(axis=1)

    col_0_4 = get_sum(['0 - 4세'])
    col_5_9 = get_sum(['5 - 9세'])
    col_10_14 = get_sum(['10 - 14세'])
    col_15_19 = get_sum(['15 - 19세'])

    df_pivot['infant'] = col_0_4 + (col_5_9 * 0.4)
    df_pivot['elementary'] = (col_5_9 * 0.6) + (col_10_14 * 0.6)
    df_pivot['adolescent'] = (col_10_14 * 0.4) + (col_15_19 * 0.8)
    df_pivot['total_pop'] = df_pivot['계']

    df_pivot['ratio_infant'] = (df_pivot['infant'] / df_pivot['total_pop']) * 100
    df_pivot['ratio_elem'] = (df_pivot['elementary'] / df_pivot['total_pop']) * 100
    df_pivot['ratio_adol'] = (df_pivot['adolescent'] / df_pivot['total_pop']) * 100

    df_price = pd.DataFrame(list(PRICE_DATA_2024.items()), columns=['region', 'price'])
    df_academy = pd.DataFrame(list(ACADEMY_DATA.items()), columns=['region', 'academy_count'])

    merged = pd.merge(df_price, df_pivot, left_on='region', right_index=True, how='inner')
    merged = pd.merge(merged, df_academy, on='region', how='inner')

    # 2. HTML에 들어갈 변수명으로 컬럼 이름 변경
    export_df = merged[
        ['region', 'price', 'academy_count', 'total_pop', 'ratio_infant', 'ratio_elem', 'ratio_adol']].copy()
    export_df.columns = ['region', 'price', 'academy', 'pop', 'infant_r', 'elem_r', 'adol_r']

    # 3. 소수점 정리 후 JSON 형태로 출력
    export_df = export_df.round({'infant_r': 2, 'elem_r': 2, 'adol_r': 2})
    js_data = export_df.to_dict(orient='records')

    print("=== 아래 텍스트를 복사해서 index.html의 RAW_DATA 배열과 교체하세요 ===")
    print(json.dumps(js_data, indent=4, ensure_ascii=False))


if __name__ == "__main__":
    export_real_data()