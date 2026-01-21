from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import asyncio
import logging

class RiskAnalyzerBot:
    """Главный класс Telegram бота"""
    
    def __init__(self, token: str):
        self.bot = Bot(token=token)
        self.dp = Dispatcher()
        
        # Инициализация модулей
        self.validator = AddressValidator()
        self.origin_analyzer = FundsOriginAnalyzer()
        self.btc_checker = BitcoinAddressChecker()
        
        # Инициализация платежной системы
        self.payment_processor = BitcoinPaymentProcessor(
            api_key="YOUR_WALLETPAY_API_KEY",
            store_id="YOUR_STORE_ID"
        )
        
        # Регистрация обработчиков
        self.register_handlers()
    
    def register_handlers(self):
        """Регистрация команд бота"""
        
        @self.dp.message(Command("start"))
        async def start_command(message: types.Message):
            await self.handle_start(message)
        
        @self.dp.message(Command("analyze"))
        async def analyze_command(message: types.Message):
            await self.handle_analyze(message)
        
        @self.dp.message(Command("subscription"))
        async def subscription_command(message: types.Message):
            await self.handle_subscription(message)
        
        @self.dp.callback_query()
        async def callback_handler(callback: types.CallbackQuery):
            await self.handle_callback(callback)
    
    async def handle_start(self, message: types.Message):
        """Обработка команды /start"""
        welcome_text = """
🔍 **RiskAnalyzer Bot** — профессиональный анализ рисков крипто-кошельков

Возможности:
• Анализ рисков в % (0-100%)
• Определение происхождения средств
• Проверка BTC/ETH адресов
• Мониторинг подозрительной активности

Команды:
/analyze [адрес] — анализ кошелька
/subscription — подписки и тарифы
/help — справка

📊 **Тарифы:**
🆓 Бесплатный: 3 анализа в день
🚀 PRO (0.001 BTC/мес): безлимитный анализ
🏢 Business (0.005 BTC/мес): API + отчеты
        """
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔍 Анализ кошелька", callback_data="quick_analyze")],
            [InlineKeyboardButton(text="💎 Тарифы и подписки", callback_data="show_tiers")],
            [InlineKeyboardButton(text="📊 Пример отчета", callback_data="sample_report")]
        ])
        
        await message.answer(welcome_text, parse_mode='Markdown', reply_markup=keyboard)
    
    async def handle_analyze(self, message: types.Message):
        """Обработка анализа кошелька"""
        try:
            # Извлечение адреса из сообщения
            parts = message.text.split()
            if len(parts) < 2:
                await message.answer("Использование: /analyze <адрес_кошелька>")
                return
            
            address = parts[1]
            
            # Валидация адреса
            validation = self.validator.validate_address(address)
            
            if not validation['is_valid']:
                await message.answer("❌ Неверный формат адреса. Проверьте правильность.")
                return
            
            # Отправка статуса анализа
            status_msg = await message.answer(f"🔍 Анализирую {validation['chain']} адрес...")
            
            # Анализ в зависимости от сети
            if validation['chain'] == 'BTC':
                result = await self.analyze_btc_wallet(address)
            elif validation['chain'] == 'ETH':
                result = await self.analyze_eth_wallet(address)
            else:
                await message.answer("❌ Поддерживаются только BTC и ETH адреса")
                return
            
            # Формирование и отправка отчета
            report = self.generate_risk_report(address, result)
            
            await message.answer(report, parse_mode='HTML')
            await self.bot.delete_message(message.chat.id, status_msg.message_id)
            
        except Exception as e:
            logging.error(f"Analysis error: {e}")
            await message.answer("❌ Ошибка анализа. Попробуйте позже.")
    
    async def analyze_btc_wallet(self, address: str) -> dict:
        """Анализ Bitcoin кошелька"""
        # Проверка баланса и транзакций
        balance_info = self.btc_checker.check_address_balance(address)
        transactions = self.btc_checker.get_address_transactions(address, limit=100)
        
        if not balance_info['success']:
            return {'error': 'Не удалось получить данные'}
        
        # Анализ происхождения средств
        origin_analysis = self.origin_analyzer.analyze_btc_origin(transactions)
        
        # Расчет общего риска
        total_risk = self.calculate_total_risk(balance_info, origin_analysis)
        
        return {
            'chain': 'BTC',
            'balance': balance_info,
            'transactions': transactions[:10],  # Последние 10 транзакций
            'origin_analysis': origin_analysis,
            'total_risk': total_risk,
            'risk_factors': self.identify_risk_factors(origin_analysis)
        }
    
    def calculate_total_risk(self, balance_info: dict, origin_analysis: dict) -> float:
        """Расчет общего процента риска"""
        base_risk = 0
        
        # Риск от происхождения средств
        for category, data in origin_analysis.items():
            base_risk += data['risk_contribution']
        
        # Дополнительные факторы риска
        if balance_info['transaction_count'] > 1000:
            base_risk += 15  # Высокая активность
        
        if balance_info['balance_btc'] > 10:
            base_risk -= 10  # Крупный баланс (менее рискованно)
        
        # Ограничение 0-100%
        return max(0, min(100, base_risk))
    
    def generate_risk_report(self, address: str, analysis: dict) -> str:
        """Генерация HTML отчета"""
        risk_pct = analysis.get('total_risk', 0)
        
        # Определение уровня риска
        if risk_pct <= 20:
            risk_level = "НИЗКИЙ"
            emoji = "🟢"
            color = "#10B981"
        elif risk_pct <= 50:
            risk_level = "УМЕРЕННЫЙ"
            emoji = "🟡"
            color = "#F59E0B"
        elif risk_pct <= 75:
            risk_level = "ВЫСОКИЙ"
            emoji = "🔴"
            color = "#EF4444"
        else:
            risk_level = "КРИТИЧЕСКИЙ"
            emoji = "☣️"
            color = "#7C3AED"
        
        # Прогресс-бар
        progress = "█" * int(risk_pct / 5) + "░" * (20 - int(risk_pct / 5))
        
        report = f"""
{emoji} <b>АНАЛИЗ РИСКА КОШЕЛЬКА</b>
━━━━━━━━━━━━━━━━━━━━━━━━

<b>📍 Адрес:</b> <code>{address[:15]}...{address[-10:]}</code>
<b>📊 Общий риск:</b> <span style="color: {color}"><b>{risk_pct}%</b></span>
<b>🏷️ Уровень:</b> {risk_level}

[{progress}]

<b>💰 БАЛАНС:</b>
• Текущий: {analysis['balance'].get('balance_btc', 0):.8f} BTC
• Всего транзакций: {analysis['balance'].get('transaction_count', 0)}

<b>🏷️ КАТЕГОРИИ ПРОИСХОЖДЕНИЯ:</b>
"""
        
        # Добавление категорий
        origin_data = analysis.get('origin_analysis', {})
        for i, (category, data) in enumerate(list(origin_data.items())[:5], 1):
            if data['amount_percentage'] > 5:  # Показываем только значимые категории
                bar = "█" * int(data['amount_percentage'] / 10)
                report += f"\n{i}. {data['name']}: {bar} {data['amount_percentage']:.1f}%"
        
        # Факторы риска
        if analysis.get('risk_factors'):
            report += "\n\n<b>⚠️ ФАКТОРЫ РИСКА:</b>"
            for i, factor in enumerate(analysis['risk_factors'][:3], 1):
                report += f"\n{i}. {factor}"
        
        # Рекомендации
        report += "\n\n<b>💡 РЕКОМЕНДАЦИИ:</b>"
        if risk_pct <= 30:
            report += "\n• Кошелек выглядит безопасно"
            report += "\n• Продолжайте стандартные практики безопасности"
        elif risk_pct <= 60:
            report += "\n• Проверьте историю транзакций"
            report += "\n• Избегайте взаимодействия с подозрительными контрактами"
        else:
            report += "\n• Рекомендуется использовать новый кошелек"
            report += "\n• Проведите дополнительную проверку"
        
        report += "\n\n<i>Отчет сгенерирован: " + datetime.now().strftime("%d.%m.%Y %H:%M") + "</i>"
        
        return report
    
    async def handle_subscription(self, message: types.Message):
        """Обработка подписок"""
        subscription_text = """
💎 <b>ВЫБОР ПОДПИСКИ</b>

<b>🆓 БЕСПЛАТНЫЙ</b>
• 3 анализа в день
• Базовый отчет
• Только BTC/ETH

<b>🚀 PRO - 0.001 BTC/месяц</b>
• Безлимитный анализ
• Расширенный отчет
• Анализ происхождения средств
• 5+ блокчейнов
• История анализов (30 дней)

<b>🏢 BUSINESS - 0.005 BTC/месяц</b>
• Всё из PRO +
• API доступ (1000 запросов/день)
• White-label отчеты
• Приоритетная поддержка
• Кастомные интеграции
        """
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🆓 Бесплатный", callback_data="tier_free"),
                InlineKeyboardButton(text="🚀 PRO (0.001 BTC)", callback_data="tier_pro")
            ],
            [
                InlineKeyboardButton(text="🏢 Business (0.005 BTC)", callback_data="tier_business")
            ],
            [
                InlineKeyboardButton(text="📋 Сравнение", callback_data="compare_tiers")
            ]
        ])
        
        await message.answer(subscription_text, parse_mode='HTML', reply_markup=keyboard)
    
    async def handle_callback(self, callback: types.CallbackQuery):
        """Обработка inline кнопок"""
        data = callback.data
        
        if data.startswith("tier_"):
            tier = data.split("_")[1]
            await self.process_subscription_payment(callback, tier)
        
        elif data == "quick_analyze":
            await callback.message.answer(
                "Введите адрес кошелька для анализа:\n\n"
                "Примеры:\n"
                "<code>1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa</code> (BTC)\n"
                "<code>0x742d35Cc6634C0532925a3b844Bc9e</code> (ETH)",
                parse_mode='HTML'
            )
        
        await callback.answer()
    
    async def process_subscription_payment(self, callback: types.CallbackQuery, tier: str):
        """Обработка платежа за подписку"""
        tier_prices = {
            'free': 0,
            'pro': 0.001,  # 0.001 BTC
            'business': 0.005  # 0.005 BTC
        }
        
        tier_names = {
            'free': 'Бесплатный',
            'pro': 'PRO',
            'business': 'Business'
        }
        
        if tier == 'free':
            await callback.message.answer(
                "✅ Вы используете бесплатный тариф.\n"
                "Для расширенных функций выберите PRO или Business."
            )
            return
        
        # Создание платежной ссылки
        amount_btc = tier_prices[tier]
        external_id = f"sub_{callback.from_user.id}_{int(datetime.now().timestamp())}"
        
        payment_result = self.payment_processor.create_payment_link(
            amount_btc=amount_btc,
            description=f"Подписка {tier_names[tier]} на RiskAnalyzer",
            user_id=callback.from_user.id,
            external_id=external_id
        )
        
        if payment_result['success']:
            payment_text = f"""
💳 <b>ОПЛАТА ПОДПИСКИ {tier_names[tier].upper()}</b>

Сумма: <code>{amount_btc:.6f} BTC</code>
Тариф: {tier_names[tier]}
Действует: 30 дней

<b>Инструкция:</b>
1. Нажмите кнопку ниже для оплаты
2. Оплатите счёт в вашем крипто-кошельке
3. Подписка активируется автоматически

⏰ Счёт действителен 1 час
            """
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📲 Оплатить Bitcoin", url=payment_result['pay_link'])],
                [InlineKeyboardButton(text="🔄 Проверить статус", callback_data=f"check_payment_{external_id}")]
            ])
            
            await callback.message.answer(payment_text, parse_mode='HTML', reply_markup=keyboard)
        else:
            await callback.message.answer(f"❌ Ошибка создания счёта: {payment_result.get('error', 'Unknown error')}")

async def main():
    """Основная функция запуска бота"""
    bot = RiskAnalyzerBot(token="YOUR_BOT_TOKEN")
    
    # Запуск бота
    await bot.dp.start_polling(bot.bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())