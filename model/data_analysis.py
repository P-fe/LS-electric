# ================================
# 📦 1. 모듈 임포트
# ================================
import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error
from xgboost import XGBRegressor
from datetime import datetime

# ================================
# 📂 2. 데이터 불러오기
# ================================
train_df = pd.read_csv("data/train.csv")
test_df = pd.read_csv("data/test.csv")

# ================================
# 🕒 3. datetime 처리 및 파생 변수 생성
# ================================
train_df['측정일시'] = pd.to_datetime(train_df['측정일시'])
test_df['측정일시'] = pd.to_datetime(test_df['측정일시'])

for df in [train_df, test_df]:
    df['월'] = df['측정일시'].dt.month
    df['일'] = df['측정일시'].dt.day
    df['시간'] = df['측정일시'].dt.hour
    df['요일'] = df['측정일시'].dt.weekday
    df['주말여부'] = df['요일'].apply(lambda x: 1 if x >= 5 else 0)

# ================================
# 📌 4. 계절 파생 변수
# ================================
def get_season(month):
    if month in [6, 7, 8]:
        return '여름'
    elif month in [3, 4, 5, 9, 10]:
        return '봄가을'
    else:
        return '겨울'

train_df['계절'] = train_df['월'].apply(get_season)
test_df['계절'] = test_df['월'].apply(get_season)

# ================================
# ⏰ 5. 시간대 파생 변수
# ================================
def get_time_zone(hour, month):
    season = get_season(month)
    if season in ['여름', '봄가을']:
        if 22 <= hour or hour < 8:
            return '경부하'
        elif (8 <= hour < 11) or (12 <= hour < 13) or (18 <= hour < 22):
            return '중간부하'
        else:
            return '최대부하'
    else:  # 겨울
        if 22 <= hour or hour < 8:
            return '경부하'
        elif (8 <= hour < 9) or (12 <= hour < 16) or (19 <= hour < 22):
            return '중간부하'
        else:
            return '최대부하'

train_df['시간대'] = train_df.apply(lambda row: get_time_zone(row['시간'], row['월']), axis=1)
test_df['시간대'] = test_df.apply(lambda row: get_time_zone(row['시간'], row['월']), axis=1)

# ================================
# 💰 6. 전력요금 단가 매핑 (2024.10.24 기준 고압A 선택3)
# ================================



# ⚡️ 요금 단가 테이블
rate_table = {
    'before': {
        '여름':    {'경부하': 93.1, '중간부하': 146.3, '최대부하': 216.6},
        '봄가을': {'경부하': 93.1, '중간부하': 115.2, '최대부하': 138.9},
        '겨울':   {'경부하': 100.4, '중간부하': 146.5, '최대부하': 193.4}
    },
    'after': {
        '여름':    {'경부하': 110.0, '중간부하': 163.2, '최대부하': 233.5},
        '봄가을': {'경부하': 110.0, '중간부하': 132.1, '최대부하': 155.8},
        '겨울':   {'경부하': 117.3, '중간부하': 163.4, '최대부하': 210.3}
    }
}

# 📅 적용 시점
# 적용 시점 컬럼 추가
cutoff_date = datetime(2024, 10, 24)
train_df['적용시점'] = train_df['측정일시'].apply(lambda x: 'before' if x < cutoff_date else 'after')
test_df['적용시점'] = test_df['측정일시'].apply(lambda x: 'before' if x < cutoff_date else 'after')

# 단가 매핑 함수
def get_unit_price(row):
    return rate_table[row['적용시점']][row['계절']][row['시간대']]

# 적용
train_df['요금단가(원/kWh)'] = train_df.apply(get_unit_price, axis=1)
test_df['요금단가(원/kWh)'] = test_df.apply(get_unit_price, axis=1)

# ================================
# 🧼 7. 불필요한 컬럼 제거 및 인코딩
# ================================
# 작업유형 인코딩
le = LabelEncoder()
train_df['작업유형'] = le.fit_transform(train_df['작업유형'])
test_df['작업유형'] = le.transform(test_df['작업유형'])

# 제거할 열 목록
drop_cols = [
    '측정일시', '전력사용량(kWh)', '지상무효전력량(kVarh)', '진상무효전력량(kVarh)',
    '탄소배출량(tCO2)', '지상역률(%)', '진상역률(%)', '시간대', '계절', '적용시점'
]

train_df = train_df.drop(columns=[col for col in drop_cols if col in train_df.columns])
test_df = test_df.drop(columns=[col for col in drop_cols if col in test_df.columns])

# ================================
# 📊 8. 모델 입력/출력 정의
# ================================
target = '전기요금(원)'
features = ['작업유형', '월', '일', '시간', '요일', '주말여부', '요금단가(원/kWh)']

X = train_df[features]
y = train_df[target]
X_test = test_df[features]

# ================================
# 🔧 9. 학습 및 검증 분할
# ================================
X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)

# ================================
# 🤖 10. XGBoost 모델 학습
# ================================
model = XGBRegressor(n_estimators=200, max_depth=4, learning_rate=0.1, random_state=42)
model.fit(X_train, y_train)

# ================================
# 📈 11. 검증 성능 평가
# ================================

from sklearn.metrics import mean_squared_error, r2_score
import numpy as np

val_pred = model.predict(X_val)

# 기존 MAE
mae = mean_absolute_error(y_val, val_pred)
print(f"✅ MAE (평균절대오차): {mae:.2f}")

# 추가 지표
mse = mean_squared_error(y_val, val_pred)
rmse = np.sqrt(mse)
r2 = r2_score(y_val, val_pred)

print(f"📉 MSE (평균제곱오차): {mse:.2f}")
print(f"📏 RMSE (제곱근 평균제곱오차): {rmse:.2f}")
print(f"📊 R² Score (결정계수): {r2:.4f}")


# ================================
# 🧪 12. 테스트 데이터 예측 및 저장
# ================================

test_df['전기요금(원)'] = model.predict(X_test)
submission = test_df[['id', '전기요금(원)']]
submission.to_csv("submission.csv", index=False)
print("📁 submission.csv 파일 저장 완료")


print(test_df.columns)