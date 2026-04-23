#!/usr/bin/env node

/**
 * JSX 语法测试脚本
 * 用于验证 DecisionSimulationPage.tsx 的 JSX 结构是否正确
 */

const fs = require('fs');
const path = require('path');

console.log('🔍 开始检查 JSX 语法...\n');

const filePath = path.join(__dirname, 'web/src/pages/DecisionSimulationPage.tsx');

if (!fs.existsSync(filePath)) {
  console.error('❌ 文件不存在:', filePath);
  process.exit(1);
}

const content = fs.readFileSync(filePath, 'utf-8');
const lines = content.split('\n');

console.log('📊 文件统计:');
console.log(`   总行数: ${lines.length}`);
console.log(`   文件大小: ${(content.length / 1024).toFixed(2)} KB\n`);

// 检查关键区域的括号匹配
console.log('🔎 检查关键区域 (line 1820-2100):\n');

let issues = [];
let bracketStack = [];
let braceStack = [];
let parenStack = [];

// 检查 1820-2100 行的括号匹配
for (let i = 1819; i < Math.min(2100, lines.length); i++) {
  const line = lines[i];
  const lineNum = i + 1;
  
  // 跳过注释和字符串内的括号
  let inString = false;
  let inComment = false;
  let stringChar = '';
  
  for (let j = 0; j < line.length; j++) {
    const char = line[j];
    const nextChar = line[j + 1];
    
    // 处理注释
    if (!inString && char === '/' && nextChar === '/') {
      inComment = true;
      break;
    }
    
    // 处理字符串
    if ((char === '"' || char === "'" || char === '`') && (j === 0 || line[j-1] !== '\\')) {
      if (!inString) {
        inString = true;
        stringChar = char;
      } else if (char === stringChar) {
        inString = false;
        stringChar = '';
      }
    }
    
    if (inString || inComment) continue;
    
    // 检查括号
    if (char === '{') {
      braceStack.push({ line: lineNum, col: j + 1, context: line.trim().substring(0, 50) });
    } else if (char === '}') {
      if (braceStack.length === 0) {
        issues.push(`Line ${lineNum}: 多余的 '}' - ${line.trim()}`);
      } else {
        braceStack.pop();
      }
    } else if (char === '(') {
      parenStack.push({ line: lineNum, col: j + 1, context: line.trim().substring(0, 50) });
    } else if (char === ')') {
      if (parenStack.length === 0) {
        issues.push(`Line ${lineNum}: 多余的 ')' - ${line.trim()}`);
      } else {
        parenStack.pop();
      }
    }
  }
}

// 检查特定的问题行
const line1827 = lines[1826]?.trim() || '';
const line1923 = lines[1922]?.trim() || '';
const line1925 = lines[1924]?.trim() || '';

console.log('📍 关键行检查:');
console.log(`   Line 1827: ${line1827.substring(0, 80)}`);
console.log(`   Line 1923: ${line1923}`);
console.log(`   Line 1925: ${line1925.substring(0, 80)}\n`);

// 检查条件渲染模式
const wsPhasePattern = /wsPhase === 'done' && canRenderPersonas &&/;
const canRenderPattern = /\{canRenderPersonas \?/;

let wsPhaseMatches = [];
let canRenderMatches = [];

for (let i = 1819; i < Math.min(2100, lines.length); i++) {
  const line = lines[i];
  const lineNum = i + 1;
  
  if (wsPhasePattern.test(line)) {
    wsPhaseMatches.push({ line: lineNum, content: line.trim() });
  }
  if (canRenderPattern.test(line)) {
    canRenderMatches.push({ line: lineNum, content: line.trim() });
  }
}

console.log('🎯 条件渲染检查:');
console.log(`   wsPhase === 'done' && canRenderPersonas 出现次数: ${wsPhaseMatches.length}`);
wsPhaseMatches.forEach(m => console.log(`      Line ${m.line}: ${m.content.substring(0, 60)}`));

console.log(`\n   {canRenderPersonas ? 出现次数: ${canRenderMatches.length}`);
canRenderMatches.forEach(m => console.log(`      Line ${m.line}: ${m.content.substring(0, 60)}`));

console.log('\n');

// 输出问题
if (issues.length > 0) {
  console.log('❌ 发现问题:\n');
  issues.forEach(issue => console.log(`   ${issue}`));
  console.log('');
}

if (braceStack.length > 0) {
  console.log('⚠️  未闭合的大括号 {}:\n');
  braceStack.forEach(b => console.log(`   Line ${b.line}, Col ${b.col}: ${b.context}`));
  console.log('');
}

if (parenStack.length > 0) {
  console.log('⚠️  未闭合的小括号 ():\n');
  parenStack.forEach(p => console.log(`   Line ${p.line}, Col ${p.col}: ${p.context}`));
  console.log('');
}

// 最终结果
if (issues.length === 0 && braceStack.length === 0 && parenStack.length === 0) {
  console.log('✅ JSX 语法检查通过！\n');
  console.log('💡 建议: 运行 npm run build 进行完整验证\n');
  process.exit(0);
} else {
  console.log('❌ JSX 语法检查失败\n');
  console.log('💡 建议: 检查上述问题并修复\n');
  process.exit(1);
}
