/**
 * Simple logger utility for frontend
 */

type LogLevel = 'debug' | 'info' | 'warn' | 'error';

interface LogEntry {
  timestamp: string;
  level: LogLevel;
  message: string;
  data?: unknown;
}

class Logger {
  private isDevelopment = import.meta.env.DEV;

  private log(level: LogLevel, message: string, data?: unknown) {
    const entry: LogEntry = {
      timestamp: new Date().toISOString(),
      level,
      message,
      data,
    };

    // In development, use console methods
    if (this.isDevelopment) {
      const consoleMethod = {
        debug: console.debug,
        info: console.info,
        warn: console.warn,
        error: console.error,
      }[level];

      consoleMethod(`[${entry.timestamp}] ${message}`, data || '');
    }

    // In production, you might want to send logs to a service
    // Example: sendToLogService(entry);
  }

  debug(message: string, data?: unknown) {
    this.log('debug', message, data);
  }

  info(message: string, data?: unknown) {
    this.log('info', message, data);
  }

  warn(message: string, data?: unknown) {
    this.log('warn', message, data);
  }

  error(message: string, error?: Error | unknown) {
    const errorData = error instanceof Error 
      ? { error: error.message, stack: error.stack }
      : { error: error };
    
    this.log('error', message, errorData);
  }
}

export const logger = new Logger(); 