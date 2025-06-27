import React, { Suspense, useEffect, useState } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, useGLTF, Html, Preload } from '@react-three/drei';
import { logger } from '@/utils/logger';

// Avatar model component
function AvatarModel({ modelPath }: { modelPath: string }) {
  const { scene } = useGLTF(modelPath);
  
  useEffect(() => {
    logger.info('Avatar model loaded', { modelPath });
  }, [modelPath]);
  
  return <primitive object={scene} scale={[1, 1, 1]} position={[0, -1, 0]} />;
}

// Loading component
function LoadingFallback() {
  return (
    <Html center>
      <div className="text-white text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4"></div>
        <p>Loading avatar...</p>
      </div>
    </Html>
  );
}

interface AvatarCanvasProps {
  modelPath: string;
  className?: string;
  enableControls?: boolean;
  autoRotate?: boolean;
}

export const AvatarCanvas: React.FC<AvatarCanvasProps> = ({
  modelPath,
  className = '',
  enableControls = true,
  autoRotate = false,
}) => {
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Preload the model
  useEffect(() => {
    useGLTF.preload(modelPath);
  }, [modelPath]);

  const handleError = (error: Error) => {
    logger.error('Failed to load avatar model', error);
    setError(error.message);
    setIsLoading(false);
  };

  return (
    <div className={`relative w-full h-full bg-gradient-to-b from-gray-900 to-gray-800 rounded-lg overflow-hidden ${className}`}>
      {error ? (
        <div className="absolute inset-0 flex items-center justify-center text-white">
          <div className="text-center">
            <p className="text-red-400 mb-2">Failed to load avatar</p>
            <p className="text-sm text-gray-400">{error}</p>
          </div>
        </div>
      ) : (
        <Canvas
          camera={{ position: [0, 0, 5], fov: 50 }}
          onCreated={() => setIsLoading(false)}
          onError={handleError}
        >
          {/* Lighting */}
          <ambientLight intensity={0.5} />
          <spotLight
            position={[10, 10, 10]}
            angle={0.15}
            penumbra={1}
            decay={0}
            intensity={Math.PI}
          />
          <pointLight position={[-10, -10, -10]} decay={0} intensity={Math.PI} />
          
          {/* Avatar Model with Suspense */}
          <Suspense fallback={<LoadingFallback />}>
            <AvatarModel modelPath={modelPath} />
            <Preload all />
          </Suspense>
          
          {/* Controls */}
          {enableControls && (
            <OrbitControls
              enablePan={false}
              enableZoom={false}
              autoRotate={autoRotate}
              autoRotateSpeed={1}
              minPolarAngle={Math.PI / 3}
              maxPolarAngle={Math.PI / 1.5}
            />
          )}
        </Canvas>
      )}
      
      {/* Loading overlay */}
      {isLoading && !error && (
        <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center">
          <div className="text-white text-center">
            <div className="animate-pulse">
              <div className="w-16 h-16 bg-blue-500 rounded-full mx-auto mb-4"></div>
              <p>Initializing 3D environment...</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Lazy load the component for better performance
export default React.memo(AvatarCanvas); 