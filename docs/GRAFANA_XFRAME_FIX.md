# Grafana X-Frame-Options 에러 해결 가이드

## 문제 증상

```
Refused to display 'http://192.168.80.99:8080/' in a frame because it set 'X-Frame-Options' to 'deny'.
```

직접 URL 접속은 성공하지만 iframe에서 로드되지 않습니다.

## 해결 방법

### 방법 1: Grafana 설정 파일 수정 (권장)

#### 1.1 설정 파일 위치 찾기

**Docker (볼륨 마운트):**
```bash
# 1. Grafana 컨테이너 이름 확인
docker ps | grep grafana

# 2. 볼륨 마운트 경로 확인
docker inspect <grafana-container-name> | grep -A 10 Mounts

# 3. 호스트에서 볼륨 경로 확인 (Windows)
docker volume inspect grafana-storage

# 4. 설정 파일 경로 (일반적인 경우)
# Windows: \\wsl$\docker-desktop-data\data\docker\volumes\<volume-name>\_data\grafana.ini
# Linux: /var/lib/docker/volumes/<volume-name>/_data/grafana.ini
```

**Linux (일반 설치):**
```bash
/etc/grafana/grafana.ini
```

**Windows (일반 설치):**
```
C:\Program Files\GrafanaLabs\grafana\conf\grafana.ini
```

#### 1.2 설정 파일 수정 (볼륨 마운트된 경우)

**Docker 볼륨에서 설정 파일 수정:**

1. **볼륨 경로 찾기:**
   ```bash
   # Windows (WSL2 사용 시)
   docker volume inspect grafana-storage
   # 출력에서 Mountpoint 확인
   # 예: /var/lib/docker/volumes/grafana-storage/_data
   
   # Windows에서 접근
   # \\wsl$\docker-desktop-data\data\docker\volumes\grafana-storage\_data
   ```

2. **설정 파일 편집:**
   - 위 경로에서 `grafana.ini` 파일 찾기
   - 파일이 없으면 생성
   - `[security]` 섹션 추가 또는 수정:
     ```ini
     [security]
     allow_embedding = true
     ```

3. **또는 컨테이너 내부에서 수정:**
   ```bash
   # 컨테이너 내부 접속
   docker exec -it grafana sh
   
   # 설정 파일 편집
   vi /etc/grafana/grafana.ini
   # 또는
   echo "[security]" >> /etc/grafana/grafana.ini
   echo "allow_embedding = true" >> /etc/grafana/grafana.ini
   ```

**전체 예시:**
```ini
[security]
# Allow embedding Grafana in other websites
allow_embedding = true

# Set to true if you want to allow browsers to render Grafana in a <frame>, <iframe>, <embed> or <object>
# allow_embedding = false
```

#### 1.3 Grafana 서버 재시작

**Docker:**
```bash
docker restart grafana
```

**Linux (systemd):**
```bash
sudo systemctl restart grafana-server
```

**Windows:**
- 서비스 관리자에서 Grafana 서비스 재시작
- 또는 PowerShell에서:
```powershell
Restart-Service Grafana
```

### 방법 2: 환경 변수로 설정 (Docker) - 가장 간단한 방법

Docker를 사용하는 경우 환경 변수로 설정하는 것이 가장 간단합니다.

#### 2.1 docker-compose.yml 수정

`docker-compose.yml` 파일을 열고 Grafana 서비스에 환경 변수 추가:

```yaml
services:
  grafana:
    image: grafana/grafana
    environment:
      - GF_SECURITY_ALLOW_EMBEDDING=true
    # ... 기타 설정
```

#### 2.2 Docker 명령어로 실행하는 경우

```bash
docker run -e GF_SECURITY_ALLOW_EMBEDDING=true grafana/grafana
```

#### 2.3 기존 컨테이너에 환경 변수 추가

```bash
# 1. 컨테이너 중지
docker stop grafana

# 2. 컨테이너 재생성 (환경 변수 추가)
docker run -d \
  --name grafana \
  -e GF_SECURITY_ALLOW_EMBEDDING=true \
  -v grafana-storage:/var/lib/grafana \
  -p 8080:3000 \
  grafana/grafana
```

**주의:** 볼륨 데이터를 유지하려면 `-v` 옵션을 포함해야 합니다.

### 방법 3: Grafana UI에서 설정 (일부 버전)

일부 Grafana 버전에서는 UI에서 설정할 수 있습니다:

1. Grafana에 로그인
2. Administration → Settings → Security
3. "Allow embedding" 체크
4. 저장 후 재시작

**주의:** 이 방법은 모든 Grafana 버전에서 지원되지 않을 수 있습니다.

## 확인 방법

### 1. 설정 확인

Grafana 서버 재시작 후 다음 명령으로 확인:

```bash
curl -I http://192.168.80.99:8080
```

응답 헤더에 `X-Frame-Options: SAMEORIGIN` 또는 헤더가 없어야 합니다.
`X-Frame-Options: DENY`가 있으면 설정이 적용되지 않은 것입니다.

### 2. 브라우저에서 테스트

다음 HTML 파일을 만들어 테스트:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Grafana Embed Test</title>
</head>
<body>
    <h1>Grafana Dashboard Embed Test</h1>
    <iframe 
        src="http://192.168.80.99:8080/d/my6g9qv/coneyor-sensor?orgId=1&from=now-5m&to=now&timezone=browser&var-var_field=Temperature"
        width="100%" 
        height="800px"
        frameborder="0">
    </iframe>
</body>
</html>
```

브라우저에서 이 파일을 열어 대시보드가 표시되는지 확인합니다.

### 3. 브라우저 콘솔 확인

F12를 눌러 개발자 도구를 열고 Console 탭에서 에러 메시지를 확인합니다.

## 문제 해결 체크리스트

- [ ] `grafana.ini` 파일에 `allow_embedding = true` 추가
- [ ] Grafana 서버 재시작 완료
- [ ] 브라우저 캐시 삭제 (Ctrl+Shift+Delete)
- [ ] 페이지 새로고침 (F5)
- [ ] 직접 URL 접속 테스트 (성공해야 함)
- [ ] iframe 임베딩 테스트 (성공해야 함)

## 추가 참고사항

### Public Dashboard 사용

Public Dashboard을 사용하면 인증 없이 임베딩할 수 있습니다:

1. Grafana에 로그인
2. 대시보드 선택
3. 대시보드 설정 (⚙️) → Sharing → Public Dashboard
4. "Generate public URL" 클릭
5. 생성된 Public Dashboard URL 사용

Public Dashboard URL 형식:
```
http://192.168.80.99:8080/public-dashboards/...
```

### CORS 설정 (필요시)

다른 도메인에서 접근하는 경우 CORS 설정도 필요할 수 있습니다:

```ini
[security]
allow_embedding = true
cors_allow_origin = http://localhost:5173,http://192.168.80.99:5173
```

## 참고 자료

- [Grafana 공식 문서 - Allow Embedding](https://grafana.com/docs/grafana/latest/setup-grafana/configure-security/configure-authentication/allow-embedding/)
- [Grafana 설정 파일 참조](https://grafana.com/docs/grafana/latest/setup-grafana/configure-grafana/)

