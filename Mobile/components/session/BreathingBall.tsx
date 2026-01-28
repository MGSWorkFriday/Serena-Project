/**
 * Breathing Ball Animation Component
 * Uses React Native Reanimated for smooth 60fps animations
 */
import { useEffect } from 'react';
import { View, StyleSheet } from 'react-native';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withRepeat,
  withTiming,
  Easing,
  useDerivedValue,
  interpolate,
} from 'react-native-reanimated';
import { ThemedText } from '@/components/themed-text';
import { calculateBreathY, getCycleDuration } from '@/utils/breathingAnimation';

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

export function BreathingBall({
  breathCycle,
  color = '#3498db',
  size = 280,
}: BreathingBallProps) {
  const progress = useSharedValue(0);

  // Default cycle if not provided
  const cycle = breathCycle || { in: 4, out: 4, hold1: 0, hold2: 0 };
  const a = cycle.in;
  const b = cycle.hold1 || 0;
  const c = cycle.out;
  const d = cycle.hold2 || 0;
  const totalDuration = getCycleDuration(a, b, c, d);

  useEffect(() => {
    if (totalDuration <= 0) return;

    // Reset and start animation loop
    progress.value = 0;
    progress.value = withRepeat(
      withTiming(1, {
        duration: totalDuration * 1000, // Convert to milliseconds
        easing: Easing.linear,
      }),
      -1, // Infinite repeat
      false
    );
  }, [totalDuration, a, b, c, d]);

  // Calculate Y position based on progress (using worklet)
  const yValue = useDerivedValue(() => {
    'worklet';
    const t = progress.value * totalDuration;
    return calculateBreathY(t, a, b, c, d);
  });

  // Animated style for ball position and size
  const ballStyle = useAnimatedStyle(() => {
    'worklet';
    // Map Y value (-1 to 1) to screen position
    // Y = -1 means bottom (exhale, bigger), Y = 1 means top (inhale, smaller)
    const centerY = 0;
    const range = size * 0.25; // Movement range
    const translateY = -yValue.value * range;

    // Scale based on Y position (bigger when at bottom/exhale, smaller at top/inhale)
    const scale = interpolate(yValue.value, [-1, 1], [1.3, 0.7], 'clamp');

    return {
      transform: [
        { translateY },
        { scale },
      ],
    };
  });

  // Animated style for ball opacity/color intensity
  const ballColorStyle = useAnimatedStyle(() => {
    'worklet';
    // Slightly adjust opacity based on position
    const opacity = interpolate(yValue.value, [-1, 1], [0.85, 1.0], 'clamp');
    return {
      opacity,
    };
  });

  if (totalDuration <= 0) {
    return (
      <View style={[styles.container, { width: size, height: size }]}>
        <ThemedText style={styles.placeholder}>Geen cyclus gedefinieerd</ThemedText>
      </View>
    );
  }

  return (
    <View style={[styles.container, { width: size, height: size }]}>
      {/* Animated breathing ball */}
      <Animated.View style={[styles.ballContainer, ballStyle]}>
        <Animated.View style={[styles.ball, { backgroundColor: color }, ballColorStyle]} />
        {/* Inner glow effect */}
        <Animated.View style={[styles.ballInner, { backgroundColor: color }]} />
      </Animated.View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    justifyContent: 'center',
    alignItems: 'center',
    position: 'relative',
  },
  ballContainer: {
    justifyContent: 'center',
    alignItems: 'center',
    width: 120,
    height: 120,
  },
  ball: {
    width: 100,
    height: 100,
    borderRadius: 50,
    position: 'absolute',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.4,
    shadowRadius: 12,
    elevation: 10,
  },
  ballInner: {
    width: 60,
    height: 60,
    borderRadius: 30,
    position: 'absolute',
    opacity: 0.3,
  },
  placeholder: {
    textAlign: 'center',
    opacity: 0.6,
  },
});
