"""
NUCLEUS V1.2 - Credentials Manager
Manages secure storage and retrieval of integration credentials using GCP Secret Manager
"""

import os
import json
from typing import Dict, Any, Optional
from google.cloud import secretmanager
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class CredentialsManager:
    """
    Manages credentials for third-party integrations.
    
    Uses GCP Secret Manager for secure storage of actual credentials.
    Database only stores metadata and references to secrets.
    """
    
    def __init__(self, project_id: Optional[str] = None):
        """Initialize credentials manager with GCP project."""
        self.project_id = project_id or os.getenv("GCP_PROJECT_ID", "thrive-system1")
        self.client = secretmanager.SecretManagerServiceClient()
        
    def _build_secret_path(self, entity_id: str, service_name: str) -> str:
        """Build secret path for Secret Manager."""
        # Format: nucleus-credentials-{entity_id}-{service_name}
        return f"nucleus-credentials-{entity_id}-{service_name}"
    
    def _build_secret_name(self, entity_id: str, service_name: str) -> str:
        """Build full secret name for Secret Manager."""
        secret_path = self._build_secret_path(entity_id, service_name)
        return f"projects/{self.project_id}/secrets/{secret_path}"
    
    def _build_version_name(self, entity_id: str, service_name: str, version: str = "latest") -> str:
        """Build full secret version name."""
        secret_name = self._build_secret_name(entity_id, service_name)
        return f"{secret_name}/versions/{version}"
    
    def store_credentials(
        self,
        entity_id: str,
        service_name: str,
        credentials: Dict[str, Any],
        labels: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Store credentials in GCP Secret Manager.
        
        Args:
            entity_id: Entity ID
            service_name: Service name (gmail, github, etc.)
            credentials: Credentials dictionary to store
            labels: Optional labels for the secret
            
        Returns:
            Secret path reference for database storage
        """
        try:
            secret_path = self._build_secret_path(entity_id, service_name)
            parent = f"projects/{self.project_id}"
            
            # Prepare labels
            secret_labels = {
                "entity_id": str(entity_id),
                "service": service_name,
                "managed_by": "nucleus",
                "created_at": datetime.utcnow().strftime("%Y%m%d")
            }
            if labels:
                secret_labels.update(labels)
            
            # Try to create the secret first
            try:
                secret = self.client.create_secret(
                    request={
                        "parent": parent,
                        "secret_id": secret_path,
                        "secret": {
                            "replication": {"automatic": {}},
                            "labels": secret_labels
                        }
                    }
                )
                logger.info(f"Created new secret: {secret_path}")
            except Exception as e:
                # Secret might already exist, that's okay
                logger.info(f"Secret {secret_path} already exists, will add new version")
            
            # Add secret version with the credentials
            secret_name = self._build_secret_name(entity_id, service_name)
            credentials_json = json.dumps(credentials)
            
            version = self.client.add_secret_version(
                request={
                    "parent": secret_name,
                    "payload": {"data": credentials_json.encode("UTF-8")}
                }
            )
            
            logger.info(f"Stored credentials for {service_name} (entity {entity_id})")
            return secret_path
            
        except Exception as e:
            logger.error(f"Failed to store credentials: {str(e)}")
            raise
    
    def retrieve_credentials(
        self,
        entity_id: str,
        service_name: str,
        version: str = "latest"
    ) -> Dict[str, Any]:
        """
        Retrieve credentials from GCP Secret Manager.
        
        Args:
            entity_id: Entity ID
            service_name: Service name
            version: Secret version (default: "latest")
            
        Returns:
            Credentials dictionary
        """
        try:
            version_name = self._build_version_name(entity_id, service_name, version)
            
            response = self.client.access_secret_version(
                request={"name": version_name}
            )
            
            credentials_json = response.payload.data.decode("UTF-8")
            credentials = json.loads(credentials_json)
            
            logger.info(f"Retrieved credentials for {service_name} (entity {entity_id})")
            return credentials
            
        except Exception as e:
            logger.error(f"Failed to retrieve credentials: {str(e)}")
            raise
    
    def update_credentials(
        self,
        entity_id: str,
        service_name: str,
        credentials: Dict[str, Any]
    ) -> str:
        """
        Update credentials (creates new version).
        
        Args:
            entity_id: Entity ID
            service_name: Service name
            credentials: New credentials dictionary
            
        Returns:
            Secret path reference
        """
        # Updating is the same as storing (creates new version)
        return self.store_credentials(entity_id, service_name, credentials)
    
    def delete_credentials(
        self,
        entity_id: str,
        service_name: str
    ) -> bool:
        """
        Delete credentials from Secret Manager.
        
        Args:
            entity_id: Entity ID
            service_name: Service name
            
        Returns:
            True if successful
        """
        try:
            secret_name = self._build_secret_name(entity_id, service_name)
            
            self.client.delete_secret(
                request={"name": secret_name}
            )
            
            logger.info(f"Deleted credentials for {service_name} (entity {entity_id})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete credentials: {str(e)}")
            raise
    
    def test_credentials(
        self,
        entity_id: str,
        service_name: str,
        credentials: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Test if credentials are valid.
        
        Args:
            entity_id: Entity ID
            service_name: Service name
            credentials: Optional credentials to test (if not provided, retrieves from Secret Manager)
            
        Returns:
            True if credentials are valid
        """
        try:
            if credentials is None:
                credentials = self.retrieve_credentials(entity_id, service_name)
            
            # Service-specific validation would go here
            # For now, just check if credentials exist and have required fields
            
            if service_name == "gmail":
                required_fields = ["access_token", "refresh_token", "token_uri", "client_id", "client_secret"]
                return all(field in credentials for field in required_fields)
            
            elif service_name == "github":
                return "access_token" in credentials
            
            elif service_name == "notion":
                return "access_token" in credentials
            
            else:
                # Generic check
                return bool(credentials)
                
        except Exception as e:
            logger.error(f"Failed to test credentials: {str(e)}")
            return False
