import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  resetOnPropsChange?: boolean;
}

interface State {
  hasError: boolean;
  error?: Error;
  errorInfo?: ErrorInfo;
  errorId: string;
}

export class ErrorBoundary extends Component<Props, State> {
  private resetTimeoutId: number | null = null;

  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      errorId: `error_${Date.now()}`
    };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return {
      hasError: true,
      error,
      errorId: `error_${Date.now()}`
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('🚨 ErrorBoundary caught an error:', error, errorInfo);
    
    this.setState({
      error,
      errorInfo
    });

    // 调用用户提供的错误处理函数
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // 特定于数字人组件的错误处理
    this.handleDigitalHumanErrors(error, errorInfo);

    // 5秒后自动重置错误状态
    this.resetTimeoutId = window.setTimeout(() => {
      this.resetErrorBoundary();
    }, 5000);
  }

  componentDidUpdate(prevProps: Props) {
    const { hasError } = this.state;
    const { resetOnPropsChange } = this.props;

    // 如果设置了resetOnPropsChange，当props变化时重置错误
    if (hasError && prevProps.children !== this.props.children && resetOnPropsChange) {
      this.resetErrorBoundary();
    }
  }

  componentWillUnmount() {
    if (this.resetTimeoutId) {
      clearTimeout(this.resetTimeoutId);
    }
  }

  private handleDigitalHumanErrors(error: Error, errorInfo: ErrorInfo) {
    const errorMessage = error.message.toLowerCase();
    const componentStack = errorInfo.componentStack.toLowerCase();

    // 检查是否是Three.js相关错误
    if (errorMessage.includes('three') || componentStack.includes('digitalhumanmodel')) {
      console.warn('🤖 数字人组件错误，尝试清理资源...');
      
      // 尝试清理Three.js资源
      this.cleanupThreeJSResources();
      
      // 尝试清理音频上下文
      this.cleanupAudioContext();
    }

    // 检查是否是WebGL相关错误
    if (errorMessage.includes('webgl') || errorMessage.includes('context')) {
      console.warn('🎮 WebGL上下文错误，建议刷新页面');
      
      // 可以在这里添加用户提示逻辑
      this.notifyWebGLError();
    }
  }

  private cleanupThreeJSResources() {
    try {
      // 清理可能的Three.js资源
      if (window && (window as any).__THREE_RESOURCES) {
        const resources = (window as any).__THREE_RESOURCES;
        
        // 清理几何体
        if (resources.geometries) {
          resources.geometries.forEach((geometry: any) => {
            if (geometry.dispose) geometry.dispose();
          });
          resources.geometries.clear();
        }

        // 清理材质
        if (resources.materials) {
          resources.materials.forEach((material: any) => {
            if (material.dispose) material.dispose();
          });
          resources.materials.clear();
        }
      }
    } catch (cleanupError) {
      console.warn('⚠️ 资源清理失败:', cleanupError);
    }
  }

  private cleanupAudioContext() {
    try {
      // 关闭可能的音频上下文
      if (window && (window as any).audioContexts) {
        const contexts = (window as any).audioContexts;
        contexts.forEach((ctx: AudioContext) => {
          if (ctx.state !== 'closed') {
            ctx.close().catch(console.warn);
          }
        });
        (window as any).audioContexts = [];
      }
    } catch (cleanupError) {
      console.warn('⚠️ 音频上下文清理失败:', cleanupError);
    }
  }

  private notifyWebGLError() {
    // 可以触发用户通知
    const event = new CustomEvent('webgl-error', {
      detail: { 
        error: this.state.error,
        suggestion: '请刷新页面或检查浏览器WebGL支持'
      }
    });
    window.dispatchEvent(event);
  }

  public resetErrorBoundary = () => {
    if (this.resetTimeoutId) {
      clearTimeout(this.resetTimeoutId);
      this.resetTimeoutId = null;
    }

    this.setState({
      hasError: false,
      error: undefined,
      errorInfo: undefined,
      errorId: `reset_${Date.now()}`
    });
  };

  render() {
    if (this.state.hasError) {
      // 自定义错误UI
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="error-boundary-fallback">
          <div className="error-container">
            <h2>🚨 组件错误</h2>
            <p>数字人组件遇到了问题，正在尝试恢复...</p>
            
            <details className="error-details">
              <summary>错误详情</summary>
              <pre className="error-stack">
                {this.state.error?.message}
                {this.state.errorInfo?.componentStack}
              </pre>
            </details>
              
              <button 
              onClick={this.resetErrorBoundary}
              className="reset-button"
              >
              🔄 重试
              </button>
          </div>

          <style jsx>{`
            .error-boundary-fallback {
              display: flex;
              align-items: center;
              justify-content: center;
              min-height: 200px;
              padding: 20px;
              background: linear-gradient(135deg, #ffeaa7, #fab1a0);
              border-radius: 8px;
              margin: 10px;
            }
            
            .error-container {
              text-align: center;
              max-width: 500px;
            }
            
            .error-details {
              margin: 15px 0;
              text-align: left;
            }
            
            .error-stack {
              background: #2d3748;
              color: #e2e8f0;
              padding: 10px;
              border-radius: 4px;
              font-size: 12px;
              overflow-x: auto;
            }
            
            .reset-button {
              background: #4299e1;
              color: white;
              border: none;
              padding: 10px 20px;
              border-radius: 6px;
              cursor: pointer;
              font-size: 14px;
              transition: background 0.2s;
            }
            
            .reset-button:hover {
              background: #3182ce;
            }
          `}</style>
        </div>
      );
    }

    return this.props.children;
  }
}