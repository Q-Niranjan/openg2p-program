/** @odoo-module **/

import {patch} from "@web/core/utils/patch";
import {ListController} from "@web/views/list/list_controller";

patch(ListController.prototype, {

    setup() {
        super.setup();
        this.is_manager = false;
        this.is_validator = false;
        this.is_finance_validator = false;
        this.is_program_cycle_approver = false;
        this.check_role();
    },

    async check_role() {
        const user = this.env.services.user;
        try {

            const [is_manager, is_validator, is_finance_validator,is_program_cycle_approver] = await Promise.all([
                user.hasGroup("g2p_programs.g2p_program_manager"),
                user.hasGroup("g2p_programs.g2p_program_validator"),
                user.hasGroup("g2p_programs.g2p_finance_validator"),
                user.hasGroup("g2p_programs.g2p_program_cycle_approver"),
            ]);
            
            this.is_manager = is_manager;
            this.is_validator = is_validator;
            this.is_finance_validator = is_finance_validator;
            this.is_program_cycle_approver = is_program_cycle_approver;

        } catch (error) {
            console.error("Error checking user roles:", error);
        }
    },
});
