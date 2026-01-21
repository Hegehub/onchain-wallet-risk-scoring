import requests
import json
from typing import List, Dict

class BitcoinAddressChecker:
    """Проверка баланса и транзакций Bitcoin адресов[citation:2]"""
    
    def __init__(self):
        self.api_url = "https://blockchain.info"
        self.satoshi = 1e8  # 1 BTC в сатоши
    
    def check_address_balance(self, address: str) -> Dict:
        """Проверка баланса одного адреса"""
        try:
            # Используем API blockchain.info[citation:2]
            url = f"{self.api_url}/balance?active={address}"
            response = requests.get(url, timeout=10)
            data = response.json()
            
            if address in data:
                address_data = data[address]
                balance_btc = address_data['final_balance'] / self.satoshi
                
                return {
                    'success': True,
                    'address': address,
                    'balance_btc': balance_btc,
                    'balance_satoshi': address_data['final_balance'],
                    'total_received': address_data['total_received'] / self.satoshi,
                    'total_sent': address_data['total_sent'] / self.satoshi,
                    'transaction_count': address_data['n_tx'],
                    'unconfirmed_balance': address_data['unconfirmed_balance'] / self.satoshi
                }
            else:
                return {'success': False, 'error': 'Address not found'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_address_transactions(self, address: str, limit: int = 50) -> List[Dict]:
        """Получение истории транзакций"""
        try:
            url = f"{self.api_url}/rawaddr/{address}?limit={limit}"
            response = requests.get(url, timeout=10)
            data = response.json()
            
            transactions = []
            for tx in data.get('txs', []):
                transaction = {
                    'hash': tx['hash'],
                    'time': datetime.fromtimestamp(tx['time']),
                    'confirmations': tx.get('block_height', 0),
                    'inputs': [],
                    'outputs': []
                }
                
                # Анализ входов
                for inp in tx.get('inputs', []):
                    if 'prev_out' in inp:
                        transaction['inputs'].append({
                            'address': inp['prev_out'].get('addr'),
                            'value': inp['prev_out'].get('value', 0) / self.satoshi
                        })
                
                # Анализ выходов
                for out in tx.get('out', []):
                    transaction['outputs'].append({
                        'address': out.get('addr'),
                        'value': out.get('value', 0) / self.satoshi,
                        'spent': out.get('spent', False)
                    })
                
                transactions.append(transaction)
            
            return transactions
            
        except Exception as e:
            return []
    
    def check_multiple_addresses(self, addresses: List[str]) -> Dict:
        """Проверка нескольких адресов (до 100 за запрос)[citation:2]"""
        try:
            # Объединяем адреса через | как в blockchain.info API[citation:2]
            addresses_str = '|'.join(addresses[:100])  # Лимит API
            
            url = f"{self.api_url}/balance?active={addresses_str}"
            response = requests.get(url, timeout=15)
            data = response.json()
            
            results = {}
            total_balance = 0
            
            for addr in addresses[:100]:
                if addr in data:
                    balance_btc = data[addr]['final_balance'] / self.satoshi
                    results[addr] = {
                        'balance_btc': balance_btc,
                        'transaction_count': data[addr]['n_tx']
                    }
                    total_balance += balance_btc
            
            return {
                'success': True,
                'results': results,
                'total_balance_btc': total_balance,
                'addresses_checked': len(results)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}