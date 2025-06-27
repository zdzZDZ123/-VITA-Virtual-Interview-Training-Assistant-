import React, { useState, useRef, useEffect, Suspense } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, ContactShadows, Float } from '@react-three/drei';
import * as THREE from 'three';
import { DigitalHumanModel } from './DigitalHumanModel';
import { LipSyncController } from './LipSyncController';
import { SmartExpressionController } from './SmartExpressionController';
import { EnhancedLighting } from './EnhancedLighting';
import { getAvatarModel } from '../../config/avatarConfig';

interface DigitalHumanViewProps {
  audioUrl?: string;
  audioData?: ArrayBuffer;
  expression?: string;
  action?: string;
  onReady?: () => void;
  className?: string;
  modelUrl?: string;
  avatarId?: string;
  interviewStage?: 'greeting' | 'questioning' | 'listening' | 'evaluating' | 'encouraging' | 'closing';
  isAISpeaking?: boolean;
  isUserSpeaking?: boolean;
  currentMessage?: string;
  emotionalContext?: 'positive' | 'neutral' | 'challenging';
  lightingPreset?: 'studio' | 'office' | 'warm' | 'professional';
  enableSmartExpressions?: boolean;
}

// Loading component with better styling
const LoadingFallback = () => (
  <div className="flex items-center justify-center h-full bg-gradient-to-br from-blue-50 to-indigo-100">
    <div className="text-center">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
      <p className="text-gray-600 font-medium">Loading Digital Human...</p>
    </div>
  </div>
);

