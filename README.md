# CCTV Monitoring

Initial increments of a CCTV monitoring module. This iteration focuses on backend setup
and delivering the bridge integration needed to obtain browser-friendly stream URLs:

- Camera model to persist stream metadata (RTSP URLs, credentials, grouping info)
- Access rights for internal users and CCTV managers
- Basic tree/form views plus placeholder dashboard action
- Configurable RTSP bridge settings and a JSON controller that returns short-lived HLS/WebRTC
  URLs for each camera

## Bridge integration (Step 1)

1. Configure the bridge endpoint under *Settings ▸ General Settings ▸ CCTV* by entering the
   base URL (e.g., `http://bridge:8001`), optional API key, preferred output protocol,
   and desired stream TTL. A reference implementation lives in `bridge_service/`.
2. When the UI needs to show a camera, it should call `POST /cctv/stream/<camera_id>` (JSON).
   The controller checks access rights, calls the external bridge’s `/api/streams` endpoint
   with the camera’s RTSP URL/credentials, and returns:

```json
{
  "playback_url": "https://bridge.local/hls/camera-1/index.m3u8",
  "protocol": "hls",
  "expires_at": "2024-05-01 12:30:00",
  "meta": {
    "...": "bridge response payload for debugging"
  }
}
```

The bridge service itself can be implemented with ffmpeg, GStreamer, or RTSP Simple Server;
Odoo only requires that it exposes `/api/streams` and returns a JSON body with `playback_url`
and optional `expires_in`.

## Next increments

1. **Dashboard widget** – ship an OWL/JavaScript component inside `web.assets_backend` that retrieves
   the prepared stream URLs via RPC and renders them in a responsive grid with play/pause controls.
2. **Health monitoring** – scheduled job that pings each camera, updates `status/last_check`, and raises
   alerts if cameras stay offline longer than a configured tolerance.

These steps will be addressed in future commits to keep changes incremental and easy to review.
