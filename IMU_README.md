IMU access from web (deep notes)

Summary

- Modern mobile browsers expose IMU sensors (accelerometer, gyroscope) via two main approaches:
  1. Generic Sensor API (Accelerometer, Gyroscope) — recommended when available. Provides high-resolution, sensor-specific access and a clean JS API.
  2. DeviceMotion / DeviceOrientation events — older, widely supported on mobile, but less precise and inconsistent across devices.

Key points

- HTTPS required for sensors in most browsers (Chrome on Android, Safari on iOS) when using secure contexts.
- iOS Safari (and iOS WebViews) require an explicit user gesture and a permission prompt via DeviceMotionEvent.requestPermission().
- Chrome for Android uses the Generic Sensor API when available, but some OEM browsers or older Chrome versions may only provide DeviceMotion events.
- Permissions: Some browsers treat motion sensors as "powerful features" requiring explicit allow via site settings or origin trial flags for older versions.

Generic Sensor API

- Classes: Accelerometer, LinearAccelerationSensor, Gyroscope, AbsoluteOrientationSensor, RelativeOrientationSensor
- Units: Accelerometer/Gyroscope provide SI units (m/s^2 and rad/s respectively) for reading properties x/y/z.
- Usage: create new Accelerometer({frequency:60}), then .start(), and listen for 'reading' events or read properties directly.
- Permissions: some browsers implement a secure-context-only policy; you may still need to request user gesture on iOS via DeviceMotionEvent.requestPermission().

DeviceMotion / DeviceOrientation

- Events: 'devicemotion' (acceleration, rotationRate) and 'deviceorientation' (alpha,beta,gamma absolute orientation angles).
- rotationRate values are typically in deg/s for alpha/beta/gamma.
- acceleration may be null on some devices; accelerationIncludingGravity is more commonly populated.
- Historically used by many pages; still the most compatible fallback.

Browser quirks & support

- Chrome on Android: good support for Generic Sensor API (vince 2018+), but availability depends on device and Android version.
- Safari on iOS: does not expose Generic Sensor API; use DeviceMotionEvent after calling DeviceMotionEvent.requestPermission() in a user gesture (button click).
- Firefox: limited Generic Sensor support behind flags in some versions; devicemotion support exists.
- Desktop: browsers may expose sensors for laptops with IMUs, but often not. Mobile is primary target.

Permissions and UX

- Always trigger permission requests from an explicit user gesture (e.g., a button click). iOS requires this, and it's best practice generally.
- Show clear UI explaining why the site needs motion sensors.
- Provide graceful fallback: if Generic Sensor API is blocked or missing, fall back to DeviceMotion and inform the user.

Testing checklist

- Serve the page over HTTPS. Chrome on Android blocks sensors on insecure origins.
- Test on a recent Chrome for Android and an iPhone (Safari) because behavior differs.
- On iOS: call DeviceMotionEvent.requestPermission() from a button click and handle "granted"/"denied".
- Inspect site settings in Chrome (Site settings -> Sensors / Motion & Orientation) to ensure not blocked.

Implementation notes for the provided sample

- The sample prefers the Generic Sensor API and falls back to DeviceMotionEvent.
- Values are displayed live and the accelerometer values drive a visual dot.
- Gyro values are converted from rad/s to deg/s when presented (Generic Sensor API gives rad/s; DeviceMotion rotationRate uses deg/s).

Troubleshooting

- If nothing appears: check the console for errors. Common issues: insecure origin, missing permission, sensor disabled in site settings.
- On some Android devices the Generic Sensor API may throw SecurityError if the site is not HTTPS.
- If acceleration shows as null, try using accelerationIncludingGravity instead.

References

- Generic Sensor API: https://developer.mozilla.org/en-US/docs/Web/API/Generic_Sensor_API
- DeviceMotionEvent: https://developer.mozilla.org/en-US/docs/Web/API/DeviceMotionEvent
- Web spec and notes: W3C Generic Sensor API
