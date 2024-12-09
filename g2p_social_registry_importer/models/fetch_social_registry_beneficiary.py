from odoo import _, api, fields, models

from .social_registry_api import SocialRegistryAPI
from .social_registry_query_builder import SocialRegistryQueryBuilder
from .social_registry_partner_processor import SocialRegistryPartnerProcessor
from .social_registry_record_processor import SocialRegistryRecordProcessor

class G2PFetchSocialRegistryBeneficiary(models.Model):
    _name = "g2p.fetch.social.registry.beneficiary"
    _inherit = ["social.registry.partner.processor", "social.registry.record.processor"]
    _description = "Fetch Social Registry Beneficiary"

    name = fields.Char(required=True)
    data_source_id = fields.Many2one("spp.data.source", required=True)
    target_registry = fields.Selection(
        [("group", "Group"), ("individual", "Individual")],
        required=True,
    )
    target_program = fields.Many2one(
        "g2p.program",
        domain=("[('target_type', '=', target_registry)]"),
    )
    query_domain = fields.Text(string="Query Domain", default="[]")
    field_to_import = fields.Text(string="Fields To Import", default="[]", required=True)
    last_sync_date = fields.Datetime(string="Last synced on", required=False)
    imported_registrant_ids = fields.One2many(
        "g2p.social.registry.imported.registrants",
        "fetch_social_registry_id",
        "Imported Registrants",
        readonly=True,
    )

    @api.onchange("registry")
    def onchange_target_registry(self):
        for rec in self:
            rec.target_program = None

    def fetch_social_registry_beneficiary(self):
        # Make API request to fetch beneficiary data
        api = SocialRegistryAPI(self.env)
        response = api.make_request(self.data_source_id, self.prepare_graphql_query())
        print(response.text)

        # Get max registrant limit from system parameters
        config_parameters = self.env["ir.config_parameter"].sudo()
        max_registrant = int(
            config_parameters.get_param("g2p_import_social_registry.max_registrants_count_job_queue")
        )
        sticky = False

        # Process API response
        if response.ok:
            kind = "success"
            message = _("Successfully Imported Social Registry Beneficiaries")

            search_responses = response.json().get("message", {}).get("search_response", [])

            if not search_responses:
                kind = "warning"
                message = _("No imported beneficiary")

            for search_response in search_responses:
                reg_record = search_response.get("data", {}).get("reg_records", [])
                registrants = reg_record.get("getRegistrants", [])
                total_partners_count = reg_record.get("totalRegistrantCount", "")

                # Choose between sync/async processing based on total count
                if total_partners_count:
                    if total_partners_count < max_registrant:
                        # Process synchronously for small batches
                        self.process_registrants(registrants)  
                    else:
                        # Process async for large batches
                        self.process_registrants_async(registrants, total_partners_count)  
                        kind = "success"
                        message = _("Fetching from Social Registry Started Asynchronously.")
                        sticky = True
                else:
                    kind = "success"
                    message = _("No matching records found.")

                # Update last sync timestamp
                self.last_sync_date = fields.Datetime.now()
        else:
            kind = "danger"
            message = response.json().get("error", {}).get("message", "")
            if not message:
                message = _("{reason}: Unable to connect to API.").format(reason=response.reason)
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Social Registry"),
                "message": message,
                "sticky": sticky,
                "type": kind,
                "next": {
                    "type": "ir.actions.act_window_close",
                },
            },
        }

    def prepare_graphql_query(self):
        query_builder = SocialRegistryQueryBuilder(
            target_registry=self.target_registry,
            last_sync_date=self.last_sync_date
        )
        query = query_builder.build_query(self.query_domain, self.field_to_import)
        return query
