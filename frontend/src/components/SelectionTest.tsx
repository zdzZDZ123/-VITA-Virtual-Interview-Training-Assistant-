import React, { useState } from 'react';

export const SelectionTest: React.FC = () => {
  const [interviewType, setInterviewType] = useState<'behavioral' | 'technical' | 'situational'>('behavioral');
  const [avatarModel, setAvatarModel] = useState<string>('simple');

  const interviewTypes = [
    { value: 'behavioral', label: '行为面试', icon: '👥' },
    { value: 'technical', label: '技术面试', icon: '💻' },
    { value: 'situational', label: '情境面试', icon: '🎯' }
  ];

  const avatarModels = [
    { value: 'simple', label: '简约风格', icon: '🎨' },
    { value: 'demo', label: '高质量演示', icon: '✨' },
    { value: 'female', label: '女性面试官', icon: '👩‍💼' },
    { value: 'male', label: '男性面试官', icon: '👨‍💼' }
  ];

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold mb-8">选择功能测试</h1>
      
      {/* 面试类型选择测试 */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold mb-4">面试类型选择</h2>
        <p className="mb-4 text-gray-600">当前选择: {interviewType}</p>
        <div className="grid grid-cols-3 gap-4">
          {interviewTypes.map((type) => (
            <button
              key={type.value}
              onClick={() => {
                console.log('点击面试类型:', type.value);
                setInterviewType(type.value as 'behavioral' | 'technical' | 'situational');
              }}
              className={`p-4 border-2 rounded-lg transition-all ${
                interviewType === type.value
                  ? 'border-blue-500 bg-blue-50 text-blue-700'
                  : 'border-gray-300 hover:border-gray-400'
              }`}
            >
              <div className="text-2xl mb-2">{type.icon}</div>
              <div className="font-semibold">{type.label}</div>
              {interviewType === type.value && (
                <div className="mt-2 text-xs bg-blue-100 px-2 py-1 rounded">已选择</div>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* 数字人模型选择测试 */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold mb-4">数字人模型选择</h2>
        <p className="mb-4 text-gray-600">当前选择: {avatarModel}</p>
        <div className="grid grid-cols-2 gap-4">
          {avatarModels.map((model) => (
            <button
              key={model.value}
              onClick={() => {
                console.log('点击数字人模型:', model.value);
                setAvatarModel(model.value);
              }}
              className={`p-4 border-2 rounded-lg transition-all ${
                avatarModel === model.value
                  ? 'border-green-500 bg-green-50 text-green-700'
                  : 'border-gray-300 hover:border-gray-400'
              }`}
            >
              <div className="text-2xl mb-2">{model.icon}</div>
              <div className="font-semibold">{model.label}</div>
              {avatarModel === model.value && (
                <div className="mt-2 text-xs bg-green-100 px-2 py-1 rounded">已选择</div>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* 状态显示 */}
      <div className="bg-gray-100 p-4 rounded-lg">
        <h3 className="font-semibold mb-2">当前状态:</h3>
        <p>面试类型: <span className="font-mono bg-white px-2 py-1 rounded">{interviewType}</span></p>
        <p>数字人模型: <span className="font-mono bg-white px-2 py-1 rounded">{avatarModel}</span></p>
      </div>

      {/* 测试按钮 */}
      <div className="mt-8">
        <button
          onClick={() => {
            alert(`选择结果:\n面试类型: ${interviewType}\n数字人模型: ${avatarModel}`);
          }}
          className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          显示选择结果
        </button>
      </div>
    </div>
  );
}; 