const { loadConfig, validateConfig, saveConfig } = require('./config');
const { getSnsFiles, lintFiles, moveToPosted } = require('./file-manager');
const { postTweet } = require('./twitter-api');
const { log, generateSummary, saveLog } = require('./logger');

/**
 * ファイル一覧表示（簡略化版）
 */
async function planSchedule(options = {}) {
  try {
    log('=== ファイル一覧表示 ===');

    const config = await loadConfig(options.configPath);

    // フォルダパス決定（CLI オプション > 設定ファイル > デフォルト）
    const snsDir = options.snsDir || config.folders.input;
    const files = await getSnsFiles(snsDir);

    if (files.length === 0) {
      log('投稿対象ファイルが見つかりません');
      return { success: true, files: [] };
    }

    log(`\n=== 投稿待ちファイル一覧 ===`);
    log(`総件数: ${files.length}件`);
    log(`次回投稿ファイル: ${files[0].name}\n`);

    // 最初の10件を表示
    const displayCount = Math.min(files.length, 10);
    for (let i = 0; i < displayCount; i++) {
      const file = files[i];
      const marker = i === 0 ? '👉' : '  ';
      const preview = file.content.substring(0, 50);
      const truncated = file.content.length > 50 ? '...' : '';

      log(`${marker} ${i + 1}. ${file.name}`);
      log(`   内容: "${preview}${truncated}"`);
      if (i === 0) {
        log(`   ⭐ 次回投稿ファイル`);
      }
      log('');
    }

    if (files.length > 10) {
      log(`... 他 ${files.length - 10} 件`);
    }

    return {
      success: true,
      files,
      config
    };
  } catch (error) {
    log(`表示エラー: ${error.message}`, 'ERROR');
    return { success: false, error: error.message };
  }
}

/**
 * 投稿実行（簡略化版）
 */
async function runPosting(options = {}) {
  try {
    log('=== 投稿実行開始 ===');

    const config = await loadConfig(options.configPath);

    // 設定検証（簡略化）
    const configErrors = validateConfig(config);
    if (configErrors.length > 0) {
      log('設定エラー:', 'ERROR');
      configErrors.forEach(error => log(`  - ${error}`, 'ERROR'));
      return { success: false, errors: configErrors };
    }

    // フォルダパス決定（CLI オプション > 設定ファイル > デフォルト）
    const snsDir = options.snsDir || config.folders.input;
    const files = await getSnsFiles(snsDir);
    if (files.length === 0) {
      log('投稿対象ファイルが見つかりません');
      return { success: true, results: [] };
    }

    const isSimulation = !options.dueOnly;

    // シンプルに最初の1件のみ処理（フォルダ内の最初のファイル）
    const fileToPost = files[0];
    log(`投稿ファイル: ${fileToPost.name} (${files.length}件中の1件目)`);

    const results = [];

    try {
      log(`\n処理中: ${fileToPost.name}`);

      const result = await postTweet(fileToPost.content, config.twitterApi, isSimulation);

      if (result.success) {
        // 実際の投稿の場合のみファイル移動
        if (!isSimulation) {
          await moveToPosted(fileToPost.path, true, config.folders.posted);
        }

        results.push({
          file: fileToPost.name,
          success: true,
          id: result.id,
          simulation: result.simulation || false
        });
      } else {
        throw new Error('投稿失敗');
      }

    } catch (error) {
      log(`投稿エラー: ${fileToPost.name} - ${error.message}`, 'ERROR');

      results.push({
        file: fileToPost.name,
        success: false,
        error: error.message
      });
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
    
    const config = await loadConfig(options.configPath);
    const snsDir = options.snsDir || config.folders.input;
    const results = await lintFiles(snsDir);
    
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