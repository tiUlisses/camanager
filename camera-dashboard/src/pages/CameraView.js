import React from 'react';
import VideoPlayer from '../components/VideoPlayer';

function CameraView({ cameraId }) {
  const videoSrc = `/streams/output/${cameraId}/stream.m3u8`;


  return (
    <div>
    
      <VideoPlayer src={videoSrc} />
    </div>
  );
}

export default CameraView;
