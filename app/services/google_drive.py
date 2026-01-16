from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from typing import List, Dict
from app.services.google_docs import GoogleDocsReader

class GoogleDriveService:
    def __init__(self, credentials_path: str):
        self.credentials = service_account.Credentials.from_service_account_file(
            credentials_path,
            scopes=[
                'https://www.googleapis.com/auth/drive.readonly',
                'https://www.googleapis.com/auth/documents.readonly'
            ]
        )
        self.drive_service = build('drive', 'v3', credentials=self.credentials)
        self.docs_reader = GoogleDocsReader(credentials_path)
    
    def list_documents_in_folder(self, folder_id: str) -> List[Dict[str, str]]:
        """List all Google Docs in a folder"""
        try:
            query = f"'{folder_id}' in parents and mimeType='application/vnd.google-apps.document' and trashed=false"
            
            results = self.drive_service.files().list(
                q=query,
                fields="files(id, name, modifiedTime)",
                orderBy="modifiedTime desc"
            ).execute()
            
            files = results.get('files', [])
            
            return [
                {
                    'id': file['id'],
                    'name': file['name'],
                    'modified': file.get('modifiedTime', 'Unknown')
                }
                for file in files
            ]
        
        except HttpError as e:
            if e.resp.status == 404:
                raise Exception(
                    f"Folder not found. Please check:\n"
                    f"1. The folder ID is correct\n"
                    f"2. The folder exists in Google Drive"
                )
            elif e.resp.status == 403:
                raise Exception(
                    f"Permission denied. Please ensure:\n"
                    f"1. The folder is shared with your service account\n"
                    f"2. Service account email has at least 'Viewer' access\n"
                    f"3. Check your GOOGLE_DRIVE_FOLDER_ID in .env"
                )
            else:
                raise Exception(f"Error accessing Google Drive: {str(e)}")
        except Exception as e:
            raise Exception(f"Error listing documents in folder: {str(e)}")
    
    def get_document_content(self, document_id: str) -> str:
        """Get content of a specific document"""
        return self.docs_reader.read_document(document_id)
    
    def get_document_metadata(self, document_id: str) -> Dict[str, str]:
        """Get metadata for a document"""
        try:
            file = self.drive_service.files().get(
                fileId=document_id,
                fields="id, name, modifiedTime, createdTime, webViewLink"
            ).execute()
            
            return {
                'id': file['id'],
                'name': file['name'],
                'modified': file.get('modifiedTime', 'Unknown'),
                'created': file.get('createdTime', 'Unknown'),
                'url': file.get('webViewLink', '')
            }
        
        except HttpError as e:
            if e.resp.status == 404:
                raise Exception(f"Document not found: {document_id}")
            elif e.resp.status == 403:
                raise Exception(f"Permission denied for document: {document_id}")
            else:
                raise Exception(f"Error getting document metadata: {str(e)}")
        except Exception as e:
            raise Exception(f"Error getting document metadata: {str(e)}")