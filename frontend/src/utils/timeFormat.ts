/**
 * 时间格式化工具函数
 */

/**
 * 将秒数格式化为 MM:SS 格式
 * @param seconds 秒数
 * @returns 格式化的时间字符串
 */
export const formatTime = (seconds: number): string => {
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  
  return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
};

/**
 * 将毫秒格式化为可读的时间字符串
 * @param milliseconds 毫秒数
 * @returns 格式化的时间字符串
 */
export const formatDuration = (milliseconds: number): string => {
  const totalSeconds = Math.floor(milliseconds / 1000);
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  
  if (hours > 0) {
    return `${hours}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
  }
  
  return `${minutes}:${seconds.toString().padStart(2, '0')}`;
};

/**
 * 获取相对时间字符串（如：刚刚、1分钟前）
 * @param date 日期对象
 * @returns 相对时间字符串
 */
export const getRelativeTime = (date: Date): string => {
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSeconds = Math.floor(diffMs / 1000);
  const diffMinutes = Math.floor(diffSeconds / 60);
  const diffHours = Math.floor(diffMinutes / 60);
  const diffDays = Math.floor(diffHours / 24);
  
  if (diffSeconds < 60) {
    return '刚刚';
  } else if (diffMinutes < 60) {
    return `${diffMinutes}分钟前`;
  } else if (diffHours < 24) {
    return `${diffHours}小时前`;
  } else if (diffDays < 7) {
    return `${diffDays}天前`;
  } else {
    return date.toLocaleDateString('zh-CN');
  }
};

/**
 * 格式化时间秒数为人类可读的字符串
 * @param seconds 秒数
 * @returns 人类可读的时间字符串 (例如: "1分23秒" 或 "1小时23分45秒")
 */
export const formatTimeHuman = (seconds: number): string => {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const remainingSeconds = seconds % 60;

  if (hours > 0) {
    if (minutes > 0) {
      return `${hours}小时${minutes}分${remainingSeconds}秒`;
    } else {
      return `${hours}小时${remainingSeconds}秒`;
    }
  } else if (minutes > 0) {
    return `${minutes}分${remainingSeconds}秒`;
  } else {
    return `${remainingSeconds}秒`;
  }
};

/**
 * 获取时间戳的可读格式
 * @param timestamp 时间戳 (Date 对象或毫秒数)
 * @returns 格式化的时间字符串
 */
export const formatTimestamp = (timestamp: Date | number): string => {
  const date = timestamp instanceof Date ? timestamp : new Date(timestamp);
  return date.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });
}; 