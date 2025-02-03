from datetime import date

import odoo.addons.g2p_odk_importer.models.odk_client as base_odk_client


def patched_addl_data(self, mapped_json):
    odk_import = self.env["odk.import"].browse(self.id)

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
            del mapped_json["program_registrant_info_ids"]
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


base_odk_client.ODKClient.get_addl_data = patched_addl_data
