// Dry Dock Stories – harita bölümü (Remotion).
// Küre üzerinde kamera uçuşu, ilerleyerek çizilen rota, işaret, yer adları.
// Bütün zamanlar bölümün uzunluğuna göre 0–1 arası oranla verilir (t, at, start, end).
import React, {useMemo} from 'react';
import {AbsoluteFill, useCurrentFrame, Easing} from 'remotion';
import {geoOrthographic, geoPath, geoGraticule10, geoInterpolate, geoDistance, geoArea} from 'd3-geo';
import {feature} from 'topojson-client';
import land110 from 'world-atlas/land-110m.json';
import land10 from 'world-atlas/land-10m.json';

const W = 1080, H = 1920;
const CX = 540, CY = 760;          // odak noktası: altyazı bandının (alt üçte bir) üstünde
const BASE_R = 470;                // zoom 1: kürenin yarıçapı (piksel)
const FONT = 'DejaVu Sans, sans-serif';

const C = {
  bg: '#04080d', sea: '#0c2131', land: '#3a4a57', coast: '#7f93a4', grat: '#16324a',
  rim: '#6fa6cf', route: '#f2b544', marker: '#ff5a3c', water: '#5f97bf',
  sea_label: '#8fb7d6', land_label: '#cfd8df', place: '#ffffff', tag_bg: 'rgba(8,18,28,0.72)',
};

const clamp01 = (x) => Math.max(0, Math.min(1, x));
const smooth = (a, b, x) => { const u = clamp01((x - a) / (b - a)); return u * u * (3 - 2 * u); };
const ease = Easing.inOut(Easing.cubic);
const fadeIn = (p, at, dur = 0.07) => (at == null ? 1 : clamp01((p - at) / dur));

// ---- kara verisi -------------------------------------------------------
function polygonsOf(fc) {
  const out = [];
  const feats = fc.type === 'FeatureCollection' ? fc.features : [fc];
  for (const f of feats) {
    const g = f.geometry;
    if (!g) continue;
    if (g.type === 'Polygon') out.push(g.coordinates);
    if (g.type === 'MultiPolygon') out.push(...g.coordinates);
  }
  // Çökmüş minik adalar (birkaç noktalı halka) d3'te bütün küreyi kaplayan çokgen sayılır; at.
  return out.filter((poly) => geoArea({type: 'Polygon', coordinates: poly}) < 2 * Math.PI);
}
const WIDE = {type: 'MultiPolygon', coordinates: polygonsOf(feature(land110, land110.objects.land))};
const DETAIL_ALL = polygonsOf(feature(land10, land10.objects.land));

function ringBox(ring) {
  let x0 = 180, y0 = 90, x1 = -180, y1 = -90;
  for (const [x, y] of ring) { if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y; }
  return [x0, y0, x1, y1];
}
function detailLand(box) {
  const [a0, b0, a1, b1] = box;
  const keep = DETAIL_ALL.filter((poly) => {
    const [x0, y0, x1, y1] = ringBox(poly[0]);
    return x1 >= a0 && x0 <= a1 && y1 >= b0 && y0 <= b1;
  });
  return {type: 'MultiPolygon', coordinates: keep};
}

// ---- kamera -------------------------------------------------------------
function cameraAt(keys, p) {
  const k = [...keys].sort((a, b) => a.t - b.t);
  if (p <= k[0].t) return k[0];
  for (let i = 0; i < k.length - 1; i++) {
    const a = k[i], b = k[i + 1];
    if (p <= b.t) {
      const u = ease(clamp01((p - a.t) / Math.max(1e-6, b.t - a.t)));
      const [lon, lat] = geoInterpolate([a.lon, a.lat], [b.lon, b.lat])(u);
      const zoom = Math.exp(Math.log(a.zoom) + (Math.log(b.zoom) - Math.log(a.zoom)) * u);
      return {lon, lat, zoom};
    }
  }
  return k[k.length - 1];
}

// ---- rota: oranla kısmi çizgi -------------------------------------------
function partialLine(points, f) {
  if (f <= 0 || points.length < 2) return [];
  const seg = [];
  let total = 0;
  for (let i = 0; i < points.length - 1; i++) { const d = geoDistance(points[i], points[i + 1]); seg.push(d); total += d; }
  let left = f * total;
  const out = [points[0]];
  for (let i = 0; i < seg.length; i++) {
    if (left >= seg[i]) { out.push(points[i + 1]); left -= seg[i]; continue; }
    out.push(geoInterpolate(points[i], points[i + 1])(seg[i] ? left / seg[i] : 0));
    break;
  }
  return out;
}

