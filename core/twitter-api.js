const https = require('https');
const { generateOAuthHeader } = require('./oauth');
const { log } = require('./logger');

/**
 * 指数バックオフでリトライ
 */
async function retryWithBackoff(fn, maxRetries = 4) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      if (error.statusCode === 429 || (error.statusCode >= 500 && error.statusCode < 600)) {
        const delay = Math.min(1500 * Math.pow(1.5, i), 45000); // 1.5s -> 3s -> 6s -> ... 最大45s
        log(`Rate limit or server error (${error.statusCode}). Retrying in ${delay}ms...`);
        await new Promise(resolve => setTimeout(resolve, delay));
        continue;
      }
      throw error;
    }
  }
  throw new Error(`Failed after ${maxRetries} retries`);
}

/**
 * HTTPSリクエストを実行
 */
function makeRequest(hostname, path, method, headers, body = null) {
  return new Promise((resolve, reject) => {
    const options = {
      hostname,
      port: 443,
      path,
      method,
      headers
    };

    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        const response = {
          statusCode: res.statusCode,
          headers: res.headers,
          body: data
        };

        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(response);
        } else {
          const error = new Error(`HTTP ${res.statusCode}: ${data}`);
          error.statusCode = res.statusCode;
          error.response = response;
          reject(error);
        }
      });
    });

    req.on('error', reject);
    
    if (body) {
      req.write(body);
    }
    req.end();
  });
}

/**
 * ツイートを投稿
 */
async function postTweet(text, apiConfig, isSimulation = false) {
  if (isSimulation) {
    log(`[シミュレーション] 投稿予定: "${text.substring(0, 50)}${text.length > 50 ? '...' : ''}"`);
    return {
      success: true,
      simulation: true,
      id: 'sim_' + Date.now(),
      text: text
    };
  }

  const { apiKey, apiKeySecret, accessToken, accessTokenSecret } = apiConfig;
  
  // 280文字制限（コードポイントベース）
  let tweetText = text;
  if ([...tweetText].length > 280) {
    tweetText = [...tweetText].slice(0, 277).join('') + '...';
    log(`文字数制限により切り詰めました: ${[...text].length} -> 280文字`);
  }

  const tweetData = JSON.stringify({ text: tweetText });
  
  // api.x.com を第一候補、失敗時 api.twitter.com
  const endpoints = [
    { hostname: 'api.x.com', name: 'X API' },
    { hostname: 'api.twitter.com', name: 'Twitter API' }
  ];

  for (const endpoint of endpoints) {
    try {
      log(`${endpoint.name}への投稿を試行中...`);
      
      const result = await retryWithBackoff(async () => {
        const authHeader = generateOAuthHeader(
          'POST',
          `https://${endpoint.hostname}/2/tweets`,
          apiKey,
          apiKeySecret,
          accessToken,
          accessTokenSecret
        );

        const headers = {
          'Authorization': authHeader,
          'Content-Type': 'application/json',
          'Content-Length': Buffer.byteLength(tweetData)
        };

        const response = await makeRequest(
          endpoint.hostname,
          '/2/tweets',
          'POST',
          headers,
          tweetData
        );

        return response;
      });

      const responseData = JSON.parse(result.body);
      log(`投稿成功 (${endpoint.name}): ID=${responseData.data?.id}`);
      
      return {
        success: true,
        id: responseData.data?.id,
        text: tweetText,
        endpoint: endpoint.name
      };

    } catch (error) {
      log(`${endpoint.name}での投稿失敗: ${error.message}`);
      if (endpoint === endpoints[endpoints.length - 1]) {
        // 最後のエンドポイントも失敗
        throw error;
      }
      // 次のエンドポイントを試行
    }
  }
}

module.exports = {
  postTweet,
  retryWithBackoff
};