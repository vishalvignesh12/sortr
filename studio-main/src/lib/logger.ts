// Logging service for the application
export class Logger {
  private static instance: Logger;
  private logs: LogEntry[] = [];
  private logLevel: LogLevel = 'info';
  private observers: Array<(log: LogEntry) => void> = [];

  private constructor() {}

  public static getInstance(): Logger {
    if (!Logger.instance) {
      Logger.instance = new Logger();
    }
    return Logger.instance;
  }

  public setLogLevel(level: LogLevel) {
    this.logLevel = level;
  }

  public log(level: LogLevel, message: string, meta?: Record<string, unknown>) {
    const logLevels: Record<LogLevel, number> = {
      error: 0,
      warn: 1,
      info: 2,
      debug: 3
    };

    const currentLevel = logLevels[this.logLevel];
    const messageLevel = logLevels[level];

    if (messageLevel <= currentLevel) {
      const logEntry: LogEntry = {
        timestamp: new Date(),
        level,
        message,
        meta
      };

      this.logs.push(logEntry);

      // Keep only last 1000 logs
      if (this.logs.length > 1000) {
        this.logs = this.logs.slice(-1000);
      }

      // Notify observers
      this.observers.forEach(observer => observer(logEntry));
    }
  }

  public error(message: string, meta?: Record<string, unknown>) {
    this.log('error', message, meta);
  }

  public warn(message: string, meta?: Record<string, unknown>) {
    this.log('warn', message, meta);
  }

  public info(message: string, meta?: Record<string, unknown>) {
    this.log('info', message, meta);
  }

  public debug(message: string, meta?: Record<string, unknown>) {
    this.log('debug', message, meta);
  }

  public getLogs(level?: LogLevel): LogEntry[] {
    if (level) {
      return this.logs.filter(log => log.level === level);
    }
    return [...this.logs];
  }

  public subscribe(observer: (log: LogEntry) => void): () => void {
    this.observers.push(observer);

    // Return unsubscribe function
    return () => {
      const index = this.observers.indexOf(observer);
      if (index !== -1) {
        this.observers.splice(index, 1);
      }
    };
  }

  public clear() {
    this.logs = [];
  }
}

export type LogLevel = 'debug' | 'info' | 'warn' | 'error';

export interface LogEntry {
  timestamp: Date;
  level: LogLevel;
  message: string;
  meta?: Record<string, unknown>;
}

// Predefined logger instance
export const logger = Logger.getInstance();