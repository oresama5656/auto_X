const { log } = require('./logger');

/**
 * JST基準で日付操作
 */
function getJSTDate(date = null) {
  const baseDate = date ? new Date(date) : new Date();
  return new Date(baseDate.toLocaleString("en-US", {timeZone: "Asia/Tokyo"}));
}

/**
 * 日付文字列をJSTのDateオブジェクトに変換
 */
function parseJSTDate(dateString) {
  if (dateString === 'auto') return null;
  
  // YYYY-MM-DD形式の場合、JSTとして解釈
  if (/^\d{4}-\d{2}-\d{2}$/.test(dateString)) {
    const [year, month, day] = dateString.split('-').map(Number);
    return new Date(year, month - 1, day); // Dateコンストラクタはローカルタイムゾーン
  }
  
  return new Date(dateString);
}

/**
 * 週末判定
 */
function isWeekend(date) {
  const day = date.getDay();
  return day === 0 || day === 6; // 日曜日(0)または土曜日(6)
}

/**
 * 投稿時刻を計算
 */
function calculatePostTime(config, baseDate) {
  const { postTime, autoTimeOffset } = config.posting;
  
  if (postTime === 'auto') {
    // 現在時刻 + オフセット分
    const now = getJSTDate();
    return new Date(now.getTime() + autoTimeOffset * 60 * 1000);
  } else if (typeof postTime === 'string' && postTime.includes(':')) {
    // HH:MM形式
    const [hours, minutes] = postTime.split(':').map(Number);
    const targetDate = new Date(baseDate);
    targetDate.setHours(hours, minutes, 0, 0);
    return targetDate;
  }
  
  throw new Error(`無効な投稿時刻設定: ${postTime}`);
}

/**
 * スケジュール計算
 */
function calculateSchedule(files, config) {
  const { posting } = config;
  
  if (!posting.use) {
    return files.map(file => ({
      file: file.name,
      scheduled: false,
      reason: 'スケジューリングが無効'
    }));
  }

  let startDate;
  if (posting.startDate === 'auto') {
    // 次回投稿可能時刻を計算
    startDate = calculatePostTime(config, getJSTDate());
  } else {
    startDate = parseJSTDate(posting.startDate);
    if (!startDate) {
      throw new Error(`無効な開始日付: ${posting.startDate}`);
    }
  }

  const schedule = [];
  let currentDate = new Date(startDate);
  const intervalMs = posting.interval * 24 * 60 * 60 * 1000; // 日数をミリ秒に

  for (let i = 0; i < files.length; i++) {
    const file = files[i];
    
    // 週末スキップ処理
    if (posting.skipWeekends) {
      while (isWeekend(currentDate)) {
        currentDate = new Date(currentDate.getTime() + 24 * 60 * 60 * 1000); // 1日追加
      }
    }

    schedule.push({
      file: file.name,
      path: file.path,
      content: file.content,
      scheduledTime: new Date(currentDate),
      scheduled: true
    });

    // 次の投稿日を計算
    currentDate = new Date(currentDate.getTime() + intervalMs);
  }

  return schedule;
}

/**
 * 期日到来分をフィルタリング
 */
function filterDueItems(schedule, currentTime = null) {
  const now = currentTime || getJSTDate();
  
  return schedule.filter(item => {
    if (!item.scheduled) return false;
    return item.scheduledTime <= now;
  });
}

/**
 * スケジュール表示
 */
function displaySchedule(schedule) {
  if (schedule.length === 0) {
    log('スケジュールされた投稿はありません');
    return;
  }

  log('\n=== 投稿スケジュール ===');
  
  const scheduled = schedule.filter(s => s.scheduled);
  if (scheduled.length === 0) {
    log('スケジュールされた投稿はありません');
    return;
  }

  // スケジュール範囲を表示
  const times = scheduled.map(s => s.scheduledTime);
  const startTime = new Date(Math.min(...times));
  const endTime = new Date(Math.max(...times));
  
  log(`期間: ${formatJSTDateTime(startTime)} ～ ${formatJSTDateTime(endTime)}`);
  log(`総件数: ${scheduled.length}件\n`);

  // 各アイテムの詳細
  scheduled.forEach((item, index) => {
    const preview = item.content ? 
      `"${item.content.substring(0, 30)}${item.content.length > 30 ? '...' : ''}"`
      : '内容未読込';
    
    log(`${index + 1}. ${item.file}`);
    log(`   予定時刻: ${formatJSTDateTime(item.scheduledTime)}`);
    log(`   内容: ${preview}\n`);
  });
}

/**
 * JST日時フォーマット
 */
function formatJSTDateTime(date) {
  const jstDate = new Date(date.toLocaleString("en-US", {timeZone: "Asia/Tokyo"}));
  return jstDate.toLocaleString('ja-JP', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    timeZone: 'Asia/Tokyo'
  }) + ' JST';
}

module.exports = {
  calculateSchedule,
  filterDueItems,
  displaySchedule,
  getJSTDate,
  parseJSTDate,
  calculatePostTime,
  formatJSTDateTime
};