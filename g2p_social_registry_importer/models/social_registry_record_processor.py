import logging
from odoo import models
from odoo.addons.queue_job.delay import group

_logger = logging.getLogger(__name__)

class SocialRegistryRecordProcessor(models.AbstractModel):
    _name = "social.registry.record.processor"
    _description = "Social Registry Record Processor"

   

    def process_registrants(self, registrants):
        for record in registrants:
            self.process_record(record)

    def process_registrants_async(self, registrants, count):
        # Get maximum batch size to prevent memory overload during async processing
        max_registrant = int(
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("g2p_import_social_registry.max_registrants_count_job_queue")
        )
        _logger.warning("Fetching Registrant Asynchronously!")
        jobs = []
        # Process registrants in batches to prevent memory overload
        for i in range(0, count, max_registrant):
            jobs.append(self.delayable().process_registrants(registrants[i : i + max_registrant]))
        #group all jobs and schedule them for execution
        main_job = group(*jobs)
        main_job.delay()
    
    def process_record(self, record):
        # First handle partner processing
        partner_id, is_created = self.process_partner(record)
        # Then handle record processing
        self.process_import_record(partner_id, is_created)
        return partner_id

    def process_import_record(self, partner_id, is_created):
        social_registry_imported_individuals = self.env["g2p.social.registry.imported.registrants"]
        
        # Check if this partner was previously imported in this fetch session
        existing_record = social_registry_imported_individuals.search([
            ("fetch_social_registry_id", "=", self.id),
            ("registrant_id", "=", partner_id.id),
        ], limit=1)

        if not existing_record:
            #Create new import record
            social_registry_imported_individuals.create({
                "fetch_social_registry_id": self.id,
                "registrant_id": partner_id.id,
                "is_group": partner_id.is_group,
                "is_created": is_created,
                "is_updated": not is_created,
            })
        else:
            #Update existing import record
            existing_record.update({"is_updated": True})
