# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

auto_X is a Node.js-based automated X (Twitter) posting system that uses GitHub Actions for scheduling. The system reads text files from the `sns/` directory and posts them to X API according to a configured schedule.

## Common Development Commands

```bash
# Install dependencies
npm install

# Run tests
npm test
npm run test:watch

# Linting and validation
npm run lint                    # Validate posting files
node cli/index.js lint

# Development and planning
npm run plan                    # Show posting schedule
npm run run                     # Simulation mode
node cli/index.js run --due-only    # Execute due posts (production)

# Configuration management
node cli/index.js migrate-config    # Migrate legacy config
```

## Architecture Overview

### Core Components
- `core/` - Business logic modules (OAuth, API client, scheduler, file manager)
- `cli/` - Command-line interface using Commander.js
- `scripts/` - Legacy compatibility layer

### Key Design Patterns
- **Modular Architecture**: Core logic separated from CLI and GitHub Actions
- **Functional Programming**: Pure functions with JSON input/output for testability
- **Error Handling**: Exponential backoff for rate limiting, graceful API fallbacks
- **Configuration**: Backward compatibility with legacy config keys

### Authentication
- OAuth 1.0a implementation with RFC3986-compliant percent encoding
- API credentials read from environment variables (preferred) or config file
- Dual endpoint support: api.x.com (primary) → api.twitter.com (fallback)

### Scheduling System
- JST timezone-based scheduling
- Configurable intervals (fractional days supported)
- Weekend skipping capability
- Auto-start or fixed start date options

## File Structure & Conventions

```
core/
├── oauth.js          # OAuth 1.0a signature generation
├── twitter-api.js    # X API client with retry logic
├── scheduler.js      # Date/time calculations
├── file-manager.js   # File operations and validation
├── config.js         # Configuration loading/migration
├── logger.js         # JST logging utilities
└── index.js          # Core API exports

sns/
├── *.txt            # Posting queue (UTF-8, 280 chars max)
└── posted/          # Archive for successful posts
```

## Testing

Jest framework with focus on core functions:
- OAuth signature generation
- Scheduling calculations  
- Configuration validation
- File processing logic

Run specific test suites:
```bash
npm test oauth
npm test scheduler  
npm test config
```

## GitHub Actions Integration

Workflow triggers:
- **Scheduled**: Daily 09:00 JST (`cron: '0 0 * * *'`)
- **Manual**: workflow_dispatch with simulation mode option

Environment variables required:
- `TW_API_KEY`
- `TW_API_KEY_SECRET`
- `TW_ACCESS_TOKEN`
- `TW_ACCESS_TOKEN_SECRET`

## Security Considerations

- API credentials never logged or exposed in output
- GitHub Actions uses minimum required permissions
- No PR triggers to prevent secret exposure
- Configuration supports environment variable override

## Error Handling Patterns

- **Rate Limiting**: Exponential backoff (1.5s → 3s → 6s → ... max 45s)
- **API Failures**: Multi-endpoint fallback with retry logic
- **File Operations**: Backup creation before modifications
- **Validation**: Comprehensive input validation with detailed error messages

## Development Workflow

1. Add/modify posting files in `sns/`
2. Validate with `npm run lint`
3. Test schedule with `npm run plan`
4. Simulate execution with `npm run run`
5. Deploy via GitHub Actions or manual `--due-only` execution

## Configuration Schema

New format (`configs/sns.json`):
```json
{
  "posting": {
    "use": boolean,
    "startDate": "auto" | "YYYY-MM-DD",
    "interval": number,
    "postTime": "auto" | "HH:MM", 
    "autoTimeOffset": number,
    "skipWeekends": boolean
  },
  "twitterApi": { /* credentials */ }
}
```

Legacy key migration is automatic and backwards compatible.