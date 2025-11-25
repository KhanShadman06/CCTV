from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    cctv_bridge_base_url = fields.Char(
        string="CCTV Bridge Base URL",
        config_parameter="cctv_monitoring.bridge_base_url",
        help="Base URL of the RTSP bridge that exposes /api/streams.",
    )
    cctv_bridge_api_key = fields.Char(
        string="CCTV Bridge API Key",
        config_parameter="cctv_monitoring.bridge_api_key",
        help="Optional API key sent as Bearer token to the bridge service.",
    )
    cctv_bridge_protocol = fields.Selection(
        selection=[
            ("hls", "HLS"),
            ("webrtc", "WebRTC"),
        ],
        default="hls",
        config_parameter="cctv_monitoring.bridge_protocol",
        string="Bridge Output Protocol",
    )
    cctv_bridge_session_ttl = fields.Integer(
        string="Stream TTL (seconds)",
        default=60,
        config_parameter="cctv_monitoring.bridge_session_ttl",
        help="How long the generated playback URL should stay valid.",
    )
    cctv_mediamtx_base_url = fields.Char(
        string="Mediamtx Base URL",
        config_parameter="cctv_monitoring.mediamtx_base_url",
        help="Base URL of the WebRTC gateway (e.g., http://mediamtx:8889).",
    )
