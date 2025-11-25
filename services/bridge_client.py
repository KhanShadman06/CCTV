import logging
from datetime import timedelta
from typing import Any, Dict

import requests

from odoo import _, fields
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class BridgeClient:
    """Lightweight client that talks to an external RTSP bridge service."""

    def __init__(self, env):
        self.env = env

    def _config_parameters(self):
        params = self.env["ir.config_parameter"].sudo()
        base_url = (params.get_param("cctv_monitoring.bridge_base_url") or "").strip()
        protocol = params.get_param("cctv_monitoring.bridge_protocol", "hls") or "hls"
        api_key = params.get_param("cctv_monitoring.bridge_api_key") or False
        ttl = params.get_param("cctv_monitoring.bridge_session_ttl", "60")
        mediamtx_base = (params.get_param("cctv_monitoring.mediamtx_base_url") or "").strip()
        try:
            ttl = int(ttl)
        except (TypeError, ValueError):
            ttl = 60

        return {
            "bridge_base_url": base_url.rstrip("/") if base_url else "",
            "protocol": protocol,
            "api_key": api_key,
            "ttl": ttl,
            "mediamtx_base_url": mediamtx_base.rstrip("/") if mediamtx_base else "",
        }

    def request_stream(self, camera) -> Dict[str, Any]:
        config = self._config_parameters()
        protocol = config["protocol"]

        if protocol == "webrtc":
            mediamtx_base = config["mediamtx_base_url"]
            if not mediamtx_base:
                raise UserError(
                    _("Configure the Mediamtx Base URL under Settings > General Settings > CCTV.")
                )
            path = camera.webrtc_path or camera.identifier or f"camera-{camera.id}"
            path = path.strip("/")
            playback_url = f"{mediamtx_base}/{path or camera.id}/whep"
            return {
                "playback_url": playback_url,
                "protocol": "webrtc",
                "expires_at": False,
                "raw_response": {"path": path},
            }

        base_url = config["bridge_base_url"]
        if not base_url:
            raise UserError(
                _("Configure the CCTV Bridge Base URL under Settings > General Settings > CCTV."),
            )
        api_key = config["api_key"]
        ttl = config["ttl"]

        payload = {
            "source": camera.stream_url,
            "protocol": protocol,
            "username": camera.username or "",
            "password": camera.password or "",
            "camera_id": camera.id,
            "session_ttl": ttl,
        }
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        endpoint = f"{base_url}/api/streams"
        try:
            response = requests.post(endpoint, json=payload, timeout=10, headers=headers)
            response.raise_for_status()
        except requests.RequestException as exc:
            _logger.exception("Bridge request failed for camera %s", camera.id)
            raise UserError(_("Bridge service is unavailable: %s") % exc) from exc

        try:
            data = response.json()
        except ValueError as exc:
            _logger.error("Bridge returned a non-JSON payload: %s", response.text)
            raise UserError(_("Unexpected response from bridge service.")) from exc

        playback_url = data.get("playback_url") or data.get("url") or data.get("hls_url")
        if not playback_url:
            raise UserError(_("Bridge service did not return a playback URL."))

        expires_in = data.get("expires_in") or ttl
        expires_at = False
        if expires_in:
            try:
                expires_delta = timedelta(seconds=int(expires_in))
                expires_at = fields.Datetime.to_string(fields.Datetime.now() + expires_delta)
            except (TypeError, ValueError):
                expires_at = False

        return {
            "playback_url": playback_url,
            "protocol": data.get("protocol") or protocol,
            "expires_at": expires_at,
            "raw_response": data,
        }
