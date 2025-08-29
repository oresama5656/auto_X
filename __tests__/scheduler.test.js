const { calculateSchedule, filterDueItems, getJSTDate, parseJSTDate } = require('../core/scheduler');

describe('Scheduler Functions', () => {
  const mockConfig = {
    posting: {
      use: true,
      startDate: 'auto',
      interval: 0.5,
      postTime: 'auto',
      autoTimeOffset: 30,
      skipWeekends: false
    }
  };

  const mockFiles = [
    { name: '001-test.txt', path: '/path/001-test.txt', content: 'Test post 1' },
    { name: '002-test.txt', path: '/path/002-test.txt', content: 'Test post 2' },
    { name: '003-test.txt', path: '/path/003-test.txt', content: 'Test post 3' }
  ];

  describe('getJSTDate', () => {
    test('should return Date object in JST', () => {
      const jstDate = getJSTDate();
      expect(jstDate instanceof Date).toBe(true);
    });

    test('should handle specific date input', () => {
      const inputDate = new Date('2024-01-01T00:00:00Z');
      const jstDate = getJSTDate(inputDate);
      expect(jstDate instanceof Date).toBe(true);
    });
  });

  describe('parseJSTDate', () => {
    test('should return null for auto', () => {
      expect(parseJSTDate('auto')).toBeNull();
    });

    test('should parse YYYY-MM-DD format', () => {
      const parsed = parseJSTDate('2024-01-01');
      expect(parsed instanceof Date).toBe(true);
      expect(parsed.getFullYear()).toBe(2024);
      expect(parsed.getMonth()).toBe(0); // 0-indexed
      expect(parsed.getDate()).toBe(1);
    });

    test('should handle ISO date strings', () => {
      const parsed = parseJSTDate('2024-01-01T12:00:00');
      expect(parsed instanceof Date).toBe(true);
    });
  });

  describe('calculateSchedule', () => {
    test('should return disabled schedule when posting.use is false', () => {
      const disabledConfig = {
        ...mockConfig,
        posting: { ...mockConfig.posting, use: false }
      };

      const schedule = calculateSchedule(mockFiles, disabledConfig);
      expect(schedule).toHaveLength(3);
      expect(schedule[0].scheduled).toBe(false);
      expect(schedule[0].reason).toBe('スケジューリングが無効');
    });

    test('should create schedule with auto start date', () => {
      const schedule = calculateSchedule(mockFiles, mockConfig);
      
      expect(schedule).toHaveLength(3);
      expect(schedule[0].scheduled).toBe(true);
      expect(schedule[0].scheduledTime instanceof Date).toBe(true);
      expect(schedule[0].file).toBe('001-test.txt');
      expect(schedule[0].content).toBe('Test post 1');

      // 間隔チェック（0.5日 = 12時間）
      const timeDiff = schedule[1].scheduledTime.getTime() - schedule[0].scheduledTime.getTime();
      expect(timeDiff).toBe(0.5 * 24 * 60 * 60 * 1000);
    });

    test('should handle custom start date', () => {
      const customConfig = {
        ...mockConfig,
        posting: { ...mockConfig.posting, startDate: '2024-01-01' }
      };

      const schedule = calculateSchedule(mockFiles, customConfig);
      expect(schedule[0].scheduledTime.getFullYear()).toBe(2024);
      expect(schedule[0].scheduledTime.getMonth()).toBe(0);
      expect(schedule[0].scheduledTime.getDate()).toBe(1);
    });

    test('should skip weekends when configured', () => {
      const weekendConfig = {
        ...mockConfig,
        posting: { 
          ...mockConfig.posting, 
          startDate: '2024-01-06', // Saturday
          skipWeekends: true 
        }
      };

      const schedule = calculateSchedule(mockFiles, weekendConfig);
      
      // 土曜日開始だが月曜日に調整されるはず
      const firstDate = schedule[0].scheduledTime;
      expect(firstDate.getDay()).not.toBe(0); // 日曜日でない
      expect(firstDate.getDay()).not.toBe(6); // 土曜日でない
    });

    test('should handle empty files array', () => {
      const schedule = calculateSchedule([], mockConfig);
      expect(schedule).toHaveLength(0);
    });
  });

  describe('filterDueItems', () => {
    test('should filter items due by current time', () => {
      const now = new Date();
      const pastTime = new Date(now.getTime() - 60 * 60 * 1000); // 1時間前
      const futureTime = new Date(now.getTime() + 60 * 60 * 1000); // 1時間後

      const mockSchedule = [
        { file: 'past.txt', scheduled: true, scheduledTime: pastTime },
        { file: 'future.txt', scheduled: true, scheduledTime: futureTime },
        { file: 'unscheduled.txt', scheduled: false }
      ];

      const dueItems = filterDueItems(mockSchedule, now);
      expect(dueItems).toHaveLength(1);
      expect(dueItems[0].file).toBe('past.txt');
    });

    test('should handle empty schedule', () => {
      const dueItems = filterDueItems([]);
      expect(dueItems).toHaveLength(0);
    });

    test('should use current time when not provided', () => {
      const mockSchedule = [
        { file: 'test.txt', scheduled: true, scheduledTime: new Date(Date.now() - 1000) }
      ];

      const dueItems = filterDueItems(mockSchedule);
      expect(dueItems).toHaveLength(1);
    });
  });
});