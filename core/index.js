const { loadConfig, validateConfig } = require('./config');
const { getSnsFiles, lintFiles, moveToPosted } = require('./file-manager');
const { calculateSchedule, filterDueItems, displaySchedule } = require('./scheduler');
const { postTweet } = require('./twitter-api');
const { log, generateSummary, saveLog } = require('./logger');

/**
 * スケジュール計画を実行
 */
async function planSchedule(options = {}) {
  try {
    log('=== スケジュール計画開始 ===');
    
    const config = await loadConfig(options.configPath);
    const files = await getSnsFiles(options.snsDir);
    
    if (files.length === 0) {
      log('投稿対象ファイルが見つかりません');
      return { success: true, schedule: [], files: [] };
    }

    const schedule = calculateSchedule(files, config);
    displaySchedule(schedule);

    return {
      success: true,
      schedule,
      files,
      config
    };
  } catch (error) {
    log(`計画エラー: ${error.message}`, 'ERROR');
    return { success: false, error: error.message };
  }
}

/**
 * 投稿実行
 */
async function runPosting(options = {}) {
  try {
    log('=== 投稿実行開始 ===');
    
    const config = await loadConfig(options.configPath);
    
    // 設定検証
    const configErrors = validateConfig(config);
    if (configErrors.length > 0) {
      log('設定エラー:', 'ERROR');
      configErrors.forEach(error => log(`  - ${error}`, 'ERROR'));
      return { success: false, errors: configErrors };
    }

    const files = await getSnsFiles(options.snsDir);
    if (files.length === 0) {
      log('投稿対象ファイルが見つかりません');
      return { success: true, results: [] };
    }

    const schedule = calculateSchedule(files, config);
    const isSimulation = !options.dueOnly;

    let itemsToProcess;
    if (options.dueOnly) {
      itemsToProcess = filterDueItems(schedule);
      if (itemsToProcess.length === 0) {
        log('期日到来の投稿はありません');
        return { success: true, results: [] };
      }
      log(`期日到来: ${itemsToProcess.length}件の投稿を実行`);
    } else {
      itemsToProcess = schedule.filter(s => s.scheduled);
      log('シミュレーションモードで実行');
    }

    const results = [];

    for (const item of itemsToProcess) {
      try {
        log(`\n処理中: ${item.file}`);
        
        const result = await postTweet(item.content, config.twitterApi, isSimulation);
        
        if (result.success) {
          // 実際の投稿の場合のみファイル移動
          if (!isSimulation) {
            await moveToPosted(item.path, true);
          }
          
          results.push({
            file: item.file,
            success: true,
            id: result.id,
            simulation: result.simulation || false,
            scheduledTime: item.scheduledTime
          });
        } else {
          throw new Error('投稿失敗');
        }

      } catch (error) {
        log(`投稿エラー: ${item.file} - ${error.message}`, 'ERROR');
        
        results.push({
          file: item.file,
          success: false,
          error: error.message,
          scheduledTime: item.scheduledTime
        });
      }
    }

    // 結果要約
    generateSummary(results);
    
    // ログ保存
    if (options.saveLog) {
      const logContent = results.map(r => 
        `${r.file}: ${r.success ? 'SUCCESS' : 'FAILED'} ${r.id || r.error || ''}`
      ).join('\n');
      await saveLog(logContent);
    }

    return {
      success: true,
      results,
      simulation: isSimulation
    };

  } catch (error) {
    log(`実行エラー: ${error.message}`, 'ERROR');
    return { success: false, error: error.message };
  }
}

/**
 * ファイル検証
 */
async function lintSnsFiles(options = {}) {
  try {
    log('=== ファイル検証開始 ===');
    
    const results = await lintFiles(options.snsDir);
    
    return {
      success: true,
      results
    };
  } catch (error) {
    log(`検証エラー: ${error.message}`, 'ERROR');
    return { success: false, error: error.message };
  }
}

/**
 * 設定移行
 */
async function migrateConfiguration(options = {}) {
  try {
    log('=== 設定移行開始 ===');
    
    const config = await loadConfig(options.configPath);
    await saveConfig(config, options.outputPath || options.configPath);
    
    log('設定移行が完了しました');
    return { success: true, config };
  } catch (error) {
    log(`移行エラー: ${error.message}`, 'ERROR');
    return { success: false, error: error.message };
  }
}

module.exports = {
  planSchedule,
  runPosting,
  lintSnsFiles,
  migrateConfiguration
};