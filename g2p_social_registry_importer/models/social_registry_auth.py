import logging
import requests
from odoo import _, models
from odoo.exceptions import ValidationError
from ..models import constants

_logger = logging.getLogger(__name__)

class SocialRegistryAuth(models.AbstractModel):
    _name = "social.registry.auth"
    _description = "Social Registry Authentication"

    def get_auth_token(self, data_source,paths):
        # paths = self.get_data_source_paths(data_source)
        auth_url = self.get_social_registry_auth_url(data_source, paths)

        # Get authentication credentials from system parameters
        client_id = self.env["ir.config_parameter"].sudo().get_param("g2p_import_social_registry.client_id")
        client_secret = self.env["ir.config_parameter"].sudo().get_param("g2p_import_social_registry.client_password")
        grant_type = self.env["ir.config_parameter"].sudo().get_param("g2p_import_social_registry.grant_type")

        # Prepare OAuth2 token request payload
        data = {
            "grant_type": grant_type,
            "client_id": client_id,
            "client_secret": client_secret,
        }

        # Make authentication request with timeout
        response = requests.post(
            auth_url,
            data=data,
            timeout=constants.REQUEST_TIMEOUT,
        )

        _logger.debug("Authentication API response: %s", response.text)

        # Return formatted bearer token if successful, otherwise raise error
        if response.ok:
            result = response.json()
            return f'{result.get("token_type")} {result.get("access_token")}'
        else:
            raise ValidationError(_("{reason}: Unable to connect to API.").format(reason=response.reason))


    def get_data_source_paths(self, data_source):
        # Dictionary to store API endpoint paths from data source configuration
        paths = {}
        for path_id in data_source.data_source_path_ids:
            paths[path_id.key] = path_id.value

        # Validate that required search path exists
        if constants.DATA_SOURCE_SEARCH_PATH_NAME not in paths:
            raise ValidationError(
                _("No path in data source named {path} is configured!").format(
                    path=constants.DATA_SOURCE_SEARCH_PATH_NAME
                )
            )

        # Validate that required auth path exists
        if constants.DATA_SOURCE_AUTH_PATH_NAME not in paths:
            raise ValidationError(
                _("No path in data source named {path} is configured!").format(
                    path=constants.DATA_SOURCE_AUTH_PATH_NAME
                )
            )
        return paths

    def get_social_registry_auth_url(self, data_source, paths):
        url = data_source.url
        auth_path = paths.get(constants.DATA_SOURCE_AUTH_PATH_NAME)

        # Handle both absolute paths (starting with /) and full URLs
        if auth_path.lstrip().startswith("/"):
            return f"{url}{auth_path}"
        else:
            return auth_path

   