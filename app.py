# app.py - Flask 애플리케이션 파일
from flask import Flask, render_template, jsonify, request, redirect, url_for, session, flash
from datetime import datetime, timedelta
import random
import os
import time  # time 모듈 추가
from werkzeug.utils import secure_filename
import json
import requests
import re

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
    'operation_hours': '09:00-18:00',
    'notices': [  # 공지사항 설정 추가
        {
            'id': 1,
            'title': '키오스크 이용 안내',
            'content': '화면을 터치하여 이용하세요',
            'type': 'info',  # info, warning, important
            'active': True,
            'created_at': datetime.now().isoformat()
        },
        {
            'id': 2,
            'title': '문의 및 운영시간',
            'content': '문의: 000-0000\n운영시간: 09:00-18:00',
            'type': 'info',
            'active': True,
            'created_at': datetime.now().isoformat()
        }
    ],
    'meal_settings': {
        'neis_api_key': '',          # 나이스 API 키
        'school_code': '',           # 학교 코드 (10자리)
        'office_code': '',           # 교육청 코드 (10자리)
        'school_kind': 'mis',        # 학교급 (els: 초등학교, mis: 중학교, his: 고등학교)
        'auto_update': True,         # 자동 갱신 여부
        'update_time': '06:00',      # 갱신 시간
        'update_interval': 1,        # 갱신 간격 (일)
        'cache_duration': 24,        # 캐시 유지 시간 (시간)
        'last_updated': None,        # 마지막 갱신 시간
        'cached_meals': {},          # 캐시된 급식 데이터
        'error_count': 0,            # 연속 오류 횟수
        'last_error': None           # 마지막 오류 메시지
    }
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

# 나이스 API 호출 함수
def fetch_meal_from_neis(school_code, office_code, api_key, date_str):
    """
    나이스 교육정보 개발 포털 API에서 급식 정보를 가져오는 함수
    """
    try:
        base_url = "https://open.neis.go.kr/hub/mealServiceDietInfo"
        
        params = {
            'KEY': api_key,
            'Type': 'json',
            'pIndex': 1,
            'pSize': 100,
            'ATPT_OFCDC_SC_CODE': office_code,
            'SD_SCHUL_CODE': school_code,
            'MLSV_YMD': date_str
        }
        
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # API 오류 응답 확인
        if 'RESULT' in data and data['RESULT']['CODE'] != 'INFO-000':
            error_msg = data['RESULT']['MESSAGE']
            raise Exception(f"NEIS API Error: {error_msg}")
        
        if 'mealServiceDietInfo' in data and len(data['mealServiceDietInfo']) > 1:
            meals = data['mealServiceDietInfo'][1]['row']
            meal_data = []
            
            for meal in meals:
                # 메뉴 정리 (HTML 태그 및 알레르기 정보 제거)
                menu_text = meal['DDISH_NM']
                # <br/> 태그를 줄바꿈으로 변경
                menu_text = menu_text.replace('<br/>', '\n')
                # 알레르기 정보 제거 (숫자. 형태)
                menu_text = re.sub(r'\d+\.', '', menu_text)
                # 불필요한 공백 제거
                menu_items = [item.strip() for item in menu_text.split('\n') if item.strip()]
                
                meal_data.append({
                    'date': f"{date_str[:4]}년 {date_str[4:6]}월 {date_str[6:8]}일",
                    'type': meal['MMEAL_SC_NM'],  # 조식, 중식, 석식
                    'items': menu_items,
                    'cal_info': meal.get('CAL_INFO', ''),  # 칼로리 정보
                    'ntr_info': meal.get('NTR_INFO', '')   # 영양 정보
                })
            
            return meal_data
        else:
            return None
            
    except Exception as e:
        print(f"나이스 API 호출 오류: {e}")
        raise e

