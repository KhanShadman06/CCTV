import re

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
    webrtc_path = fields.Char(
        string="WebRTC Path",
        help="Path name served by the WebRTC gateway (defaults to Identifier or Name).",
    )
    play_url = fields.Char(compute="_compute_play_url", store=False)
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

    def _compute_play_url(self):
        db_name = self.env.cr.dbname
        for camera in self:
            if camera.id:
                camera.play_url = f"/cctv/play/{camera.id}?db={db_name}"
            else:
                camera.play_url = False

    def _generate_webrtc_path(self):
        self.ensure_one()
        base = self.identifier or (self.name or "")
        base = base.strip() or f"camera-{self.id or ''}"
        slug = re.sub(r"[^a-zA-Z0-9]+", "-", base)
        slug = re.sub(r"-{2,}", "-", slug).strip("-")
        return (slug or f"camera-{self.id}").lower()

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record, vals in zip(records, vals_list):
            if not vals.get("webrtc_path"):
                record.webrtc_path = record._generate_webrtc_path()
        return records

    def write(self, vals):
        res = super().write(vals)
        if "webrtc_path" not in vals:
            for record in self:
                if not record.webrtc_path:
                    record.webrtc_path = record._generate_webrtc_path()
        return res
