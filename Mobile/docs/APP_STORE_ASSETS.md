# App Store Assets Documentation

## Overview

This document outlines the required assets for publishing the Serena app to the App Store (iOS) and Google Play Store (Android).

## Required Assets

### iOS App Store

#### 1. App Icon
- **Size**: 1024x1024 pixels
- **Format**: PNG (no transparency)
- **Location**: `assets/images/icon.png`
- **Requirements**:
  - Square image
  - No rounded corners (iOS adds them automatically)
  - No text or UI elements
  - High contrast for visibility

#### 2. Launch Screen / Splash Screen
- **Sizes**:
  - iPhone: 1242x2688 (iPhone 11 Pro Max)
  - iPad: 2048x2732
- **Format**: PNG or PDF (vector)
- **Location**: `assets/images/splash-icon.png`
- **Requirements**:
  - App logo centered
  - Background color matching app theme
  - No text (optional app name)

#### 3. Screenshots
- **Required Sizes**:
  - iPhone 6.7" (iPhone 14 Pro Max): 1290x2796
  - iPhone 6.5" (iPhone 11 Pro Max): 1242x2688
  - iPhone 5.5" (iPhone 8 Plus): 1242x2208
  - iPad Pro 12.9": 2048x2732
  - iPad Pro 11": 1668x2388
- **Quantity**: Minimum 3, maximum 10 per device
- **Requirements**:
  - Show key features
  - Breathing ball animation
  - Session screen
  - Device management
  - History screen

#### 4. App Preview Video (Optional)
- **Duration**: 15-30 seconds
- **Format**: MP4 or MOV
- **Resolution**: Match screenshot sizes
- **Requirements**:
  - Show app in action
  - Breathing ball animation
  - Real-time data visualization

### Android (Google Play Store)

#### 1. App Icon
- **Size**: 512x512 pixels
- **Format**: PNG (no transparency)
- **Location**: `assets/images/android-icon.png`
- **Requirements**:
  - Square image
  - High resolution
  - No text

#### 2. Feature Graphic
- **Size**: 1024x500 pixels
- **Format**: PNG or JPG
- **Requirements**:
  - Promotional banner
  - App name and tagline
  - Key features

#### 3. Screenshots
- **Required Sizes**:
  - Phone: 1080x1920 (minimum)
  - Tablet: 1200x1920 (minimum)
- **Quantity**: Minimum 2, maximum 8
- **Requirements**:
  - Show key features
  - High quality
  - No device frames needed

#### 4. Promo Video (Optional)
- **Duration**: Up to 2 minutes
- **Format**: YouTube link or MP4
- **Requirements**:
  - Show app functionality
  - Professional quality

## Current Assets Status

### ✅ Existing Assets
- `assets/images/icon.png` - App icon (192x192)
- `assets/images/android-icon-background.png` - Android icon background
- `assets/images/android-icon-foreground.png` - Android icon foreground
- `assets/images/android-icon-monochrome.png` - Android monochrome icon
- `assets/images/splash-icon.png` - Splash screen icon
- `assets/images/favicon.png` - Web favicon

### ⚠️ Assets Needing Updates

1. **App Icon (1024x1024)**
   - Current: 192x192
   - Needed: 1024x1024 for App Store
   - Action: Create high-resolution version

2. **Screenshots**
   - Current: None
   - Needed: Device-specific screenshots
   - Action: Capture screenshots from app

3. **Feature Graphic (Android)**
   - Current: None
   - Needed: 1024x500 promotional banner
   - Action: Design feature graphic

## Design Guidelines

### Color Scheme
- Primary: #3b82f6 (Blue)
- Background: Light (#ffffff) / Dark (#111827)
- Accent: #4cc9f0 (Cyan)

### Typography
- Font: System default (SF Pro on iOS, Roboto on Android)
- Headings: Bold, 24-32px
- Body: Regular, 16px

### Branding
- App Name: "Serena"
- Tagline: "Breathing & Heart Rate Monitor"
- Description: "Monitor your breathing exercises with real-time heart rate and respiratory rate tracking using Polar H10."

## Asset Creation Checklist

### iOS
- [ ] Create 1024x1024 app icon
- [ ] Create launch screen assets
- [ ] Capture iPhone screenshots (all required sizes)
- [ ] Capture iPad screenshots (all required sizes)
- [ ] Create app preview video (optional)

### Android
- [ ] Create 512x512 app icon
- [ ] Create feature graphic (1024x500)
- [ ] Capture phone screenshots
- [ ] Capture tablet screenshots
- [ ] Create promo video (optional)

## Tools & Resources

### Design Tools
- **Figma**: For creating icons and graphics
- **Sketch**: Alternative design tool
- **Adobe Illustrator**: For vector graphics

### Screenshot Tools
- **iOS Simulator**: Built-in screenshot tool
- **Android Studio**: Built-in screenshot tool
- **Fastlane**: Automated screenshot generation

### Icon Generators
- **App Icon Generator**: https://www.appicon.co/
- **IconKitchen**: https://icon.kitchen/
- **MakeAppIcon**: https://makeappicon.com/

## Next Steps

1. **Design Phase**
   - Create high-resolution app icon
   - Design feature graphic
   - Plan screenshot layouts

2. **Capture Phase**
   - Set up test devices/simulators
   - Capture screenshots for all required sizes
   - Record app preview video

3. **Optimization Phase**
   - Optimize image file sizes
   - Test assets on store previews
   - Ensure compliance with store guidelines

## References

- [Apple App Store Guidelines](https://developer.apple.com/app-store/review/guidelines/)
- [Google Play Store Guidelines](https://support.google.com/googleplay/android-developer/answer/9866151)
- [Expo Asset Guidelines](https://docs.expo.dev/guides/app-icons/)
