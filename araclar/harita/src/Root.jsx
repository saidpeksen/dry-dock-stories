import React from 'react';
import {Composition} from 'remotion';
import {MapScene} from './MapScene.jsx';

// Kare sayısı, boyut ve hız dışarıdan (render.mjs) gelir; varsayılanlar yalnız önizleme içindir.
export const Root = () => (
  <Composition
    id="Harita"
    component={MapScene}
    width={1080}
    height={1920}
    fps={30}
    durationInFrames={240}
    defaultProps={{frames: 240, camera: [{t: 0, lon: 20, lat: 20, zoom: 1}]}}
    calculateMetadata={({props}) => ({durationInFrames: Math.max(1, Math.round(props.frames || 240))})}
  />
);
