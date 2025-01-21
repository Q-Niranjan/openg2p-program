from datetime import date

from odoo import models


class G2POdkConfig(models.Model):
    _inherit = "odk.config"

    def handle_addl_data(self, mapped_json: dict, odk_import=None, **kwargs):
        program_id = None
        if odk_import:
            program_id = odk_import.target_program.id

        if program_id:
            mapped_json["program_membership_ids"] = [
                (
                    0,
                    0,
                    {
                        "program_id": program_id,
                        "state": "draft",
                        "enrollment_date": date.today(),
                    },
                )
            ]

        if "program_registrant_info_ids" in mapped_json:
            prog_reg_info = mapped_json.get("program_registrant_info_ids", None)

            if not program_id:
                mapped_json.pop("program_registrant_info_ids")
                return mapped_json

            mapped_json["program_registrant_info_ids"] = [
                (
                    0,
                    0,
                    {
                        "program_id": program_id,
                        "state": "active",
                        "program_registrant_info": prog_reg_info if prog_reg_info else None,
                    },
                )
            ]
        return mapped_json
