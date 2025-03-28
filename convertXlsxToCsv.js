import fs from 'fs';
import path from 'path';
import xlsx from 'xlsx';

// === 清洗函数 ===
function cleanText(text) {
  if (typeof text !== 'string') return text;
  return text.replace(/\r/g, '').replace(/_x000d_/g, '');
}

// === 主逻辑 ===
function convertXlsxToCsv(xlsxPath, csvPath, clean = true) {
  if (!fs.existsSync(xlsxPath)) {
    console.error(`❌ File not found: ${xlsxPath}`);
    return;
  }

  const workbook = xlsx.readFile(xlsxPath);
  const sheetName = workbook.SheetNames[0];
  const worksheet = workbook.Sheets[sheetName];

  if (clean) {
    const range = xlsx.utils.decode_range(worksheet['!ref']);
    for (let R = range.s.r; R <= range.e.r; ++R) {
      for (let C = range.s.c; C <= range.e.c; ++C) {
        const cellAddress = xlsx.utils.encode_cell({ r: R, c: C });
        const cell = worksheet[cellAddress];
        if (cell && cell.t === 's' && typeof cell.v === 'string') {
          cell.v = cleanText(cell.v);
        }
      }
    }
  }

  const csvContent = xlsx.utils.sheet_to_csv(worksheet);
  fs.writeFileSync(csvPath, csvContent, 'utf8');
  console.log(`✅ Converted: ${xlsxPath} → ${csvPath}`);
}

// === 调用示例 ===
const inputXlsx = path.resolve('results.xlsx');
const outputCsv = path.resolve('results.csv');
convertXlsxToCsv(inputXlsx, outputCsv);
