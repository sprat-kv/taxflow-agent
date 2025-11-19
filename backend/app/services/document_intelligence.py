from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeResult
from app.core.config import settings

class DocumentIntelligenceService:
    """Service wrapper for Azure Document Intelligence API."""
    
    def __init__(self):
        self.client = DocumentIntelligenceClient(
            endpoint=settings.DOCUMENTINTELLIGENCE_ENDPOINT,
            credential=AzureKeyCredential(settings.DOCUMENTINTELLIGENCE_API_KEY)
        )
    
    def analyze_tax_document(self, pdf_bytes: bytes) -> AnalyzeResult:
        """
        Analyze a tax document using Azure's prebuilt tax model.
        
        Args:
            pdf_bytes: PDF file contents as bytes
            
        Returns:
            AnalyzeResult containing document fields and metadata
        """
        poller = self.client.begin_analyze_document("prebuilt-tax.us", pdf_bytes)
        return poller.result()

_service_instance = None

def get_document_intelligence_service() -> DocumentIntelligenceService:
    """Get or create singleton instance of DocumentIntelligenceService."""
    global _service_instance
    if _service_instance is None:
        _service_instance = DocumentIntelligenceService()
    return _service_instance

