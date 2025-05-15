"""
예약된 새로고침 및 화면 보호기 일정을 체크하는 스크립트
이 스크립트는 cron이나 task scheduler로 주기적으로 실행해야 합니다.
"""

import requests
import time
import logging
from datetime import datetime

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("schedule_check.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('schedule_checker')

def check_schedules():
    """새로고침 및 화면 보호기 예약 체크"""
    try:
        # 새로고침 예약 체크
        refresh_response = requests.get('http://localhost:8080/api/refresh/check')
        refresh_data = refresh_response.json()
        
        if refresh_data.get('triggered', False):
            logger.info('예약된 새로고침이 실행되었습니다.')
        
        # 화면 보호기 예약 체크도 추가 가능
        
        logger.info('예약 체크 완료')
        
    except Exception as e:
        logger.error(f'예약 체크 중 오류 발생: {str(e)}')

if __name__ == "__main__":
    logger.info('예약 체크 스크립트 시작')
    check_schedules()
