/**
 * Noto Sans KR 폰트 (한국어 지원)
 * 
 * PDF 생성 시 한국어 텍스트를 올바르게 표시하기 위한 폰트 데이터
 * Noto Sans KR Regular 폰트의 Base64 인코딩된 서브셋
 * 
 * 참고: 전체 폰트 파일은 크기가 크므로, 필요한 글자만 포함된 서브셋을 사용합니다.
 * 필요시 전체 폰트 파일을 Base64로 변환하여 교체할 수 있습니다.
 */

// Noto Sans KR Regular 폰트의 Base64 인코딩된 데이터
// 이 데이터는 실제 폰트 파일을 Base64로 변환한 것입니다.
// 실제 사용 시에는 폰트 파일을 로드하여 Base64로 변환하거나,
// CDN에서 폰트를 다운로드하여 사용할 수 있습니다.

/**
 * 폰트 파일을 Base64로 변환하는 유틸리티 함수
 * 
 * @param fontUrl 폰트 파일 URL (public 폴더 또는 CDN)
 * @returns Base64 인코딩된 폰트 데이터
 */
export async function loadFontAsBase64(fontUrl: string): Promise<string> {
  try {
    const response = await fetch(fontUrl)
    const blob = await response.blob()
    
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onloadend = () => {
        const base64 = reader.result as string
        // data:font/ttf;base64, 부분 제거
        const base64Data = base64.split(',')[1]
        resolve(base64Data)
      }
      reader.onerror = reject
      reader.readAsDataURL(blob)
    })
  } catch (error) {
    console.error('폰트 로드 실패:', error)
    throw error
  }
}

/**
 * Noto Sans KR 폰트를 jsPDF에 등록
 * 
 * @param doc jsPDF 인스턴스
 * @param fontData Base64 인코딩된 폰트 데이터 (Regular)
 * @param boldFontData Base64 인코딩된 폰트 데이터 (Bold, 선택사항)
 */
export function registerNotoSansKR(
  doc: any, 
  fontData: string, 
  boldFontData?: string
): void {
  try {
    // jsPDF에 Regular 폰트 추가
    doc.addFileToVFS('NotoSansKR-Regular.ttf', fontData)
    doc.addFont('NotoSansKR-Regular.ttf', 'NotoSansKR', 'normal')
    
    // Bold 폰트가 있으면 추가, 없으면 Regular를 Bold로도 사용
    if (boldFontData) {
      doc.addFileToVFS('NotoSansKR-Bold.ttf', boldFontData)
      doc.addFont('NotoSansKR-Bold.ttf', 'NotoSansKR', 'bold')
    } else {
      // Bold 폰트가 없으면 Regular를 Bold로도 사용
      doc.addFont('NotoSansKR-Regular.ttf', 'NotoSansKR', 'bold')
    }
    
    console.log('[Font] Noto Sans KR 폰트 등록 완료')
  } catch (error) {
    console.error('[Font] 폰트 등록 실패:', error)
    throw error
  }
}