const Label = ({x, y, text, kind, opacity, anchor}) => {
  const st = {
    sea: {fill: C.sea_label, size: 34, italic: true, spacing: 7, weight: 400},
    land: {fill: C.land_label, size: 32, italic: false, spacing: 9, weight: 700},
    place: {fill: C.place, size: 34, italic: false, spacing: 3, weight: 700},
    water: {fill: '#a9d2ee', size: 30, italic: true, spacing: 4, weight: 700},
  }[kind || 'place'];
  return (
    <text x={x} y={y} textAnchor={anchor || 'middle'} fontFamily={FONT} fontSize={st.size} fontWeight={st.weight}
      fontStyle={st.italic ? 'italic' : 'normal'} letterSpacing={st.spacing} fill={st.fill} opacity={opacity}
      stroke="#05101a" strokeWidth={7} paintOrder="stroke" strokeLinejoin="round">{text}</text>
  );
};

export const MapScene = (props) => {
  const frame = useCurrentFrame();
  const frames = Math.max(1, Math.round(props.frames || 240));
  const p = frames > 1 ? frame / (frames - 1) : 1;
  const keys = props.camera && props.camera.length ? props.camera : [{t: 0, lon: 0, lat: 20, zoom: 1}];

  // Ayrıntılı kara yalnız yakın çekim bölgesi için hazırlanır (her karede bütün dünyayı işlememek için).
  const detail = useMemo(() => {
    const close = keys.filter((k) => k.zoom >= 3);
    if (!close.length) return null;
    const lons = close.map((k) => k.lon), lats = close.map((k) => k.lat);
    const m = 360 / Math.min(...close.map((k) => k.zoom));   // görünen genişliğin kaba üst sınırı
    return detailLand([Math.min(...lons) - m, Math.min(...lats) - m, Math.max(...lons) + m, Math.max(...lats) + m]);
  }, [JSON.stringify(keys)]);

  const cam = cameraAt(keys, p);
  const proj = geoOrthographic()
    .rotate([-cam.lon, -cam.lat])
    .translate([CX, CY])
    .scale(BASE_R * cam.zoom)
    .clipAngle(90)
    .clipExtent([[-40, -40], [W + 40, H + 40]]);
  const path = geoPath(proj);
  const center = [cam.lon, cam.lat];
  const visible = (lon, lat) => geoDistance([lon, lat], center) < Math.PI / 2 - 0.03;
  const at = (lon, lat) => proj([lon, lat]);

  const mixDetail = detail ? smooth(3.5, 6, cam.zoom) : 0;
  const rim = 1 - smooth(1.4, 2.6, cam.zoom);

  // rota
  const route = props.route;
  let routeD = null, head = null;
  if (route && route.points && route.points.length > 1) {
    const f = ease(clamp01((p - (route.start ?? 0.3)) / Math.max(1e-6, (route.end ?? 0.8) - (route.start ?? 0.3))));
    const pts = partialLine(route.points, f);
    if (pts.length > 1) {
      routeD = path({type: 'LineString', coordinates: pts});
      const a = at(...pts[pts.length - 2]), b = at(...pts[pts.length - 1]);
      if (a && b && f < 0.999) head = {x: b[0], y: b[1], ang: Math.atan2(b[1] - a[1], b[0] - a[0]) * 180 / Math.PI};
    }
  }

  const fps = 30;
  const tSec = frame / fps;

  return (
    <AbsoluteFill style={{backgroundColor: C.bg}}>
      <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`}>
        <defs>
          <radialGradient id="vignette" cx="50%" cy="40%" r="75%">
            <stop offset="55%" stopColor="#000" stopOpacity="0" />
            <stop offset="100%" stopColor="#000" stopOpacity="0.65" />
          </radialGradient>
          <radialGradient id="light" cx="50%" cy="38%" r="55%">
            <stop offset="0%" stopColor="#3d6f94" stopOpacity="0.28" />
            <stop offset="100%" stopColor="#3d6f94" stopOpacity="0" />
          </radialGradient>
          <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="7" result="b" />
            <feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
          <filter id="soft" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="14" /></filter>
        </defs>

        {rim > 0 && <path d={path({type: 'Sphere'})} fill="none" stroke={C.rim} strokeWidth={18} opacity={0.35 * rim} filter="url(#soft)" />}
        <path d={path({type: 'Sphere'})} fill={C.sea} />
        <path d={path(geoGraticule10())} fill="none" stroke={C.grat} strokeWidth={1.2} opacity={0.9} />
        {mixDetail < 1 && <path d={path(WIDE)} fill={C.land} stroke={C.coast} strokeWidth={1.4} opacity={1 - mixDetail} />}
        {mixDetail > 0 && <path d={path(detail)} fill={C.land} stroke={C.coast} strokeWidth={1.6} opacity={mixDetail} />}

        {(props.lines || []).map((l, i) => {
          const o = fadeIn(p, l.at);
          return o > 0 ? <path key={'l' + i} d={path({type: 'LineString', coordinates: l.points})} fill="none"
            stroke={l.color || C.water} strokeWidth={l.width || 6} strokeLinecap="round" strokeLinejoin="round" opacity={o} /> : null;
        })}

        {(props.dots || []).map((d, i) => {
          const o = fadeIn(p, (d.at ?? 0) + (d.stagger ?? 0) * i, 0.04);
          if (o <= 0 || !visible(d.lon, d.lat)) return null;
          const q = at(d.lon, d.lat);
          return q ? <circle key={'d' + i} cx={q[0]} cy={q[1]} r={d.r || 7} fill={d.color || '#d9e3ea'} opacity={0.9 * o} /> : null;
        })}

        {routeD && <path d={routeD} fill="none" stroke={C.route} strokeWidth={7} strokeLinecap="round" strokeLinejoin="round" filter="url(#glow)" />}
        {head && (
          <g transform={`translate(${head.x},${head.y}) rotate(${head.ang})`}>
            <path d="M 24 0 L 10 -8 L -18 -8 L -18 8 L 10 8 Z" fill="#fff4dc" stroke="#3a2a10" strokeWidth={2} />
          </g>
        )}

        {(props.markers || []).map((m, i) => {
          const o = fadeIn(p, m.at);
          if (o <= 0 || !visible(m.lon, m.lat)) return null;
          const q = at(m.lon, m.lat);
          if (!q) return null;
          const since = Math.max(0, tSec - (m.at ?? 0) * frames / fps);
          const rings = [0, 0.6].map((off, j) => {
            const ph = ((since + off) % 1.2) / 1.2;
            return <circle key={j} cx={q[0]} cy={q[1]} r={14 + 46 * ph} fill="none" stroke={C.marker} strokeWidth={4} opacity={o * (1 - ph)} />;
          });
          return (
            <g key={'m' + i}>
              {rings}
              <circle cx={q[0]} cy={q[1]} r={13} fill={C.marker} stroke="#fff" strokeWidth={4} opacity={o} />
              {m.label && <Label x={q[0] + (m.dx ?? 34)} y={q[1] + (m.dy ?? 12)} text={m.label} kind="place" anchor={m.anchor || 'start'} opacity={o} />}
            </g>
          );
        })}

        {(props.labels || []).map((l, i) => {
          const o = fadeIn(p, l.at) * (1 - fadeIn(p, l.until ?? 2));
          if (o <= 0 || !visible(l.lon, l.lat)) return null;
          const q = at(l.lon, l.lat);
          return q ? <Label key={'t' + i} x={q[0] + (l.dx || 0)} y={q[1] + (l.dy || 0)} text={l.text} kind={l.kind} anchor={l.anchor} opacity={o} /> : null;
        })}

        <rect x={0} y={0} width={W} height={H} fill="url(#light)" />
        <rect x={0} y={0} width={W} height={H} fill="url(#vignette)" />

        {props.tag && (() => {
          const o = fadeIn(p, props.tag_at ?? 0.05, 0.08);
          const w = 40 + props.tag.length * 25;
          return (
            <g opacity={o}>
              <rect x={CX - w / 2} y={196} width={w} height={70} rx={35} fill={C.tag_bg} stroke="#2c4a63" strokeWidth={2} />
              <text x={CX} y={243} textAnchor="middle" fontFamily={FONT} fontSize={34} fontWeight={700} letterSpacing={6} fill="#e8eef3">{props.tag}</text>
            </g>
          );
        })()}
      </svg>
    </AbsoluteFill>
  );
};
