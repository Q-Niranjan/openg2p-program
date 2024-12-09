from odoo import models, fields, api

class G2PCreateNewImporterWiz(models.TransientModel):
    _name = "g2p.social.registry.importer.create.wizard"
    _description = "Social Registry Importer Creation Wizard"
    _inherit = "g2p.fetch.social.registry.beneficiary"

    query_domain = fields.Text(string="Query Domain",default="[]")
