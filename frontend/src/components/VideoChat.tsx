import React from 'react';

interface VideoChatProps {
  // 预留接口，用于后续WebRTC功能扩展
  placeholder?: boolean;
}

const VideoChat: React.FC<VideoChatProps> = () => {
  return (
    <div className="w-full h-full bg-gray-700 rounded-lg flex items-center justify-center">
      <div className="text-center text-gray-400">
        <svg className="w-16 h-16 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
        </svg>
        <p>WebRTC 视频聊天</p>
        <p className="text-sm">功能开发中...</p>
      </div>
    </div>
  );
};

export default VideoChat; 