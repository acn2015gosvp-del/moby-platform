#!/bin/bash
# 프론트엔드 상태 확인 스크립트

echo "=== 프론트엔드 상태 확인 ==="
echo ""

# 포트 5173 확인
echo "1. 포트 5173 상태:"
netstat -ano | findstr :5173 || echo "포트 5173이 열려있지 않습니다."

echo ""
echo "2. Node 프로세스:"
Get-Process -Name node -ErrorAction SilentlyContinue | Select-Object Id, ProcessName, StartTime | Format-Table

echo ""
echo "3. 프론트엔드 디렉토리 확인:"
if [ -d "frontend" ]; then
    echo "✅ frontend 디렉토리 존재"
    if [ -f "frontend/package.json" ]; then
        echo "✅ package.json 존재"
    else
        echo "❌ package.json 없음"
    fi
    if [ -f "frontend/vite.config.ts" ]; then
        echo "✅ vite.config.ts 존재"
    else
        echo "❌ vite.config.ts 없음"
    fi
else
    echo "❌ frontend 디렉토리 없음"
fi

echo ""
echo "=== 확인 완료 ==="

