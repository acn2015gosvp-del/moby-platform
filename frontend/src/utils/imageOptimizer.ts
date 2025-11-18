/**
 * 이미지 최적화 유틸리티
 * 
 * 이미지 URL 변환, 크기 조정, 포맷 변환 등의 유틸리티 함수
 */

/**
 * 이미지 URL에 크기 파라미터 추가
 * 
 * @param url 원본 이미지 URL
 * @param width 원하는 너비
 * @param height 원하는 높이 (선택)
 * @returns 최적화된 이미지 URL
 */
export function optimizeImageUrl(
  url: string,
  width?: number,
  height?: number
): string {
  if (!width && !height) {
    return url
  }

  // URL 파라미터 추가 (실제 구현 시 이미지 서비스에 맞게 조정)
  const params = new URLSearchParams()
  if (width) params.set('w', width.toString())
  if (height) params.set('h', height.toString())
  params.set('q', '80') // 품질 설정

  const separator = url.includes('?') ? '&' : '?'
  return `${url}${separator}${params.toString()}`
}

/**
 * WebP 포맷 지원 여부 확인
 */
export function supportsWebP(): boolean {
  if (typeof window === 'undefined') {
    return false
  }

  const canvas = document.createElement('canvas')
  canvas.width = 1
  canvas.height = 1
  return canvas.toDataURL('image/webp').indexOf('data:image/webp') === 0
}

/**
 * 최적의 이미지 포맷 선택
 * 
 * @param baseUrl 기본 이미지 URL
 * @returns 최적의 포맷 URL
 */
export function getOptimalImageFormat(baseUrl: string): string {
  if (supportsWebP()) {
    // WebP 포맷으로 변환 (실제 구현 시 이미지 서비스에 맞게 조정)
    return baseUrl.replace(/\.(jpg|jpeg|png)$/i, '.webp')
  }
  return baseUrl
}

/**
 * 반응형 이미지 srcset 생성
 * 
 * @param baseUrl 기본 이미지 URL
 * @param sizes 크기 배열
 * @returns srcset 문자열
 */
export function generateSrcSet(baseUrl: string, sizes: number[]): string {
  return sizes
    .map((size) => `${optimizeImageUrl(baseUrl, size)} ${size}w`)
    .join(', ')
}

/**
 * 이미지 프리로드
 * 
 * @param url 이미지 URL
 */
export function preloadImage(url: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const img = new Image()
    img.onload = () => resolve()
    img.onerror = reject
    img.src = url
  })
}

/**
 * 이미지 크기 조정 (클라이언트 사이드)
 * 
 * @param file 이미지 파일
 * @param maxWidth 최대 너비
 * @param maxHeight 최대 높이
 * @param quality 품질 (0-1)
 * @returns 최적화된 Blob
 */
export async function resizeImage(
  file: File,
  maxWidth: number,
  maxHeight: number,
  quality: number = 0.8
): Promise<Blob> {
  return new Promise((resolve, reject) => {
    const img = new Image()
    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d')

    if (!ctx) {
      reject(new Error('Canvas context not available'))
      return
    }

    img.onload = () => {
      // 비율 유지하며 크기 계산
      let width = img.width
      let height = img.height

      if (width > maxWidth) {
        height = (height * maxWidth) / width
        width = maxWidth
      }

      if (height > maxHeight) {
        width = (width * maxHeight) / height
        height = maxHeight
      }

      canvas.width = width
      canvas.height = height

      // 이미지 그리기
      ctx.drawImage(img, 0, 0, width, height)

      // Blob으로 변환
      canvas.toBlob(
        (blob) => {
          if (blob) {
            resolve(blob)
          } else {
            reject(new Error('Failed to create blob'))
          }
        },
        file.type || 'image/jpeg',
        quality
      )
    }

    img.onerror = reject
    img.src = URL.createObjectURL(file)
  })
}

