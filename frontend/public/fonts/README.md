# 폰트 파일 배치 안내

PDF 생성 시 한국어가 올바르게 표시되도록 하려면, 이 폴더에 Noto Sans KR 폰트 파일을 배치해야 합니다.

## 폰트 파일 다운로드

1. Google Fonts에서 Noto Sans KR 다운로드:
   - https://fonts.google.com/noto/specimen/Noto+Sans+KR
   - "Download family" 버튼 클릭

2. 압축 해제 후 다음 파일을 이 폴더에 복사:
   - `NotoSansKR-Regular.ttf` (일반 텍스트용)
   - `NotoSansKR-Bold.ttf` (굵은 텍스트용, 선택사항)

## 파일 구조

```
frontend/
  public/
    fonts/
      NotoSansKR-Regular.ttf  ← 이 파일을 배치
      NotoSansKR-Bold.ttf      ← 선택사항
```

## 대안: 온라인 폰트 사용

폰트 파일을 배치하지 않으면, 코드에서 GitHub의 폰트 파일을 다운로드하려고 시도합니다.
하지만 CORS 정책으로 인해 실패할 수 있으므로, 로컬 파일 사용을 권장합니다.

## 라이선스

Noto Sans KR은 SIL Open Font License 1.1 하에 배포되는 무료 폰트입니다.
상업적 사용이 가능합니다.

