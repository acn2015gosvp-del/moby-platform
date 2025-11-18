/**
 * 이미지 프리로더 훅
 * 
 * 이미지를 미리 로드하여 사용자 경험을 개선합니다.
 */

import { useEffect, useState } from 'react'
import { preloadImage } from '@/utils/imageOptimizer'

interface UseImagePreloaderOptions {
  urls: string[]
  onComplete?: () => void
  onError?: (url: string, error: Error) => void
}

export function useImagePreloader({ urls, onComplete, onError }: UseImagePreloaderOptions) {
  const [loadedCount, setLoadedCount] = useState(0)
  const [failedCount, setFailedCount] = useState(0)
  const [isComplete, setIsComplete] = useState(false)

  useEffect(() => {
    if (urls.length === 0) {
      setIsComplete(true)
      onComplete?.()
      return
    }

    let isMounted = true
    let completed = 0
    let failed = 0

    const loadImages = async () => {
      const promises = urls.map(async (url) => {
        try {
          await preloadImage(url)
          if (isMounted) {
            completed++
            setLoadedCount(completed)
          }
        } catch (error) {
          if (isMounted) {
            failed++
            setFailedCount(failed)
            onError?.(url, error as Error)
          }
        }
      })

      await Promise.allSettled(promises)

      if (isMounted) {
        setIsComplete(true)
        onComplete?.()
      }
    }

    loadImages()

    return () => {
      isMounted = false
    }
  }, [urls, onComplete, onError])

  return {
    loadedCount,
    failedCount,
    totalCount: urls.length,
    isComplete,
    progress: urls.length > 0 ? (loadedCount / urls.length) * 100 : 100,
  }
}

