/**
 * Breathing Wave Visualization Component
 * Shows a scrolling sine wave with a ball moving along it
 * Based on SerenaWebApp's breathing_ball.js
 */
import { useEffect } from 'react';
import { View, StyleSheet, Dimensions } from 'react-native';
import Animated, {
  useSharedValue,
  useDerivedValue,
  useAnimatedProps,
  useFrameCallback,
} from 'react-native-reanimated';
import Svg, { Path, Circle, Line, Text as SvgText, G, Rect } from 'react-native-svg';
import { ThemedText } from '@/components/themed-text';
import { getCycleDuration } from '@/utils/breathingAnimation';

const AnimatedPath = Animated.createAnimatedComponent(Path);
const AnimatedCircle = Animated.createAnimatedComponent(Circle);

interface BreathingBallProps {
  breathCycle?: {
    in: number;
    hold1?: number;
    out: number;
    hold2?: number;
  };
  color?: string;
  size?: number;
}

// Configuration
const VIEW_SECONDS = 12; // Seconds visible on screen
const PADDING = { top: 20, right: 15, bottom: 35, left: 40 };

// Colors matching SerenaWebApp
const COLORS = {
  graph: '#00ffff',
  ball: '#3498db',
  ballBorder: '#ffffff',
  axis: '#bdc3c7',
  grid: '#465c6b',
  text: '#ecf0f1',
  background: '#2c3e50',
};

/**
 * Interpolate for smooth sine-like transitions (cosine easing)
 */
function interpolateBreath(t: number): number {
  'worklet';
  return (1 - Math.cos(t * Math.PI)) / 2;
}

/**
 * Calculate Y value for a given time in the breathing cycle
 * Returns 0-1 where 0 = exhale (bottom), 1 = inhale (top)
 */
function calculateWaveY(
  timeInSeconds: number,
  inhale: number,
  inhaleHold: number,
  exhale: number,
  exhaleHold: number
): number {
  'worklet';
  const totalTime = inhale + inhaleHold + exhale + exhaleHold;
  if (totalTime <= 0) return 0.5;

  let t = timeInSeconds % totalTime;
  if (t < 0) t += totalTime;

  let y: number;

  if (t < inhale) {
    // Inhaling - going up
    y = interpolateBreath(t / inhale);
  } else if (t < inhale + inhaleHold) {
    // Hold at top
    y = 1;
  } else if (t < inhale + inhaleHold + exhale) {
    // Exhaling - going down
    y = 1 - interpolateBreath((t - (inhale + inhaleHold)) / exhale);
  } else {
    // Hold at bottom
    y = 0;
  }

  return y;
}

