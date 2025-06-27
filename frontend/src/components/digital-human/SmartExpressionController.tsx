import React, { useState, useCallback, useEffect } from 'react';
import { getStageRecommendations, FACIAL_EXPRESSIONS, BODY_ACTIONS } from '../../config/avatarConfig';

interface SmartExpressionControllerProps {
  interviewStage: 'greeting' | 'questioning' | 'listening' | 'evaluating' | 'encouraging' | 'closing';
  isAISpeaking: boolean;
  isUserSpeaking: boolean;
  currentMessage?: string;
  onExpressionChange: (expression: string) => void;
  onActionChange: (action: string) => void;
  emotionalContext?: 'positive' | 'neutral' | 'challenging';
}

export const SmartExpressionController: React.FC<SmartExpressionControllerProps> = ({
  interviewStage,
  isAISpeaking,
  isUserSpeaking,
  currentMessage,
  onExpressionChange,
  onActionChange,
  emotionalContext = 'neutral'
}) => {
  const [currentExpression, setCurrentExpression] = useState('neutral');
  const [currentAction, setCurrentAction] = useState('idle');
  const [lastChangeTime, setLastChangeTime] = useState(Date.now());

  // 分析消息内容的情感倾向
  const analyzeMessageSentiment = useCallback((message: string): 'positive' | 'neutral' | 'challenging' => {
    if (!message) return 'neutral';
    
    const positiveKeywords = ['好', '很好', '优秀', '不错', '棒', '成功', '完成', '解决', '满意'];
    const challengingKeywords = ['困难', '挑战', '问题', '失败', '错误', '不足', '改进', '缺点'];
    
    const lowerMessage = message.toLowerCase();
    
    const positiveCount = positiveKeywords.filter(word => lowerMessage.includes(word)).length;
    const challengingCount = challengingKeywords.filter(word => lowerMessage.includes(word)).length;
    
    if (positiveCount > challengingCount) return 'positive';
    if (challengingCount > positiveCount) return 'challenging';
    return 'neutral';
  }, []);

  // 根据面试阶段和上下文选择合适的表情和动作
  const __REMOVED_API_KEY__ = useCallback(() => {
    try {
      const recommendations = getStageRecommendations ? getStageRecommendations(interviewStage) : null;
      const sentiment = currentMessage ? analyzeMessageSentiment(currentMessage) : emotionalContext;
      
      let selectedExpression = 'neutral';
      let selectedAction = 'idle';
      
      // 根据当前状态选择表情和动作
      if (isAISpeaking) {
        // AI正在说话
        selectedAction = 'talking';
        
        switch (interviewStage) {
          case 'greeting':
            selectedExpression = sentiment === 'positive' ? 'smile' : 'encouraging';
            selectedAction = 'gesture_welcome';
            break;
          case 'questioning':
            selectedExpression = 'neutral';
            selectedAction = 'gesture_explain';
            break;
          case 'evaluating':
            selectedExpression = sentiment === 'positive' ? 'pleased' : 'thinking';
            selectedAction = 'lean_forward';
            break;
          case 'encouraging':
            selectedExpression = 'encouraging';
            selectedAction = 'nod';
            break;
          case 'closing':
            selectedExpression = 'smile';
            selectedAction = 'gesture_welcome';
            break;
          default:
            selectedExpression = 'neutral';
            selectedAction = 'talking';
        }
      } else if (isUserSpeaking) {
        // 用户正在说话，AI在倾听
        selectedAction = 'listening';
        
        switch (sentiment) {
          case 'positive':
            selectedExpression = 'pleased';
            selectedAction = 'nod';
            break;
          case 'challenging':
            selectedExpression = 'concerned';
            selectedAction = 'lean_forward';
            break;
          default:
            selectedExpression = 'neutral';
            selectedAction = 'listening';
        }
      } else {
        // 空闲状态
        selectedAction = 'idle';
        
        // 根据面试阶段选择默认表情
        if (recommendations && recommendations.expressions) {
          const stageExpressions = recommendations.expressions;
          selectedExpression = stageExpressions[Math.floor(Math.random() * stageExpressions.length)];
          
          // 偶尔添加一些自然的动作
          const now = Date.now();
          if (now - lastChangeTime > 5000) { // 5秒后可能改变动作
            const stageActions = recommendations.actions;
            if (Math.random() < 0.3) { // 30%概率执行动作
              selectedAction = stageActions[Math.floor(Math.random() * stageActions.length)];
              setLastChangeTime(now);
            }
          }
        }
      }
      
      return { expression: selectedExpression, action: selectedAction };
    } catch (error) {
      console.warn('Error in __REMOVED_API_KEY__:', error);
      return { expression: 'neutral', action: 'idle' };
    }
  }, [interviewStage, isAISpeaking, isUserSpeaking, currentMessage, emotionalContext, analyzeMessageSentiment, lastChangeTime]);

  // 定期更新表情和动作
  useEffect(() => {
    const updateExpressionAndAction = () => {
      const { expression, action } = __REMOVED_API_KEY__();
      
      if (expression !== currentExpression) {
        setCurrentExpression(expression);
        onExpressionChange(expression);
      }
      
      if (action !== currentAction) {
        setCurrentAction(action);
        onActionChange(action);
      }
    };
    
    // 立即更新一次
    updateExpressionAndAction();
    
    // 设置定期更新
    const interval = setInterval(updateExpressionAndAction, 2000); // 每2秒检查一次
    
    return () => clearInterval(interval);
  }, [interviewStage, isAISpeaking, isUserSpeaking, currentMessage, emotionalContext, __REMOVED_API_KEY__, currentExpression, currentAction, onExpressionChange, onActionChange]);

  // 当状态发生重大变化时立即更新
  useEffect(() => {
    const { expression, action } = __REMOVED_API_KEY__();
    
    if (expression !== currentExpression) {
      setCurrentExpression(expression);
      onExpressionChange(expression);
    }
    
    if (action !== currentAction) {
      setCurrentAction(action);
      onActionChange(action);
    }
  }, [isAISpeaking, isUserSpeaking, interviewStage]);

  return null; // 这是一个逻辑组件，不渲染任何UI
};

export default SmartExpressionController;