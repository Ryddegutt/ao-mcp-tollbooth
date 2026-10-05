import os
import requests
from dotenv import load_dotenv

load_dotenv()

TOLLBOOTH_WALLET_ADDRESS = os.getenv("TOLLBOOTH_WALLET_ADDRESS", "")
PRICE_PER_TRIAGE_AO = float(os.getenv("PRICE_PER_TRIAGE_AO", "0.001"))
REQUIRE_PAYMENT = os.getenv("REQUIRE_PAYMENT", "true").lower() == "true"

def verify_ao_payment(tx_id: str, expected_recipient: str = TOLLBOOTH_WALLET_ADDRESS) -> bool:
    """
    Verifiserer transaksjons-ID via Arweave/AO GraphQL gateway.
    """
    if not tx_id:
        return False
        
    url = "https://arweave.net/graphql"
    query = """
    query ($txId: ID!) {
      transaction(id: $txId) {
        id
        recipient
        quantity {
          ar
        }
      }
    }
    """
    try:
        response = requests.post(url, json={"query": query, "variables": {"txId": tx_id}}, timeout=10)
        if response.status_code != 200:
            return False
            
        data = response.json()
        tx = data.get("data", {}).get("transaction")
        
        if not tx:
            return False
            
        return tx.get("recipient") == expected_recipient
    except Exception as e:
        print(f"Feil ved verifisering av betaling: {e}")
        return False