from odoo import api, fields, models

from ..services.bridge_client import BridgeClient


class CctvCameraGroup(models.Model):
    _name = "cctv.camera.group"
    _description = "CCTV Camera Group"
    _order = "name"

    name = fields.Char(required=True)
    description = fields.Text()
    color = fields.Integer(string="Color Index", default=0)
    camera_ids = fields.One2many("cctv.camera", "group_id", string="Cameras")
    camera_count = fields.Integer(compute="_compute_camera_count", store=False)

    @api.depends("camera_ids")
    def _compute_camera_count(self):
        for group in self:
            group.camera_count = len(group.camera_ids)


class CctvCamera(models.Model):
    _name = "cctv.camera"
    _description = "CCTV Camera"
    _order = "sequence, name"

    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    identifier = fields.Char(string="Camera ID")
    location = fields.Char()
    group_id = fields.Many2one("cctv.camera.group", string="Group")
    protocol = fields.Selection(
        selection=[
            ("rtsp", "RTSP"),
            ("rtmp", "RTMP"),
            ("hls", "HLS"),
            ("webrtc", "WebRTC"),
        ],
        default="rtsp",
        required=True,
    )
    stream_url = fields.Char(required=True)
    snapshot_url = fields.Char()
    username = fields.Char()
    password = fields.Char(
        copy=False,
        help="Stored for bridge services that need camera auth.",
    )
    refresh_interval = fields.Integer(
        default=60,
        help="Seconds between stream token refresh attempts when using vendor APIs.",
    )
    note = fields.Text()
    is_active = fields.Boolean(default=True)
    status = fields.Selection(
        selection=[
            ("unknown", "Unknown"),
            ("online", "Online"),
            ("offline", "Offline"),
            ("error", "Error"),
        ],
        default="unknown",
    )
    last_check = fields.Datetime(readonly=True)

    _sql_constraints = [
        ("stream_url_not_null", "CHECK(stream_url <> '')", "Stream URL is required."),
    ]

    def action_open_stream(self):
        """Open the inline player that fetches a short-lived playback URL via the bridge."""
        self.ensure_one()
        db_name = self.env.cr.dbname
        return {
            "type": "ir.actions.act_url",
            "url": f"/cctv/play/{self.id}?db={db_name}",
            "target": "new",
        }

    def request_bridge_session(self):
        """Shortcut used by controllers/tests to obtain a playback URL."""
        self.ensure_one()
        return BridgeClient(self.env).request_stream(self)
