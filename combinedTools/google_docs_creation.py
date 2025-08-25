from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import os
import re

def create_google_docs_summary(markdown: str):
    """
    Create a meeting summary in Google Docs with proper formatting
    """
    
    SCOPES = ["https://www.googleapis.com/auth/documents"]
    
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
        creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    
    service = build("docs", "v1", credentials=creds)
    
    document = {"title": "PORTIA TESTING Meet - Meeting Preparation"}
    doc = service.documents().create(body=document).execute()
    document_id = doc.get("documentId")
    
    requests = []
    current_index = 1
    
    lines = markdown.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if line.startswith('# '):
            requests.append({
                "insertText": {
                    "location": {"index": current_index},
                    "text": line[2:] + "\n"
                }
            })
            requests.append({
                "updateParagraphStyle": {
                    "range": {
                        "startIndex": current_index,
                        "endIndex": current_index + len(line[2:])
                    },
                    "paragraphStyle": {
                        "namedStyleType": "HEADING_1"
                    },
                    "fields": "namedStyleType"
                }
            })
            current_index += len(line[2:]) + 1
            
        elif line.startswith('## '):
            requests.append({
                "insertText": {
                    "location": {"index": current_index},
                    "text": line[3:] + "\n"
                }
            })
            requests.append({
                "updateParagraphStyle": {
                    "range": {
                        "startIndex": current_index,
                        "endIndex": current_index + len(line[3:])
                    },
                    "paragraphStyle": {
                        "namedStyleType": "HEADING_2"
                    },
                    "fields": "namedStyleType"
                }
            })
            current_index += len(line[3:]) + 1
            
        elif line.startswith('### '):
            requests.append({
                "insertText": {
                    "location": {"index": current_index},
                    "text": line[4:] + "\n"
                }
            })
            requests.append({
                "updateParagraphStyle": {
                    "range": {
                        "startIndex": current_index,
                        "endIndex": current_index + len(line[4:])
                    },
                    "paragraphStyle": {
                        "namedStyleType": "HEADING_3"
                    },
                    "fields": "namedStyleType"
                }
            })
            current_index += len(line[4:]) + 1
            
        elif line.startswith('- '):
            requests.append({
                "insertText": {
                    "location": {"index": current_index},
                    "text": line[2:] + "\n"
                }
            })
            requests.append({
                "createParagraphBullets": {
                    "range": {
                        "startIndex": current_index,
                        "endIndex": current_index + len(line[2:])
                    },
                    "bulletPreset": "BULLET_DISC_CIRCLE_SQUARE"
                }
            })
            current_index += len(line[2:]) + 1
            
        elif line.startswith('|'):
            requests.append({
                "insertText": {
                    "location": {"index": current_index},
                    "text": line + "\n"
                }
            })
            current_index += len(line) + 1
            
        else:
            requests.append({
                "insertText": {
                    "location": {"index": current_index},
                    "text": line + "\n"
                }
            })
            current_index += len(line) + 1
    
    if requests:
        service.documents().batchUpdate(
            documentId=document_id, 
            body={"requests": requests}
        ).execute()
    
    return f"https://docs.google.com/document/d/{document_id}"


# print(create_google_docs_summary(markdown_summary))
