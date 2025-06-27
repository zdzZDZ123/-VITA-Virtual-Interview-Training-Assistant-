import React, { useEffect, useRef, useState } from 'react';
import { Camera, CameraOff } from 'lucide-react';
import { Button } from '../ui/button';
import { logger } from '@/utils/logger';

interface WebcamViewProps {
  onStreamReady: (stream: MediaStream) => void;
  onStreamError: (error: Error) => void;
  className?: string;
  autoStart?: boolean;
}

export const WebcamView: React.FC<WebcamViewProps> = ({
  onStreamReady,
  onStreamError,
  className = '',
  autoStart = false,
}) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isActive, setIsActive] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Start webcam
  const startWebcam = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 1280 },
          height: { ideal: 720 },
          facingMode: 'user',
        },
        audio: false,
      });

      streamRef.current = stream;

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }

      setIsActive(true);
      onStreamReady(stream);
      logger.info('Webcam started successfully');
    } catch (err) {
      const error = err as Error;
      logger.error('Failed to start webcam', error);
      setError(error.message);
      onStreamError(error);
    } finally {
      setIsLoading(false);
    }
  };

  // Stop webcam
  const stopWebcam = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }

    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }

    setIsActive(false);
    logger.info('Webcam stopped');
  };

  // Toggle webcam
  const toggleWebcam = () => {
    if (isActive) {
      stopWebcam();
    } else {
      startWebcam();
    }
  };

  // Auto start on mount if enabled
  useEffect(() => {
    if (autoStart) {
      startWebcam();
    }

    // Cleanup on unmount
    return () => {
      stopWebcam();
    };
  }, []);

  return (
    <div className={`relative ${className}`}>
      {/* Video element */}
      <div className="relative w-full h-full bg-gray-900 rounded-lg overflow-hidden">
        {isActive ? (
          <video
            ref={videoRef}
            className="w-full h-full object-cover"
            autoPlay
            playsInline
            muted
          />
        ) : (
          <div className="flex items-center justify-center w-full h-full">
            <div className="text-center">
              <CameraOff className="w-16 h-16 mx-auto mb-4 text-gray-500" />
              <p className="text-gray-400">Camera is off</p>
            </div>
          </div>
        )}

        {/* Loading overlay */}
        {isLoading && (
          <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center">
            <div className="text-white">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white mx-auto mb-2"></div>
              <p>Starting camera...</p>
            </div>
          </div>
        )}

        {/* Error message */}
        {error && (
          <div className="absolute bottom-4 left-4 right-4 bg-red-500 text-white p-3 rounded">
            <p className="text-sm">{error}</p>
          </div>
        )}
      </div>

      {/* Control button */}
      <div className="absolute bottom-4 right-4">
        <Button
          onClick={toggleWebcam}
          disabled={isLoading}
          variant={isActive ? 'destructive' : 'default'}
          size="sm"
          className="shadow-lg"
        >
          {isActive ? (
            <>
              <CameraOff className="w-4 h-4 mr-2" />
              Stop Camera
            </>
          ) : (
            <>
              <Camera className="w-4 h-4 mr-2" />
              Start Camera
            </>
          )}
        </Button>
      </div>
    </div>
  );
}; 