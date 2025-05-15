# app.py - Flask 애플리케이션 파일
from flask import Flask, render_template, jsonify, request, redirect, url_for, session, flash
from datetime import datetime
import random
import os
import time  # time 모듈 추가
from werkzeug.utils import secure_filename
import json

app = Flask(__name__)
app.secret_key = os.urandom(24)  # 세션 암호화를 위한 비밀 키

# 파일 업로드 관련 설정
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')

# 업로드 폴더가 없으면 생성
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 최대 16MB 파일 크기 제한

# 기본 설정값
DEFAULT_CONFIG = {
    'admin_password': 'admin1234',  # 초기 관리자 비밀번호
    'posters': [
        {'id': 1, 'src': 'https://via.placeholder.com/595x842?text=공지사항+1', 'alt': '공지사항 1'},
        {'id': 2, 'src': 'https://via.placeholder.com/595x842?text=행사안내+포스터', 'alt': '행사안내 포스터'},
        {'id': 3, 'src': 'https://via.placeholder.com/595x842?text=학사일정+안내', 'alt': '학사일정 안내'},
        {'id': 4, 'src': 'https://via.placeholder.com/595x842?text=활동+사진', 'alt': '활동 사진'}
    ],
    'kiosk_title': '학교 키오스크',
    'contact_info': '000-0000',
    'operation_hours': '09:00-18:00'
}

# 파일 확장자 검증 함수
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 설정 로드 함수
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        # 설정 파일이 없으면 기본 설정 저장 후 반환
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG

# 설정 저장 함수
def save_config(config):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=4)

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
    config = load_config()
    return jsonify(config.get('posters', DEFAULT_CONFIG['posters']))

@app.route('/')
def index():
    return render_template('index.html')

# 관리자 로그인 페이지
@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        config = load_config()
        password = request.form.get('password')
        
        if password == config.get('admin_password', DEFAULT_CONFIG['admin_password']):
            session['logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            flash('비밀번호가 올바르지 않습니다.', 'error')
    
    return render_template('admin_login.html')

# 관리자 로그아웃
@app.route('/admin/logout')
def admin_logout():
    session.pop('logged_in', None)
    flash('로그아웃되었습니다.', 'info')
    return redirect(url_for('admin_login'))

# 관리자 대시보드
@app.route('/admin/dashboard', methods=['GET'])
def admin_dashboard():
    if not session.get('logged_in'):
        flash('로그인이 필요합니다.', 'error')
        return redirect(url_for('admin_login'))
    
    config = load_config()
    return render_template('admin_dashboard.html', config=config)

# 포스터 관리 API
@app.route('/admin/posters', methods=['POST'])
def manage_posters():
    if not session.get('logged_in'):
        return jsonify({'error': '인증되지 않은 접근입니다.'}), 401
    
    config = load_config()
    
    # 파일 업로드 처리
    if 'posterImage' in request.files:
        file = request.files['posterImage']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # 새 포스터 정보
            poster_title = request.form.get('posterTitle', '새 포스터')
            new_poster = {
                'id': max(poster['id'] for poster in config['posters']) + 1 if config['posters'] else 1,
                'src': f'/static/uploads/{filename}',
                'alt': poster_title
            }
            
            # 포스터 목록에 추가
            config['posters'].append(new_poster)
            save_config(config)
            
            return jsonify({'success': True, 'poster': new_poster})
    
    return jsonify({'error': '파일 업로드에 실패했습니다.'}), 400

# 포스터 삭제 API
@app.route('/admin/posters/<int:poster_id>', methods=['DELETE'])
def delete_poster(poster_id):
    if not session.get('logged_in'):
        return jsonify({'error': '인증되지 않은 접근입니다.'}), 401
    
    config = load_config()
    
    # 기존 포스터 찾기
    for i, poster in enumerate(config['posters']):
        if poster['id'] == poster_id:
            # 업로드된 파일이면 삭제
            if poster['src'].startswith('/static/uploads/'):
                try:
                    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                             poster['src'].lstrip('/'))
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except Exception as e:
                    print(f"파일 삭제 오류: {e}")
            
            # 목록에서 제거
            del config['posters'][i]
            save_config(config)
            return jsonify({'success': True})
    
    return jsonify({'error': '포스터를 찾을 수 없습니다.'}), 404

# 설정 업데이트 API
@app.route('/admin/settings', methods=['POST'])
def update_settings():
    if not session.get('logged_in'):
        return jsonify({'error': '인증되지 않은 접근입니다.'}), 401
    
    config = load_config()
    
    # 비밀번호 변경
    new_password = request.form.get('adminPassword')
    if new_password and len(new_password) >= 6:
        config['admin_password'] = new_password
    
    # 키오스크 설정 업데이트
    config['kiosk_title'] = request.form.get('kioskTitle', DEFAULT_CONFIG['kiosk_title'])
    config['contact_info'] = request.form.get('contactInfo', DEFAULT_CONFIG['contact_info'])
    config['operation_hours'] = request.form.get('operationHours', DEFAULT_CONFIG['operation_hours'])
    
    save_config(config)
    return jsonify({'success': True})

