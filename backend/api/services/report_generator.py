"""
LLM 기반 보고서 생성 서비스 모듈

Gemini API를 사용하여 주간/일일 보고서를 자동 생성합니다.
"""

import logging
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None

from backend.api.services.schemas.models.core.config import settings

logger = logging.getLogger(__name__)


class MOBYReportGenerator:
    """MOBY 주간 보고서 자동 생성기 (Gemini 2.5 Flash)"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Args:
            api_key: Gemini API 키 (없으면 환경변수 GEMINI_API_KEY 사용)
        """
        if not GEMINI_AVAILABLE:
            raise ImportError(
                "google-generativeai 패키지가 설치되지 않았습니다. "
                "pip install google-generativeai를 실행하세요."
            )
        
        api_key = api_key or os.getenv('GEMINI_API_KEY') or getattr(settings, 'GEMINI_API_KEY', None)
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY가 설정되지 않았습니다. "
                ".env 파일에 GEMINI_API_KEY를 설정하거나 환경 변수로 제공해주세요."
            )
        
        genai.configure(api_key=api_key)
        
        # Gemini 2.5 Flash 모델 설정
        self.model = genai.GenerativeModel(
            model_name='gemini-2.0-flash-exp',  # 최신 모델 사용
            generation_config={
                'temperature': 0.18,  # 일관성을 위해 낮은 temperature
                'top_p': 0.8,
                'top_k': 40,
                'max_output_tokens': 8192,
            }
        )
        logger.info("MOBYReportGenerator 초기화 완료")
    
    def generate_report(self, report_data: Dict[str, Any]) -> str:
        """
        보고서 데이터를 기반으로 주간 보고서 생성
        
        Args:
            report_data: 보고서 생성에 필요한 모든 데이터
                - metadata: 보고 기간, 설비명, 생성 시각
                - sensor_stats: 센서별 통계
                - alarms: 알람 목록
                - mlp_anomalies: MLP 탐지 결과
                - if_anomalies: Isolation Forest 탐지 결과
                - correlations: 센서 간 상관계수
                
        Returns:
            생성된 마크다운 보고서 문자열
        """
        try:
            prompt = self._build_prompt(report_data)
            
            logger.info("보고서 생성 시작...")
            response = self.model.generate_content(prompt)
            
            if not response.text:
                raise ValueError("Gemini API가 빈 응답을 반환했습니다.")
            
            logger.info(f"보고서 생성 완료. 길이: {len(response.text)} 문자")
            return response.text
            
        except Exception as e:
            logger.exception(f"보고서 생성 중 오류 발생: {e}")
            raise
    
    def _build_prompt(self, data: Dict[str, Any]) -> str:
        """보고서 생성을 위한 프롬프트 구성"""
        
        prompt = f"""당신은 산업 설비 모니터링 전문가입니다. 아래 센서 데이터와 이상 탐지 결과를 바탕으로, 
엔지니어링 팀을 위한 주간 보고서를 작성해주세요.

# 보고서 작성 지침

## 형식 요구사항
- 마크다운 형식으로 작성
- 제공된 템플릿 구조를 정확히 따를 것
- 표는 정렬된 형태로 작성

## 내용 요구사항
1. **Executive Summary**: 3-4문장으로 핵심 발견사항 요약
   - 주요 센서 상관관계
   - 이상 탐지 건수 및 심각도
   - 즉시 조치 필요 여부
   
2. **센서별 통계**: 제공된 수치를 표로 정리
   - 임계값 초과 시 **굵은 글씨**로 강조
   
3. **이상 탐지 상세**: 각 이상에 대해
   - 발생 시각 및 유형
   - 원시 데이터 JSON 포함
   - **물리적 해석**: 왜 이 패턴이 발생했는지, 설비 관점에서 설명
   - 구체적 권장 조치
   
4. **상관 분석 인사이트**: 
   - 센서 간 관계의 **공학적 의미** 해석
   - 시간적 패턴 분석
   - 근본 원인 추론
   
5. **권장 사항**: 우선순위별 분류 (High/Medium/Ongoing)

## 톤 및 스타일
- 전문적이고 명확한 기술 문서 스타일
- 불확실한 추측보다는 데이터 기반 분석
- 과장하지 않되, 위험 신호는 명확히 지적

---

# 입력 데이터 구조
아래 JSON은 다음 키를 포함합니다:
- `metadata`: 보고 기간, 설비명, 생성 시각
- `sensor_stats`: 센서별 통계 (온도, 습도, 진동, 가속도, 자이로, 음압, 기압)
- `alarms`: 규칙 기반 임계값 초과 알람 목록
- `mlp_anomalies`: MLP 모델이 탐지한 알려진 이상 패턴
- `if_anomalies`: Isolation Forest가 탐지한 미지의 이상 (Novelty)
- `correlations`: 센서 간 상관계수 및 해석

# 입력 데이터
```json
{json.dumps(data, indent=2, ensure_ascii=False)}
```

---

# 보고서 템플릿

아래 구조를 따라 보고서를 작성하세요:
```markdown
# 📘 MOBY 설비 모니터링 · 이상 탐지 주간 보고서

| 항목 | 내용 |
| :--- | :--- |
| **보고 기간** | [자동 입력] |
| **설비** | [자동 입력] |
| **생성 일시** | [자동 입력] |

---

## 1. 📊 Executive Summary

[핵심 발견사항을 3-4문장으로 요약]

---

## 2. 📈 센서별 통계 요약

### 2.1 온도/습도 (DHT11)
[표 작성]

### 2.2 진동 (Vibration)
[표 작성]

### 2.3 가속도/자이로 (MPU-6050)
[표 작성]

### 2.4 음압 (Sound)
[표 작성]

### 2.5 기압 (Pressure)
[표 작성]

---

## 3. ⚠️ 알람 및 이상 탐지 상세

### 3.1 규칙 기반 센서 알람
[표 작성]

### 3.2 MLP 기반 이상 탐지 (알려진 이상)
[각 이상별 상세 분석]

### 3.3 Isolation Forest 기반 미지의 이상 (Novelty)
[Novelty 패턴 분석]

---

## 4. 🔗 상관 분석 및 주간 인사이트

### 4.1 센서 간 상관계수
[표 작성]

### 4.2 주요 인사이트
[번호 목록으로 핵심 인사이트 정리]

---

## 5. 🛠️ 권장 사항

### 즉시 조치 (High Priority)
[체크박스 항목]

### 중기 조치 (Medium Priority)
[체크박스 항목]

### 모니터링 지속 (Ongoing)
[체크박스 항목]
```

이제 위 템플릿에 맞춰 보고서를 작성해주세요.
"""
        return prompt


# 전역 보고서 생성기 인스턴스
_report_generator: Optional[MOBYReportGenerator] = None


def get_report_generator() -> MOBYReportGenerator:
    """
    보고서 생성기 인스턴스를 싱글톤 패턴으로 반환합니다.
    
    Returns:
        MOBYReportGenerator: 보고서 생성기 인스턴스
        
    Raises:
        ImportError: google-generativeai 패키지가 설치되지 않은 경우
        ValueError: GEMINI_API_KEY가 설정되지 않은 경우
    """
    global _report_generator
    if _report_generator is None:
        _report_generator = MOBYReportGenerator()
    return _report_generator


def reset_report_generator():
    """보고서 생성기 인스턴스를 리셋합니다. (테스트용)"""
    global _report_generator
    _report_generator = None
    logger.debug("보고서 생성기가 리셋되었습니다.")

