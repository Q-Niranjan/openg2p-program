import json
import logging
import uuid
from datetime import datetime, timezone

import requests
from ..models import constants
from odoo import _
from ..models import constants

_logger = logging.getLogger(__name__)

class SocialRegistryAPI:
    def __init__(self, env):
        self.env = env

    def make_request(self, data_source_id, query):
        
        # Get authentication and paths
        auth = self.env["social.registry.auth"]
        paths = auth.get_data_source_paths(data_source_id)
        auth_token = auth.get_auth_token(data_source_id,paths)
        
        today_isoformat = datetime.now(timezone.utc).isoformat()

        # Generate unique identifiers for request traceability
        message_id = str(uuid.uuid4())      
        transaction_id = str(uuid.uuid4())   
        reference_id = str(uuid.uuid4())     

        # Build hierarchical request structure:
        # data -> {header, message -> {search_request}} 
        header = self.get_header_for_body(
            today_isoformat,
            message_id,
        )

        message = self.get_message(
            today_isoformat,
            transaction_id=transaction_id,
            reference_id=reference_id,
            query=query,
        )

        data = self.get_data("", header, message)
        data = json.dumps(data)
        url = self.get_social_registry_search_url(data_source_id, paths)

        # Make request
        response = requests.post(
            url,
            data=data,
            headers={"Authorization": auth_token},
            timeout=constants.REQUEST_TIMEOUT,
        )

        if not response.ok:
            _logger.error("Social Registry Search API response: %s", response.text)
        response.raise_for_status()

        return response

    def get_header_for_body(self,today_isoformat, message_id):
        # Use system URL as sender ID for request tracking
        sender_id = self.env["ir.config_parameter"].sudo().get_param("web.base.url") or ""
        receiver_id = "Social Registry"
        return {
            "version": "1.0.0",
            "message_id": message_id,
            "message_ts": today_isoformat,
            "action": "search",
            "sender_id": sender_id,
            "sender_uri": "",
            "receiver_id": receiver_id,
            "total_count": 0,
        }

    def get_message(self, today_isoformat, transaction_id, reference_id, query):
        search_request = self.get_search_request(reference_id, today_isoformat, query)
        return {
            "transaction_id": transaction_id,
            "search_request": [search_request],
        }

    def get_search_request(self, reference_id, today_isoformat, query):
        return {
            "reference_id": reference_id,
            "timestamp": today_isoformat,
            "search_criteria": {
                "reg_type": "G2P:RegistryType:Individual",
                "query_type": constants.QUERY_TYPE,
                "query": query,
            },
        }

    def get_data(self, signature, header, message):
        return {
            "signature": signature,
            "header": header,
            "message": message,
        }

    def get_social_registry_search_url(self, data_source_id, paths):
        # Construct full API URL by combining base URL with search endpoint path
        url = data_source_id.url
        search_path = paths.get(constants.DATA_SOURCE_SEARCH_PATH_NAME)
        return f"{url}{search_path}"
