const crypto = require('crypto');

/**
 * RFC3986準拠のパーセントエンコード
 */
function percentEncode(str) {
  return encodeURIComponent(str)
    .replace(/[!'()*]/g, function(c) {
      return '%' + c.charCodeAt(0).toString(16).toUpperCase();
    });
}

/**
 * OAuth 1.0a署名を生成
 */
function generateOAuthSignature(method, url, params, consumerSecret, tokenSecret = '') {
  // パラメータをソート
  const sortedParams = Object.keys(params)
    .sort()
    .map(key => `${percentEncode(key)}=${percentEncode(params[key])}`)
    .join('&');

  // ベース文字列を作成
  const baseString = [
    method.toUpperCase(),
    percentEncode(url),
    percentEncode(sortedParams)
  ].join('&');

  // 署名キーを作成
  const signingKey = `${percentEncode(consumerSecret)}&${percentEncode(tokenSecret)}`;

  // HMAC-SHA1で署名
  const signature = crypto
    .createHmac('sha1', signingKey)
    .update(baseString)
    .digest('base64');

  return signature;
}

/**
 * OAuth 1.0a認証ヘッダーを生成
 */
function generateOAuthHeader(method, url, apiKey, apiKeySecret, accessToken, accessTokenSecret) {
  const timestamp = Math.floor(Date.now() / 1000).toString();
  const nonce = crypto.randomBytes(16).toString('hex') + timestamp;

  const oauthParams = {
    oauth_consumer_key: apiKey,
    oauth_token: accessToken,
    oauth_signature_method: 'HMAC-SHA1',
    oauth_timestamp: timestamp,
    oauth_nonce: nonce,
    oauth_version: '1.0'
  };

  // 署名を生成
  const signature = generateOAuthSignature(method, url, oauthParams, apiKeySecret, accessTokenSecret);
  oauthParams.oauth_signature = signature;

  // Authorizationヘッダーを構築
  const authHeader = 'OAuth ' + Object.keys(oauthParams)
    .map(key => `${percentEncode(key)}="${percentEncode(oauthParams[key])}"`)
    .join(', ');

  return authHeader;
}

module.exports = {
  percentEncode,
  generateOAuthSignature,
  generateOAuthHeader
};