from odoo import fields, models

class RegistryConfig(models.TransientModel):
    _inherit = "res.config.settings"

    enable_social_registry_async = fields.Boolean(
        config_parameter="g2p_import_social_registry.enable_async",
        string="Enable Background Processing"
    )