from odoo import api, fields, models


class OdkImport(models.Model):
    _inherit = "odk.import"

    target_program = fields.Many2one("g2p.program", domain="[('target_type', '=', target_registry)]")

    @api.onchange("target_registry")
    def onchange_target_registry(self):
        for rec in self:
            rec.target_program = None