# 화면 보호기 상태 및 예약 저장용 변수
screensaver_status = {
    'active': False,
    'schedules': []
}

# 화면 보호기 상태 API
@app.route('/api/screensaver/status', methods=['GET'])
def get_screensaver_status():
    return jsonify(screensaver_status)

# 화면 보호기 활성화/비활성화 API
@app.route('/api/screensaver/toggle', methods=['POST'])
def toggle_screensaver():
    if not session.get('logged_in'):
        return jsonify({'error': '인증되지 않은 접근입니다.'}), 401
    
    data = request.json
    screensaver_status['active'] = data.get('active', False)
    
    return jsonify({'success': True, 'status': screensaver_status})

# 화면 보호기 예약 관리 API
@app.route('/api/screensaver/schedules', methods=['POST'])
def manage_screensaver_schedules():
    if not session.get('logged_in'):
        return jsonify({'error': '인증되지 않은 접근입니다.'}), 401
    
    data = request.json
    action = data.get('action')
    
    if action == 'add':
        schedule = {
            'id': int(time.time() * 1000),  # 유니크 ID 생성
            'days': data.get('days', []),   # 요일 배열 (0=일, 1=월, ..., 6=토)
            'time': data.get('time', ''),   # 24시간 형식 (HH:MM)
            'action': data.get('scheduleAction', 'activate')  # 'activate' 또는 'deactivate'
        }
        screensaver_status['schedules'].append(schedule)
        return jsonify({'success': True, 'schedule': schedule})
    
    elif action == 'remove':
        schedule_id = data.get('id')
        screensaver_status['schedules'] = [s for s in screensaver_status['schedules'] if s['id'] != schedule_id]
        return jsonify({'success': True})
    
    elif action == 'clear':
        screensaver_status['schedules'] = []
        return jsonify({'success': True})
    
    return jsonify({'error': '잘못된 요청입니다.'}), 400

# 원격 새로고침 API
@app.route('/api/refresh', methods=['POST'])
def refresh_kiosk():
    if not session.get('logged_in'):
        return jsonify({'error': '인증되지 않은 접근입니다.'}), 401
    
    return jsonify({'success': True, 'action': 'refresh'})

# 새로고침 상태 및 예약 저장용 변수
refresh_status = {
    'needsRefresh': False,
    'lastRefreshTime': None,
    'schedules': []
}

# 새로고침 상태 API
@app.route('/api/refresh/status', methods=['GET'])
def get_refresh_status():
    status = refresh_status.copy()
    
    # 상태를 반환한 후 needsRefresh 플래그 초기화
    if refresh_status.get('needsRefresh', False):
        refresh_status['needsRefresh'] = False
    
    return jsonify(status)

# 원격 새로고침 요청 API
@app.route('/api/refresh/trigger', methods=['POST'])
def trigger_refresh():
    if not session.get('logged_in'):
        return jsonify({'error': '인증되지 않은 접근입니다.'}), 401
    
    refresh_status['needsRefresh'] = True
    refresh_status['lastRefreshTime'] = datetime.now().isoformat()
    
    return jsonify({'success': True, 'message': '새로고침 요청이 전송되었습니다.'})

# 새로고침 예약 관리 API
@app.route('/api/refresh/schedules', methods=['POST'])
def manage_refresh_schedules():
    if not session.get('logged_in'):
        return jsonify({'error': '인증되지 않은 접근입니다.'}), 401
    
    data = request.json
    action = data.get('action')
    
    if action == 'add':
        schedule = {
            'id': int(time.time() * 1000),  # 유니크 ID 생성
            'days': data.get('days', []),   # 요일 배열 (0=일, 1=월, ..., 6=토)
            'time': data.get('time', ''),   # 24시간 형식 (HH:MM)
            'description': data.get('description', '자동 새로고침')  # 설명
        }
        refresh_status['schedules'].append(schedule)
        return jsonify({'success': True, 'schedule': schedule})
    
    elif action == 'remove':
        schedule_id = data.get('id')
        refresh_status['schedules'] = [s for s in refresh_status['schedules'] if s['id'] != schedule_id]
        return jsonify({'success': True})
    
    elif action == 'clear':
        refresh_status['schedules'] = []
        return jsonify({'success': True})
    
    return jsonify({'error': '잘못된 요청입니다.'}), 400

# 새로고침 예약 체크 API (서버에서 주기적으로 실행되어 예약된 시간에 needsRefresh 플래그 설정)
@app.route('/api/refresh/check', methods=['GET'])
def check_refresh_schedules():
    now = datetime.now()
    current_day = now.weekday()
    current_time = now.strftime('%H:%M')
    
    triggered = False
    
    for schedule in refresh_status.get('schedules', []):
        if current_day in schedule.get('days', []) and current_time == schedule.get('time'):
            refresh_status['needsRefresh'] = True
            refresh_status['lastRefreshTime'] = now.isoformat()
            triggered = True
    
    return jsonify({'success': True, 'triggered': triggered})

if __name__ == '__main__':
    # 시작시 기본 설정 로드
    load_config()
    app.run(debug=True, host='0.0.0.0', port=8080)