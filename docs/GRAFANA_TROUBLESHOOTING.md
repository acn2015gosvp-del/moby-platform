# Grafana 대시보드 로딩 문제 해결 가이드

## 문제 증상
- 모니터링 페이지에서 Grafana 대시보드가 로드되지 않음
- "대시보드 로딩 시간이 초과되었습니다" 에러 메시지 표시

## 가능한 원인 및 해결 방법

### 1. Grafana 서버가 실행 중이지 않음

**확인 방법:**
```bash
# 브라우저에서 직접 접속 시도
http://192.168.80.99:3001
```

**해결 방법:**
- Grafana 서버가 실행 중인지 확인
- Docker를 사용하는 경우: `docker ps | grep grafana`
- 서비스로 실행하는 경우: `systemctl status grafana-server`

### 2. Grafana 설정에서 iframe 임베딩이 차단됨

**확인 방법:**
Grafana 설정 파일(`grafana.ini`) 또는 환경 변수에서 다음 설정 확인:

```ini
[security]
allow_embedding = true
```

**해결 방법:**

#### 방법 1: 설정 파일 수정
1. Grafana 설정 파일 위치 확인:
   - Linux: `/etc/grafana/grafana.ini`
   - Docker: 환경 변수 또는 볼륨 마운트된 설정 파일
   - Windows: Grafana 설치 디렉토리의 `conf/grafana.ini`

2. `[security]` 섹션에 추가:
   ```ini
   [security]
   allow_embedding = true
   ```

3. Grafana 서버 재시작

#### 방법 2: 환경 변수 사용 (Docker)
```bash
docker run -e GF_SECURITY_ALLOW_EMBEDDING=true grafana/grafana
```

#### 방법 3: Grafana UI에서 확인
1. Grafana에 로그인
2. Settings → Security → Allow embedding 체크
3. 저장 후 Grafana 재시작

### 3. 대시보드 UID가 올바르지 않음

**확인 방법:**
1. Grafana에 로그인
2. 대시보드로 이동
3. 대시보드 설정 → General → UID 확인
4. 생성된 URL의 UID와 비교

**예시:**
- 생성된 URL: `http://192.168.80.99:3001/d/conveyor-dashboard/view?...`
- 실제 Grafana 대시보드 UID가 `conveyor-dashboard`와 일치하는지 확인

**해결 방법:**
- 백엔드에서 올바른 `dashboardUID`를 반환하도록 수정
- 또는 Grafana 대시보드 UID를 백엔드 설정과 일치하도록 변경

### 4. CORS 문제

**확인 방법:**
브라우저 콘솔(F12)에서 CORS 관련 에러 확인

**해결 방법:**
Grafana 설정에서 CORS 허용:
```ini
[security]
allow_embedding = true
cors_allow_origin = *
```

또는 특정 도메인만 허용:
```ini
cors_allow_origin = http://localhost:5173,http://192.168.80.99:5173
```

## 빠른 진단 방법

### 1. "새 창에서 열기" 버튼 클릭
- 모니터링 페이지의 에러 메시지에서 "새 창에서 열기 (권장)" 버튼 클릭
- URL이 새 창에서 열림
- **새 창에서 대시보드가 정상적으로 표시되면**: iframe 임베딩 설정 문제
- **새 창에서도 대시보드가 표시되지 않으면**: Grafana 서버 또는 대시보드 UID 문제

### 2. 브라우저 콘솔 확인
1. F12 키를 눌러 개발자 도구 열기
2. Console 탭에서 에러 메시지 확인
3. Network 탭에서 실패한 요청 확인

### 3. Grafana 서버 직접 접속
```
http://192.168.80.99:3001
```
- Grafana 로그인 페이지가 표시되면 서버는 정상
- 연결이 안 되면 서버가 실행 중이지 않음

## 생성된 URL 확인

모니터링 페이지의 에러 메시지에 생성된 URL이 표시됩니다:
```
http://192.168.80.99:3001/d/conveyor-dashboard/view?orgId=1&from=now-1h&to=now&refresh=30s&kiosk=tv&var-device_id=conveyor-belt-1
```

이 URL을 브라우저 주소창에 직접 입력하여 테스트할 수 있습니다.

## 일반적인 해결 순서

1. ✅ Grafana 서버가 실행 중인지 확인
2. ✅ Grafana 설정에서 `allow_embedding = true` 확인
3. ✅ 대시보드 UID가 올바른지 확인
4. ✅ "새 창에서 열기"로 URL 직접 테스트
5. ✅ 브라우저 콘솔에서 네트워크 에러 확인

## 추가 리소스

- [Grafana 공식 문서 - Embedding](https://grafana.com/docs/grafana/latest/setup-grafana/configure-security/configure-authentication/allow-embedding/)
- [Grafana 설정 파일 참조](https://grafana.com/docs/grafana/latest/setup-grafana/configure-grafana/)

