/**
 * 최적화된 이미지 컴포넌트
 * 
 * 레이지 로딩, 플레이스홀더, 에러 처리 등을 포함한 이미지 컴포넌트
 */

import { useState, useRef, useEffect, type ImgHTMLAttributes } from 'react'

interface OptimizedImageProps extends Omit<ImgHTMLAttributes<HTMLImageElement>, 'loading'> {
  src: string
  alt: string
  placeholder?: string
  fallback?: string
  lazy?: boolean
  aspectRatio?: string
}

export function OptimizedImage({
  src,
  alt,
  placeholder,
  fallback = '/placeholder.png',
  lazy = true,
  aspectRatio,
  className = '',
  ...props
}: OptimizedImageProps) {
  const [imageSrc, setImageSrc] = useState<string>(placeholder || src)
  const [isLoaded, setIsLoaded] = useState(false)
  const [hasError, setHasError] = useState(false)
  const imgRef = useRef<HTMLImageElement>(null)

  useEffect(() => {
    // Intersection Observer를 사용한 레이지 로딩
    if (!lazy || !imgRef.current) {
      return
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const img = entry.target as HTMLImageElement
            if (img.dataset.src) {
              img.src = img.dataset.src
              img.removeAttribute('data-src')
            }
            observer.unobserve(img)
          }
        })
      },
      { rootMargin: '50px' }
    )

    observer.observe(imgRef.current)

    return () => {
      if (imgRef.current) {
        observer.unobserve(imgRef.current)
      }
    }
  }, [lazy])

  const handleLoad = () => {
    setIsLoaded(true)
    if (placeholder && imageSrc === placeholder) {
      setImageSrc(src)
    }
  }

  const handleError = () => {
    setHasError(true)
    if (fallback && imageSrc !== fallback) {
      setImageSrc(fallback)
    }
  }

  const containerStyle: React.CSSProperties = {
    position: 'relative',
    overflow: 'hidden',
    ...(aspectRatio && { aspectRatio }),
  }

  return (
    <div style={containerStyle} className={className}>
      <img
        ref={imgRef}
        src={lazy ? undefined : imageSrc}
        data-src={lazy ? imageSrc : undefined}
        alt={alt}
        loading={lazy ? 'lazy' : 'eager'}
        onLoad={handleLoad}
        onError={handleError}
        className={`
          w-full h-full object-cover
          transition-opacity duration-300
          ${isLoaded ? 'opacity-100' : 'opacity-0'}
          ${hasError ? 'opacity-50' : ''}
        `}
        {...props}
      />
      {!isLoaded && !hasError && placeholder && (
        <div className="absolute inset-0 bg-gray-200 animate-pulse flex items-center justify-center">
          <span className="text-gray-400 text-sm">로딩 중...</span>
        </div>
      )}
      {hasError && (
        <div className="absolute inset-0 bg-gray-100 flex items-center justify-center">
          <span className="text-gray-400 text-sm">이미지를 불러올 수 없습니다</span>
        </div>
      )}
    </div>
  )
}