export const DigitalHumanView: React.FC<DigitalHumanViewProps> = ({
  audioUrl,
  audioData,
  expression = 'neutral',
  action = 'idle',
  onReady,
  className = '',
  modelUrl,
  avatarId = 'simple',
  interviewStage = 'greeting',
  isAISpeaking = false,
  isUserSpeaking = false,
  currentMessage,
  emotionalContext = 'neutral',
  lightingPreset = 'professional',
  enableSmartExpressions = true,
}) => {
  const [isModelLoaded, setIsModelLoaded] = useState(false);
  const [currentAudio, setCurrentAudio] = useState<HTMLAudioElement | null>(null);
  const [audioError, setAudioError] = useState<string>('');
  const [audioLoadingState, setAudioLoadingState] = useState<'idle' | 'loading' | 'ready' | 'error'>('idle');
  const [smartExpression, setSmartExpression] = useState(expression);
  const [smartAction, setSmartAction] = useState(action);
  const lipSyncControllerRef = useRef<LipSyncController | null>(null);
  const audioUrlsRef = useRef<Set<string>>(new Set());
  
  // 获取当前数字人模型配置
  const avatarConfig = getAvatarModel(avatarId);

  useEffect(() => {
    if (audioUrl || audioData) {
      setAudioLoadingState('loading');
      setAudioError('');
      
      const audio = new Audio();
      
      audio.preload = 'auto';
      audio.crossOrigin = 'anonymous';
      
      const handleAudioError = (error: ErrorEvent | Event) => {
        console.error('Audio loading/playback error:', error);
        let errorMsg = '音频播放失败';
        
        if (audio.error) {
          switch (audio.error.code) {
            case MediaError.MEDIA_ERR_ABORTED:
              errorMsg = '音频加载被中断';
              break;
            case MediaError.MEDIA_ERR_NETWORK:
              errorMsg = '网络错误，无法加载音频';
              break;
            case MediaError.MEDIA_ERR_DECODE:
              errorMsg = '音频解码失败，格式不支持';
              break;
            case MediaError.MEDIA_ERR_SRC_NOT_SUPPORTED:
              errorMsg = '音频格式不支持';
              break;
          }
        }
        
        setAudioError(errorMsg);
        setAudioLoadingState('error');
      };
      
      const handleAudioLoaded = () => {
        console.log('Audio loaded successfully:', audio.duration + 's');
        setAudioLoadingState('ready');
      };
      
      const handleAudioEnded = () => {
        console.log('Audio playback ended');
        setCurrentAudio(null);
        setAudioLoadingState('idle');
      };
      
      audio.addEventListener('error', handleAudioError);
      audio.addEventListener('canplaythrough', handleAudioLoaded);
      audio.addEventListener('ended', handleAudioEnded);
      
      if (audioUrl) {
        audio.src = audioUrl;
      } else if (audioData) {
        const blob = new Blob([audioData], { type: 'audio/mpeg' });
        const blobUrl = URL.createObjectURL(blob);
        audio.src = blobUrl;
        audioUrlsRef.current.add(blobUrl);
      }

      setCurrentAudio(audio);
      
      const playAudio = async () => {
        try {
          await audio.play();
          console.log('Audio started playing automatically');
        } catch (playError) {
          console.warn('Auto-play prevented by browser:', playError);
          setAudioError('请点击页面任意位置以开始音频播放');
          
          const handleUserInteraction = async () => {
            try {
              await audio.play();
              setAudioError('');
              document.removeEventListener('click', handleUserInteraction);
              document.removeEventListener('touchstart', handleUserInteraction);
            } catch (retryError) {
              console.error('Failed to play audio after user interaction:', retryError);
            }
          };
          
          document.addEventListener('click', handleUserInteraction, { once: true });
          document.addEventListener('touchstart', handleUserInteraction, { once: true });
        }
      };
      
      if (audio.readyState >= HTMLMediaElement.HAVE_CURRENT_DATA) {
        playAudio();
      } else {
        audio.addEventListener('canplay', playAudio, { once: true });
      }

      return () => {
        audio.removeEventListener('error', handleAudioError);
        audio.removeEventListener('canplaythrough', handleAudioLoaded);
        audio.removeEventListener('ended', handleAudioEnded);
        audio.pause();
        audio.src = '';
      };
    }
  }, [audioUrl, audioData]);

  // Cleanup blob URLs on unmount
  useEffect(() => {
    return () => {
      audioUrlsRef.current.forEach(url => {
        URL.revokeObjectURL(url);
      });
      audioUrlsRef.current.clear();
    };
  }, []);

  const handleModelLoaded = () => {
    setIsModelLoaded(true);
    onReady?.();
  };

  const handleExpressionChange = (newExpression: string) => {
    setSmartExpression(newExpression);
  };

  const handleActionChange = (newAction: string) => {
    setSmartAction(newAction);
  };

  // 根据面试阶段和情感上下文调整相机位置
  const getCameraPosition = (): [number, number, number] => {
    switch (interviewStage) {
      case 'greeting':
        return [0, 1.5, 3.5]; // 稍微远一点，显示全身
      case 'questioning':
      case 'evaluating':
        return [0, 1.8, 2.8]; // 聚焦头部和上身
      case 'listening':
        return [0.2, 1.6, 3.0]; // 轻微侧角度
      case 'encouraging':
      case 'closing':
        return [0, 1.5, 3.2]; // 友好距离
      default:
        return [0, 1.6, 3.0];
    }
  };

  return (
    <div className={`relative w-full h-full bg-gradient-to-br from-slate-50 to-blue-50 ${className}`}>
      {/* Audio Error Display */}
      {audioError && (
        <div className="absolute top-4 left-4 right-4 z-10">
          <div className="bg-yellow-100 border-l-4 border-yellow-500 text-yellow-700 p-3 rounded shadow-lg">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium">{audioError}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Audio Loading Indicator */}
      {audioLoadingState === 'loading' && (
        <div className="absolute top-4 right-4 z-10">
          <div className="bg-blue-100 text-blue-800 px-3 py-2 rounded-lg shadow-lg flex items-center">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2"></div>
            <span className="text-sm font-medium">Loading Audio...</span>
          </div>
        </div>
      )}

      {/* Model Status Indicator */}
      {!isModelLoaded && (
        <div className="absolute bottom-4 left-4 z-10">
          <div className="bg-gray-100 text-gray-700 px-3 py-2 rounded-lg shadow-lg flex items-center">
            <div className="animate-pulse rounded-full h-3 w-3 bg-gray-400 mr-2"></div>
            <span className="text-sm">Initializing Digital Human...</span>
          </div>
        </div>
      )}

      {/* Avatar Quality Badge */}
      <div className="absolute top-4 left-4 z-10">
        <div className={`px-3 py-1 rounded-full text-xs font-medium shadow-lg ${
          avatarConfig.quality === 'premium' ? 'bg-green-100 text-green-800' :
          avatarConfig.quality === 'standard' ? 'bg-blue-100 text-blue-800' :
          'bg-gray-100 text-gray-800'
        }`}>
          {avatarConfig.name} ({avatarConfig.quality})
        </div>
      </div>

      {/* 3D Canvas */}
      <Canvas
        camera={{
          position: getCameraPosition(),
          fov: 50,
          near: 0.1,
          far: 1000
        }}
        shadows
        gl={{
          antialias: true,
          alpha: true,
          powerPreference: 'high-performance'
        }}
        dpr={[1, 2]} // 响应式像素比
      >
        {/* Enhanced Lighting System */}
        <EnhancedLighting 
          environmentPreset={lightingPreset}
          shadowQuality="high"
          ambientIntensity={0.6}
          directionalIntensity={1.2}
        />
        
        {/* Environment and Background - 使用自定义环境而非preset避免HDR文件加载问题 */}
        {/* <Environment 
          preset="studio" 
          background={false}
          environmentIntensity={0.4}
        /> */}
        
        {/* 使用简单的立方体环境贴图替代HDR */}
        <mesh visible={false}>
          <sphereGeometry args={[100, 32, 16]} />
          <meshBasicMaterial color="#f8fafc" side={THREE.BackSide} />
        </mesh>
        
        {/* Contact Shadows for better grounding */}
        <ContactShadows 
          position={[0, -1, 0]} 
          opacity={0.3} 
          scale={4} 
          blur={2} 
          far={2}
          color="#000000"
        />
        
        {/* Fog for depth */}
        <fog attach="fog" args={['#f8fafc', 8, 15]} />
        
        {/* Smart Expression Controller */}
        {enableSmartExpressions && (
          <SmartExpressionController
            interviewStage={interviewStage}
            isAISpeaking={isAISpeaking}
            isUserSpeaking={isUserSpeaking}
            currentMessage={currentMessage}
            emotionalContext={emotionalContext}
            onExpressionChange={handleExpressionChange}
            onActionChange={handleActionChange}
          />
        )}
        
        {/* Digital Human Model with Float animation */}
        <Suspense fallback={null}>
          <Float
            speed={0.5}
            rotationIntensity={0.1}
            floatIntensity={0.2}
            floatingRange={[0, 0.1]}
          >
            <DigitalHumanModel
              expression={enableSmartExpressions ? smartExpression : expression}
              action={enableSmartExpressions ? smartAction : action}
              audio={currentAudio}
              onLoaded={handleModelLoaded}
              lipSyncControllerRef={lipSyncControllerRef}
              modelUrl={modelUrl}
              avatarId={avatarId}
              interviewStage={interviewStage}
            />
          </Float>
        </Suspense>
        
        {/* Camera Controls */}
        <OrbitControls
          enablePan={false}
          enableZoom={true}
          enableRotate={true}
          minDistance={2}
          maxDistance={6}
          minPolarAngle={Math.PI / 6}
          maxPolarAngle={Math.PI / 2}
          target={[0, 1.5, 0]}
          autoRotate={false}
          autoRotateSpeed={0.5}
        />
      </Canvas>
      
      {/* Loading Overlay */}
      {!isModelLoaded && (
        <div className="absolute inset-0 flex items-center justify-center bg-gradient-to-br from-blue-50/80 to-indigo-100/80 backdrop-blur-sm">
          <LoadingFallback />
        </div>
      )}
    </div>
  );
};