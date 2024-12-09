import ast
import json
from odoo.exceptions import ValidationError

class SocialRegistryQueryBuilder:
    def __init__(self, target_registry=None, last_sync_date=None):
        self.target_registry = target_registry
        self.last_sync_date = last_sync_date

    def build_query(self, query_domain, field_to_import):
        """Generates the GraphQL query string based on the provided domain and fields."""
        query = "{ getRegistrants(\n"

        # Build domain
        ordered_domain = self._build_domain(query_domain)
        
        # Add domain to query if present
        if ordered_domain:
            # Double encode to prevent GraphQL query injection and ensure proper escaping
            domain_json = json.dumps(json.dumps(ordered_domain))
            query += f'    queryDomain: {domain_json}\n'

        # Add fields
        query += "  ) {\n"
        query += self._format_fields(field_to_import)
        query += "\n},totalRegistrantCount}"
        print(query)
        return query.strip()

    def _build_domain(self, query_domain):
        ordered_domain = []
        
        # Initialize domain list
        try:
            domain = ast.literal_eval(query_domain) if isinstance(query_domain, str) else query_domain
        except (ValueError, SyntaxError) as e:
            raise ValueError("Invalid query_domain format. Expected a valid domain expression.")

        # Add target registry filter if specified
        if self.target_registry:
            is_group = self.target_registry == "group"
            ordered_domain.append(("is_group", "=", is_group))

        # Add last sync date filter if exists
        if self.last_sync_date:
            # ISO 8601 format required for GraphQL date comparison
            ordered_domain.append(
                ("create_date", ">", self.last_sync_date.strftime("%Y-%m-%dT%H:%M:%S.000Z"))
            )

        # Combine ordered_domain with domain
        ordered_domain.extend(domain)
        
        return ordered_domain

    def _format_fields(self, field_to_import):
        try:
            # If it's a string, clean it up first
            if isinstance(field_to_import, str):
                # Remove all whitespace and newlines to normalize the string
                cleaned_input = ''.join(field_to_import.split())
                fields = ast.literal_eval(cleaned_input)
            else:
                fields = field_to_import

            # Check if fields is a list of strings
            if not isinstance(fields, list) or not all(isinstance(f, str) for f in fields):
                raise ValueError("Fields must be a list of strings")
                
            return ",\n    ".join(fields + [""])
            
        except (ValueError, SyntaxError) as e:
            raise ValueError(f"Invalid field_to_import format. Expected a list of field names. Error: {str(e)}")
