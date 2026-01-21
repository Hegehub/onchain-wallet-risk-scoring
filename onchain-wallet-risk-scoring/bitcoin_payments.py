import requests
import hashlib
import hmac
import base64
from datetime import datetime, timedelta

class BitcoinPaymentProcessor:
    """Обработчик платежей в Bitcoin через WalletPay API[citation:4]"""
    
    def __init__(self, api_key: str, store_id: str):
        self.api_key = api_key
        self.store_id = store_id
        self.base_url = "https://pay.wallet.tg/wpay/store-api/v1"
        
    def create_payment_link(self, amount_btc: float, description: str, 
                          user_id: int, external_id: str) -> dict:
        """Создание ссылки для оплаты в Bitcoin[citation:4]"""
        
        headers = {
            'Wpay-Store-Api-Key': self.api_key,
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        
        # Конвертация в сатоши (1 BTC = 100,000,000 сатоши)
        amount_satoshi = int(amount_btc * 100000000)
        
        payload = {
            'amount': {
                'currencyCode': 'BTC',
                'amount': str(amount_satoshi),
            },
            'description': description,
            'externalId': external_id,
            'timeoutSeconds': 3600,  # 1 час
            'customerTelegramUserId': str(user_id),
            'returnUrl': f'https://t.me/your_bot',  # Ваш бот
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/order",
                json=payload,
                headers=headers,
                timeout=10
            )
            data = response.json()
            
            if response.status_code == 200 and data.get('status') in ['SUCCESS', 'ALREADY']:
                return {
                    'success': True,
                    'pay_link': data['data']['payLink'],
                    'payment_id': data['data']['id'],
                    'amount_btc': amount_btc,
                    'expires_at': datetime.now() + timedelta(seconds=3600)
                }
            else:
                return {'success': False, 'error': data.get('message', 'Unknown error')}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def check_payment_status(self, payment_id: str) -> dict:
        """Проверка статуса платежа"""
        headers = {
            'Wpay-Store-Api-Key': self.api_key,
            'Accept': 'application/json',
        }
        
        try:
            response = requests.get(
                f"{self.base_url}/order/{payment_id}",
                headers=headers,
                timeout=10
            )
            data = response.json()
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'status': data['data']['status'],
                    'paid_at': data['data'].get('paidAt'),
                    'amount_paid': data['data'].get('selectedPaymentOption', {}).get('amount', {})
                }
            else:
                return {'success': False, 'error': 'Payment not found'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def verify_webhook_signature(self, request) -> bool:
        """Верификация подписи вебхука[citation:4]"""
        ENCODING = 'utf-8'
        
        text = '.'.join([
            request.method,
            request.path,
            request.headers.get('WalletPay-Timestamp'),
            base64.b64encode(request.get_data()).decode(ENCODING),
        ])
        
        signature = base64.b64encode(hmac.new(
            bytes(self.api_key, ENCODING),
            msg=bytes(text, ENCODING),
            digestmod=hashlib.sha256
        ).digest())
        
        return request.headers.get('Walletpay-Signature') == signature.decode(ENCODING)