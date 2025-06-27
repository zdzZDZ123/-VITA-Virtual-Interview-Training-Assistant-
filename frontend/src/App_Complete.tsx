import React, { useState } from 'react';
import { useInterviewStore } from './store/useInterviewStore';
import './index.css';

function App() {
  const [currentMode, setCurrentMode] = useState<'setup' | 'interview'>('setup');
  const [interviewType, setInterviewType] = useState<'behavioral' | 'technical' | 'situational'>('technical');
  const [jobDescription, setJobDescription] = useState('');
  const [interviewMode, setInterviewMode] = useState<'text' | 'voice' | 'digital'>('text');
  const { startSession, submitAnswer, currentQuestion, isLoading, error } = useInterviewStore();

  const handleStartInterview = async (mode: 'text' | 'voice' | 'digital') => {
    if (!jobDescription.trim()) {
      alert('请输入职位描述');
      return;
    }
    
    try {
      setInterviewMode(mode);
      
      await startSession({
        job_description: jobDescription,
        interview_type: interviewType
      });
      
      setCurrentMode('interview');
    } catch (error) {
      console.error('启动面试失败:', error);
      const errorMessage = error?.response?.data?.detail?.[0]?.msg || error?.message || '未知错误';
      alert(`启动面试失败: ${errorMessage}`);
    }
  };

  const handleSubmitAnswer = async (answer: string) => {
    if (!answer.trim()) return;
    
    try {
      await submitAnswer(answer);
    } catch (error) {
      console.error('提交答案失败:', error);
      alert('提交答案失败');
    }
  };

  const handleEndInterview = () => {
    setCurrentMode('setup');
  };

  if (currentMode === 'setup') {
    return (
      <div style={{ 
        minHeight: '100vh', 
        background: 'linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%)',
        padding: '2rem'
      }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
          {/* 标题区域 */}
          <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
            <h1 style={{ 
              fontSize: '4rem', 
              fontWeight: 'bold', 
              color: '#1565c0',
              marginBottom: '1rem',
              textShadow: '2px 2px 4px rgba(0,0,0,0.1)'
            }}>
              VITA
            </h1>
            <p style={{ 
              fontSize: '1.5rem', 
              color: '#424242',
              marginBottom: '0.5rem'
            }}>
              Virtual Interview & Training Assistant
            </p>
            <p style={{ color: '#757575', fontSize: '1.1rem' }}>
              AI驱动的智能面试训练平台
            </p>
          </div>

          <div style={{
            background: 'white',
            borderRadius: '1rem',
            boxShadow: '0 10px 30px rgba(0,0,0,0.1)',
            padding: '2rem'
          }}>
            <h2 style={{ 
              fontSize: '1.8rem', 
              fontWeight: '600', 
              color: '#333',
              marginBottom: '2rem'
            }}>
              开始您的面试体验
            </h2>
            
            {/* 面试类型选择 */}
            <div style={{ marginBottom: '2rem' }}>
              <label style={{ 
                display: 'block', 
                fontSize: '1rem', 
                fontWeight: '500', 
                color: '#555',
                marginBottom: '1rem'
              }}>
                选择面试类型
              </label>
              <div style={{ 
                display: 'grid', 
                gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
                gap: '1rem'
              }}>
                {[
                  { value: 'behavioral', label: '行为面试', desc: '基于过往经历评估', icon: '🧠' },
                  { value: 'technical', label: '技术面试', desc: '专业技能考察', icon: '💻' },
                  { value: 'situational', label: '情景面试', desc: '应变能力测试', icon: '🎯' }
                ].map((option) => (
                  <label
                    key={option.value}
                    style={{
                      border: interviewType === option.value ? '2px solid #2196F3' : '2px solid #e0e0e0',
                      borderRadius: '0.5rem',
                      padding: '1rem',
                      cursor: 'pointer',
                      background: interviewType === option.value ? '#e3f2fd' : 'white',
                      transition: 'all 0.3s ease'
                    }}
                  >
                    <input
                      type="radio"
                      name="interviewType"
                      value={option.value}
                      checked={interviewType === option.value}
                      onChange={(e) => setInterviewType(e.target.value as typeof interviewType)}
                      style={{ display: 'none' }}
                    />
                    <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>{option.icon}</div>
                    <div style={{ fontWeight: '600', color: '#333', marginBottom: '0.25rem' }}>
                      {option.label}
                    </div>
                    <div style={{ fontSize: '0.9rem', color: '#666' }}>{option.desc}</div>
                  </label>
                ))}
              </div>
            </div>

            {/* 职位描述输入 */}
            <div style={{ marginBottom: '2rem' }}>
              <label style={{ 
                display: 'block', 
                fontSize: '1rem', 
                fontWeight: '500', 
                color: '#555',
                marginBottom: '0.5rem'
              }}>
                职位描述
              </label>
              <textarea
                value={jobDescription}
                onChange={(e) => setJobDescription(e.target.value)}
                placeholder="请详细描述您要应聘的职位，包括职责、要求等..."
                style={{
                  width: '100%',
                  height: '120px',
                  padding: '1rem',
                  border: '2px solid #e0e0e0',
                  borderRadius: '0.5rem',
                  fontSize: '1rem',
                  resize: 'none',
                  outline: 'none',
                  transition: 'border-color 0.3s ease'
                }}
                onFocus={(e) => e.target.style.borderColor = '#2196F3'}
                onBlur={(e) => e.target.style.borderColor = '#e0e0e0'}
              />
            </div>

            {/* 面试模式选择 */}
            <div style={{ 
              display: 'grid', 
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
              gap: '1rem'
            }}>
              {[
                { mode: 'text', icon: '💬', title: '文本面试', desc: '传统问答模式', color: '#4CAF50' },
                { mode: 'voice', icon: '🎤', title: '语音面试', desc: '实时语音交互', color: '#9C27B0' },
                { mode: 'digital', icon: '🤖', title: '数字人面试', desc: '3D虚拟面试官', color: '#FF5722' }
              ].map((option) => (
                <button
                  key={option.mode}
                  onClick={() => handleStartInterview(option.mode as any)}
                  disabled={isLoading}
                  style={{
                    padding: '2rem 1rem',
                    border: '2px solid #e0e0e0',
                    borderRadius: '0.5rem',
                    background: 'white',
                    cursor: isLoading ? 'not-allowed' : 'pointer',
                    textAlign: 'center',
                    transition: 'all 0.3s ease',
                    opacity: isLoading ? 0.6 : 1
                  }}
                  onMouseEnter={(e) => {
                    if (!isLoading) {
                      e.target.style.borderColor = option.color;
                      e.target.style.background = option.color + '10';
                      e.target.style.transform = 'translateY(-2px)';
                      e.target.style.boxShadow = '0 4px 20px rgba(0,0,0,0.1)';
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!isLoading) {
                      e.target.style.borderColor = '#e0e0e0';
                      e.target.style.background = 'white';
                      e.target.style.transform = 'translateY(0)';
                      e.target.style.boxShadow = 'none';
                    }
                  }}
                >
                  <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>{option.icon}</div>
                  <div style={{ fontWeight: '600', color: '#333', marginBottom: '0.5rem' }}>
                    {option.title}
                  </div>
                  <div style={{ fontSize: '0.9rem', color: '#666' }}>{option.desc}</div>
                </button>
              ))}
            </div>

            {error && (
              <div style={{
                marginTop: '1rem',
                padding: '1rem',
                background: '#ffebee',
                border: '1px solid #f44336',
                borderRadius: '0.5rem',
                color: '#c62828'
              }}>
                错误: {error}
              </div>
            )}

            {isLoading && (
              <div style={{
                marginTop: '1rem',
                textAlign: 'center',
                padding: '1rem',
                background: '#e3f2fd',
                borderRadius: '0.5rem',
                color: '#1565c0'
              }}>
                🚀 正在启动面试会话，请稍候...
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  // 面试进行中 - 简化版本
  return (
    <div style={{ minHeight: '100vh', background: '#f5f5f5' }}>
      <div style={{
        background: 'white',
        boxShadow: '0 2px 10px rgba(0,0,0,0.1)',
        borderBottom: '1px solid #e0e0e0',
        padding: '1rem 2rem'
      }}>
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center' 
        }}>
          <h1 style={{ fontSize: '1.5rem', fontWeight: '600', color: '#333' }}>
            {interviewMode === 'text' && '💬 文本面试'}
            {interviewMode === 'voice' && '🎤 语音面试'}
            {interviewMode === 'digital' && '🤖 数字人面试'}
          </h1>
          <button
            onClick={handleEndInterview}
            style={{
              padding: '0.5rem 1rem',
              background: '#f44336',
              color: 'white',
              border: 'none',
              borderRadius: '0.5rem',
              cursor: 'pointer',
              fontSize: '1rem'
            }}
          >
            结束面试
          </button>
        </div>
      </div>

      <div style={{ padding: '2rem', maxWidth: '800px', margin: '0 auto' }}>
        <div style={{
          background: 'white',
          borderRadius: '1rem',
          padding: '2rem',
          boxShadow: '0 4px 20px rgba(0,0,0,0.1)',
          marginBottom: '2rem'
        }}>
          <h3 style={{ color: '#333', marginBottom: '1rem', fontSize: '1.2rem' }}>
            面试问题:
          </h3>
          <div style={{
            background: '#f8f9fa',
            padding: '1.5rem',
            borderRadius: '0.5rem',
            borderLeft: '4px solid #2196F3'
          }}>
            {currentQuestion || '正在加载问题...'}
          </div>
        </div>

        {interviewMode === 'text' && (
          <SimpleTextInterview onSubmit={handleSubmitAnswer} isLoading={isLoading} />
        )}
        {interviewMode === 'voice' && (
          <div style={{
            background: 'white',
            borderRadius: '1rem',
            padding: '2rem',
            textAlign: 'center'
          }}>
            <p style={{ color: '#666', fontSize: '1.1rem' }}>
              🎤 语音面试模式正在开发中...
            </p>
          </div>
        )}
        {interviewMode === 'digital' && (
          <div style={{
            background: 'white',
            borderRadius: '1rem',
            padding: '2rem',
            textAlign: 'center'
          }}>
            <p style={{ color: '#666', fontSize: '1.1rem' }}>
              🤖 数字人面试模式正在开发中...
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

// 简单的文本面试组件
function SimpleTextInterview({ onSubmit, isLoading }: { 
  onSubmit: (answer: string) => void; 
  isLoading: boolean;
}) {
  const [answer, setAnswer] = useState('');

  const handleSubmit = () => {
    if (answer.trim()) {
      onSubmit(answer);
      setAnswer('');
    }
  };

  return (
    <div style={{
      background: 'white',
      borderRadius: '1rem',
      padding: '2rem',
      boxShadow: '0 4px 20px rgba(0,0,0,0.1)'
    }}>
      <h3 style={{ color: '#333', marginBottom: '1rem', fontSize: '1.2rem' }}>
        您的回答:
      </h3>
      <textarea
        value={answer}
        onChange={(e) => setAnswer(e.target.value)}
        placeholder="请输入您的回答..."
        style={{
          width: '100%',
          height: '150px',
          padding: '1rem',
          border: '2px solid #e0e0e0',
          borderRadius: '0.5rem',
          fontSize: '1rem',
          resize: 'none',
          outline: 'none',
          marginBottom: '1rem'
        }}
      />
      <button
        onClick={handleSubmit}
        disabled={isLoading || !answer.trim()}
        style={{
          padding: '1rem 2rem',
          background: isLoading || !answer.trim() ? '#ccc' : '#2196F3',
          color: 'white',
          border: 'none',
          borderRadius: '0.5rem',
          cursor: isLoading || !answer.trim() ? 'not-allowed' : 'pointer',
          fontSize: '1rem',
          fontWeight: '600'
        }}
      >
        {isLoading ? '提交中...' : '提交回答'}
      </button>
    </div>
  );
}

export default App; 