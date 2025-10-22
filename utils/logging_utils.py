"""
로깅 관련 유틸리티 함수 모듈

파이프라인의 각 단계를 추적하고 로그하는 기능을 제공합니다.
"""
import json
from datetime import datetime


def log_step(step_name: str, details: dict = None):
    """
    파이프라인 각 단계의 처리 과정을 로그로 남깁니다

    Args:
        step_name (str): 단계 이름
        details (dict, optional): 단계에 대한 추가 상세 정보
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    print(f"\n{'='*80}")
    print(f"[{timestamp}] 🔹 {step_name}")
    print(f"{'='*80}")
    if details:
        for key, value in details.items():
            if isinstance(value, (dict, list)):
                print(f"  {key}: {json.dumps(value, indent=2, ensure_ascii=False)}")
            else:
                print(f"  {key}: {value}")
    print()
