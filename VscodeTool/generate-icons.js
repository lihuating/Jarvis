const sharp = require('sharp');
const fs = require('fs');
const path = require('path');

async function createIcon(size, outputPath) {
  // 创建一个简单的渐变圆形图标
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${size} ${size}">
      <defs>
        <linearGradient id="grad${size}" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" style="stop-color:#4CAF50;stop-opacity:1" />
          <stop offset="100%" style="stop-color:#2196F3;stop-opacity:1" />
        </linearGradient>
      </defs>
      <circle cx="${size/2}" cy="${size/2}" r="${size/2 - 2}" fill="url(#grad${size})"/>
      <text x="${size/2}" y="${size * 0.65}" font-family="Arial, sans-serif" font-size="${size * 0.5}" font-weight="bold" fill="white" text-anchor="middle">J</text>
    </svg>
  `;

  await sharp(Buffer.from(svg))
    .png()
    .toFile(outputPath);
  
  console.log(`Created ${outputPath}`);
}

async function main() {
  const mediaDir = path.join(__dirname, 'media');
  
  // 确保 media 目录存在
  if (!fs.existsSync(mediaDir)) {
    fs.mkdirSync(mediaDir, { recursive: true });
  }

  // 生成 128x128 图标
  await createIcon(128, path.join(mediaDir, 'jarvis-128.png'));
  
  // 生成 24x24 activitybar 图标
  await createIcon(24, path.join(mediaDir, 'jarvis-activitybar.png'));
  
  console.log('All icons generated successfully!');
}

main().catch(console.error);
