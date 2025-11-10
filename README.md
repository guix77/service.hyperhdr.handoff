# HyperHDR Handoff - Kodi Service Addon

If your LED device is used for both HyperHDR and ambient lighting, this addon handles control handoff to ensure seamless operation. It automatically enables the HyperHDR LEDDEVICE component during video playback in Kodi, and disables it when playback stops.

## Requirements

- Kodi 19+ (Matrix) or later
- HyperHDR running with JSON-RPC API enabled (default port: 8090)

## Configuration

Go to **Settings → Add-ons → My add-ons → Services → HyperHDR Handoff** and configure:
- **HyperHDR URL**: Default `http://127.0.0.1:8090/json-rpc`
- **Startup Delay**: Delay before initializing (default: 5.0s)
- **Request Timeout**: HTTP timeout (default: 2s)
- **Retry Count**: Number of retries (default: 5)
- **Retry Sleep**: Delay between retries (default: 0.8s)
- **Enable Time Range**: Enable time-based activation control (default: disabled)
- **Time Range Start**: Start time in HH:MM format (default: 20:00)
- **Time Range End**: End time in HH:MM format (default: 06:00)

## How It Works

- On Kodi startup: Forces HyperHDR LEDDEVICE to OFF
- On video playback start: Sets HyperHDR LEDDEVICE to ON (if time range is disabled or current time is within range)
- On video playback stop/end: Sets HyperHDR LEDDEVICE to OFF (if time range is disabled or current time is within range)

### Time Range Feature

When **Enable Time Range** is enabled, the addon will only activate/deactivate HyperHDR during the specified time range. Outside this range, the addon does nothing (no activation on video start, no deactivation on video stop).

**Examples:**
- Range `20:00-06:00`: HyperHDR is managed from 8 PM to 6 AM (crosses midnight)
- Range `09:00-17:00`: HyperHDR is managed from 9 AM to 5 PM (same day)
- When disabled: HyperHDR is always managed regardless of time (default behavior)

## Troubleshooting

- Verify HyperHDR is running and accessible
- Check the URL in addon settings
- Check Kodi logs for `[HyperHDR Handoff]` entries

## License

MIT - See [LICENSE](LICENSE) file for details.
