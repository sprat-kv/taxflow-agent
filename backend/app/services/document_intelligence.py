from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeResult
from app.core.config import settings

class DocumentIntelligenceService:
    def __init__(self):
        self.client = DocumentIntelligenceClient(
            endpoint=settings.DOCUMENTINTELLIGENCE_ENDPOINT,
            credential=AzureKeyCredential(settings.DOCUMENTINTELLIGENCE_API_KEY)
        )
    
    def analyze_tax_document(self, pdf_bytes: bytes) -> AnalyzeResult:
        poller = self.client.begin_analyze_document("prebuilt-tax.us", pdf_bytes)
        return poller.result()

_service_instance = None

def get_document_intelligence_service() -> DocumentIntelligenceService:
    global _service_instance
    if _service_instance is None:
        _service_instance = DocumentIntelligenceService()
    return _service_instance

