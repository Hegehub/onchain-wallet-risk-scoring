# Установите библиотеку: pip install git+https://github.com/0x9090/CrypocurrencyAddressValidation.git
from cryptocurrencyaddressvalidation import Validation

class AddressValidator:
    """Валидация адресов криптовалют"""
    
    @staticmethod
    def validate_btc_address(address: str) -> bool:
        """Проверка адреса Bitcoin (P2PKH, P2SH, Bech32)[citation:6]"""
        try:
            return Validation.validate('BTC', 'MAINNET', address)
        except:
            return False
    
    @staticmethod
    def validate_eth_address(address: str) -> bool:
        """Проверка адреса Ethereum"""
        try:
            return Validation.validate('ETH', 'MAINNET', address)
        except:
            # Базовая проверка формата
            return address.startswith('0x') and len(address) == 42
    
    @staticmethod
    def validate_address(address: str, chain: str = 'auto') -> dict:
        """Универсальная проверка адреса"""
        result = {
            'is_valid': False,
            'chain': 'unknown',
            'details': {}
        }
        
        # Автоопределение сети
        if chain == 'auto':
            if AddressValidator.validate_btc_address(address):
                result['is_valid'] = True
                result['chain'] = 'BTC'
            elif AddressValidator.validate_eth_address(address):
                result['is_valid'] = True
                result['chain'] = 'ETH'
        else:
            if chain.upper() == 'BTC':
                result['is_valid'] = AddressValidator.validate_btc_address(address)
                result['chain'] = 'BTC'
            elif chain.upper() == 'ETH':
                result['is_valid'] = AddressValidator.validate_eth_address(address)
                result['chain'] = 'ETH'
        
        return result