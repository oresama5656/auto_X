#!/usr/bin/env node

/**
 * 互換ランチャー
 * 旧スクリプトとの互換性のため、core/cli を呼び出すだけのシンプルなラッパー
 */

const { spawn } = require('child_process');
const path = require('path');

const cliPath = path.join(__dirname, '..', 'cli', 'index.js');

// コマンドライン引数を解析
const args = process.argv.slice(2);

// デフォルトは run コマンド
let command = 'run';
let cliArgs = [];

// 引数があれば解析
if (args.length > 0) {
  // --due-only や --help などのオプションはそのまま渡す
  if (args[0].startsWith('--') || args[0].startsWith('-')) {
    cliArgs = ['run', ...args];
  } else {
    // コマンドが指定されている場合
    command = args[0];
    cliArgs = args;
  }
} else {
  cliArgs = ['run'];
}

console.log(`[互換ランチャー] CLI実行: node cli/index.js ${cliArgs.join(' ')}`);

// CLI を実行
const child = spawn('node', [cliPath, ...cliArgs], {
  stdio: 'inherit',
  cwd: path.join(__dirname, '..')
});

child.on('close', (code) => {
  process.exit(code);
});

child.on('error', (error) => {
  console.error('実行エラー:', error.message);
  process.exit(1);
});