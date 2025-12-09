"""
LLM 기반 보고서 생성 서비스 모듈

Gemini API를 사용하여 주간/일일 보고서를 자동 생성합니다.
"""

import logging
import json
import os
import time
import re
from datetime import datetime, date
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session

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
                        'max_output_tokens': 8192,  # 토큰 한도 증가
                    }
                )
                
                # 모델이 실제로 작동하는지 간단한 테스트 요청
                test_response = test_model.generate_content("test")
                
                # 안전하게 테스트 응답 확인
                test_text = None
                try:
                    if hasattr(test_response, 'text') and test_response.text:
                        test_text = test_response.text
                    elif hasattr(test_response, 'candidates') and test_response.candidates:
                        candidate = test_response.candidates[0]
                        if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                            parts = candidate.content.parts
                            if parts and hasattr(parts[0], 'text'):
                                test_text = parts[0].text
                
                except AttributeError:
                    # response.text 접근 실패 시 candidates에서 추출 시도
                    if hasattr(test_response, 'candidates') and test_response.candidates:
                        candidate = test_response.candidates[0]
                        if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                            parts = candidate.content.parts
                            if parts and hasattr(parts[0], 'text'):
                                test_text = parts[0].text
                
                if test_text:
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
                
                # API 키 정지 상태 감지
                if "CONSUMER_SUSPENDED" in error_msg or "has been suspended" in error_msg.lower():
                    # 첫 번째 정지 오류 발견 시 즉시 중단하고 명확한 메시지 반환
                    api_key_masked = api_key[:10] + "..." if api_key and len(api_key) > 10 else "***"
                    raise ValueError(
                        f"🚫 Gemini API 키가 정지되었습니다.\n\n"
                        f"**문제**: API 키가 Google에 의해 정지되었습니다.\n"
                        f"**원인**: 할당량 초과, 정책 위반, 또는 보안 문제일 수 있습니다.\n\n"
                        f"**해결 방법**:\n"
                        f"1. Google AI Studio (https://makersuite.google.com/app/apikey)에 접속\n"
                        f"2. 새로운 API 키 생성 또는 기존 키 상태 확인\n"
                        f"3. .env 파일의 GEMINI_API_KEY 값을 새 API 키로 업데이트\n"
                        f"4. 백엔드 서버 재시작\n\n"
                        f"**참고**: 현재 사용 중인 API 키: {api_key_masked}\n"
                        f"상세 오류: {error_msg[:200]}"
                    )
                
                # 429 할당량 초과 오류는 모델 초기화 단계에서는 재시도하지 않고 다음 모델로 넘어감
                # (할당량이 초과된 경우 다른 모델도 동일한 할당량을 공유하므로)
                if "429" in error_msg or "quota" in error_msg.lower() or "exceeded" in error_msg.lower():
                    logger.warning(f"⚠️ 모델 '{model_name}' 할당량 초과. 다음 모델 시도...")
                
                continue
        
        if self.model is None:
            # API 키 정지 상태가 이미 감지되었는지 확인
            has_suspended_error = any("CONSUMER_SUSPENDED" in err or "has been suspended" in err.lower() for err in errors)
            
            if has_suspended_error:
                # 정지 오류가 있으면 이미 위에서 처리되었을 것이지만, 안전장치
                api_key_masked = api_key[:10] + "..." if api_key and len(api_key) > 10 else "***"
                raise ValueError(
                    f"🚫 Gemini API 키가 정지되었습니다.\n\n"
                    f"**해결 방법**:\n"
                    f"1. Google AI Studio (https://makersuite.google.com/app/apikey)에서 새 API 키 생성\n"
                    f"2. .env 파일의 GEMINI_API_KEY 업데이트\n"
                    f"3. 백엔드 서버 재시작\n\n"
                    f"**현재 API 키**: {api_key_masked}"
                )
            
            error_summary = "\n".join([f"  - {err}" for err in errors])
            raise ValueError(
                f"사용 가능한 Gemini 모델을 찾을 수 없습니다.\n\n"
                f"시도한 모델들:\n{error_summary}\n\n"
                f"API 키와 할당량을 확인하세요. "
                f"Google AI Studio (https://makersuite.google.com/app/apikey)에서 API 키 상태를 확인하세요."
            )
        
        logger.info(f"✅ MOBYReportGenerator 초기화 완료! 사용 모델: {self.model_name}")
    
    def _summarize_data_for_prompt(self, data: Dict[str, Any]) -> str:
        """프롬프트 크기를 줄이기 위해 데이터를 요약합니다."""
        try:
            # 센서 통계 요약 (핵심 필드만)
            sensor_stats_summary = {}
            for key, value in data.get("sensor_stats", {}).items():
                if isinstance(value, dict):
                    # 핵심 필드만 추출
                    summary = {}
                    
                    # 첫 번째 값이 dict인지 확인 (중첩 구조 감지)
                    first_value = next(iter(value.values()), None) if value else None
                    if isinstance(first_value, dict):
                        # 중첩된 구조 (진동, 가속도, 자이로: x, y, z 축)
                        for axis_key, axis_value in value.items():
                            if isinstance(axis_value, dict):
                                axis_summary = {}
                                for k in ["mean", "max", "min", "peak", "rms", "std", "p95"]:
                                    if k in axis_value:
                                        axis_summary[k] = axis_value[k]
                                if axis_summary:
                                    summary[axis_key] = axis_summary
                    else:
                        # 단순 구조 (온도, 습도, 음압, 기압)
                        for k in ["mean", "max", "min", "threshold_violations", "std", "p95"]:
                            if k in value:
                                summary[k] = value[k]
                    
                    if summary:
                        sensor_stats_summary[key] = summary
                else:
                    sensor_stats_summary[key] = value
            
            # 요약된 데이터 구성
            summarized = {
                "metadata": data.get("metadata", {}),
                "sensor_stats": sensor_stats_summary,
                "alarms_count": len(data.get("alarms", [])),
                "alarms_sample": data.get("alarms", [])[:10],  # 최대 10개만
                "mlp_anomalies_count": len(data.get("mlp_anomalies", [])),
                "mlp_anomalies_sample": data.get("mlp_anomalies", [])[:5],  # 최대 5개만
                "if_anomalies_count": len(data.get("if_anomalies", [])),
                "if_anomalies_sample": data.get("if_anomalies", [])[:5],  # 최대 5개만
                "correlations": data.get("correlations", {})
            }
            
            return json.dumps(summarized, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"데이터 요약 실패, 전체 데이터 사용: {e}")
            # 요약 실패 시 전체 데이터 사용 (안전장치)
            return json.dumps(data, indent=2, ensure_ascii=False)
    
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
            
            start_time = time.time()
            logger.info(f"Gemini API 호출 중... (모델: {self.model_name}, 최적화된 설정: max_tokens=8192)")
            
            # 429 오류 재시도 로직
            max_retries = 3
            retry_count = 0
            response = None
            last_error = None
            
            while retry_count < max_retries:
                try:
                    response = self.model.generate_content(
                        prompt,
                        generation_config={
                            "max_output_tokens": 8192,
                            "temperature": 0.7,
                        }
                    )
                    # 성공 시 루프 종료
                    break
                    
                except Exception as e:
                    error_msg = str(e)
                    last_error = e
                    
                    # 429 할당량 초과 오류 감지
                    is_quota_error = (
                        "429" in error_msg or 
                        "quota" in error_msg.lower() or 
                        "rate limit" in error_msg.lower() or 
                        "exceeded" in error_msg.lower()
                    )
                    
                    if is_quota_error and retry_count < max_retries - 1:
                        # retry_delay 파싱
                        retry_seconds = None
                        retry_match = re.search(r'retry in ([\d.]+)s', error_msg, re.IGNORECASE)
                        if retry_match:
                            retry_seconds = float(retry_match.group(1))
                        else:
                            # 기본 대기 시간 (20초)
                            retry_seconds = 20.0
                        
                        retry_count += 1
                        wait_time = min(retry_seconds + 2, 60)  # 최대 60초까지 대기
                        logger.warning(
                            f"⚠️ Gemini API 할당량 초과 (시도 {retry_count}/{max_retries}). "
                            f"{wait_time:.1f}초 후 재시도합니다..."
                        )
                        time.sleep(wait_time)
                        continue
                    else:
                        # 429가 아니거나 최대 재시도 횟수 초과
                        if "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
                            raise ValueError(f"Gemini API 호출 시간 초과 (60초): {error_msg}")
                        raise
            
            elapsed_time = time.time() - start_time
            
            # 안전하게 응답 텍스트 추출
            response_text = None
            try:
                # 먼저 response.text를 시도 (일반적인 경우)
                if hasattr(response, 'text') and response.text:
                    response_text = response.text
                elif hasattr(response, 'candidates') and response.candidates:
                    # candidates에서 텍스트 추출
                    for candidate in response.candidates:
                        if hasattr(candidate, 'content') and candidate.content:
                            if hasattr(candidate.content, 'parts'):
                                parts_text = []
                                for part in candidate.content.parts:
                                    if hasattr(part, 'text') and part.text:
                                        parts_text.append(part.text)
                                if parts_text:
                                    response_text = ''.join(parts_text)
                                    break
                        elif hasattr(candidate, 'parts'):
                            # 직접 parts가 있는 경우
                            parts_text = []
                            for part in candidate.parts:
                                if hasattr(part, 'text') and part.text:
                                    parts_text.append(part.text)
                            if parts_text:
                                response_text = ''.join(parts_text)
                                break
                
                if not response_text:
                    # finish_reason 확인
                    finish_reason = None
                    if hasattr(response, 'candidates') and response.candidates:
                        finish_reason = getattr(response.candidates[0], 'finish_reason', None)
                    
                    error_detail = f"응답에 유효한 텍스트가 없습니다."
                    if finish_reason:
                        error_detail += f" finish_reason: {finish_reason}"
                    
                    logger.error(f"Gemini API 응답 처리 실패: {error_detail}")
                    logger.error(f"응답 구조: candidates={hasattr(response, 'candidates')}, text={hasattr(response, 'text')}")
                    
                    raise ValueError(f"Gemini API가 빈 응답을 반환했습니다. {error_detail}")
                
            except AttributeError as ae:
                # response.text 접근 시 발생하는 AttributeError 처리
                logger.error(f"Gemini API 응답 구조 오류: {ae}")
                logger.error(f"응답 타입: {type(response)}, 속성: {dir(response)}")
                
                # 대체 방법으로 텍스트 추출 시도
                if hasattr(response, 'candidates') and response.candidates:
                    try:
                        candidate = response.candidates[0]
                        if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                            parts = candidate.content.parts
                            if parts and hasattr(parts[0], 'text'):
                                response_text = parts[0].text
                            else:
                                raise ValueError(f"응답에 유효한 Part가 없습니다. finish_reason: {getattr(candidate, 'finish_reason', 'unknown')}")
                        else:
                            raise ValueError(f"응답 구조가 예상과 다릅니다: {type(candidate)}")
                    except Exception as e:
                        raise ValueError(f"Gemini API 응답 처리 실패: {str(e)}")
                else:
                    raise ValueError(f"Gemini API 응답에 candidates가 없습니다. 응답 타입: {type(response)}")
            
            # 재시도가 있었는지 로깅
            if retry_count > 0:
                logger.info(f"✅ 보고서 생성 완료 (재시도 {retry_count}회 후 성공, 소요 시간: {elapsed_time:.2f}초, 길이: {len(response_text)} 문자, 모델: {self.model_name})")
            else:
                logger.info(f"✅ 보고서 생성 완료 (소요 시간: {elapsed_time:.2f}초, 길이: {len(response_text)} 문자, 모델: {self.model_name})")
            return response_text
            
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
                    
                    # 안전하게 응답 텍스트 추출 (위와 동일한 로직)
                    response_text = None
                    try:
                        if hasattr(response, 'text') and response.text:
                            response_text = response.text
                        elif hasattr(response, 'candidates') and response.candidates:
                            for candidate in response.candidates:
                                if hasattr(candidate, 'content') and candidate.content:
                                    if hasattr(candidate.content, 'parts'):
                                        parts_text = []
                                        for part in candidate.content.parts:
                                            if hasattr(part, 'text') and part.text:
                                                parts_text.append(part.text)
                                        if parts_text:
                                            response_text = ''.join(parts_text)
                                            break
                    
                    except AttributeError as ae:
                        logger.error(f"재시도 중 응답 처리 오류: {ae}")
                        if hasattr(response, 'candidates') and response.candidates:
                            candidate = response.candidates[0]
                            if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                                parts = candidate.content.parts
                                if parts and hasattr(parts[0], 'text'):
                                    response_text = parts[0].text
                    
                    if not response_text:
                        raise ValueError("Gemini API가 빈 응답을 반환했습니다 (재시도).")
                    
                    logger.info(f"보고서 생성 완료 (재시도 성공). 길이: {len(response_text)} 문자")
                    return response_text
                except Exception as retry_error:
                    logger.error(f"재시도 실패: {retry_error}")
                    raise ValueError(
                        f"Gemini 모델을 찾을 수 없습니다. "
                        f"사용 시도 모델: {current_model}. "
                        f"재시도 후 오류: {retry_error}. "
                        f"서버를 재시작해주세요."
                    )
            
            # 429 할당량 초과 오류 처리
            if "429" in error_msg or "quota" in error_msg.lower() or "rate limit" in error_msg.lower() or "exceeded" in error_msg.lower():
                # 할당량 초과 상세 정보 추출
                retry_seconds = None
                if "retry_delay" in error_msg or "retry in" in error_msg.lower():
                    import re
                    retry_match = re.search(r'retry in ([\d.]+)s', error_msg, re.IGNORECASE)
                    if retry_match:
                        retry_seconds = float(retry_match.group(1))
                
                quota_info = ""
                is_free_tier = False
                if "free_tier" in error_msg.lower() or "free tier" in error_msg.lower() or "limit: 20" in error_msg:
                    quota_info = " (무료 티어 일일 한도: 20회)"
                    is_free_tier = True
                elif "limit: 0" in error_msg:
                    quota_info = " (Free tier에서 이 모델 사용 불가)"
                elif "limit:" in error_msg:
                    import re
                    limit_match = re.search(r'limit:\s*(\d+)', error_msg)
                    if limit_match:
                        limit = limit_match.group(1)
                        quota_info = f" (일일 한도: {limit}회)"
                
                retry_info = ""
                if retry_seconds:
                    retry_minutes = int(retry_seconds // 60)
                    retry_secs = int(retry_seconds % 60)
                    if retry_minutes > 0:
                        retry_info = f"\n⏰ 재시도 가능 시간: 약 {retry_minutes}분 {retry_secs}초 후"
                    else:
                        retry_info = f"\n⏰ 재시도 가능 시간: 약 {retry_secs}초 후"
                
                # 사용자 친화적인 에러 메시지 생성
                if is_free_tier:
                    error_detail = (
                        f"⚠️ Gemini API 무료 티어 할당량 초과\n\n"
                        f"**현재 상황**:\n"
                        f"- 무료 티어 일일 요청 한도(20회)를 초과했습니다.\n"
                        f"- 오늘 더 이상 보고서를 생성할 수 없습니다.{retry_info}\n\n"
                        f"**해결 방법**:\n"
                        f"1. 내일 다시 시도하세요 (할당량이 자동으로 리셋됩니다).\n"
                        f"2. Google AI Studio에서 유료 플랜으로 업그레이드하세요.\n"
                        f"3. 할당량 사용량 확인: https://ai.dev/usage?tab=rate-limit\n\n"
                        f"**참고**:\n"
                        f"- 할당량 정책: https://ai.google.dev/gemini-api/docs/rate-limits"
                    )
                else:
                    error_detail = (
                        f"⚠️ Gemini API 할당량 초과\n\n"
                        f"**현재 상황**:\n"
                        f"- API 요청 할당량을 초과했습니다.{quota_info}{retry_info}\n\n"
                        f"**해결 방법**:\n"
                        f"1. 할당량이 리셋될 때까지 기다리세요.{retry_info}\n"
                        f"2. Google AI Studio에서 할당량을 확인하세요.\n"
                        f"3. 할당량 사용량 확인: https://ai.dev/usage?tab=rate-limit\n\n"
                        f"**참고**:\n"
                        f"- 할당량 정책: https://ai.google.dev/gemini-api/docs/rate-limits"
                    )
                
                raise ValueError(error_detail)
            
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
**중요: 간결하고 핵심적인 내용만 작성하세요. 불필요한 반복이나 장황한 설명을 피하세요.**

1. **Executive Summary**: 2-3문장으로 핵심 발견사항 요약
   - 주요 센서 상관관계
   - 이상 탐지 건수 및 심각도
   - 즉시 조치 필요 여부
   
2. **센서별 통계**: 제공된 수치를 표로 정리 (간결하게)
   - **필수**: 주어진 sensor_stats의 수치를 그대로 사용하여 마크다운 표를 작성하라.
   - **온도/습도/음압**: mean, min, max, std, p95 값을 모두 표에 포함하라.
   - **진동 데이터**: X, Y, Z축의 mean, peak(절댓값 최대), rms(Root Mean Square)를 반드시 구분하여 표기하라.
   - **데이터가 0이거나 미미하더라도**: '정상 범위 내 작동'으로 해석하여 보고서를 작성하고, 빈 표를 만들지 마라.
   - **"데이터 없음" 또는 "통계 데이터 없음"이라고 표시하지 마라.** 모든 센서에 대해 표를 작성하라.
   - 임계값 초과 시 **굵은 글씨**로 강조
   
3. **이상 탐지 상세**: 각 이상에 대해 (핵심만)
   - 발생 시각 및 유형
   - **물리적 해석**: 왜 이 패턴이 발생했는지, 설비 관점에서 간단히 설명
   - 구체적 권장 조치 (1-2줄)
   - 원시 데이터 JSON은 중요한 경우만 포함
   
4. **상관 분석 인사이트**: 
   - 센서 간 관계의 **공학적 의미** 해석 (간결하게)
   - 시간적 패턴 분석 (핵심만)
   - 근본 원인 추론 (간단히)
   
5. **권장 사항**: 우선순위별 분류 (High/Medium/Ongoing) - 각 항목 1-2줄

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

# 입력 데이터 (요약 버전 - 핵심 정보만 포함하여 프롬프트 크기 최소화)
```json
{self._summarize_data_for_prompt(data)}
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

| 센서 | Mean | Min | Max | Std | P95 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 온도 | [sensor_stats.temperature.mean 값 사용] | [sensor_stats.temperature.min 값 사용] | [sensor_stats.temperature.max 값 사용] | [sensor_stats.temperature.std 값 사용] | [sensor_stats.temperature.p95 값 사용] |
| 습도 | [sensor_stats.humidity.mean 값 사용] | [sensor_stats.humidity.min 값 사용] | [sensor_stats.humidity.max 값 사용] | [sensor_stats.humidity.std 값 사용] | [sensor_stats.humidity.p95 값 사용] |

### 2.2 진동 (Vibration - MPU6050)

| 축 | Mean | Peak (절댓값 최대) | RMS (Root Mean Square) |
| :--- | :--- | :--- | :--- |
| X | [sensor_stats.vibration.x.mean 값 사용] | [sensor_stats.vibration.x.peak 값 사용] | [sensor_stats.vibration.x.rms 값 사용] |
| Y | [sensor_stats.vibration.y.mean 값 사용] | [sensor_stats.vibration.y.peak 값 사용] | [sensor_stats.vibration.y.rms 값 사용] |
| Z | [sensor_stats.vibration.z.mean 값 사용] | [sensor_stats.vibration.z.peak 값 사용] | [sensor_stats.vibration.z.rms 값 사용] |

### 2.3 가속도 (Acceleration - MPU-6050)

| 축 | Mean | Min | Max | Std | P95 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| X | [sensor_stats.acceleration.x.mean 값 사용] | [sensor_stats.acceleration.x.min 값 사용] | [sensor_stats.acceleration.x.max 값 사용] | [sensor_stats.acceleration.x.std 값 사용] | [sensor_stats.acceleration.x.p95 값 사용] |
| Y | [sensor_stats.acceleration.y.mean 값 사용] | [sensor_stats.acceleration.y.min 값 사용] | [sensor_stats.acceleration.y.max 값 사용] | [sensor_stats.acceleration.y.std 값 사용] | [sensor_stats.acceleration.y.p95 값 사용] |
| Z | [sensor_stats.acceleration.z.mean 값 사용] | [sensor_stats.acceleration.z.min 값 사용] | [sensor_stats.acceleration.z.max 값 사용] | [sensor_stats.acceleration.z.std 값 사용] | [sensor_stats.acceleration.z.p95 값 사용] |

### 2.4 자이로 (Gyro - MPU-6050)

| 축 | Mean | Min | Max | Std | P95 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| X | [sensor_stats.gyro.x.mean 값 사용] | [sensor_stats.gyro.x.min 값 사용] | [sensor_stats.gyro.x.max 값 사용] | [sensor_stats.gyro.x.std 값 사용] | [sensor_stats.gyro.x.p95 값 사용] |
| Y | [sensor_stats.gyro.y.mean 값 사용] | [sensor_stats.gyro.y.min 값 사용] | [sensor_stats.gyro.y.max 값 사용] | [sensor_stats.gyro.y.std 값 사용] | [sensor_stats.gyro.y.p95 값 사용] |
| Z | [sensor_stats.gyro.z.mean 값 사용] | [sensor_stats.gyro.z.min 값 사용] | [sensor_stats.gyro.z.max 값 사용] | [sensor_stats.gyro.z.std 값 사용] | [sensor_stats.gyro.z.p95 값 사용] |

**중요**: 가속도와 자이로 테이블은 반드시 마크다운 표 형식으로 작성하세요. HTML 태그를 직접 사용하지 마세요. 마크다운 표가 자동으로 HTML `<table>` 태그로 변환됩니다.

### 2.5 음압 (Sound)

| 센서 | Mean | Min | Max | Std | P95 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 음압 | [sensor_stats.sound.mean 값 사용] | [sensor_stats.sound.min 값 사용] | [sensor_stats.sound.max 값 사용] | [sensor_stats.sound.std 값 사용] | [sensor_stats.sound.p95 값 사용] |

### 2.6 기압 (Pressure)

| 센서 | Mean | Min | Max | Std | P95 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 기압 | [sensor_stats.pressure.mean 값 사용] | [sensor_stats.pressure.min 값 사용] | [sensor_stats.pressure.max 값 사용] | [sensor_stats.pressure.std 값 사용] | [sensor_stats.pressure.p95 값 사용] |

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


def generate_daily_alert_report_text(db: Session, target_date: Optional[date] = None) -> str:
    """
    금일 발생한 알림을 조회하여 보고서 텍스트를 생성합니다.
    
    Args:
        db: 데이터베이스 세션
        target_date: 조회할 날짜 (없으면 오늘)
        
    Returns:
        생성된 보고서 텍스트 (마크다운 형식)
    """
    from backend.api.services.alert_history_service import get_today_alerts
    
    try:
        if target_date is None:
            target_date = date.today()
        
        # 금일 알림 조회
        alerts = get_today_alerts(db, target_date)
        
        if not alerts:
            return f"# 📊 MOBY 일일 이상징후 보고서\n\n**보고 날짜:** {target_date}\n\n**발생한 이상징후가 없습니다.** ✅\n"
        
        # 보고서 텍스트 생성
        report_lines = [
            f"# 📊 MOBY 일일 이상징후 보고서",
            f"",
            f"**보고 날짜:** {target_date}",
            f"**총 발생 건수:** {len(alerts)}건",
            f"",
            f"---",
            f"",
            f"## 발생한 이상징후 목록",
            f"",
        ]
        
        # 미확인 알림 수 계산
        unchecked_count = sum(1 for alert in alerts if alert.check_status.value == "UNCHECKED")
        if unchecked_count > 0:
            report_lines.append(f"⚠️ **미확인 알림:** {unchecked_count}건")
            report_lines.append(f"")
        
        # 알림별 상세 정보
        for idx, alert in enumerate(alerts, 1):
            status_icon = "❌" if alert.check_status.value == "UNCHECKED" else "✅"
            report_lines.extend([
                f"### {idx}. {status_icon} {alert.message}",
                f"",
                f"- **디바이스 ID:** {alert.device_id}",
                f"- **발생 시각:** {alert.occurred_at.strftime('%Y-%m-%d %H:%M:%S')}",
            ])
            
            if alert.error_code:
                report_lines.append(f"- **에러 코드:** {alert.error_code}")
            
            if alert.raw_value:
                try:
                    raw_data = json.loads(alert.raw_value)
                    report_lines.append(f"- **원시 데이터:** `{json.dumps(raw_data, ensure_ascii=False)[:100]}...`")
                except:
                    report_lines.append(f"- **원시 데이터:** `{alert.raw_value[:100]}...`")
            
            if alert.check_status.value == "CHECKED" and alert.checked_by:
                report_lines.append(f"- **확인자:** {alert.checked_by}")
            
            report_lines.append(f"")
        
        # 요약
        report_lines.extend([
            f"---",
            f"",
            f"## 요약",
            f"",
            f"- 총 발생 건수: **{len(alerts)}건**",
            f"- 미확인 건수: **{unchecked_count}건**",
            f"- 확인 완료 건수: **{len(alerts) - unchecked_count}건**",
        ])
        
        report_text = "\n".join(report_lines)
        
        logger.info(f"✅ 일일 알림 보고서 텍스트 생성 완료. 날짜: {target_date}, 건수: {len(alerts)}")
        
        return report_text
        
    except Exception as e:
        logger.error(
            f"❌ 일일 알림 보고서 생성 실패. 날짜: {target_date}, 오류: {e}",
            exc_info=True
        )
        return f"# ❌ 보고서 생성 실패\n\n날짜: {target_date}\n오류: {str(e)}"


def generate_daily_alert_report_html(db: Session, target_date: Optional[date] = None) -> str:
    """
    금일 발생한 알림을 조회하여 HTML 형식의 보고서를 생성합니다.
    
    Args:
        db: 데이터베이스 세션
        target_date: 조회할 날짜 (없으면 오늘)
        
    Returns:
        생성된 HTML 보고서
    """
    try:
        import markdown
    except ImportError:
        logger.warning("markdown 라이브러리가 설치되지 않았습니다. 마크다운 형식으로 반환합니다.")
        # markdown이 없으면 마크다운 텍스트를 그대로 반환
        markdown_text = generate_daily_alert_report_text(db, target_date)
        # 간단한 HTML 변환
        html = markdown_text.replace('\n', '<br>').replace('**', '<strong>').replace('**', '</strong>')
        return f'<div style="font-family: sans-serif; padding: 20px;">{html}</div>'
    
    # 마크다운 텍스트 생성
    markdown_text = generate_daily_alert_report_text(db, target_date)
    
    # HTML로 변환
    html = markdown.markdown(markdown_text, extensions=['extra', 'codehilite'])
    
    return html


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

