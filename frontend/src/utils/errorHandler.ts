/**
 * 에러 처리 유틸리티
 * 
 * 백엔드에서 오는 다양한 형식의 에러를 일관된 문자열로 변환합니다.
 */

/**
 * API 에러를 사용자 친화적인 메시지로 변환
 * 
 * @param err - Axios 에러 객체 또는 일반 에러
 * @param defaultMessage - 기본 에러 메시지
 * @returns 사용자 친화적인 에러 메시지 문자열
 */
export const extractErrorMessage = (err: any, defaultMessage: string = '오류가 발생했습니다.'): string => {
  if (!err) {
    return defaultMessage
  }

  // Axios 에러 응답이 있는 경우
  if (err.response?.data) {
    const data = err.response.data

    // ErrorResponse 형식: { success: false, error: { message: "...", code: "...", field: "..." } }
    if (data.error?.message) {
      return data.error.message
    }

    // Pydantic 검증 에러 (배열): { detail: [{ type, loc, msg, input, ctx }, ...] }
    if (Array.isArray(data.detail)) {
      return data.detail
        .map((e: any) => {
          // msg 필드가 있으면 사용
          if (e.msg) {
            const field = e.loc && e.loc.length > 1 ? e.loc[e.loc.length - 1] : ''
            return field ? `${field}: ${e.msg}` : e.msg
          }
          // msg가 없으면 객체를 문자열로 변환
          return JSON.stringify(e)
        })
        .join(', ')
    }

    // 단일 detail 문자열: { detail: "..." }
    if (typeof data.detail === 'string') {
      return data.detail
    }

    // 객체인 경우 문자열로 변환 (디버깅용)
    if (data.detail && typeof data.detail === 'object') {
      return JSON.stringify(data.detail)
    }

    // message 필드가 있는 경우
    if (data.message) {
      return data.message
    }
  }

  // 일반 에러 메시지
  if (err.message) {
    return err.message
  }

  return defaultMessage
}

