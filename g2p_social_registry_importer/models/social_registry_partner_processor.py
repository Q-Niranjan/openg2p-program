from odoo import models
from camel_converter import dict_to_snake


class SocialRegistryPartnerProcessor(models.AbstractModel):
    _name = "social.registry.partner.processor"
    _description = "Social Registry Partner Processing Logic"


    def process_partner(self, record):
        # 1. Extract and clean identifiers
        identifiers = record.get("regIds", [])
        partner_id, clean_identifiers = self.get_partner_and_clean_identifier(identifiers)

        # 2. Track if this is a new partner
        is_created = not bool(partner_id)

        # 3. Prepare and update partner data
        partner_data = self.get_individual_data(record)
        partner_data.update({"data_source_id": self.data_source_id.id})
        partner_id = self.create_or_update_registrant(partner_id, partner_data)

        # 4. Handle identifiers and program assignment
        self.create_registrant_id(clean_identifiers, partner_id)
        self.assign_registrant_to_program(partner_id, self.target_program)

        return partner_id, is_created
    
    
    def get_partner_and_clean_identifier(self, identifiers):
        clean_identifiers = []
        partner_id = None
        # Iterate through identifiers to find existing partner and clean identifier records
        for identifier in identifiers:
            identifier_type = identifier.get("idTypeAsStr", "")
            identifier_value = identifier.get("value", "")
            if identifier_type and identifier_value:
                # Check if identifier type is already created. Create record if no existing identifier type
                id_type = self.env["g2p.id.type"].search([("name", "=", identifier_type)], limit=1)
                if not id_type:
                    id_type = self.env["g2p.id.type"].create({"name": identifier_type})

                clean_identifiers.append({"id_type": id_type, "value": identifier_value})

                if not partner_id:
                    reg_id = self.env["g2p.reg.id"].search(
                        [
                            ("id_type", "=", id_type.id),
                            ("value", "=", identifier_value),
                        ],
                        limit=1,
                    )
                    if reg_id:
                        partner_id = reg_id.partner_id

        return partner_id, clean_identifiers

    def get_individual_data(self, record):
        vals = dict_to_snake(record)
        return vals

    def get_member_kind(self, data):
        # TODO: Kind will be in List
        kind_str = data.get("kind").get("name") if data.get("kind") else None
        kind = self.env["g2p.group.membership.kind"].search([("name", "=", kind_str)], limit=1)
        return kind if kind else None

    def get_member_relationship(self, individual, data):
        # TODO: Add relationship logic
        return None

    def update_reg_id(self, partner_data):
        if "reg_ids" in partner_data:
            partner_data["reg_ids"] = [
                (
                    0,
                    0,
                    {
                        "id_type": self.env["g2p.id.type"]
                        .sudo()
                        .search([("name", "=", reg_id.get("id_type").get("name"))], limit=1)
                        .id,
                        "value": reg_id.get("value"),
                        "expiry_date": reg_id.get("expiry_date"),
                        "status": reg_id.get("status"),
                        "description": reg_id.get("description"),
                    },
                )
                for reg_id in partner_data["reg_ids"]
            ]
        return partner_data

    def create_or_update_registrant(self, partner_id, partner_data):
        partner_data.update({"is_registrant": True})

        if self.target_registry == "group":
            partner_data.update({"is_group": True})

        if "phone_number_ids" in partner_data:
            # Transform phone numbers into Odoo's (0, 0, vals) creation format
            partner_data["phone_number_ids"] = [
                (0, 0, {
                    "phone_no": phone.get("phone_no", None),
                    "date_collected": phone.get("date_collected", None),
                    "disabled": phone.get("disabled", None),
                })
                for phone in partner_data["phone_number_ids"]
            ]

        # Reset reg_ids to prevent duplication since they're handled separately
        if "reg_ids" in partner_data:
            partner_data["reg_ids"] = []

        if "group_membership_ids" in partner_data and self.target_registry == "group":
            # Process group memberships and relationships for group registries
            individual_ids = []
            relationships_ids = []
            for individual_mem in partner_data.get("group_membership_ids"):
                individual_data = individual_mem.get("individual")
                individual_data.update({"is_registrant": True, "phone_number_ids": []})

                update_individual_data = self.update_reg_id(individual_data)

                individual = self.env["res.partner"].sudo().create(update_individual_data)
                if individual:
                    kind = self.get_member_kind(individual_mem)
                    individual_data = {"individual": individual.id}
                    if kind:
                        individual_data["kind"] = [(4, kind.id)]

                    relationship = self.get_member_relationship(individual.id, individual_mem)

                    if relationship:
                        relationships_ids.append((0, 0, relationship))

                    individual_ids.append((0, 0, individual_data))

                partner_data["related_1_ids"] = relationships_ids
                partner_data["group_membership_ids"] = individual_ids

        if partner_id:
            partner_id.write(partner_data)
        else:
            partner_id = self.env["res.partner"].create(partner_data)

        return partner_id

    def create_registrant_id(self, clean_identifiers, partner_id):
        for clean_identifier in clean_identifiers:
            partner_reg_id = self.env["g2p.reg.id"].search(
                [
                    ("id_type", "=", clean_identifier["id_type"].id),
                    ("partner_id", "=", partner_id.id),
                ]
            )
            if not partner_reg_id:
                reg_data = {
                    "id_type": clean_identifier["id_type"].id,
                    "partner_id": partner_id.id,
                    "value": clean_identifier["value"],
                }
                self.env["g2p.reg.id"].create(reg_data)

    def assign_registrant_to_program(self, partner_id, target_program):
        program_membership = self.env["g2p.program_membership"]

        if target_program and not program_membership.search(
            [("partner_id", "=", partner_id.id), ("program_id", "=", target_program.id)],
            limit=1,
        ):
            program_membership.create({"partner_id": partner_id.id, "program_id": target_program.id})
