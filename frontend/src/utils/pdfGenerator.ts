/**
 * PDF 생성 유틸리티 (html2pdf.js + marked 버전)
 * 
 * 마크다운을 HTML로 완전히 변환한 후 PDF로 생성합니다.
 * 테이블, 헤더, 리스트 등 모든 마크다운 문법을 지원합니다.
 * 한국어 폰트(Noto Sans KR)가 PDF에 포함되어 한글이 올바르게 표시됩니다.
 */

import html2canvas from 'html2canvas'
import { jsPDF } from 'jspdf'
import { marked } from 'marked'

/**
 * 한국어 폰트를 로드하고 CSS에 추가
 */
function loadKoreanFont(): void {
  // 이미 로드되었는지 확인
  if (document.getElementById('noto-sans-kr-font')) {
    return
  }

  // @font-face 스타일 추가
  const style = document.createElement('style')
  style.id = 'noto-sans-kr-font'
  style.textContent = `
    @font-face {
      font-family: 'Noto Sans KR';
      font-style: normal;
      font-weight: 400;
      src: url('/fonts/NotoSansKR-Regular.ttf') format('truetype');
      font-display: swap;
    }
    
    @font-face {
      font-family: 'Noto Sans KR';
      font-style: normal;
      font-weight: 700;
      src: url('/fonts/NotoSansKR-Bold.ttf') format('truetype');
      font-display: swap;
    }
  `
  document.head.appendChild(style)
}

/**
 * 보고서 텍스트를 PDF로 변환하여 다운로드
 * 
 * @param content 보고서 내용 (마크다운 또는 텍스트)
 * @param filename 다운로드할 파일명 (확장자 제외)
 * @param metadata 보고서 메타데이터 (선택사항)
 */
