# HyperHDR Handoff - Kodi Service Addon

Automatically turns HyperHDR LEDDEVICE component **ON** when Kodi starts video playback and **OFF** when playback stops or ends.

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

## How It Works

- On Kodi startup: Forces HyperHDR LEDDEVICE to OFF
- On video playback start: Sets HyperHDR LEDDEVICE to ON
- On video playback stop/end: Sets HyperHDR LEDDEVICE to OFF

## Troubleshooting

- Verify HyperHDR is running and accessible
- Check the URL in addon settings
- Check Kodi logs for `[HyperHDR Handoff]` entries

## License

MIT - See [LICENSE](LICENSE) file for details.
