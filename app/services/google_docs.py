from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from typing import Optional

class GoogleDocsReader:
    def __init__(self, credentials_path: str):
        self.credentials = service_account.Credentials.from_service_account_file(
            credentials_path,
            scopes=['https://www.googleapis.com/auth/documents.readonly']
        )
        self.service = build('docs', 'v1', credentials=self.credentials)
    
    def read_document(self, document_id: str) -> str:
        """Read and extract text from Google Doc"""
        try:
            document = self.service.documents().get(documentId=document_id).execute()
            return self._extract_text(document)
        except HttpError as e:
            # Handle specific Google API errors
            if e.resp.status == 404:
                raise Exception(f"Document not found. Please check the document ID: {document_id}")
            elif e.resp.status == 403:
                raise Exception(
                    f"Permission denied. Please ensure:\n"
                    f"1. The document is shared with your service account\n"
                    f"2. The service account has at least 'Viewer' access\n"
                    f"3. The document is not private/restricted"
                )
            else:
                raise Exception(f"Error reading document: {str(e)}")
        except Exception as e:
            raise Exception(f"Error reading document: {str(e)}")
    
    def _extract_text(self, document: dict) -> str:
        """Extract plain text from document structure"""
        text_parts = []
        
        content = document.get('body', {}).get('content', [])
        
        for element in content:
            if 'paragraph' in element:
                paragraph = element['paragraph']
                for text_element in paragraph.get('elements', []):
                    if 'textRun' in text_element:
                        text_parts.append(text_element['textRun']['content'])
            
            elif 'table' in element:
                table = element['table']
                for row in table.get('tableRows', []):
                    for cell in row.get('tableCells', []):
                        for cell_content in cell.get('content', []):
                            if 'paragraph' in cell_content:
                                paragraph = cell_content['paragraph']
                                for text_element in paragraph.get('elements', []):
                                    if 'textRun' in text_element:
                                        text_parts.append(text_element['textRun']['content'])
        
        return ''.join(text_parts).strip()