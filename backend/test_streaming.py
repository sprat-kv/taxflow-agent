"""
Test script for streaming agent workflow
Run the backend first: uv run uvicorn app.main:app --reload
Then run this script: uv run python test_streaming.py
"""
import requests
import json

BASE_URL = "http://localhost:8000/api"

def test_streaming_workflow():
    session_id = "test-session-123"
    
    request_data = {
        "filing_status": "single",
        "tax_year": "2024",
        "personal_info": {
            "filer_name": "John Doe",
            "filer_ssn": "123-45-6789",
            "home_address": "123 Main St, New York, NY 10001",
            "digital_assets": "No",
            "occupation": "Software Engineer",
            "phone": "555-1234"
        }
    }
    
    print(f"\n🚀 Starting streaming workflow for session: {session_id}\n")
    print("=" * 60)
    
    with requests.post(
        f"{BASE_URL}/sessions/{session_id}/process/stream",
        json=request_data,
        stream=True,
        headers={"Accept": "text/event-stream"}
    ) as response:
        
        if response.status_code != 200:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            return
        
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                
                if decoded_line.startswith('data: '):
                    data_str = decoded_line[6:]
                    try:
                        data = json.loads(data_str)
                        
                        if 'logs' in data:
                            for log in data['logs']:
                                icon = {
                                    'info': '📄',
                                    'success': '✅',
                                    'warning': '⚠️',
                                    'error': '❌'
                                }.get(log['type'], '•')
                                
                                print(f"{icon} [{log['node']}] {log['message']}")
                        
                        if data.get('status') == 'complete':
                            print("\n" + "=" * 60)
                            print("✅ Workflow Complete!")
                            
                            if 'final_state' in data:
                                calc = data['final_state'].get('calculation_result', {})
                                if calc:
                                    print(f"\n💰 Results:")
                                    print(f"   Gross Income: ${calc.get('gross_income', 0):,.2f}")
                                    print(f"   Tax Liability: ${calc.get('tax_liability', 0):,.2f}")
                                    print(f"   Status: {calc.get('status', 'N/A')}")
                                    print(f"   Refund/Owed: ${calc.get('refund_or_owed', 0):,.2f}")
                    
                    except json.JSONDecodeError:
                        pass

if __name__ == "__main__":
    try:
        test_streaming_workflow()
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to backend. Make sure it's running on http://localhost:8000")
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted by user")

