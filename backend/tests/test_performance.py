"""
성능 테스트 및 벤치마크

API 응답 시간, 동시 요청 처리 등을 테스트합니다.
"""

import pytest
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
from fastapi.testclient import TestClient
from typing import List, Dict
import statistics


class TestPerformance:
    """성능 테스트 클래스"""
    
    def test_single_request_latency(self, client: TestClient):
        """단일 요청 응답 시간 테스트"""
        start_time = time.time()
        response = client.get("/")
        end_time = time.time()
        
        latency = (end_time - start_time) * 1000  # ms로 변환
        
        assert response.status_code == 200
        assert latency < 100  # 100ms 이하
        
        print(f"\n단일 요청 응답 시간: {latency:.2f}ms")
    
    def test_concurrent_requests(self, client: TestClient):
        """동시 요청 처리 테스트"""
        num_requests = 10
        num_threads = 5
        
        def make_request():
            start = time.time()
            response = client.get("/")
            end = time.time()
            return {
                "status": response.status_code,
                "latency": (end - start) * 1000
            }
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(make_request) for _ in range(num_requests)]
            results = [future.result() for future in futures]
        
        # 모든 요청이 성공했는지 확인
        assert all(r["status"] == 200 for r in results)
        
        # 응답 시간 통계
        latencies = [r["latency"] for r in results]
        avg_latency = statistics.mean(latencies)
        max_latency = max(latencies)
        min_latency = min(latencies)
        
        print(f"\n동시 요청 ({num_requests}개, {num_threads} 스레드):")
        print(f"  평균 응답 시간: {avg_latency:.2f}ms")
        print(f"  최소 응답 시간: {min_latency:.2f}ms")
        print(f"  최대 응답 시간: {max_latency:.2f}ms")
        
        # 평균 응답 시간이 500ms 이하인지 확인
        assert avg_latency < 500
    
    def test_sensor_data_endpoint_performance(self, client: TestClient):
        """센서 데이터 엔드포인트 성능 테스트"""
        sensor_data = {
            "device_id": "perf_test_sensor",
            "temperature": 25.5,
            "humidity": 60.0,
            "vibration": 0.5,
            "sound": 45.0
        }
        
        # 여러 요청의 응답 시간 측정
        latencies = []
        num_requests = 20
        
        for _ in range(num_requests):
            start = time.time()
            response = client.post("/sensors/data", json=sensor_data)
            end = time.time()
            
            assert response.status_code in [200, 202, 429]  # 429도 허용 (rate limit)
            if response.status_code != 429:  # rate limit이 아닌 경우만 측정
                latencies.append((end - start) * 1000)
            # Rate limit 방지를 위한 짧은 딜레이 추가
            time.sleep(0.05)  # 50ms 딜레이
        
        # latencies가 비어있지 않은 경우에만 통계 계산
        if latencies:
            avg_latency = statistics.mean(latencies)
            if len(latencies) >= 20:
                p95_latency = statistics.quantiles(latencies, n=20)[18]  # 95th percentile
            else:
                p95_latency = max(latencies)  # 데이터가 적으면 최대값 사용
            
            print(f"\n센서 데이터 엔드포인트 성능 ({num_requests}개 요청, {len(latencies)}개 성공):")
            print(f"  평균 응답 시간: {avg_latency:.2f}ms")
            print(f"  95th percentile: {p95_latency:.2f}ms")
            
            # 평균 응답 시간이 1초 이하인지 확인
            assert avg_latency < 1000
        else:
            # 모든 요청이 rate limit에 걸린 경우 테스트 스킵
            pytest.skip("All requests hit rate limit, skipping performance test")
    
    def test_alert_evaluation_performance(self, client: TestClient, auth_headers):
        """알림 평가 엔드포인트 성능 테스트"""
        alert_data = {
            "vector": [3.0, 4.0, 5.0],
            "threshold": 5.0,
            "sensor_id": "perf_test_sensor",
            "enable_llm_summary": False  # LLM 요약 비활성화로 성능 테스트
        }
        
        latencies = []
        num_requests = 10
        
        for _ in range(num_requests):
            start = time.time()
            response = client.post("/alerts/evaluate", json=alert_data, headers=auth_headers)
            end = time.time()
            
            assert response.status_code in [200, 201, 204]  # 204도 허용 (이상 없음)
            latencies.append((end - start) * 1000)
        
        avg_latency = statistics.mean(latencies)
        
        print(f"\n알림 평가 엔드포인트 성능 ({num_requests}개 요청):")
        print(f"  평균 응답 시간: {avg_latency:.2f}ms")
        
        # 평균 응답 시간이 2초 이하인지 확인
        assert avg_latency < 2000
    
    def test_throughput(self, client: TestClient):
        """처리량(Throughput) 테스트"""
        sensor_data = {
            "device_id": "throughput_test",
            "temperature": 25.5,
            "humidity": 60.0
        }
        
        num_requests = 50
        duration = 5  # 초
        
        start_time = time.time()
        successful_requests = 0
        
        while time.time() - start_time < duration:
            response = client.post("/sensors/data", json=sensor_data)
            if response.status_code in [200, 202]:
                successful_requests += 1
            # Rate limit 방지를 위한 짧은 딜레이 추가
            time.sleep(0.05)  # 50ms 딜레이
        
        actual_duration = time.time() - start_time
        throughput = successful_requests / actual_duration
        
        print(f"\n처리량 테스트 ({actual_duration:.2f}초):")
        print(f"  성공한 요청 수: {successful_requests}")
        print(f"  처리량: {throughput:.2f} requests/second")
        
        # 초당 최소 5개 요청 처리 가능한지 확인
        assert throughput >= 5