# 급식 데이터 갱신 함수
def update_meal_cache():
    """
    급식 데이터를 갱신하고 캐시에 저장하는 함수
    """
    config = load_config()
    meal_settings = config.get('meal_settings', DEFAULT_CONFIG['meal_settings'])
    
    if not all([meal_settings.get('neis_api_key'), 
                meal_settings.get('school_code'), 
                meal_settings.get('office_code')]):
        return False, "API 설정이 완료되지 않았습니다."
    
    try:
        # 오늘부터 일주일간의 급식 정보 가져오기
        today = datetime.now()
        cached_meals = {}
        success_count = 0
        
        for i in range(7):
            target_date = today + timedelta(days=i)
            date_str = target_date.strftime('%Y%m%d')
            
            try:
                meal_data = fetch_meal_from_neis(
                    meal_settings['school_code'],
                    meal_settings['office_code'],
                    meal_settings['neis_api_key'],
                    date_str
                )
                
                if meal_data:
                    cached_meals[date_str] = meal_data
                    success_count += 1
                    
            except Exception as e:
                print(f"날짜 {date_str} 급식 데이터 가져오기 실패: {e}")
                continue
        
        # 캐시 업데이트
        config['meal_settings']['cached_meals'] = cached_meals
        config['meal_settings']['last_updated'] = datetime.now().isoformat()
        config['meal_settings']['error_count'] = 0
        config['meal_settings']['last_error'] = None
        save_config(config)
        
        return True, f"{success_count}/7일 급식 데이터 갱신 완료"
        
    except Exception as e:
        error_msg = str(e)
        config['meal_settings']['error_count'] = config['meal_settings'].get('error_count', 0) + 1
        config['meal_settings']['last_error'] = error_msg
        save_config(config)
        print(f"급식 데이터 갱신 오류: {error_msg}")
        return False, error_msg

# 급식 메뉴를 제공하는 API
@app.route('/api/meal')
def get_meal():
    config = load_config()
    meal_settings = config.get('meal_settings', DEFAULT_CONFIG['meal_settings'])
    
    # 캐시된 데이터가 있고 유효한지 확인
    if (meal_settings.get('cached_meals') and 
        meal_settings.get('last_updated')):
        
        try:
            last_updated = datetime.fromisoformat(meal_settings['last_updated'])
            cache_duration = meal_settings.get('cache_duration', 24)
            
            if datetime.now() - last_updated < timedelta(hours=cache_duration):
                # 오늘 급식 정보 반환
                today_str = datetime.now().strftime('%Y%m%d')
                today_meals = meal_settings['cached_meals'].get(today_str, [])
                
                if today_meals:
                    # 중식 정보 우선, 없으면 첫 번째 식사
                    lunch_meal = next((meal for meal in today_meals if '중식' in meal.get('type', '')), 
                                    today_meals[0] if today_meals else None)
                    if lunch_meal:
                        return jsonify(lunch_meal)
        except Exception as e:
            print(f"캐시된 급식 데이터 처리 오류: {e}")
    
    # 캐시된 데이터가 없거나 만료된 경우 기본 데이터 반환
    meals = [
        {
            'date': datetime.now().strftime('%Y년 %m월 %d일'),
            'type': '중식',
            'items': ['미역국', '제육볶음', '김치', '잡곡밥', '배추된장국', '과일 샐러드']
        },
        {
            'date': datetime.now().strftime('%Y년 %m월 %d일'),
            'type': '중식',
            'items': ['된장찌개', '불고기', '시금치나물', '깍두기', '쌀밥', '요구르트']
        },
        {
            'date': datetime.now().strftime('%Y년 %m월 %d일'),
            'type': '중식',
            'items': ['김치찌개', '고등어구이', '콩나물무침', '깻잎무침', '현미밥', '바나나']
        }
    ]
    return jsonify(random.choice(meals))

# 포스터 정보를 제공하는 API
@app.route('/api/posters')
def get_posters():
    config = load_config()
    return jsonify(config.get('posters', DEFAULT_CONFIG['posters']))

# 공지사항 정보를 제공하는 API
@app.route('/api/notices')
def get_notices():
    config = load_config()
    active_notices = [notice for notice in config.get('notices', []) if notice.get('active', True)]
    return jsonify(active_notices)

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
@app.route('/admin/dashboard')
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

