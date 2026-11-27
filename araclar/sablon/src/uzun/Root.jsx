import React from 'react';
import {Composition} from 'remotion';
import {Uzun, W, H} from './Uzun.jsx';

// Kare sayısı ve içerik kurgu_uzun.py'nin yazdığı props'tan gelir; varsayılanlar yalnız önizleme içindir.
export const Root = () => (
  <Composition
    id="Uzun"
    component={Uzun}
    width={W}
    height={H}
    fps={30}
    durationInFrames={300}
    defaultProps={{frames: 300, blocks: [], chunks: [], cards: [], notes: [], audio: null}}
    calculateMetadata={({props}) => ({durationInFrames: Math.max(1, Math.round(props.frames || 300))})}
  />
);
