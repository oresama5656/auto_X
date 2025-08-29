const { percentEncode, generateOAuthSignature, generateOAuthHeader } = require('../core/oauth');

describe('OAuth Functions', () => {
  describe('percentEncode', () => {
    test('should encode special characters according to RFC3986', () => {
      expect(percentEncode('Hello World')).toBe('Hello%20World');
      expect(percentEncode("test!'()*")).toBe('test%21%27%28%29%2A');
      expect(percentEncode('日本語')).toBe('%E6%97%A5%E6%9C%AC%E8%AA%9E');
    });

    test('should not encode unreserved characters', () => {
      expect(percentEncode('abc123-_.~')).toBe('abc123-_.~');
    });

    test('should handle empty string', () => {
      expect(percentEncode('')).toBe('');
    });
  });

  describe('generateOAuthSignature', () => {
    test('should generate consistent signature for same inputs', () => {
      const method = 'POST';
      const url = 'https://api.twitter.com/2/tweets';
      const params = {
        oauth_consumer_key: 'test_key',
        oauth_token: 'test_token',
        oauth_signature_method: 'HMAC-SHA1',
        oauth_timestamp: '1234567890',
        oauth_nonce: 'test_nonce',
        oauth_version: '1.0'
      };
      const consumerSecret = 'test_consumer_secret';
      const tokenSecret = 'test_token_secret';

      const signature1 = generateOAuthSignature(method, url, params, consumerSecret, tokenSecret);
      const signature2 = generateOAuthSignature(method, url, params, consumerSecret, tokenSecret);

      expect(signature1).toBe(signature2);
      expect(typeof signature1).toBe('string');
      expect(signature1.length).toBeGreaterThan(0);
    });

    test('should handle empty token secret', () => {
      const method = 'POST';
      const url = 'https://api.twitter.com/2/tweets';
      const params = {
        oauth_consumer_key: 'test_key',
        oauth_signature_method: 'HMAC-SHA1',
        oauth_timestamp: '1234567890',
        oauth_nonce: 'test_nonce',
        oauth_version: '1.0'
      };
      const consumerSecret = 'test_consumer_secret';

      const signature = generateOAuthSignature(method, url, params, consumerSecret);
      expect(typeof signature).toBe('string');
      expect(signature.length).toBeGreaterThan(0);
    });
  });

  describe('generateOAuthHeader', () => {
    test('should generate valid OAuth header format', () => {
      const method = 'POST';
      const url = 'https://api.twitter.com/2/tweets';
      const apiKey = 'test_api_key';
      const apiKeySecret = 'test_api_key_secret';
      const accessToken = 'test_access_token';
      const accessTokenSecret = 'test_access_token_secret';

      const header = generateOAuthHeader(method, url, apiKey, apiKeySecret, accessToken, accessTokenSecret);

      expect(header).toMatch(/^OAuth /);
      expect(header).toContain('oauth_consumer_key');
      expect(header).toContain('oauth_token');
      expect(header).toContain('oauth_signature_method');
      expect(header).toContain('oauth_timestamp');
      expect(header).toContain('oauth_nonce');
      expect(header).toContain('oauth_version');
      expect(header).toContain('oauth_signature');
      expect(header).toContain('HMAC-SHA1');
    });

    test('should generate different nonce for different calls', () => {
      const method = 'POST';
      const url = 'https://api.twitter.com/2/tweets';
      const apiKey = 'test_api_key';
      const apiKeySecret = 'test_api_key_secret';
      const accessToken = 'test_access_token';
      const accessTokenSecret = 'test_access_token_secret';

      const header1 = generateOAuthHeader(method, url, apiKey, apiKeySecret, accessToken, accessTokenSecret);
      const header2 = generateOAuthHeader(method, url, apiKey, apiKeySecret, accessToken, accessTokenSecret);

      // nonceが異なることを確認
      const nonce1 = header1.match(/oauth_nonce="([^"]+)"/)[1];
      const nonce2 = header2.match(/oauth_nonce="([^"]+)"/)[1];
      expect(nonce1).not.toBe(nonce2);
    });
  });
});