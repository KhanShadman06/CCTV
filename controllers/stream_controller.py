import logging

from odoo import _, http
from odoo.exceptions import AccessError
from odoo.http import request
from werkzeug.exceptions import NotFound

from ..services.bridge_client import BridgeClient

_logger = logging.getLogger(__name__)


class CctvStreamController(http.Controller):
    @http.route("/cctv/stream/<int:camera_id>", type="json", auth="user", methods=["POST"], csrf=False)
    def fetch_stream(self, camera_id):
        """Return a short-lived playback URL for the requested camera."""

        user = request.env.user
        if not user.has_group("cctv_monitoring.group_cctv_user"):
            raise AccessError(_("You are not allowed to view CCTV streams."))

        camera = request.env["cctv.camera"].browse(camera_id)
        if not camera.exists():
            raise NotFound()

        camera.check_access_rights("read")
        camera.check_access_rule("read")
        camera.ensure_one()

        bridge_client = BridgeClient(request.env)
        session = bridge_client.request_stream(camera.sudo())

        payload = {
            "playback_url": session["playback_url"],
            "protocol": session["protocol"],
            "expires_at": session["expires_at"],
        }
        if session.get("raw_response"):
            payload["meta"] = session["raw_response"]

        _logger.info("Bridge session granted for camera %s via protocol %s", camera.id, session["protocol"])
        return payload

    @http.route("/cctv/play/<int:camera_id>", type="http", auth="user")
    def play_stream(self, camera_id):
        """Render a minimal player page that embeds the bridge output."""

        user = request.env.user
        if not user.has_group("cctv_monitoring.group_cctv_user"):
            raise AccessError(_("You are not allowed to view CCTV streams."))

        camera = request.env["cctv.camera"].browse(camera_id)
        if not camera.exists():
            raise NotFound()

        camera.check_access_rights("read")
        camera.check_access_rule("read")
        camera.ensure_one()

        session = camera.sudo().request_bridge_session()
        return request.render(
            "cctv_monitoring.stream_player",
            {
                "camera": camera,
                "session": session,
            },
        )