# 공지사항 관리 API
@app.route('/admin/notices', methods=['GET', 'POST', 'PUT', 'DELETE'])
def manage_notices():
    if not session.get('logged_in'):
        return jsonify({'error': '인증되지 않은 접근입니다.'}), 401
    
    config = load_config()
    
    if request.method == 'GET':
        # 모든 공지사항 반환
        return jsonify(config.get('notices', []))
    
    elif request.method == 'POST':
        # 새 공지사항 추가
        data = request.json
        new_notice = {
            'id': max(notice['id'] for notice in config.get('notices', [])) + 1 if config.get('notices') else 1,
            'title': data.get('title', ''),
            'content': data.get('content', ''),
            'type': data.get('type', 'info'),
            'active': data.get('active', True),
            'created_at': datetime.now().isoformat()
        }
        
        if 'notices' not in config:
            config['notices'] = []
        config['notices'].append(new_notice)
        save_config(config)
        
        return jsonify({'success': True, 'notice': new_notice})
    
    elif request.method == 'PUT':
        # 공지사항 수정
        data = request.json
        notice_id = data.get('id')
        
        for notice in config.get('notices', []):
            if notice['id'] == notice_id:
                notice['title'] = data.get('title', notice['title'])
                notice['content'] = data.get('content', notice['content'])
                notice['type'] = data.get('type', notice['type'])
                notice['active'] = data.get('active', notice['active'])
                notice['updated_at'] = datetime.now().isoformat()
                
                save_config(config)
                return jsonify({'success': True, 'notice': notice})
        
        return jsonify({'error': '공지사항을 찾을 수 없습니다.'}), 404
    
    elif request.method == 'DELETE':
        # 공지사항 삭제
        notice_id = request.json.get('id')
        
        for i, notice in enumerate(config.get('notices', [])):
            if notice['id'] == notice_id:
                del config['notices'][i]
                save_config(config)
                return jsonify({'success': True})
        
        return jsonify({'error': '공지사항을 찾을 수 없습니다.'}), 404

# 공지사항 상태 토글 API
@app.route('/admin/notices/<int:notice_id>/toggle', methods=['POST'])
def toggle_notice_status(notice_id):
    if not session.get('logged_in'):
        return jsonify({'error': '인증되지 않은 접근입니다.'}), 401
    
    config = load_config()
    
    for notice in config.get('notices', []):
        if notice['id'] == notice_id:
            notice['active'] = not notice.get('active', True)
            notice['updated_at'] = datetime.now().isoformat()
            save_config(config)
            return jsonify({'success': True, 'active': notice['active']})
    
    return jsonify({'error': '공지사항을 찾을 수 없습니다.'}), 404

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
    
    # 급식 설정 업데이트
    if 'meal_settings' not in config:
        config['meal_settings'] = DEFAULT_CONFIG['meal_settings'].copy()
    
    config['meal_settings']['neis_api_key'] = request.form.get('neisApiKey', '').strip()
    config['meal_settings']['school_code'] = request.form.get('schoolCode', '').strip()
    config['meal_settings']['office_code'] = request.form.get('officeCode', '').strip()
    config['meal_settings']['school_kind'] = request.form.get('schoolKind', 'mis')
    config['meal_settings']['auto_update'] = request.form.get('autoUpdate') == 'on'
    config['meal_settings']['update_time'] = request.form.get('updateTime', '06:00')
    config['meal_settings']['update_interval'] = int(request.form.get('updateInterval', 1))
    config['meal_settings']['cache_duration'] = int(request.form.get('cacheDuration', 24))
    
    save_config(config)
    return jsonify({'success': True})

