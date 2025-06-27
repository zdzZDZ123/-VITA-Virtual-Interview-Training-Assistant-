import React, { useEffect, useState, useCallback } from 'react';
import { FACIAL_EXPRESSIONS, BODY_ACTIONS, __REMOVED_API_KEY__ } from '../../config/avatarConfig';

interface ExpressionManagerProps {
  avatarId: string;
  interviewStage: 'greeting' | 'questioning' | 'listening' | 'evaluating' | 'closing';
  currentMessage?: string;
  isAISpeaking: boolean;
  isUserSpeaking: boolean;
  emotionalContext?: 'positive' | 'neutral' | 'encouraging' | 'serious';
  onExpressionChange: (expression: string) => void;
  onActionChange: (action: string) => void;
  enableSmartTransitions?: boolean;
}

interface ExpressionState {
  current: string;
  previous: string;
  duration: number;
  intensity: number;
}

interface ActionState {
  current: string;
  previous: string;
  duration: number;
}

export const ExpressionManager: React.FC<ExpressionManagerProps> = ({
  avatarId,
  interviewStage,
  currentMessage,
  isAISpeaking,
  isUserSpeaking,
  emotionalContext = 'neutral',
  onExpressionChange,
  onActionChange,
  enableSmartTransitions = true
}) => {
  const [expressionState, setExpressionState] = useState<ExpressionState>({
    current: 'neutral',
    previous: 'neutral',
    duration: 0,
    intensity: 0.5
  });
  
  const [actionState, setActionState] = useState<ActionState>({
    current: 'idle',
    previous: 'idle',
    duration: 0
  });
  
  const [transitionTimer, setTransitionTimer] = useState<NodeJS.Timeout | null>(null);
  const [isTransitioning, setIsTransitioning] = useState(false);

  // 分析消息情感
  const analyzeMessageSentiment = useCallback((message: string): 'positive' | 'neutral' | 'negative' => {
    if (!message) return 'neutral';
    
    const positiveWords = ['好', '棒', '优秀', '不错', '很好', 'excellent', 'great', 'good', 'wonderful', 'amazing'];
    const negativeWords = ['不好', '差', '错误', '问题', '困难', 'bad', 'wrong', 'error', 'problem', 'difficult'];
    
    const lowerMessage = message.toLowerCase();
    
    const positiveCount = positiveWords.filter(word => lowerMessage.includes(word)).length;
    const negativeCount = negativeWords.filter(word => lowerMessage.includes(word)).length;
    
    if (positiveCount > negativeCount) return 'positive';
    if (negativeCount > positiveCount) return 'negative';
    return 'neutral';
  }, []);

  // 获取推荐的表情和动作
  const __REMOVED_API_KEY__ = useCallback(() => {
    const recommendations = __REMOVED_API_KEY__(avatarId, interviewStage);
    
    // 根据当前状态调整推荐
    let recommendedExpression = recommendations.expressions[0] || 'neutral';
    let recommendedAction = recommendations.actions[0] || 'idle';
    
    // 根据说话状态调整
    if (isAISpeaking) {
      recommendedExpression = emotionalContext === 'encouraging' ? 'encouraging' : 'speaking';
      recommendedAction = 'gesturing';
    } else if (isUserSpeaking) {
      recommendedExpression = 'listening';
      recommendedAction = 'nodding';
    }
    
    // 根据消息情感调整
    if (currentMessage) {
      const sentiment = analyzeMessageSentiment(currentMessage);
      
      switch (sentiment) {
        case 'positive':
          recommendedExpression = 'pleased';
          break;
        case 'negative':
          recommendedExpression = 'concerned';
          break;
        default:
          // 保持当前推荐
          break;
      }
    }
    
    // 根据面试阶段微调
    switch (interviewStage) {
      case 'greeting':
        recommendedExpression = 'welcoming';
        recommendedAction = 'greeting';
        break;
      case 'questioning':
        recommendedExpression = isAISpeaking ? 'inquisitive' : 'neutral';
        recommendedAction = isAISpeaking ? 'gesturing' : 'idle';
        break;
      case 'listening':
        recommendedExpression = 'attentive';
        recommendedAction = 'nodding';
        break;
      case 'evaluating':
        recommendedExpression = 'thoughtful';
        recommendedAction = 'thinking';
        break;
      case 'closing':
        recommendedExpression = 'professional';
        recommendedAction = 'concluding';
        break;
    }
    
    return { expression: recommendedExpression, action: recommendedAction };
  }, [avatarId, interviewStage, isAISpeaking, isUserSpeaking, currentMessage, emotionalContext, analyzeMessageSentiment]);

  // 平滑过渡到新表情
  const transitionToExpression = useCallback((newExpression: string, intensity: number = 0.7) => {
    if (newExpression === expressionState.current && !isTransitioning) return;
    
    setIsTransitioning(true);
    
    // 清除之前的定时器
    if (transitionTimer) {
      clearTimeout(transitionTimer);
    }
    
    // 更新表情状态
    setExpressionState(prev => ({
      current: newExpression,
      previous: prev.current,
      duration: 0,
      intensity
    }));
    
    // 通知父组件
    onExpressionChange(newExpression);
    
    // 设置过渡完成定时器
    const timer = setTimeout(() => {
      setIsTransitioning(false);
    }, 500); // 500ms过渡时间
    
    setTransitionTimer(timer);
  }, [expressionState.current, isTransitioning, transitionTimer, onExpressionChange]);

  // 平滑过渡到新动作
  const transitionToAction = useCallback((newAction: string) => {
    if (newAction === actionState.current) return;
    
    setActionState(prev => ({
      current: newAction,
      previous: prev.current,
      duration: 0
    }));
    
    onActionChange(newAction);
  }, [actionState.current, onActionChange]);

  // 智能表情和动作更新
  useEffect(() => {
    if (!enableSmartTransitions) return;
    
    const { expression, action } = __REMOVED_API_KEY__();
    
    // 计算表情强度
    let intensity = 0.5;
    if (isAISpeaking) intensity = 0.8;
    else if (isUserSpeaking) intensity = 0.6;
    else if (emotionalContext === 'encouraging') intensity = 0.9;
    else if (emotionalContext === 'serious') intensity = 0.7;
    
    transitionToExpression(expression, intensity);
    transitionToAction(action);
  }, [interviewStage, isAISpeaking, isUserSpeaking, currentMessage, emotionalContext, enableSmartTransitions, __REMOVED_API_KEY__, transitionToExpression, transitionToAction]);

  // 定期微表情变化（让数字人更生动）
  useEffect(() => {
    if (!enableSmartTransitions) return;
    
    const microExpressionInterval = setInterval(() => {
      // 只在非说话状态下添加微表情
      if (!isAISpeaking && !isUserSpeaking && !isTransitioning) {
        const microExpressions = ['blink', 'slight_smile', 'eyebrow_raise', 'head_tilt'];
        const randomMicro = microExpressions[Math.floor(Math.random() * microExpressions.length)];
        
        // 短暂显示微表情，然后回到主表情
        transitionToExpression(randomMicro, 0.3);
        
        setTimeout(() => {
          const { expression } = __REMOVED_API_KEY__();
          transitionToExpression(expression, 0.5);
        }, 800);
      }
    }, 5000 + Math.random() * 5000); // 5-10秒随机间隔
    
    return () => clearInterval(microExpressionInterval);
  }, [isAISpeaking, isUserSpeaking, isTransitioning, enableSmartTransitions, transitionToExpression, __REMOVED_API_KEY__]);

  // 清理定时器
  useEffect(() => {
    return () => {
      if (transitionTimer) {
        clearTimeout(transitionTimer);
      }
    };
  }, [transitionTimer]);

  // 获取表情描述
  const getExpressionDescription = (expression: string): string => {
    const expr = FACIAL_EXPRESSIONS.find(e => e.id === expression);
    return expr ? expr.description : '中性表情';
  };

  // 获取动作描述
  const getActionDescription = (action: string): string => {
    const act = BODY_ACTIONS.find(a => a.id === action);
    return act ? act.description : '静止状态';
  };

  // 手动设置表情
  const setManualExpression = (expression: string) => {
    transitionToExpression(expression, 0.8);
  };

  // 手动设置动作
  const setManualAction = (action: string) => {
    transitionToAction(action);
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h4 className="font-medium text-gray-900">表情动作控制</h4>
        <div className="flex items-center space-x-2">
          <span className={`w-2 h-2 rounded-full ${
            isTransitioning ? 'bg-yellow-400 animate-pulse' : 'bg-green-400'
          }`}></span>
          <span className="text-xs text-gray-500">
            {isTransitioning ? '过渡中' : '就绪'}
          </span>
        </div>
      </div>
      
      {/* 当前状态显示 */}
      <div className="grid grid-cols-2 gap-4 text-sm">
        <div className="space-y-2">
          <div className="font-medium text-gray-700">当前表情</div>
          <div className="bg-blue-50 rounded-lg p-3">
            <div className="font-medium text-blue-900">{expressionState.current}</div>
            <div className="text-blue-700 text-xs mt-1">
              {getExpressionDescription(expressionState.current)}
            </div>
            <div className="mt-2">
              <div className="text-xs text-blue-600 mb-1">强度</div>
              <div className="w-full bg-blue-200 rounded-full h-1.5">
                <div 
                  className="bg-blue-600 h-1.5 rounded-full transition-all duration-300"
                  style={{ width: `${expressionState.intensity * 100}%` }}
                ></div>
              </div>
            </div>
          </div>
        </div>
        
        <div className="space-y-2">
          <div className="font-medium text-gray-700">当前动作</div>
          <div className="bg-green-50 rounded-lg p-3">
            <div className="font-medium text-green-900">{actionState.current}</div>
            <div className="text-green-700 text-xs mt-1">
              {getActionDescription(actionState.current)}
            </div>
          </div>
        </div>
      </div>
      
      {/* 状态指示器 */}
      <div className="flex items-center justify-between text-xs text-gray-600">
        <div className="flex items-center space-x-4">
          <span className={`flex items-center space-x-1 ${
            isAISpeaking ? 'text-blue-600 font-medium' : ''
          }`}>
            <span className={`w-1.5 h-1.5 rounded-full ${
              isAISpeaking ? 'bg-blue-600 animate-pulse' : 'bg-gray-300'
            }`}></span>
            <span>AI说话</span>
          </span>
          
          <span className={`flex items-center space-x-1 ${
            isUserSpeaking ? 'text-green-600 font-medium' : ''
          }`}>
            <span className={`w-1.5 h-1.5 rounded-full ${
              isUserSpeaking ? 'bg-green-600 animate-pulse' : 'bg-gray-300'
            }`}></span>
            <span>用户说话</span>
          </span>
        </div>
        
        <div className="text-gray-500">
          阶段: {interviewStage} | 情感: {emotionalContext}
        </div>
      </div>
      
      {/* 快速表情控制 */}
      <div className="border-t pt-3">
        <div className="text-sm font-medium text-gray-700 mb-2">快速表情</div>
        <div className="flex flex-wrap gap-2">
          {['neutral', 'welcoming', 'encouraging', 'thoughtful', 'pleased'].map(expr => (
            <button
              key={expr}
              onClick={() => setManualExpression(expr)}
              className={`px-3 py-1 text-xs rounded-full border transition-colors ${
                expressionState.current === expr
                  ? 'bg-blue-100 border-blue-300 text-blue-700'
                  : 'bg-gray-50 border-gray-200 text-gray-600 hover:bg-gray-100'
              }`}
            >
              {expr}
            </button>
          ))}
        </div>
      </div>
      
      {/* 快速动作控制 */}
      <div>
        <div className="text-sm font-medium text-gray-700 mb-2">快速动作</div>
        <div className="flex flex-wrap gap-2">
          {['idle', 'gesturing', 'nodding', 'thinking', 'greeting'].map(action => (
            <button
              key={action}
              onClick={() => setManualAction(action)}
              className={`px-3 py-1 text-xs rounded-full border transition-colors ${
                actionState.current === action
                  ? 'bg-green-100 border-green-300 text-green-700'
                  : 'bg-gray-50 border-gray-200 text-gray-600 hover:bg-gray-100'
              }`}
            >
              {action}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default ExpressionManager;