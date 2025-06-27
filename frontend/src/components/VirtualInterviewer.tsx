import React from 'react';

interface VirtualInterviewerProps {
  currentQuestion: string;
  isAsking: boolean;
}

/**
 * 旧 InterviewRoom 使用的占位组件，现阶段仅简单展示问题文本。
 * 后续可以替换为数字人组件或删除此依赖。
 */
const VirtualInterviewer: React.FC<VirtualInterviewerProps> = ({ currentQuestion, isAsking }) => {
  return (
    <div className="flex flex-col items-center justify-center h-full text-center p-6">
      <div className="w-32 h-32 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-4xl font-bold text-white mb-4">
        AI
      </div>
      <h3 className="text-lg font-semibold mb-2">虚拟面试官</h3>
      <p className="text-gray-300 max-w-xs">
        {isAsking ? currentQuestion || '正在生成问题…' : '等待你的回答…'}
      </p>
    </div>
  );
};

export default VirtualInterviewer; 