# 급식 API 테스트
@app.route('/admin/meal/test', methods=['POST'])
def test_meal_api():
    if not session.get('logged_in'):
        return jsonify({'error': '인증되지 않은 접근입니다.'}), 401
    
    data = request.json
    api_key = data.get('apiKey', '').strip()
    school_code = data.get('schoolCode', '').strip()
    office_code = data.get('officeCode', '').strip()
    
    if not all([api_key, school_code, office_code]):
        return jsonify({'error': '모든 필드를 입력해주세요.'}), 400
    
    try:
        # 오늘 날짜로 테스트
        today_str = datetime.now().strftime('%Y%m%d')
        meal_data = fetch_meal_from_neis(school_code, office_code, api_key, today_str)
        
        if meal_data:
            return jsonify({'success': True, 'data': meal_data, 'message': 'API 테스트 성공!'})
        else:
            return jsonify({'success': True, 'data': [], 'message': '오늘 급식 정보가 없습니다.'})
            
    except Exception as e:
        error_msg = str(e)
        return jsonify({'error': f'API 테스트 실패: {error_msg}'}), 400

# 급식 데이터 수동 갱신
@app.route('/admin/meal/refresh', methods=['POST'])
def refresh_meal_data():
    if not session.get('logged_in'):
        return jsonify({'error': '인증되지 않은 접근입니다.'}), 401
    
    success, message = update_meal_cache()
    
    if success:
        return jsonify({'success': True, 'message': message})
    else:
        return jsonify({'error': f'급식 데이터 갱신 실패: {message}'}), 400

# 급식 데이터 상태 확인
@app.route('/admin/meal/status', methods=['GET'])
def get_meal_status():
    if not session.get('logged_in'):
        return jsonify({'error': '인증되지 않은 접근입니다.'}), 401
    
    config = load_config()
    meal_settings = config.get('meal_settings', DEFAULT_CONFIG['meal_settings'])
    
    status = {
        'last_updated': meal_settings.get('last_updated'),
        'cache_count': len(meal_settings.get('cached_meals', {})),
        'auto_update': meal_settings.get('auto_update', False),
        'update_time': meal_settings.get('update_time', '06:00'),
        'update_interval': meal_settings.get('update_interval', 1),
        'error_count': meal_settings.get('error_count', 0),
        'last_error': meal_settings.get('last_error'),
        'api_configured': bool(meal_settings.get('neis_api_key') and 
                              meal_settings.get('school_code') and 
                              meal_settings.get('office_code'))
    }
    
    return jsonify(status)

# 급식 갱신 스케줄 체크 API
@app.route('/api/meal/check-schedule', methods=['GET'])
def check_meal_schedule():
    config = load_config()
    meal_settings = config.get('meal_settings', DEFAULT_CONFIG['meal_settings'])
    
    if not meal_settings.get('auto_update', False):
        return jsonify({'success': True, 'updated': False, 'message': '자동 갱신이 비활성화되어 있습니다.'})
    
    now = datetime.now()
    current_time = now.strftime('%H:%M')
    update_time = meal_settings.get('update_time', '06:00')
    update_interval = meal_settings.get('update_interval', 1)
    
    # 설정된 시간에 자동 갱신 체크
    if current_time == update_time:
        last_updated = meal_settings.get('last_updated')
        should_update = True
        
        if last_updated:
            try:
                last_update_time = datetime.fromisoformat(last_updated)
                time_diff = now - last_update_time
                should_update = time_diff.days >= update_interval
            except:
                should_update = True
        
        if should_update:
            success, message = update_meal_cache()
            return jsonify({'success': True, 'updated': success, 'message': message})
    
    return jsonify({'success': True, 'updated': False, 'message': '갱신 시간이 아닙니다.'})

# 급식 데이터 캐시 정리
@app.route('/admin/meal/clear-cache', methods=['POST'])
def clear_meal_cache():
    if not session.get('logged_in'):
        return jsonify({'error': '인증되지 않은 접근입니다.'}), 401
    
    config = load_config()
    if 'meal_settings' in config:
        config['meal_settings']['cached_meals'] = {}
        config['meal_settings']['last_updated'] = None
        config['meal_settings']['error_count'] = 0
        config['meal_settings']['last_error'] = None
        save_config(config)
    
    return jsonify({'success': True, 'message': '급식 캐시가 정리되었습니다.'})

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