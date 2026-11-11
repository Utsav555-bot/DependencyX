import os
import aiofiles
from typing import Optional
from backend.app.config import settings
from backend.app.core.logging import logger

class BlobStorageService:
    def __init__(self):
        self.connection_string = settings.AZURE_STORAGE_CONNECTION_STRING.strip()
        self.container_name = settings.AZURE_STORAGE_CONTAINER_NAME
        self.local_dir = settings.LOCAL_STORAGE_DIR
        self.is_azure = bool(self.connection_string)

        if not self.is_azure:
            os.makedirs(self.local_dir, exist_ok=True)
            logger.info(f"Using Local Storage Fallback at: {os.path.abspath(self.local_dir)}")
        else:
            logger.info("Initializing Azure Blob Storage Client...")
            try:
                from azure.storage.blob import BlobServiceClient
                self.blob_service_client = BlobServiceClient.from_connection_string(self.connection_string)
                self.container_client = self.blob_service_client.get_container_client(self.container_name)
                # Ensure container exists
                if not self.container_client.exists():
                    self.container_client.create_container()
            except Exception as e:
                logger.warning(f"Could not connect to Azure Blob Storage ({e}). Falling back to local storage.")
                self.is_azure = False
                os.makedirs(self.local_dir, exist_ok=True)

    async def upload_file(self, file_content: bytes, destination_path: str, content_type: str = "application/json") -> str:
        """
        Uploads content to Azure Blob Storage or local storage.
        Returns the persistent path / URL identifier.
        """
        if self.is_azure:
            try:
                from azure.storage.blob import ContentSettings
                blob_client = self.container_client.get_blob_client(destination_path)
                blob_client.upload_blob(
                    file_content,
                    overwrite=True,
                    content_settings=ContentSettings(content_type=content_type)
                )
                logger.info(f"Uploaded to Azure Blob: {destination_path}")
                return f"azure://{self.container_name}/{destination_path}"
            except Exception as e:
                logger.error(f"Azure Blob upload error: {e}. Falling back to local disk.")
        
        # Local storage fallback
        clean_path = destination_path.replace("/", os.sep).replace("\\", os.sep)
        full_path = os.path.join(self.local_dir, clean_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        async with aiofiles.open(full_path, "wb") as f:
            await f.write(file_content)
        logger.info(f"Saved file to local storage: {full_path}")
        return f"local://{destination_path}"

    async def read_file(self, storage_path: str) -> Optional[bytes]:
        """
        Reads content from Azure Blob or local storage.
        """
        if storage_path.startswith("azure://"):
            relative_blob = storage_path.replace(f"azure://{self.container_name}/", "")
            try:
                blob_client = self.container_client.get_blob_client(relative_blob)
                download_stream = blob_client.download_blob()
                return download_stream.readall()
            except Exception as e:
                logger.error(f"Error reading from Azure Blob: {e}")
                return None
        
        # Local read
        clean_path = storage_path.replace("local://", "").replace("/", os.sep).replace("\\", os.sep)
        full_path = os.path.join(self.local_dir, clean_path)
        if not os.path.exists(full_path):
            return None
        async with aiofiles.open(full_path, "rb") as f:
            return await f.read()

storage_service = BlobStorageService()
