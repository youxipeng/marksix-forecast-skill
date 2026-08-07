# Service contract

The public skill is intentionally thin. The private backend owns forecasting, free-use accounting, and Pro entitlements.

## Configuration

- `MARKSIX_PRO_API_URL`: base URL of the private backend, for example `https://api.example.com`.
- `MARKSIX_PRO_API_KEY`: per-user key issued by `POST /v1/register`.

Do not publish a real API key.

## Endpoints

- `GET /health`: service health.
- `GET /v1/plan`: free allowance, monthly display price, and subscription URL.
- `POST /v1/register`: create a trial API key.
- `GET /v1/me`: current entitlement status.
- `POST /v1/forecast`: full forecast. A successful non-Pro response consumes one of two free forecasts.

## Important status

HTTP `402` with `{"detail":{"code":"PRO_REQUIRED",...}}` means the two full free forecasts have been consumed. Display the returned subscription URL. Do not retry in a way intended to bypass the limit.

