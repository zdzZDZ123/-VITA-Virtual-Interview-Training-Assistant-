import React from 'react';
import * as THREE from 'three';

interface EnhancedLightingProps {
  environmentPreset?: 'studio' | 'office' | 'warm' | 'professional' | 'cinematic' | 'natural';
  shadowQuality?: 'low' | 'medium' | 'high' | 'ultra';
  ambientIntensity?: number;
  directionalIntensity?: number;
  enableVolumetricLighting?: boolean;
  timeOfDay?: 'morning' | 'noon' | 'afternoon' | 'evening';
}

export const EnhancedLighting: React.FC<EnhancedLightingProps> = ({
  environmentPreset = 'professional',
  shadowQuality = 'high',
  ambientIntensity = 0.6,
  directionalIntensity = 1.2,
  enableVolumetricLighting = true,
  timeOfDay = 'noon'
}) => {
  // 根据时间调整光照颜色
  const getTimeBasedColor = (baseColor: string): string => {
    switch (timeOfDay) {
      case 'morning':
        return '#fff8e1'; // 温暖的晨光
      case 'noon':
        return '#ffffff'; // 纯白光
      case 'afternoon':
        return '#fff3e0'; // 稍微温暖
      case 'evening':
        return '#fce4ec'; // 柔和的粉色调
      default:
        return baseColor;
    }
  };

  // 获取阴影配置
  const getShadowMapSize = () => {
    switch (shadowQuality) {
      case 'low': return 512;
      case 'medium': return 1024;
      case 'high': return 2048;
      case 'ultra': return 4096;
      default: return 2048;
    }
  };

  // 环境光照配置
  const lightingConfigs = {
    studio: {
      ambient: { color: getTimeBasedColor('#f8fafc'), intensity: ambientIntensity * 0.8 },
      key: { 
        color: getTimeBasedColor('#ffffff'), 
        intensity: directionalIntensity * 1.2, 
        position: [-2, 4, 3] as [number, number, number],
        castShadow: true
      },
      fill: { 
        color: '#e2e8f0', 
        intensity: directionalIntensity * 0.6, 
        position: [2, 2, 2] as [number, number, number]
      },
      rim: { 
        color: '#cbd5e1', 
        intensity: directionalIntensity * 0.4, 
        position: [0, 2, -3] as [number, number, number]
      },
      accent: {
        color: '#3b82f6',
        intensity: directionalIntensity * 0.3,
        position: [3, 1, 1] as [number, number, number]
      }
    },
    office: {
      ambient: { color: getTimeBasedColor('#f1f5f9'), intensity: ambientIntensity * 0.9 },
      key: { 
        color: getTimeBasedColor('#f8fafc'), 
        intensity: directionalIntensity * 1.0, 
        position: [-1.5, 3.5, 2.5] as [number, number, number],
        castShadow: true
      },
      fill: { 
        color: '#e2e8f0', 
        intensity: directionalIntensity * 0.7, 
        position: [1.5, 2.5, 1.5] as [number, number, number]
      },
      rim: { 
        color: '#94a3b8', 
        intensity: directionalIntensity * 0.3, 
        position: [0, 1.5, -2.5] as [number, number, number]
      }
    },
    warm: {
      ambient: { color: getTimeBasedColor('#fef7ed'), intensity: ambientIntensity * 1.0 },
      key: { 
        color: getTimeBasedColor('#fff7ed'), 
        intensity: directionalIntensity * 1.1, 
        position: [-2, 3.5, 2] as [number, number, number],
        castShadow: true
      },
      fill: { 
        color: '#fed7aa', 
        intensity: directionalIntensity * 0.8, 
        position: [2, 2, 1] as [number, number, number]
      },
      rim: { 
        color: '#fdba74', 
        intensity: directionalIntensity * 0.5, 
        position: [0, 1, -2] as [number, number, number]
      }
    },
    professional: {
      ambient: { color: getTimeBasedColor('#f8fafc'), intensity: ambientIntensity * 0.7 },
      key: { 
        color: getTimeBasedColor('#ffffff'), 
        intensity: directionalIntensity * 1.3, 
        position: [-2.5, 4.5, 3.5] as [number, number, number],
        castShadow: true
      },
      fill: { 
        color: '#e2e8f0', 
        intensity: directionalIntensity * 0.5, 
        position: [2.5, 3, 2] as [number, number, number]
      },
      rim: { 
        color: '#cbd5e1', 
        intensity: directionalIntensity * 0.6, 
        position: [0, 2.5, -4] as [number, number, number]
      },
      accent: {
        color: '#1e40af',
        intensity: directionalIntensity * 0.2,
        position: [-3, 1, 0] as [number, number, number]
      }
    },
    cinematic: {
      ambient: { color: getTimeBasedColor('#1e293b'), intensity: ambientIntensity * 0.3 },
      key: { 
        color: getTimeBasedColor('#f1f5f9'), 
        intensity: directionalIntensity * 1.8, 
        position: [-3, 5, 4] as [number, number, number],
        castShadow: true
      },
      fill: { 
        color: '#475569', 
        intensity: directionalIntensity * 0.4, 
        position: [3, 2, 2] as [number, number, number]
      },
      rim: { 
        color: '#0ea5e9', 
        intensity: directionalIntensity * 0.8, 
        position: [0, 3, -5] as [number, number, number]
      },
      accent: {
        color: '#f59e0b',
        intensity: directionalIntensity * 0.6,
        position: [4, 1, -1] as [number, number, number]
      }
    },
    natural: {
      ambient: { color: getTimeBasedColor('#f0f9ff'), intensity: ambientIntensity * 1.1 },
      key: { 
        color: getTimeBasedColor('#fefce8'), 
        intensity: directionalIntensity * 0.9, 
        position: [-1, 4, 2] as [number, number, number],
        castShadow: true
      },
      fill: { 
        color: '#dbeafe', 
        intensity: directionalIntensity * 0.6, 
        position: [1, 2, 1] as [number, number, number]
      },
      rim: { 
        color: '#bae6fd', 
        intensity: directionalIntensity * 0.4, 
        position: [0, 1, -2] as [number, number, number]
      }
    }
  };

  const config = lightingConfigs[environmentPreset];
  const shadowMapSize = getShadowMapSize();

  return (
    <>
      {/* 环境光 */}
      <ambientLight 
        color={config.ambient.color} 
        intensity={config.ambient.intensity} 
      />
      
      {/* 主光源 (Key Light) */}
      <directionalLight
        color={config.key.color}
        intensity={config.key.intensity}
        position={config.key.position}
        castShadow={config.key.castShadow}
        shadow-mapSize={[shadowMapSize, shadowMapSize]}
        shadow-camera-near={0.1}
        shadow-camera-far={50}
        shadow-camera-left={-10}
        shadow-camera-right={10}
        shadow-camera-top={10}
        shadow-camera-bottom={-10}
        shadow-bias={-0.0001}
        shadow-normalBias={0.02}
        shadow-radius={shadowQuality === 'ultra' ? 8 : shadowQuality === 'high' ? 6 : 4}
      />
      
      {/* 补光 (Fill Light) */}
      <directionalLight
        color={config.fill.color}
        intensity={config.fill.intensity}
        position={config.fill.position}
      />
      
      {/* 轮廓光 (Rim Light) */}
      <directionalLight
        color={config.rim.color}
        intensity={config.rim.intensity}
        position={config.rim.position}
      />
      
      {/* 重点光 (Accent Light) - 仅在某些预设中使用 */}
      {config.accent && (
        <spotLight
          color={config.accent.color}
          intensity={config.accent.intensity}
          position={config.accent.position}
          angle={Math.PI / 6}
          penumbra={0.5}
          distance={10}
          decay={2}
        />
      )}
      
      {/* 体积光效果 */}
      {enableVolumetricLighting && (
        <>
          {/* 额外的点光源用于体积光效果 */}
          <pointLight
            color={getTimeBasedColor('#ffffff')}
            intensity={directionalIntensity * 0.3}
            position={[-1, 3, 1]}
            distance={8}
            decay={2}
          />
          
          <pointLight
            color={getTimeBasedColor('#e0f2fe')}
            intensity={directionalIntensity * 0.2}
            position={[2, 2, -1]}
            distance={6}
            decay={2}
          />
        </>
      )}
      
      {/* 地面反射光 */}
      <hemisphereLight
        skyColor={getTimeBasedColor('#87ceeb')}
        groundColor={getTimeBasedColor('#8b7355')}
        intensity={ambientIntensity * 0.4}
      />
    </>
  );
};

export default EnhancedLighting;