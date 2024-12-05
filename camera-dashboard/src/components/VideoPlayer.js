import React, { useEffect, useRef } from 'react';
import Hls from 'hls.js';

const VideoPlayer = ({ src }) => {
  const videoRef = useRef(null);

  useEffect(() => {
    if (Hls.isSupported()) {
      const hls = new Hls();
      hls.loadSource(src);
      hls.attachMedia(videoRef.current);
      hls.on(Hls.Events.MANIFEST_PARSED, () => {
        videoRef.current.play(); // Inicia o vídeo automaticamente quando o manifesto é carregado
      });
    } else if (videoRef.current.canPlayType('application/vnd.apple.mpegurl')) {
      videoRef.current.src = src;
      videoRef.current.addEventListener('loadedmetadata', () => {
        videoRef.current.play(); // Inicia o vídeo automaticamente para dispositivos que suportam HLS nativamente
      });
    }
  }, [src]);

  return <video ref={videoRef} controls autoPlay muted style={{ width: '100%' }} />;
};

export default VideoPlayer;
