const fs = require('fs').promises;
const path = require('path');
const { log, getJSTDateTime } = require('./logger');

/**
 * SNSディレクトリから投稿ファイルを取得
 */
async function getSnsFiles(snsDir = null) {
  try {
    if (!snsDir) {
      snsDir = path.join(process.cwd(), 'sns');
    }

    // ディレクトリの存在確認
    try {
      await fs.access(snsDir);
    } catch (error) {
      log(`SNSディレクトリが存在しません: ${snsDir}`, 'WARN');
      return [];
    }

    const files = await fs.readdir(snsDir);
    const txtFiles = files.filter(file => file.endsWith('.txt') && file !== 'README.txt');
    
    const fileList = [];
    for (const file of txtFiles) {
      const filePath = path.join(snsDir, file);
      try {
        const stats = await fs.stat(filePath);
        if (stats.isFile()) {
          const content = await fs.readFile(filePath, 'utf8');
          fileList.push({
            name: file,
            path: filePath,
            content: content.trim(),
            size: stats.size,
            modified: stats.mtime
          });
        }
      } catch (error) {
        log(`ファイル読み込みエラー: ${file} - ${error.message}`, 'WARN');
      }
    }

    // ファイル名でソート（安定した順序のため）
    fileList.sort((a, b) => a.name.localeCompare(b.name));
    
    log(`${fileList.length}件の投稿ファイルを検出`);
    return fileList;
  } catch (error) {
    log(`ファイル取得エラー: ${error.message}`, 'ERROR');
    throw error;
  }
}

/**
 * ファイル内容の検証
 */
function validateFileContent(content, filename) {
  const errors = [];
  
  if (!content || content.trim().length === 0) {
    errors.push(`空のファイル: ${filename}`);
    return errors;
  }

  // UTF-8文字数カウント（コードポイントベース）
  const codePoints = [...content];
  if (codePoints.length > 280) {
    log(`文字数超過: ${filename} (${codePoints.length}文字)`, 'WARN');
  }

  // 制御文字チェック
  const hasControlChars = /[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/.test(content);
  if (hasControlChars) {
    errors.push(`制御文字が含まれています: ${filename}`);
  }

  return errors;
}

/**
 * 全ファイルを検証
 */
async function lintFiles(snsDir = null) {
  const files = await getSnsFiles(snsDir);
  const results = [];

  log('\n=== ファイル検証開始 ===');

  for (const file of files) {
    const errors = validateFileContent(file.content, file.name);
    const codePoints = [...file.content];
    
    results.push({
      file: file.name,
      valid: errors.length === 0,
      errors,
      charCount: codePoints.length,
      size: file.size
    });

    if (errors.length === 0) {
      log(`✓ ${file.name} (${codePoints.length}文字)`);
    } else {
      log(`✗ ${file.name}:`, 'ERROR');
      errors.forEach(error => log(`  - ${error}`, 'ERROR'));
    }
  }

  const totalFiles = results.length;
  const validFiles = results.filter(r => r.valid).length;
  const invalidFiles = totalFiles - validFiles;

  log(`\n=== 検証結果 ===`);
  log(`総件数: ${totalFiles}`);
  log(`正常: ${validFiles}`);
  log(`エラー: ${invalidFiles}`);

  return results;
}

/**
 * 投稿後にファイルを移動
 */
async function moveToPosted(filePath, success = true, postedDirPath = null) {
  try {
    const filename = path.basename(filePath);
    const snsDir = path.dirname(filePath);

    // postedディレクトリのパス決定
    let postedDir;
    if (postedDirPath) {
      // 絶対パスの場合はそのまま、相対パスの場合はプロジェクトルートからの相対
      postedDir = path.isAbsolute(postedDirPath)
        ? postedDirPath
        : path.join(process.cwd(), postedDirPath);
    } else {
      // 従来の動作（投稿元ディレクトリ内のpostedフォルダ）
      postedDir = path.join(snsDir, 'posted');
    }
    
    // postedディレクトリの作成
    await fs.mkdir(postedDir, { recursive: true });

    // 新しいファイル名を生成
    const timestamp = new Date().toISOString()
      .replace(/:/g, '-')
      .replace(/\.\d{3}Z$/, '')
      .replace('T', '_');
    
    const baseName = filename.replace(/\.txt$/, '');
    const suffix = success ? 'posted' : 'failed';
    const newFilename = `${baseName}_${suffix}_${timestamp}.txt`;
    const newPath = path.join(postedDir, newFilename);

    // ファイル移動
    await fs.rename(filePath, newPath);
    
    log(`ファイル移動: ${filename} -> posted/${newFilename}`);
    return newPath;
  } catch (error) {
    log(`ファイル移動エラー: ${error.message}`, 'ERROR');
    throw error;
  }
}

/**
 * バックアップ作成
 */
async function createBackup(filePath) {
  try {
    const backupPath = filePath + '.bak';
    await fs.copyFile(filePath, backupPath);
    return backupPath;
  } catch (error) {
    log(`バックアップ作成エラー: ${error.message}`, 'WARN');
    return null;
  }
}

module.exports = {
  getSnsFiles,
  validateFileContent,
  lintFiles,
  moveToPosted,
  createBackup
};