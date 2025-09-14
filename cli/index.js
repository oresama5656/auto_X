#!/usr/bin/env node

const { Command } = require('commander');
const { planSchedule, runPosting, lintSnsFiles, migrateConfiguration } = require('../core');

const program = new Command();

program
  .name('auto-x-posting')
  .description('X (Twitter) 自動投稿システム')
  .version('1.0.0');

/**
 * スケジュール計画コマンド
 */
program
  .command('plan')
  .description('投稿スケジュールを表示')
  .option('-c, --config <path>', '設定ファイルパス', 'configs/sns.json')
  .option('-s, --sns-dir <path>', 'SNSディレクトリパス')
  .action(async (options) => {
    try {
      const result = await planSchedule(options);
      
      if (!result.success) {
        console.error('エラー:', result.error);
        process.exit(1);
      }
      
      process.exit(0);
    } catch (error) {
      console.error('予期しないエラー:', error.message);
      process.exit(1);
    }
  });

/**
 * 投稿実行コマンド
 */
program
  .command('run')
  .description('投稿を実行')
  .option('-c, --config <path>', '設定ファイルパス', 'configs/sns.json')
  .option('-s, --sns-dir <path>', 'SNSディレクトリパス')
  .option('--due-only', '期日到来分のみ投稿（実投稿）', false)
  .option('--save-log', 'ログをファイルに保存', false)
  .action(async (options) => {
    try {
      const result = await runPosting(options);
      
      if (!result.success) {
        console.error('エラー:', result.error);
        if (result.errors) {
          result.errors.forEach(error => console.error('  -', error));
        }
        process.exit(1);
      }
      
      // 結果表示
      if (result.results && result.results.length > 0) {
        const successCount = result.results.filter(r => r.success).length;
        const totalCount = result.results.length;
        
        console.log(`\n完了: ${successCount}/${totalCount} 件`);
        
        if (result.simulation) {
          console.log('※ シミュレーションモードで実行されました');
          console.log('実際に投稿するには --due-only オプションを使用してください');
        }
      }
      
      process.exit(0);
    } catch (error) {
      console.error('予期しないエラー:', error.message);
      process.exit(1);
    }
  });

/**
 * ファイル検証コマンド
 */
program
  .command('lint')
  .description('投稿ファイルを検証')
  .option('-s, --sns-dir <path>', 'SNSディレクトリパス')
  .action(async (options) => {
    try {
      const result = await lintSnsFiles(options);
      
      if (!result.success) {
        console.error('エラー:', result.error);
        process.exit(1);
      }
      
      const invalidFiles = result.results.filter(r => !r.valid);
      if (invalidFiles.length > 0) {
        console.log(`\\n${invalidFiles.length}件のファイルにエラーがあります`);
        process.exit(1);
      }
      
      console.log('すべてのファイルが正常です');
      process.exit(0);
    } catch (error) {
      console.error('予期しないエラー:', error.message);
      process.exit(1);
    }
  });

/**
 * 設定移行コマンド
 */
program
  .command('migrate-config')
  .description('旧設定を新設定に移行')
  .option('-c, --config <path>', '設定ファイルパス', 'configs/sns.json')
  .option('-o, --output <path>', '出力ファイルパス（省略時は入力と同じ）')
  .action(async (options) => {
    try {
      const result = await migrateConfiguration(options);
      
      if (!result.success) {
        console.error('エラー:', result.error);
        process.exit(1);
      }
      
      console.log('設定移行が完了しました');
      process.exit(0);
    } catch (error) {
      console.error('予期しないエラー:', error.message);
      process.exit(1);
    }
  });

/**
 * ヘルプメッセージのカスタマイズ
 */
program.addHelpText('after', `
使用例:
  $ node cli/index.js plan                    # スケジュール表示
  $ node cli/index.js run                     # シミュレーション実行
  $ node cli/index.js run --due-only          # 期日到来分のみ実投稿
  $ node cli/index.js lint                    # ファイル検証
  $ node cli/index.js migrate-config          # 設定移行

環境変数:
  TW_API_KEY                X API Key
  TW_API_KEY_SECRET         X API Key Secret  
  TW_ACCESS_TOKEN           X Access Token
  TW_ACCESS_TOKEN_SECRET    X Access Token Secret

注意事項:
  - デフォルトはシミュレーションモード
  - 実投稿には --due-only フラグが必要
  - APIキーは環境変数での設定を推奨
`);

// エラーハンドリング
process.on('uncaughtException', (error) => {
  console.error('予期しないエラーが発生しました:', error.message);
  process.exit(1);
});

process.on('unhandledRejection', (reason, promise) => {
  console.error('未処理のPromise拒否:', reason);
  process.exit(1);
});

// プログラム実行
program.parse(process.argv);