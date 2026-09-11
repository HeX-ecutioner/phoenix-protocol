# Phoenix Protocol Frontend

This is the frontend interface for Phoenix Protocol, a read-only network-device configuration compliance scanner.

## Setup

The frontend is built using React and Vite. It connects to the backend API.

### Environment Variables

Copy the `.env.example` file to `.env` or set the variables manually.

```bash
VITE_API_BASE_URL=http://localhost:5000
```

### Installation

```bash
npm install
```

### Commands

- **Run development server**: `npm run dev`
- **Build for production**: `npm run build`
- **Preview production build**: `npm run preview`

## Features

- **Upload Screen**: Read-only safety notice, device-type selector, multiple-file picker, validation, and scan button.
- **Loading State**: Displays loading feedback during analysis.
- **Dashboard**: High-level metrics, device list, tested-rule compliance percentage, and report download buttons.
- **Device Details**: Rule results, severity badges, text-based statuses, filters, evidence display, and remediation guidance.

## API Assumptions

The frontend connects to the backend API endpoints as described in the API specification:
- `GET /api/device-types`
- `POST /api/scans` (multipart/form-data)
- `GET /api/scans/{scan_id}`
- `GET /api/scans/{scan_id}/devices`
- `GET /api/scans/{scan_id}/devices/{device_id}`
- `GET /api/rules`
- `GET /api/scans/{scan_id}/report.csv`

The application uses an integrated mock mode if the real backend is unavailable, ensuring development and demonstrations can proceed using synthetic responses that exactly match the backend contract.

## Known Limitations

- **Authentication**: No authentication or authorization is implemented in the MVP.
- **Report Download**: HTML report download is omitted in the initial UI per backend capability checks, though the endpoint exists in the API. CSV reports use standard anchor download links.
- **Rules View**: The standalone rules catalog library has been integrated into the device details view for efficiency during MVP execution, but a dedicated rules library view could be expanded in the future.
- **Progress Tracking**: Scan requests are synchronous, so true progress tracking is not available. Fake percentages are avoided by design.
