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
 * スケジュール計算（固定時刻のみ）
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

  // 固定時刻配列の検証
  const times = posting.times || posting.fixedTimes; // backward compatibility
  if (!times || !Array.isArray(times)) {
    throw new Error('投稿時刻の設定が必要です (times配列)');
  }

  let startDate;
  if (posting.startDate === 'auto') {
    startDate = getJSTDate();
  } else {
    startDate = parseJSTDate(posting.startDate);
    if (!startDate) {
      throw new Error(`無効な開始日付: ${posting.startDate}`);
    }
  }

  const schedule = [];
  let currentDay = new Date(startDate);
  currentDay.setHours(0, 0, 0, 0); // 開始日の00:00に設定
  
  let fileIndex = 0;
  let timeIndex = 0;

  while (fileIndex < files.length) {
    // 週末スキップ処理
    if (posting.skipWeekends && isWeekend(currentDay)) {
      currentDay = new Date(currentDay.getTime() + 24 * 60 * 60 * 1000);
      timeIndex = 0; // 新しい日は最初の時刻から
      continue;
    }

    // 現在の日の投稿時刻を取得
    const timeStr = times[timeIndex];
    const [hours, minutes] = timeStr.split(':').map(Number);
    const scheduledTime = new Date(currentDay);
    scheduledTime.setHours(hours, minutes, 0, 0);

    // 開始日時より前の時刻はスキップ
    if (scheduledTime < startDate) {
      timeIndex++;
      if (timeIndex >= times.length) {
        // 今日の全時刻を使い切った場合、翌日へ
        currentDay = new Date(currentDay.getTime() + 24 * 60 * 60 * 1000);
        timeIndex = 0;
      }
      continue;
    }

    const file = files[fileIndex];
    schedule.push({
      file: file.name,
      path: file.path,
      content: file.content,
      scheduledTime: new Date(scheduledTime),
      scheduled: true
    });

    fileIndex++;
    timeIndex++;

    // その日の全時刻を使い切った場合、翌日へ
    if (timeIndex >= times.length) {
      currentDay = new Date(currentDay.getTime() + 24 * 60 * 60 * 1000);
      timeIndex = 0;
    }
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
  formatJSTDateTime
};