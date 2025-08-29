const { migrateLegacyConfig, validateConfig, DEFAULT_CONFIG } = require('../core/config');

describe('Config Functions', () => {
  describe('migrateLegacyConfig', () => {
    test('should migrate legacy keys to new structure', () => {
      const legacyConfig = {
        useScheduledPosting: true,
        scheduledPostingStartDate: '2024-01-01',
        scheduledPostingInterval: 1.0,
        scheduledPostingTime: '09:00',
        scheduledPostingAutoTimeOffset: 60,
        scheduledPostingSkipWeekends: true,
        twitterApi: {
          apiKey: 'test_key'
        }
      };

      const migratedConfig = migrateLegacyConfig(legacyConfig);

      expect(migratedConfig.posting.use).toBe(true);
      expect(migratedConfig.posting.startDate).toBe('2024-01-01');
      expect(migratedConfig.posting.interval).toBe(1.0);
      expect(migratedConfig.posting.postTime).toBe('09:00');
      expect(migratedConfig.posting.autoTimeOffset).toBe(60);
      expect(migratedConfig.posting.skipWeekends).toBe(true);
      expect(migratedConfig.twitterApi.apiKey).toBe('test_key');

      // Legacy keys should be removed
      expect(migratedConfig.useScheduledPosting).toBeUndefined();
      expect(migratedConfig.scheduledPostingStartDate).toBeUndefined();
    });

    test('should handle config without legacy keys', () => {
      const modernConfig = {
        posting: {
          use: true,
          interval: 0.5
        },
        twitterApi: {
          apiKey: 'test_key'
        }
      };

      const result = migrateLegacyConfig(modernConfig);
      expect(result).toEqual(modernConfig);
    });

    test('should handle empty config', () => {
      const result = migrateLegacyConfig({});
      expect(result).toEqual({});
    });
  });

  describe('validateConfig', () => {
    test('should pass validation for complete config', () => {
      const validConfig = {
        posting: {
          use: true,
          interval: 1.0
        },
        twitterApi: {
          apiKey: 'test_key',
          apiKeySecret: 'test_secret',
          accessToken: 'test_token',
          accessTokenSecret: 'test_token_secret'
        }
      };

      const errors = validateConfig(validConfig);
      expect(errors).toHaveLength(0);
    });

    test('should detect missing API keys', () => {
      const incompleteConfig = {
        posting: {
          use: true,
          interval: 1.0
        },
        twitterApi: {
          apiKey: 'test_key',
          apiKeySecret: '',
          accessToken: 'test_token',
          accessTokenSecret: ''
        }
      };

      const errors = validateConfig(incompleteConfig);
      expect(errors).toContain('Twitter API設定が不足: apiKeySecret');
      expect(errors).toContain('Twitter API設定が不足: accessTokenSecret');
    });

    test('should detect invalid interval', () => {
      const invalidConfig = {
        posting: {
          use: true,
          interval: 0
        },
        twitterApi: {
          apiKey: 'test_key',
          apiKeySecret: 'test_secret',
          accessToken: 'test_token',
          accessTokenSecret: 'test_token_secret'
        }
      };

      const errors = validateConfig(invalidConfig);
      expect(errors).toContain('投稿間隔は0より大きい値を設定してください');
    });

    test('should detect negative interval', () => {
      const invalidConfig = {
        posting: {
          use: true,
          interval: -1
        },
        twitterApi: {
          apiKey: 'test_key',
          apiKeySecret: 'test_secret',
          accessToken: 'test_token',
          accessTokenSecret: 'test_token_secret'
        }
      };

      const errors = validateConfig(invalidConfig);
      expect(errors).toContain('投稿間隔は0より大きい値を設定してください');
    });

    test('should handle multiple validation errors', () => {
      const invalidConfig = {
        posting: {
          use: true,
          interval: 0
        },
        twitterApi: {
          apiKey: '',
          apiKeySecret: '',
          accessToken: '',
          accessTokenSecret: ''
        }
      };

      const errors = validateConfig(invalidConfig);
      expect(errors.length).toBeGreaterThan(1);
      expect(errors).toContain('投稿間隔は0より大きい値を設定してください');
      expect(errors).toContain('Twitter API設定が不足: apiKey');
    });
  });

  describe('DEFAULT_CONFIG', () => {
    test('should have expected default values', () => {
      expect(DEFAULT_CONFIG.posting.use).toBe(true);
      expect(DEFAULT_CONFIG.posting.startDate).toBe('auto');
      expect(DEFAULT_CONFIG.posting.interval).toBe(0.5);
      expect(DEFAULT_CONFIG.posting.postTime).toBe('auto');
      expect(DEFAULT_CONFIG.posting.autoTimeOffset).toBe(30);
      expect(DEFAULT_CONFIG.posting.skipWeekends).toBe(false);

      expect(DEFAULT_CONFIG.twitterApi.apiKey).toBe('');
      expect(DEFAULT_CONFIG.twitterApi.apiKeySecret).toBe('');
      expect(DEFAULT_CONFIG.twitterApi.accessToken).toBe('');
      expect(DEFAULT_CONFIG.twitterApi.accessTokenSecret).toBe('');
    });

    test('should be a valid config structure', () => {
      const errors = validateConfig({
        ...DEFAULT_CONFIG,
        twitterApi: {
          apiKey: 'test',
          apiKeySecret: 'test',
          accessToken: 'test',
          accessTokenSecret: 'test'
        }
      });
      expect(errors).toHaveLength(0);
    });
  });
});