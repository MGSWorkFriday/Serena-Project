/**
 * Error Boundary Component
 * Catches React errors and displays user-friendly error messages
 */
import React, { Component, ErrorInfo, ReactNode } from 'react';
import { View, StyleSheet, TouchableOpacity, ScrollView } from 'react-native';
import { ThemedView } from '@/components/themed-view';
import { ThemedText } from '@/components/themed-text';
import { IconSymbol } from '@/components/ui/icon-symbol';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return {
      hasError: true,
      error,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('[ErrorBoundary] Caught error:', error, errorInfo);
    this.setState({
      error,
      errorInfo,
    });
    this.props.onError?.(error, errorInfo);
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <ThemedView style={styles.container}>
          <ScrollView contentContainerStyle={styles.content}>
            <View style={styles.iconContainer}>
              <IconSymbol name="exclamationmark.triangle.fill" size={64} color="#ef4444" />
            </View>
            <ThemedText type="title" style={styles.title}>
              Er is iets misgegaan
            </ThemedText>
            <ThemedText style={styles.message}>
              De app heeft een onverwachte fout ondervonden. Probeer de app opnieuw te starten.
            </ThemedText>

            {__DEV__ && this.state.error && (
              <View style={styles.errorDetails}>
                <ThemedText type="subtitle" style={styles.errorTitle}>
                  Foutdetails (Development)
                </ThemedText>
                <ThemedText style={styles.errorText}>
                  {this.state.error.toString()}
                </ThemedText>
                {this.state.errorInfo && (
                  <ThemedText style={styles.errorStack}>
                    {this.state.errorInfo.componentStack}
                  </ThemedText>
                )}
              </View>
            )}

            <TouchableOpacity onPress={this.handleReset} style={styles.resetButton}>
              <IconSymbol name="arrow.clockwise" size={20} color="#fff" />
              <ThemedText style={styles.resetButtonText}>Probeer opnieuw</ThemedText>
            </TouchableOpacity>
          </ScrollView>
        </ThemedView>
      );
    }

    return this.props.children;
  }
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  iconContainer: {
    marginBottom: 24,
  },
  title: {
    fontSize: 24,
    marginBottom: 12,
    textAlign: 'center',
  },
  message: {
    fontSize: 16,
    opacity: 0.8,
    textAlign: 'center',
    marginBottom: 32,
    lineHeight: 24,
  },
  errorDetails: {
    width: '100%',
    padding: 16,
    borderRadius: 12,
    backgroundColor: 'rgba(239, 68, 68, 0.1)',
    marginBottom: 24,
  },
  errorTitle: {
    fontSize: 14,
    marginBottom: 8,
    color: '#ef4444',
  },
  errorText: {
    fontSize: 12,
    fontFamily: 'monospace',
    color: '#ef4444',
    marginBottom: 8,
  },
  errorStack: {
    fontSize: 10,
    fontFamily: 'monospace',
    color: '#ef4444',
    opacity: 0.7,
  },
  resetButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 12,
    backgroundColor: '#3b82f6',
  },
  resetButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});
