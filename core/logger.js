const fs = require('fs').promises;
const path = require('path');

/**
 * ログレベル
 */
const LOG_LEVELS = {
  INFO: 'INFO',
  WARN: 'WARN',
  ERROR: 'ERROR'
};

/**
 * JST日時文字列を取得
 */
function getJSTDateTime() {
  const now = new Date();
  const jst = new Date(now.toLocaleString("en-US", {timeZone: "Asia/Tokyo"}));
  return jst.toISOString().replace('T', ' ').replace(/\.\d{3}Z$/, ' JST');
}

/**
 * ログメッセージを出力
 */
function log(message, level = LOG_LEVELS.INFO) {
  const timestamp = getJSTDateTime();
  const logMessage = `[${timestamp}] [${level}] ${message}`;
  console.log(logMessage);
  return logMessage;
}

/**
 * ログをファイルに保存
 */
async function saveLog(message, filename = null) {
  try {
    if (!filename) {
      const date = new Date().toISOString().split('T')[0];
      filename = `log_${date}.txt`;
    }
    
    const logPath = path.join(process.cwd(), 'logs', filename);
    await fs.mkdir(path.dirname(logPath), { recursive: true });
    await fs.appendFile(logPath, message + '\n', 'utf8');
  } catch (error) {
    console.error('ログ保存エラー:', error.message);
  }
}

/**
 * 実行結果の要約を生成
 */
function generateSummary(results) {
  const summary = {
    total: results.length,
    success: results.filter(r => r.success).length,
    failed: results.filter(r => !r.success).length,
    skipped: results.filter(r => r.skipped).length
  };

  const summaryMessage = [
    `\n=== 実行結果要約 ===`,
    `総件数: ${summary.total}`,
    `成功: ${summary.success}`,
    `失敗: ${summary.failed}`,
    `スキップ: ${summary.skipped}`,
    `実行時刻: ${getJSTDateTime()}`
  ].join('\n');

  log(summaryMessage);
  return summary;
}

module.exports = {
  log,
  saveLog,
  generateSummary,
  getJSTDateTime,
  LOG_LEVELS
};