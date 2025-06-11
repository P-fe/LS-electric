# 📦 모듈 임포트
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt

# 📂 1. 데이터 로드
train_df = pd.read_csv("data/train.csv")
train_df['측정일시'] = pd.to_datetime(train_df['측정일시'])

# 🕒 2. 계절/시간대 파생 변수 생성

def get_season(month):
    if month in [6, 7, 8]: return '여름'
    elif month in [3, 4, 5, 9, 10]: return '봄가을'
    else: return '겨울'

def get_time_zone(hour, month):
    season = get_season(month)
    if season in ['여름', '봄가을']:
        if 22 <= hour or hour < 8:
            return '경부하'
        elif (8 <= hour < 11) or (12 <= hour < 13) or (18 <= hour < 22):
            return '중간부하'
        else:
            return '최대부하'
    else:
        if 22 <= hour or hour < 8:
            return '경부하'
        elif (8 <= hour < 9) or (12 <= hour < 16) or (19 <= hour < 22):
            return '중간부하'
        else:
            return '최대부하'

train_df['월'] = train_df['측정일시'].dt.month
train_df['시간'] = train_df['측정일시'].dt.hour
train_df['계절'] = train_df['월'].apply(get_season)
train_df['시간대'] = train_df.apply(lambda row: get_time_zone(row['시간'], row['월']), axis=1)

# 📊 3. 전체 요금제 단가 테이블 (고압A/B/C 선택Ⅰ/Ⅱ/Ⅲ 각각 before/after 포함 총 18개)
rate_tables = {}
groups = ['고압A', '고압B', '고압C']
choices = ['선택1', '선택2', '선택3']
times = ['before', 'after']

rates = {
    '고압A': {
        '선택1': {'before': {'여름': [99.5, 152.4, 234.5], '봄가을': [99.5, 122.0, 152.7], '겨울': [106.5, 152.6, 210.1]},
                  'after':  {'여름': [116.4, 169.3, 251.4], '봄가을': [116.4, 138.9, 169.6], '겨울': [123.4, 169.5, 227.0]}},
        '선택2': {'before': {'여름': [94.0, 146.9, 229.0], '봄가을': [94.0, 116.5, 147.2], '겨울': [101.0, 147.1, 204.6]},
                  'after':  {'여름': [110.9, 163.8, 245.9], '봄가을': [110.9, 133.4, 164.1], '겨울': [117.9, 164.0, 221.5]}},
        '선택3': {'before': {'여름': [93.1, 146.3, 216.6], '봄가을': [93.1, 115.2, 138.9], '겨울': [100.4, 146.5, 193.4]},
                  'after':  {'여름': [110.0, 163.2, 233.5], '봄가을': [110.0, 132.1, 155.8], '겨울': [117.3, 163.4, 210.3]}}
    },
    '고압B': {
        '선택1': {'before': {'여름': [109.4, 161.7, 242.9], '봄가을': [109.4, 131.7, 162.0], '겨울': [116.4, 161.7, 217.9]},
                  'after':  {'여름': [126.3, 178.6, 259.8], '봄가을': [126.3, 148.6, 178.9], '겨울': [133.3, 178.6, 234.8]}},
        '선택2': {'before': {'여름': [105.6, 157.9, 239.1], '봄가을': [105.6, 127.9, 158.2], '겨울': [112.6, 157.9, 214.1]},
                  'after':  {'여름': [122.5, 174.8, 256.0], '봄가을': [122.5, 144.8, 175.1], '겨울': [129.5, 174.8, 231.0]}},
        '선택3': {'before': {'여름': [103.9, 156.2, 237.5], '봄가을': [103.9, 126.3, 156.6], '겨울': [111.0, 156.2, 212.4]},
                  'after':  {'여름': [120.8, 173.1, 254.4], '봄가을': [120.8, 143.2, 173.5], '겨울': [127.9, 173.1, 229.3]}}
    },
    '고압C': {
        '선택1': {'before': {'여름': [108.9, 161.8, 242.7], '봄가을': [108.9, 131.8, 162.2], '겨울': [115.8, 161.4, 218.0]},
                  'after':  {'여름': [125.8, 178.7, 259.6], '봄가을': [125.8, 148.7, 179.1], '겨울': [132.7, 178.3, 234.9]}},
        '선택2': {'before': {'여름': [104.2, 157.1, 238.0], '봄가을': [104.2, 127.1, 157.5], '겨울': [111.1, 156.7, 213.3]},
                  'after':  {'여름': [121.1, 174.0, 254.9], '봄가을': [121.1, 144.0, 174.4], '겨울': [128.0, 173.6, 230.2]}},
        '선택3': {'before': {'여름': [103.1, 156.0, 236.9], '봄가을': [103.1, 126.0, 156.4], '겨울': [110.0, 155.6, 212.2]},
                  'after':  {'여름': [120.0, 172.9, 253.8], '봄가을': [120.0, 142.9, 173.3], '겨울': [126.9, 172.5, 229.1]}}
    }
}

for group in groups:
    for choice in choices:
        for time in times:
            label = f"{group}_{choice}_{time}"
            rate_tables[label] = {
                season: {tz: rate for tz, rate in zip(['경부하', '중간부하', '최대부하'], rates[group][choice][time][season])}
                for season in ['여름', '봄가을', '겨울']
            }

# 🧠 4. 정책 요금 계산 및 차이 계산
for plan, table in rate_tables.items():
    train_df[f'정책요금_{plan}'] = train_df.apply(
        lambda row: row['전력사용량(kWh)'] * table[row['계절']][row['시간대']], axis=1
    )
    train_df[f'차이_{plan}'] = abs(train_df['전기요금(원)'] - train_df[f'정책요금_{plan}'])

# 🔍 5. 가장 유사한 요금제 추정
policy_cols = [f'차이_{plan}' for plan in rate_tables]
train_df['실제요금_유사요금제'] = train_df[policy_cols].idxmin(axis=1).str.replace('차이_', '')

# 📅 6. 적용 시점 구분
cutoff_date = datetime(2024, 10, 24)
train_df['적용시점'] = train_df['측정일시'].apply(lambda x: 'before' if x < cutoff_date else 'after')

# 📊 7. 분포 분석 및 시각화
pivot = train_df.groupby(['적용시점', '실제요금_유사요금제']).size().unstack(fill_value=0)
ax = pivot.T.plot(kind='bar', stacked=True, figsize=(12, 6), title='시점별 유사 요금제 분포')
ax.set_ylabel('건수')
plt.xticks(rotation=45)
plt.tight_layout()
plt.grid(True)
plt.show()
