const fs = require('fs').promises;
const path = require('path');
const { log } = require('./logger');

/**
 * 設定ファイルのデフォルト値
 */
const DEFAULT_CONFIG = {
  posting: {
    use: true,
    scheduleType: 'interval', // 'interval' または 'fixed'
    startDate: 'auto',
    // interval モード用設定
    interval: 0.5,
    postTime: 'auto',
    autoTimeOffset: 30,
    // fixed モード用設定
    fixedTimes: ['09:00', '12:00', '15:00', '18:00', '21:00'],
    // 共通設定
    skipWeekends: false
  },
  twitterApi: {
    apiKey: '',
    apiKeySecret: '',
    accessToken: '',
    accessTokenSecret: ''
  }
};

/**
 * 旧設定キーから新設定への変換マップ
 */
const LEGACY_KEY_MAP = {
  useScheduledPosting: 'posting.use',
  scheduledPostingStartDate: 'posting.startDate',
  scheduledPostingInterval: 'posting.interval',
  scheduledPostingTime: 'posting.postTime',
  scheduledPostingAutoTimeOffset: 'posting.autoTimeOffset',
  scheduledPostingSkipWeekends: 'posting.skipWeekends'
};

/**
 * ネストしたオブジェクトに値を設定
 */
function setNestedValue(obj, path, value) {
  const keys = path.split('.');
  let current = obj;
  
  for (let i = 0; i < keys.length - 1; i++) {
    if (!current[keys[i]]) {
      current[keys[i]] = {};
    }
    current = current[keys[i]];
  }
  
  current[keys[keys.length - 1]] = value;
}

/**
 * 環境変数からAPIキーを取得
 */
function getApiKeysFromEnv() {
  return {
    apiKey: process.env.TW_API_KEY || process.env.TWITTER_API_KEY || '',
    apiKeySecret: process.env.TW_API_KEY_SECRET || process.env.TWITTER_API_KEY_SECRET || '',
    accessToken: process.env.TW_ACCESS_TOKEN || process.env.TWITTER_ACCESS_TOKEN || '',
    accessTokenSecret: process.env.TW_ACCESS_TOKEN_SECRET || process.env.TWITTER_ACCESS_TOKEN_SECRET || ''
  };
}

/**
 * 旧設定を新設定に変換
 */
function migrateLegacyConfig(config) {
  let migrated = false;
  const newConfig = JSON.parse(JSON.stringify(config));

  for (const [oldKey, newPath] of Object.entries(LEGACY_KEY_MAP)) {
    if (config[oldKey] !== undefined) {
      setNestedValue(newConfig, newPath, config[oldKey]);
      delete newConfig[oldKey];
      migrated = true;
    }
  }

  if (migrated) {
    log('旧設定キーを新設定に変換しました');
  }

  return newConfig;
}

/**
 * 設定ファイルを読み込み
 */
async function loadConfig(configPath = null) {
  try {
    if (!configPath) {
      configPath = path.join(process.cwd(), 'configs', 'sns.json');
    }

    let config;
    try {
      const configData = await fs.readFile(configPath, 'utf8');
      config = JSON.parse(configData);
    } catch (error) {
      if (error.code === 'ENOENT') {
        log('設定ファイルが見つかりません。デフォルト設定を使用します');
        config = JSON.parse(JSON.stringify(DEFAULT_CONFIG));
      } else {
        throw error;
      }
    }

    // 旧設定の変換
    config = migrateLegacyConfig(config);

    // デフォルト値でマージ
    const mergedConfig = {
      posting: { ...DEFAULT_CONFIG.posting, ...config.posting },
      twitterApi: { ...DEFAULT_CONFIG.twitterApi, ...config.twitterApi }
    };

    // 環境変数からAPIキーを取得（ファイル設定が空の場合）
    const envKeys = getApiKeysFromEnv();
    if (!mergedConfig.twitterApi.apiKey && envKeys.apiKey) {
      mergedConfig.twitterApi = { ...mergedConfig.twitterApi, ...envKeys };
      log('環境変数からAPIキーを読み込みました');
    }

    return mergedConfig;
  } catch (error) {
    log(`設定読み込みエラー: ${error.message}`, 'ERROR');
    throw error;
  }
}

/**
 * 設定ファイルを保存
 */
async function saveConfig(config, configPath = null) {
  try {
    if (!configPath) {
      configPath = path.join(process.cwd(), 'configs', 'sns.json');
    }

    await fs.mkdir(path.dirname(configPath), { recursive: true });
    await fs.writeFile(configPath, JSON.stringify(config, null, 2), 'utf8');
    log('設定ファイルを保存しました');
  } catch (error) {
    log(`設定保存エラー: ${error.message}`, 'ERROR');
    throw error;
  }
}

/**
 * 設定を検証
 */
function validateConfig(config) {
  const errors = [];

  // API認証情報チェック
  const requiredApiKeys = ['apiKey', 'apiKeySecret', 'accessToken', 'accessTokenSecret'];
  for (const key of requiredApiKeys) {
    if (!config.twitterApi[key]) {
      errors.push(`Twitter API設定が不足: ${key}`);
    }
  }

  // posting設定チェック
  const scheduleType = config.posting.scheduleType || 'interval';
  
  if (scheduleType === 'interval') {
    if (config.posting.interval <= 0) {
      errors.push('投稿間隔は0より大きい値を設定してください');
    }
  } else if (scheduleType === 'fixed') {
    if (!config.posting.fixedTimes || !Array.isArray(config.posting.fixedTimes)) {
      errors.push('固定時刻モードでは fixedTimes 配列が必要です');
    } else if (config.posting.fixedTimes.length === 0) {
      errors.push('fixedTimes 配列は少なくとも1つの時刻が必要です');
    } else {
      // 時刻フォーマットチェック
      for (const time of config.posting.fixedTimes) {
        if (!/^([01]?[0-9]|2[0-3]):[0-5][0-9]$/.test(time)) {
          errors.push(`無効な時刻フォーマット: ${time} (HH:MM形式で入力してください)`);
        }
      }
    }
  } else {
    errors.push(`無効なスケジュールタイプ: ${scheduleType} ('interval' または 'fixed' を指定してください)`);
  }

  return errors;
}

module.exports = {
  loadConfig,
  saveConfig,
  validateConfig,
  migrateLegacyConfig,
  DEFAULT_CONFIG
};