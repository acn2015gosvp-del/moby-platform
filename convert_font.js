// convert_font.js

const fs = require('fs');
const path = require('path');

// 폰트 파일의 상대 경로 (moby-platform 폴더를 기준으로 함)
// 이 경로는 이전에 Noto Sans KR 폰트를 저장한 경로와 일치합니다.
const FONT_FILENAME = 'NotoSansKR-Regular.ttf';
const FONT_REL_PATH = path.join('frontend', 'public', 'fonts', FONT_FILENAME);

// Base64 문자열을 저장할 출력 파일 경로
const OUTPUT_FILENAME = 'NotoSansKR_Base64.txt';
const OUTPUT_REL_PATH = path.join('frontend', 'public', OUTPUT_FILENAME);


try {
    // 폰트 파일 읽기
    const fontData = fs.readFileSync(FONT_REL_PATH);
    
    // 데이터를 Base64 문자열로 변환 (jsPDF에 필요한 형식)
    const base64String = fontData.toString('base64');
    
    // Base64 문자열을 파일로 저장하여 쉽게 복사할 수 있게 함
    fs.writeFileSync(OUTPUT_REL_PATH, base64String);

    console.log(`✅ Base64 변환 성공: ${FONT_FILENAME}`);
    console.log(`변환된 데이터가 저장된 경로: ${OUTPUT_REL_PATH}`);
    console.log('\n--- 폰트 데이터 (앞부분) ---');
    console.log(base64String.substring(0, 100) + '...');
    
} catch (error) {
    console.error('❌ 파일 변환 중 오류 발생:', error.message);
    console.log(`다음 경로에 폰트 파일이 있는지 확인하세요: ${FONT_REL_PATH}`);
    console.log('Node.js가 설치되어 있지 않다면 먼저 설치해야 합니다.');
}