export async function downloadReportAsPDF(
  content: string,
  filename: string = `MOBY_Report_${new Date().toISOString().slice(0, 10)}`,
  metadata?: {
    period_start?: string
    period_end?: string
    equipment?: string
    generated_at?: string
  }
): Promise<void> {
  try {
    console.log('[PDF] HTML to PDF 변환 시작...', { filename, contentLength: content.length })
    
    // 한국어 폰트 로드
    loadKoreanFont()
    
    // Marked 옵션 설정
    marked.setOptions({
      breaks: true,      // 줄바꿈을 <br>로 변환
      gfm: true,         // GitHub Flavored Markdown 활성화
    })
    
    // 마크다운을 HTML로 변환
    const bodyHtml = await marked.parse(content)
    
    console.log('[PDF] 마크다운 변환 완료, HTML 길이:', bodyHtml.length)
    console.log('[PDF] 원본 콘텐츠 길이:', content.length)
    
    // HTML 컨텐츠 생성
    const htmlContent = `
      <div style="font-family: 'Noto Sans KR', 'Malgun Gothic', sans-serif; padding: 20px; max-width: 210mm; background: white; color: black;">
        <!-- 제목 -->
        <h1 style="text-align: center; font-size: 24px; margin-bottom: 20px; border-bottom: 2px solid #333; padding-bottom: 10px;">
          MOBY Platform 보고서
        </h1>
        
        <!-- 메타데이터 -->
        ${metadata ? `
          <div style="font-size: 12px; margin-bottom: 20px; color: #555; line-height: 1.8;">
            ${metadata.equipment ? `<p style="margin: 5px 0;"><strong>설비:</strong> ${metadata.equipment}</p>` : ''}
            ${metadata.period_start && metadata.period_end ? 
              `<p style="margin: 5px 0;"><strong>보고 기간:</strong> ${metadata.period_start} ~ ${metadata.period_end}</p>` : ''}
            ${metadata.generated_at ? `<p style="margin: 5px 0;"><strong>생성 일시:</strong> ${metadata.generated_at}</p>` : ''}
          </div>
          <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
        ` : ''}
        
        <!-- 본문 -->
        <div style="font-size: 11px; line-height: 1.6;">
          ${bodyHtml}
        </div>
        
        <!-- 스타일 추가 -->
        <style>
          /* 폰트 설정 */
          * {
            font-family: 'Noto Sans KR', 'Malgun Gothic', sans-serif !important;
          }
          
          /* 헤더 스타일 */
          h1 { font-size: 20px; margin-top: 20px; margin-bottom: 10px; color: #333; font-weight: 700; }
          h2 { font-size: 16px; margin-top: 18px; margin-bottom: 8px; color: #444; border-bottom: 1px solid #ddd; padding-bottom: 5px; font-weight: 700; }
          h3 { font-size: 14px; margin-top: 15px; margin-bottom: 6px; color: #555; font-weight: 700; }
          
          /* 단락 스타일 */
          p { margin: 8px 0; }
          
          /* 테이블 스타일 */
          table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
            font-size: 10px;
          }
          
          table th {
            background-color: #f5f5f5;
            border: 1px solid #ddd;
            padding: 8px;
            text-align: center;
            font-weight: 700;
          }
          
          table td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: center;
          }
          
          table tr:nth-child(even) {
            background-color: #fafafa;
          }
          
          /* 리스트 스타일 */
          ul, ol {
            margin: 10px 0;
            padding-left: 20px;
          }
          
          li {
            margin: 5px 0;
          }
          
          /* 강조 스타일 */
          strong {
            font-weight: 700;
            color: #333;
          }
          
          em {
            font-style: italic;
            color: #555;
          }
          
          /* 구분선 */
          hr {
            border: none;
            border-top: 1px solid #ddd;
            margin: 15px 0;
          }
          
          /* 코드 블록 */
          code {
            background-color: #f5f5f5;
            padding: 2px 5px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            font-size: 9px;
          }
          
          pre {
            background-color: #f5f5f5;
            padding: 10px;
            border-radius: 5px;
            overflow-x: auto;
            margin: 10px 0;
          }
          
          pre code {
            padding: 0;
            background-color: transparent;
          }
        </style>
      </div>
    `
    
    // HTML 요소 생성 - 더 간단하고 명확한 구조
    const element = document.createElement('div')
    element.id = 'pdf-export-container'
    element.setAttribute('data-pdf-export', 'true') // 추가 식별자
    element.innerHTML = htmlContent
    
    // 요소를 화면에 보이게 설정 (html2canvas가 캡처할 수 있도록)
    // html2canvas는 화면에 보이는 요소만 캡처할 수 있으므로 화면에 표시해야 함
    element.style.position = 'fixed'
    element.style.left = '0'
    element.style.top = '0'
    element.style.width = '794px' // A4 너비 (210mm = 794px at 96dpi)
    element.style.minHeight = '1123px' // A4 높이 (297mm = 1123px at 96dpi)
    element.style.backgroundColor = 'white'
    element.style.color = 'black'
    element.style.zIndex = '99999'
    element.style.overflow = 'visible'
    element.style.padding = '0'
    element.style.boxSizing = 'border-box'
    element.style.margin = '0'
    element.style.display = 'block'
    element.style.visibility = 'visible'
    
    // 내부 div 스타일 조정
    const innerDiv = element.querySelector('div')
    if (innerDiv) {
      innerDiv.style.margin = '0'
      innerDiv.style.padding = '20px'
      innerDiv.style.display = 'block'
      innerDiv.style.visibility = 'visible'
    }
    
    // 다른 요소들을 임시로 숨기기 (원래 상태 저장)
    const originalBodyChildren: Array<{ element: HTMLElement; display: string; visibility: string; opacity: string }> = []
    Array.from(document.body.children).forEach((child) => {
      if (child.id !== 'pdf-export-container') {
        const htmlChild = child as HTMLElement
        originalBodyChildren.push({
          element: htmlChild,
          display: htmlChild.style.display || '',
          visibility: htmlChild.style.visibility || '',
          opacity: htmlChild.style.opacity || ''
        })
        htmlChild.style.display = 'none'
        htmlChild.style.visibility = 'hidden'
        htmlChild.style.opacity = '0'
      }
    })
    
    // DOM에 추가
    document.body.appendChild(element)
    
    // 요소가 제대로 추가되었는지 확인
    const addedElement = document.getElementById('pdf-export-container')
    if (!addedElement) {
      throw new Error('PDF 컨테이너 요소를 DOM에 추가할 수 없습니다.')
    }
    
    console.log('[PDF] HTML 요소 DOM에 추가 완료')
    console.log('[PDF] 요소 내용 확인:', element.innerHTML.substring(0, 200))
    
    // 폰트 로드 및 렌더링 대기
    await new Promise(resolve => setTimeout(resolve, 1500))
    
    // 폰트 로드 확인
    if (document.fonts && typeof document.fonts.load === 'function') {
      const fontLoaded = await document.fonts.load('400 12px "Noto Sans KR"')
      console.log('[PDF] 폰트 로드 확인:', fontLoaded)
    }
    
    // PDF 생성 및 다운로드
    console.log('[PDF] PDF 생성 시작...')
    console.log('[PDF] 요소 크기:', element.offsetWidth, 'x', element.offsetHeight)
    console.log('[PDF] 요소 ID:', element.id)
    console.log('[PDF] 요소 내용 길이:', element.innerHTML.length)
    
    try {
      // 요소가 제대로 렌더링되었는지 확인
      await new Promise(resolve => setTimeout(resolve, 1500)) // 렌더링 시간 확보
      
      // 요소가 여전히 DOM에 있는지 확인
      const elementInDOM = document.getElementById('pdf-export-container')
      if (!elementInDOM) {
        throw new Error('PDF 컨테이너 요소가 DOM에서 사라졌습니다.')
      }
      
      // 요소가 실제로 화면에 보이는지 확인
      const rect = elementInDOM.getBoundingClientRect()
      console.log('[PDF] 요소 DOM 확인 완료')
      console.log('[PDF] 요소 크기:', elementInDOM.offsetWidth, 'x', elementInDOM.offsetHeight)
      console.log('[PDF] 요소 위치:', rect.left, rect.top, rect.width, rect.height)
      console.log('[PDF] 요소 내용 길이:', elementInDOM.innerHTML.length)
      
      // 요소가 비어있거나 크기가 0이면 오류
      if (elementInDOM.offsetWidth === 0 || elementInDOM.offsetHeight === 0) {
        throw new Error('PDF 컨테이너 요소의 크기가 0입니다. 내용이 렌더링되지 않았습니다.')
      }
      
      if (elementInDOM.innerHTML.length === 0) {
        throw new Error('PDF 컨테이너 요소가 비어있습니다.')
      }
      
      // html2canvas와 jsPDF를 직접 사용하여 PDF 생성
      console.log('[PDF] html2canvas 실행 시작...')
      console.log('[PDF] 요소 참조:', elementInDOM)
      console.log('[PDF] 요소 ID:', elementInDOM.id)
      
      // html2canvas로 캔버스 생성
      const canvas = await html2canvas(elementInDOM, {
        scale: 2,
        useCORS: true,
        logging: false,
        backgroundColor: '#ffffff',
        width: elementInDOM.offsetWidth,
        height: elementInDOM.offsetHeight,
      })
      
      console.log('[PDF] Canvas 생성 완료, 크기:', canvas.width, 'x', canvas.height)
      
      if (canvas.width === 0 || canvas.height === 0) {
        throw new Error('Canvas 크기가 0입니다. 요소가 제대로 렌더링되지 않았습니다.')
      }
      
      // A4 크기 계산 (mm 단위)
      const pdfWidth = 210 // A4 너비 (mm)
      const pdfHeight = 297 // A4 높이 (mm)
      const imgWidth = pdfWidth
      const imgHeight = (canvas.height * pdfWidth) / canvas.width
      
      // jsPDF로 PDF 생성
      const pdf = new jsPDF({
        orientation: imgHeight > pdfHeight ? 'portrait' : 'portrait',
        unit: 'mm',
        format: 'a4'
      })
      
      // Canvas를 이미지로 변환하여 PDF에 추가
      const imgData = canvas.toDataURL('image/png', 1.0)
      
      // PDF 높이가 A4를 초과하면 여러 페이지로 분할
      let heightLeft = imgHeight
      let position = 0
      
      pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight)
      heightLeft -= pdfHeight
      
      while (heightLeft > 0) {
        position = heightLeft - imgHeight
        pdf.addPage()
        pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight)
        heightLeft -= pdfHeight
      }
      
      // PDF 다운로드
      pdf.save(`${filename}.pdf`)
      console.log('[PDF] ✅ PDF 생성 및 다운로드 완료:', filename)
    } catch (pdfError) {
      console.error('[PDF] PDF 생성 중 오류:', pdfError)
      throw pdfError
    } finally {
      // DOM에서 제거
      const elementToRemove = document.getElementById('pdf-export-container')
      if (elementToRemove && elementToRemove.parentNode) {
        elementToRemove.parentNode.removeChild(elementToRemove)
        console.log('[PDF] PDF 컨테이너 요소 제거 완료')
      }
      
      // 다른 요소들 원래 상태로 복원
      originalBodyChildren.forEach(({ element: el, display, visibility, opacity }) => {
        el.style.display = display || ''
        el.style.visibility = visibility || ''
        el.style.opacity = opacity || ''
      })
      console.log('[PDF] 다른 요소들 원래 상태로 복원 완료')
    }
  } catch (error) {
    console.error('[PDF] PDF 생성 중 오류 발생:', error)
    const errorMessage = error instanceof Error ? error.message : String(error)
    throw new Error(`PDF 생성에 실패했습니다: ${errorMessage}`)
  }
}