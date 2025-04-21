# app.py - Flask 애플리케이션 파일
from flask import Flask, render_template, jsonify
from datetime import datetime
import random

app = Flask(__name__)

# 현재 날씨 정보를 제공하는 API (실제로는 외부 API를 사용하셔야 합니다)
@app.route('/api/weather')
def get_weather():
    # 더 다양한 날씨 정보 예시 (실제로는 외부 API를 사용해 실시간 데이터를 가져와야 함)
    weather_conditions = [
        {'condition': 'sunny', 'temperature': random.randint(20, 30), 'description': '맑음', 'feelsLike': random.randint(19, 31)},
        {'condition': 'partly-cloudy', 'temperature': random.randint(18, 28), 'description': '구름조금', 'feelsLike': random.randint(17, 29)},
        {'condition': 'cloudy', 'temperature': random.randint(18, 25), 'description': '구름많음', 'feelsLike': random.randint(17, 26)},
        {'condition': 'rainy', 'temperature': random.randint(15, 22), 'description': '비', 'feelsLike': random.randint(14, 22)},
        {'condition': 'heavy-rain', 'temperature': random.randint(14, 20), 'description': '폭우', 'feelsLike': random.randint(13, 19)},
        {'condition': 'thunderstorm', 'temperature': random.randint(15, 25), 'description': '뇌우', 'feelsLike': random.randint(14, 24)},
        {'condition': 'snowy', 'temperature': random.randint(-5, 5), 'description': '눈', 'feelsLike': random.randint(-7, 3)},
        {'condition': 'windy', 'temperature': random.randint(15, 25), 'description': '바람', 'feelsLike': random.randint(13, 23)},
        {'condition': 'foggy', 'temperature': random.randint(10, 20), 'description': '안개', 'feelsLike': random.randint(9, 19)}
    ]
    return jsonify(random.choice(weather_conditions))

# 급식 메뉴를 제공하는 API (실제로는 데이터베이스나 외부 API에서 가져와야 함)
@app.route('/api/meal')
def get_meal():
    # 급식 메뉴 예시 (실제로는 데이터베이스나 외부 API를 통해 실제 급식 정보를 가져와야 함)
    meals = [
        {
            'date': datetime.now().strftime('%Y년 %m월 %d일'),
            'items': ['미역국', '제육볶음', '김치', '잡곡밥', '배추된장국', '과일 샐러드']
        },
        {
            'date': datetime.now().strftime('%Y년 %m월 %d일'),
            'items': ['된장찌개', '불고기', '시금치나물', '깍두기', '쌀밥', '요구르트']
        },
        {
            'date': datetime.now().strftime('%Y년 %m월 %d일'),
            'items': ['김치찌개', '고등어구이', '콩나물무침', '깻잎무침', '현미밥', '바나나']
        }
    ]
    return jsonify(random.choice(meals))

# 포스터 정보를 제공하는 API
@app.route('/api/posters')
def get_posters():
    # 포스터 정보 예시 (실제로는 데이터베이스나 파일 시스템에서 가져와야 함)
    posters = [
        {'id': 1, 'src': 'https://via.placeholder.com/595x842?text=공지사항+1', 'alt': '공지사항 1'},
        {'id': 2, 'src': 'https://via.placeholder.com/595x842?text=행사안내+포스터', 'alt': '행사안내 포스터'},
        {'id': 3, 'src': 'https://via.placeholder.com/595x842?text=학사일정+안내', 'alt': '학사일정 안내'},
        {'id': 4, 'src': 'https://via.placeholder.com/595x842?text=활동+사진', 'alt': '활동 사진'}
    ]
    return jsonify(posters)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)