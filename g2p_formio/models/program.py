import json

from odoo import api, fields, models


class G2PProgram(models.Model):
    _inherit = "g2p.program"

    portal_form_builder_id = fields.Many2one(
        "formio.builder", string="Program Form", domain="[('is_form_mapped_with_program', '=', False)]"
    )

    is_multiple_form_submission = fields.Boolean(default=False)

    @api.constrains("portal_form_builder_id")
    def _constrain_portal_form_mapping(self):
        self.ensure_one()

        if self.portal_form_builder_id:
            formio_builder = self.portal_form_builder_id

            try:
                # Parse the JSON string into a dictionary
                js_options = json.loads(formio_builder.formio_js_options)

                if "editForm" in js_options and "file" in js_options["editForm"]:
                    file_components = js_options["editForm"]["file"][0]["components"]

                    for component in file_components:
                        if "defaultValue" in component and component["key"] == "url":
                            component["defaultValue"] = f"/v1/selfservice/uploadDocument/{self.id}"

                    # Convert back to JSON string and update the builder
                    formio_builder.write(
                        {
                            "formio_js_options": json.dumps(js_options, indent=4),
                            "is_form_mapped_with_program": True,
                        }
                    )
                else:
                    formio_builder.write({"is_form_mapped_with_program": False})

            except (json.JSONDecodeError, KeyError, IndexError):
                # Handle potential JSON parsing errors or missing keys
                formio_builder.write({"is_form_mapped_with_program": False})

    @api.onchange("portal_form_builder_id")
    def _onchange_portal_form_unmapping(self):
        # Check if there was a previous form that is now being removed
        previous_form = self._origin.portal_form_builder_id
        current_form = self.portal_form_builder_id

        if previous_form and not current_form:
            previous_form.write({"is_form_mapped_with_program": False})


class G2PProgramFomio(models.Model):
    _inherit = "formio.builder"

    is_form_mapped_with_program = fields.Boolean(string="Is Form Mapped", default=False)
