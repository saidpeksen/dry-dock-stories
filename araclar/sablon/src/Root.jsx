import React from 'react';
import {Composition} from 'remotion';
import {Shorts} from './Shorts.jsx';

// Kare sayısı ve içerik kurgu.py'nin yazdığı props'tan gelir; varsayılanlar yalnız önizleme içindir.
export const Root = () => (
  <Composition
    id="Shorts"
    component={Shorts}
    width={1080}
    height={1920}
    fps={30}
    durationInFrames={300}
    defaultProps={{frames: 300, blocks: [], chunks: [], audio: null}}
    calculateMetadata={({props}) => ({durationInFrames: Math.max(1, Math.round(props.frames || 300))})}
  />
);
