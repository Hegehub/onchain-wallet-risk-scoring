class FundsOriginAnalyzer:
    """Анализ категорий происхождения средств"""
    
    CATEGORIES = {
        'exchange': {'name': 'Биржи', 'risk_weight': 0.1},
        'mining': {'name': 'Майнинг', 'risk_weight': 0.2},
        'defi': {'name': 'DeFi', 'risk_weight': 0.3},
        'nft': {'name': 'NFT', 'risk_weight': 0.4},
        'gambling': {'name': 'Гемблинг', 'risk_weight': 0.7},
        'mixer': {'name': 'Миксинг', 'risk_weight': 0.9},
        'darknet': {'name': 'Даркнет', 'risk_weight': 1.0},
        'unknown': {'name': 'Неизвестно', 'risk_weight': 0.5}
    }
    
    # Базы известных адресов (упрощенный вариант)
    KNOWN_ADDRESSES = {
        'BTC': {
            'exchange_prefixes': ['1LD', '3J9', 'bc1q'],
            'mining_pools': ['1Mining', '1Pool'],
            'mixers': ['1Tornado', 'bc1qmixer']
        },
        'ETH': {
            'exchanges': {
                '0x3f5ce5fbfe3e9af3971dd833d26ba9b5c936f0be': 'binance',
                '0x28c6c06298d514db089934071355e5743bf21d60': 'binance'
            }
        }
    }
    
    def analyze_btc_origin(self, transactions: list) -> dict:
        """Анализ происхождения BTC средств"""
        category_stats = {cat: {'count': 0, 'amount': 0} for cat in self.CATEGORIES}
        
        for tx in transactions:
            category = self._categorize_btc_transaction(tx)
            category_stats[category]['count'] += 1
            category_stats[category]['amount'] += tx.get('amount', 0)
        
        return self._calculate_percentages(category_stats)
    
    def _categorize_btc_transaction(self, tx: dict) -> str:
        """Определение категории для BTC транзакции"""
        address = tx.get('address', '')
        
        # Проверка по известным адресам
        for prefix in self.KNOWN_ADDRESSES['BTC']['exchange_prefixes']:
            if address.startswith(prefix):
                return 'exchange'
        
        for pool in self.KNOWN_ADDRESSES['BTC']['mining_pools']:
            if pool in address:
                return 'mining'
        
        # Анализ по сумме (паттерны майнинга)
        if 6.25 <= tx.get('amount', 0) <= 6.35:  # Примерно награда за блок
            return 'mining'
        
        return 'unknown'
    
    def _calculate_percentages(self, stats: dict) -> dict:
        """Расчет процентного соотношения категорий"""
        total_tx = sum(cat['count'] for cat in stats.values())
        total_amount = sum(cat['amount'] for cat in stats.values())
        
        result = {}
        for cat, data in stats.items():
            if total_tx > 0:
                tx_percent = (data['count'] / total_tx) * 100
                amount_percent = (data['amount'] / total_amount) * 100 if total_amount > 0 else 0
                
                result[cat] = {
                    'name': self.CATEGORIES[cat]['name'],
                    'tx_percentage': round(tx_percent, 1),
                    'amount_percentage': round(amount_percent, 1),
                    'risk_contribution': round(amount_percent * self.CATEGORIES[cat]['risk_weight'], 1),
                    'transaction_count': data['count'],
                    'total_amount': data['amount']
                }
        
        # Сортировка по вкладу в риск
        result = dict(sorted(result.items(), 
                           key=lambda x: x[1]['risk_contribution'], 
                           reverse=True))
        
        return result