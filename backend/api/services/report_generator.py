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
        
        # 실제 사용 가능한 모델 목록을 API에서 가져오기
        self.model = None
        self.model_name = None
        
        # 먼저 실제 사용 가능한 모델 목록을 가져오기 시도
        available_model_names = []
        try:
            models = genai.list_models()
            available_model_names = [
                m.name for m in models 
                if 'generateContent' in m.supported_generation_methods
                and 'gemini' in m.name.lower()
            ]
            logger.info(f"API에서 {len(available_model_names)}개의 사용 가능한 Gemini 모델 발견")
        except Exception as e:
            logger.warning(f"모델 목록 조회 실패, 기본 목록 사용: {e}")
        
        # 직접 모델을 순차적으로 시도 (원본 노트북과 동일한 우선순위)
        # 원본 노트북에서 사용한 'gemini-2.5-flash'를 최우선으로 시도
        model_candidates = [
            'gemini-2.5-flash',              # 원본 노트북에서 사용한 모델 (최우선)
            'models/gemini-2.5-flash',      # 긴 이름 버전
            'models/gemini-flash-latest',    # 최신 Flash 모델
            'gemini-flash-latest',           # 짧은 이름
            'models/gemini-2.5-pro',         # 최신 2.5 Pro 모델
            'gemini-2.5-pro',                # 짧은 이름
            'models/gemini-pro-latest',      # 최신 Pro 모델
            'models/gemini-2.0-flash',       # 2.0 Flash 모델
            'models/gemini-1.5-flash',       # 안정적인 Flash 모델
            'gemini-1.5-flash',              # 짧은 이름
            'models/gemini-1.5-pro',         # 안정적인 Pro 모델
            'gemini-1.5-pro',                # 짧은 이름
        ]
        
        # 사용 가능한 모델이 있으면 우선순위 조정
        if available_model_names:
            # 실제 사용 가능한 모델 중에서 우선순위가 높은 것부터 찾기
            prioritized_available = []
            for candidate in model_candidates:
                # 정확히 일치하는 모델 찾기
                for available in available_model_names:
                    if candidate == available or available.endswith('/' + candidate) or candidate == available.split('/')[-1]:
                        if available not in prioritized_available:
                            prioritized_available.append(available)
                            break
            
            # 사용 가능한 모델을 앞에 배치
            if prioritized_available:
                model_candidates = prioritized_available + [m for m in model_candidates if m not in prioritized_available]
                logger.info(f"사용 가능한 모델 우선순위 조정: {prioritized_available[:3]}")
        
        self.model = None
        self.model_name = None
        errors = []
        
        logger.info(f"사용 가능한 Gemini 모델 찾기 시작 (총 {len(model_candidates)}개 모델 시도)")
        
        for idx, model_name in enumerate(model_candidates, 1):
            try:
                logger.info(f"[{idx}/{len(model_candidates)}] 모델 '{model_name}' 시도 중...")
                
                # 모델 초기화
                test_model = genai.GenerativeModel(
                    model_name=model_name,
                    generation_config={
                        'temperature': 0.18,
                        'top_p': 0.8,
                        'top_k': 40,
                        'max_output_tokens': 8192,
                    }
                )
                
                # 모델이 실제로 작동하는지 간단한 테스트 요청
                test_response = test_model.generate_content("test")
                if test_response and test_response.text:
                    # 모델이 정상 작동함
                    self.model = test_model
                    self.model_name = model_name
                    logger.info(f"✅ 모델 '{model_name}' 초기화 및 테스트 성공!")
                    break
                else:
                    raise ValueError(f"모델 '{model_name}'가 빈 응답을 반환했습니다.")
                    
            except Exception as e:
                error_msg = str(e)
                errors.append(f"{model_name}: {error_msg}")
                logger.warning(f"❌ 모델 '{model_name}' 실패: {error_msg}")
                continue
        
        if self.model is None:
            error_summary = "\n".join([f"  - {err}" for err in errors])
            raise ValueError(
                f"사용 가능한 Gemini 모델을 찾을 수 없습니다.\n\n"
                f"시도한 모델들:\n{error_summary}\n\n"
                f"API 키와 할당량을 확인하세요. "
                f"Google AI Studio (https://makersuite.google.com/app/apikey)에서 API 키 상태를 확인하세요."
            )
        
        logger.info(f"✅ MOBYReportGenerator 초기화 완료! 사용 모델: {self.model_name}")
    
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
            # 사용 중인 모델 확인 (여러 방법으로 시도)
            current_model = 'unknown'
            if self.model_name:
                current_model = self.model_name
            elif self.model:
                # GenerativeModel 객체에서 모델 이름 추출 시도
                try:
                    if hasattr(self.model, '_model_name'):
                        current_model = self.model._model_name
                    elif hasattr(self.model, 'model_name'):
                        current_model = self.model.model_name
                except:
                    pass
            
            logger.info(f"보고서 생성 시작... (저장된 모델명: {self.model_name}, 실제 사용 모델: {current_model})")
            
            # 모델이 제대로 초기화되었는지 확인
            if self.model is None or self.model_name is None:
                logger.warning("보고서 생성기가 초기화되지 않았습니다. 재초기화 시도...")
                # 재초기화 시도 (API 키는 환경변수에서 가져옴)
                try:
                    import os
                    from backend.api.services.schemas.models.core.config import settings
                    api_key = os.getenv('GEMINI_API_KEY') or getattr(settings, 'GEMINI_API_KEY', None)
                    self.__init__(api_key=api_key)
                    if self.model is None or self.model_name is None:
                        raise ValueError("보고서 생성기가 초기화되지 않았습니다. 모델을 다시 선택해주세요.")
                    logger.info(f"✅ 재초기화 완료! 새 모델: {self.model_name}")
                except Exception as init_error:
                    logger.error(f"재초기화 실패: {init_error}")
                    raise ValueError(f"보고서 생성기 재초기화 실패: {init_error}")
            
            prompt = self._build_prompt(report_data)
            
            logger.info(f"Gemini API 호출 중... (모델: {self.model_name})")
            response = self.model.generate_content(prompt)
            
            if not response.text:
                raise ValueError("Gemini API가 빈 응답을 반환했습니다.")
            
            logger.info(f"보고서 생성 완료. 길이: {len(response.text)} 문자")
            return response.text
            
        except Exception as e:
            error_msg = str(e)
            current_model = getattr(self.model, '_model_name', None) or self.model_name or 'unknown'
            logger.exception(f"보고서 생성 중 오류 발생 (모델: {current_model}): {e}")
            
            # 404 모델을 찾을 수 없음 오류 처리
            if "404" in error_msg and "not found" in error_msg.lower():
                # 모델이 없으면 인스턴스를 리셋하고 재시도
                logger.warning(f"모델 '{current_model}'을 찾을 수 없습니다. 보고서 생성기 리셋 후 재초기화 시도...")
                self.model = None
                self.model_name = None
                
                # 새로운 모델로 재초기화 시도
                try:
                    import os
                    from backend.api.services.schemas.models.core.config import settings
                    from backend.api.services.report_generator import reset_report_generator
                    
                    api_key = os.getenv('GEMINI_API_KEY') or getattr(settings, 'GEMINI_API_KEY', None)
                    
                    # 싱글톤 인스턴스 리셋
                    reset_report_generator()
                    
                    # 새 인스턴스 생성
                    new_generator = MOBYReportGenerator(api_key=api_key)
                    self.model = new_generator.model
                    self.model_name = new_generator.model_name
                    logger.info(f"✅ 새로운 모델로 재초기화 완료: {self.model_name}")
                    
                    # 재시도
                    logger.info(f"재시도 중... (새 모델: {self.model_name})")
                    response = self.model.generate_content(prompt)
                    if not response.text:
                        raise ValueError("Gemini API가 빈 응답을 반환했습니다.")
                    logger.info(f"보고서 생성 완료 (재시도 성공). 길이: {len(response.text)} 문자")
                    return response.text
                except Exception as retry_error:
                    logger.error(f"재시도 실패: {retry_error}")
                    raise ValueError(
                        f"Gemini 모델을 찾을 수 없습니다. "
                        f"사용 시도 모델: {current_model}. "
                        f"재시도 후 오류: {retry_error}. "
                        f"서버를 재시작해주세요."
                    )
            
            # 429 할당량 초과 오류 처리
            if "429" in error_msg or "quota" in error_msg.lower() or "rate limit" in error_msg.lower():
                raise ValueError(
                    "Gemini API 할당량이 초과되었습니다. "
                    "잠시 후 다시 시도하거나, Google AI Studio에서 할당량을 확인하세요. "
                    f"오류 상세: {error_msg}"
                )
            
            # 기타 오류
            raise ValueError(f"보고서 생성 중 오류가 발생했습니다 (모델: {current_model}): {error_msg}")
    
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
    """보고서 생성기 인스턴스를 리셋합니다. (모델 변경 시 필요)"""
    global _report_generator
    if _report_generator is not None:
        logger.info("🔄 보고서 생성기 인스턴스 리셋 중... (이전 모델: {})".format(
            getattr(_report_generator, 'model_name', 'unknown')
        ))
    _report_generator = None
    logger.info("✅ 보고서 생성기가 리셋되었습니다. 다음 호출 시 새 모델로 초기화됩니다.")

