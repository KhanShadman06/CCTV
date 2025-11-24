# -*- coding: utf-8 -*-
{
    "name": "CCTV Monitoring",
    "version": "1.0.0",
    "category": "Operations",
    "summary": "Manage CCTV camera streams and view dashboards inside Odoo.",
    "description": """Store CCTV camera metadata and prepare dashboards for multi-camera viewing.""",
    "author": "Your Company",
    "website": "https://example.com",
    "license": "LGPL-3",
    "depends": ["base", "web"],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/cctv_camera_views.xml",
        "views/res_config_settings_views.xml",
        "views/stream_templates.xml",
    ],
    "application": True,
    "installable": True,
}
