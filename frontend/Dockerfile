# MOBY Platform Frontend Dockerfile
# Multi-stage build for optimized production image

# Stage 1: Build stage
FROM node:20-alpine as builder

WORKDIR /app

# package.json과 package-lock.json 복사
COPY package*.json ./

# 의존성 설치
RUN npm ci

# 소스 코드 복사
COPY . .

# 프로덕션 빌드
RUN npm run build

# Stage 2: Production stage
FROM nginx:alpine

# 빌드된 파일을 nginx로 복사
COPY --from=builder /app/dist /usr/share/nginx/html

# nginx 설정 파일 복사 (선택사항)
# COPY nginx.conf /etc/nginx/nginx.conf

# 포트 노출
EXPOSE 80

# nginx 실행
CMD ["nginx", "-g", "daemon off;"]