export function BreathingBall({
  breathCycle,
  color = COLORS.ball,
  size = 280,
}: BreathingBallProps) {
  const elapsedTime = useSharedValue(0);
  const screenWidth = Dimensions.get('window').width;
  
  // Use size prop as a hint for max height, responsive width
  const componentWidth = Math.min(screenWidth - 40, 500);
  const componentHeight = Math.min(componentWidth * 0.6, size * 0.75, 250);

  // Graph dimensions
  const graphWidth = componentWidth - PADDING.left - PADDING.right;
  const graphHeight = componentHeight - PADDING.top - PADDING.bottom;

  // Default cycle if not provided
  const cycle = breathCycle || { in: 4, out: 4, hold1: 0, hold2: 0 };
  const inhale = cycle.in;
  const inhaleHold = cycle.hold1 || 0;
  const exhale = cycle.out;
  const exhaleHold = cycle.hold2 || 0;
  const totalDuration = getCycleDuration(inhale, inhaleHold, exhale, exhaleHold);

  const startTime = useSharedValue<number>(-1);

  // Use frame callback for smooth real-time animation
  useFrameCallback((frameInfo) => {
    'worklet';
    if (totalDuration <= 0) return;
    
    if (startTime.value < 0) {
      startTime.value = frameInfo.timestamp;
    }
    
    // Calculate elapsed time in seconds
    const elapsed = (frameInfo.timestamp - startTime.value) / 1000;
    elapsedTime.value = elapsed;
  }, true);

  useEffect(() => {
    // Reset start time when cycle changes
    startTime.value = -1;
    elapsedTime.value = 0;
  }, [totalDuration, inhale, inhaleHold, exhale, exhaleHold]);

  // Generate wave path
  const animatedPathProps = useAnimatedProps(() => {
    'worklet';
    const timeElapsed = elapsedTime.value;
    const pixelsPerSecond = graphWidth / VIEW_SECONDS;
    const startTimeInView = timeElapsed - VIEW_SECONDS / 2;
    
    let pathData = '';
    const step = 3; // Pixel step for smooth curve

    for (let px = 0; px <= graphWidth; px += step) {
      const t = startTimeInView + px / pixelsPerSecond;
      const val = calculateWaveY(t, inhale, inhaleHold, exhale, exhaleHold);
      
      // Map Y value (0-1) to graph coordinates
      // 0.1 to 0.9 of graph height for padding
      const yPlot = 0.1 + val * 0.8;
      const pixelY = PADDING.top + graphHeight - yPlot * graphHeight;
      const pixelX = PADDING.left + px;

      if (px === 0) {
        pathData = `M ${pixelX} ${pixelY}`;
      } else {
        pathData += ` L ${pixelX} ${pixelY}`;
      }
    }

    return { d: pathData };
  });

  // Calculate ball position (always at center X)
  const ballY = useDerivedValue(() => {
    'worklet';
    const timeElapsed = elapsedTime.value;
    const val = calculateWaveY(timeElapsed, inhale, inhaleHold, exhale, exhaleHold);
    const yPlot = 0.1 + val * 0.8;
    return PADDING.top + graphHeight - yPlot * graphHeight;
  });

  const animatedBallProps = useAnimatedProps(() => {
    'worklet';
    return {
      cy: ballY.value,
    };
  });

  // Generate grid lines
  const gridLines = [];
  const ySteps = [0, 0.5, 1.0];
  
  ySteps.forEach((val, index) => {
    const yPlot = 0.1 + val * 0.8;
    const pixelY = PADDING.top + graphHeight - yPlot * graphHeight;
    gridLines.push(
      <G key={`y-${index}`}>
        <Line
          x1={PADDING.left}
          y1={pixelY}
          x2={PADDING.left + graphWidth}
          y2={pixelY}
          stroke={COLORS.grid}
          strokeWidth={1}
          strokeDasharray="3,4"
        />
        <SvgText
          x={PADDING.left - 8}
          y={pixelY + 4}
          fill={COLORS.axis}
          fontSize={10}
          textAnchor="end"
        >
          {val.toFixed(1)}
        </SvgText>
      </G>
    );
  });

  // X-axis labels
  const xLabels = [];
  const secondsHalf = VIEW_SECONDS / 2;
  const step = componentWidth < 350 ? 4 : 2;
  
  for (let t = -Math.floor(secondsHalf); t <= Math.floor(secondsHalf); t += step) {
    const xOffset = (t / secondsHalf) * (graphWidth / 2);
    const pixelX = PADDING.left + graphWidth / 2 + xOffset;
    
    xLabels.push(
      <G key={`x-${t}`}>
        <Line
          x1={pixelX}
          y1={PADDING.top}
          x2={pixelX}
          y2={PADDING.top + graphHeight}
          stroke={t === 0 ? '#7f8c8d' : COLORS.grid}
          strokeWidth={t === 0 ? 1.5 : 1}
          strokeDasharray="3,4"
        />
        <SvgText
          x={pixelX}
          y={PADDING.top + graphHeight + 18}
          fill={COLORS.axis}
          fontSize={10}
          textAnchor="middle"
        >
          {`${t}s`}
        </SvgText>
      </G>
    );
  }

  if (totalDuration <= 0) {
    return (
      <View style={[styles.container, { width: componentWidth, height: componentHeight }]}>
        <ThemedText style={styles.placeholder}>Geen cyclus gedefinieerd</ThemedText>
      </View>
    );
  }

  const ballCenterX = PADDING.left + graphWidth / 2;

  return (
    <View style={[styles.container, { width: componentWidth, height: componentHeight }]}>
      <Svg width={componentWidth} height={componentHeight}>
        {/* Background */}
        <Rect
          x={0}
          y={0}
          width={componentWidth}
          height={componentHeight}
          fill={COLORS.background}
          rx={8}
        />

        {/* Grid lines */}
        {gridLines}
        {xLabels}

        {/* Border */}
        <Rect
          x={PADDING.left}
          y={PADDING.top}
          width={graphWidth}
          height={graphHeight}
          fill="none"
          stroke={COLORS.axis}
          strokeWidth={1}
        />

        {/* Breathing wave */}
        <AnimatedPath
          animatedProps={animatedPathProps}
          fill="none"
          stroke={COLORS.graph}
          strokeWidth={3}
          strokeLinecap="round"
          strokeLinejoin="round"
        />

        {/* Ball */}
        <AnimatedCircle
          animatedProps={animatedBallProps}
          cx={ballCenterX}
          r={12}
          fill={color}
          stroke={COLORS.ballBorder}
          strokeWidth={2}
        />
      </Svg>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    justifyContent: 'center',
    alignItems: 'center',
    borderRadius: 8,
    overflow: 'hidden',
  },
  placeholder: {
    textAlign: 'center',
    opacity: 0.6,
  },
});
