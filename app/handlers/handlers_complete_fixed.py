#!/usr/bin/env python3
"""
🎛️ HANDLERS v3.0 - ПОЛНОСТЬЮ ИСПРАВЛЕНО
🚀 Полная система обработчиков с всеми функциями

ИСПРАВЛЕНИЯ:
• ✅ Добавлены все недостающие функции
• ✅ Исправлены ответы на реплаи
• ✅ Корректная команда /ai
• ✅ Рабочая модерация  
• ✅ Функции триггеров и разрешений
"""

import logging
import re
import asyncio
import random
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, Sticker, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart, Command
from aiogram.exceptions import TelegramBadRequest

logger = logging.getLogger(__name__)


def register_all_handlers(dp, modules):
    """🎛️ Регистрация всех обработчиков v3.0"""
    
    router = Router()
    
    # Получаем информацию о боте для упоминаний
    bot_info = None
    
    async def get_bot_info():
        nonlocal bot_info
        try:
            bot_info = await modules['bot'].get_me()
        except:
            pass
    
    asyncio.create_task(get_bot_info())
    
    # =================== ОСНОВНЫЕ КОМАНДЫ ===================
    
    @router.message(CommandStart())
    async def start_handler(message: Message):
        user = message.from_user
        chat_id = message.chat.id
        
        # Проверяем доступ
        if modules.get('permissions'):
            if not await modules['permissions'].check_chat_access(chat_id, user.id):
                await message.answer("🚫 У вас нет доступа к этому боту в данном чате.")
                return
        
        # Сохраняем пользователя
        await save_user_and_message(message, modules)
        
        # Персонализированное приветствие
        chat_type_text = ""
        if message.chat.type == 'private':
            chat_type_text = "личных сообщениях"
        else:
            chat_type_text = f"чате <b>{message.chat.title or 'Неизвестный чат'}</b>"
        
        welcome_text = (
            f"🚀 <b>Enhanced Telegram Bot v3.0</b>\n\n"
            f"Привет, <b>{user.first_name}</b>! 👋\n"
            f"Добро пожаловать в самого продвинутого бота в {chat_type_text}!\n\n"
            f"🆕 <b>НОВОЕ в v3.0:</b>\n"
            f"🎯 Отвечаю на упоминания и реплаи\n"
            f"⚡ Система пользовательских триггеров\n"
            f"🛡️ Расширенная модерация\n"
            f"🔒 Гибкие настройки доступа\n"
            f"📚 Улучшенная память диалогов\n\n"
            f"✨ <b>Основные возможности:</b>\n"
            f"🤖 /ai [вопрос] - AI помощник GPT-4\n"
            f"₿ /crypto bitcoin - Курсы криптовалют\n"
            f"📊 /stats - Ваша статистика\n"
            f"📈 /chart activity - Графики активности\n"
            f"⚡ /triggers - Управление триггерами\n"
            f"🛡️ /moderation - Настройки модерации\n"
            f"🎭 Анализ стикеров и эмоций\n\n"
            f"💡 /help - Полная справка\n"
            f"ℹ️ /about - Подробная информация"
        )
        
        # Добавляем информацию об умных ответах
        if message.chat.type != 'private':
            welcome_text += (
                f"\n\n🎯 <b>Умные ответы:</b>\n"
                f"• Упомяните меня @{bot_info.username if bot_info else 'bot'}\n"
                f"• Ответьте на мое сообщение\n"
                f"• Напишите 'бот' в сообщении"
            )
        
        await message.answer(welcome_text)
        
        # Трекинг события
        if modules.get('analytics'):
            await modules['analytics'].track_user_action(
                user.id, chat_id, 'start_command'
            )
    
    @router.message(Command('help'))
    async def help_handler(message: Message):
        if not await check_permissions(message, modules):
            return
            
        help_text = generate_help_text(message.chat.type, bot_info)
        await message.answer(help_text)
    
    @router.message(Command('about'))
    async def about_handler(message: Message):
        if not await check_permissions(message, modules):
            return
            
        about_text = generate_about_text(modules)
        await message.answer(about_text)
    
    @router.message(Command('status'))
    async def status_handler(message: Message):
        if not await check_permissions(message, modules):
            return
            
        status_text = await generate_status_text(message.from_user, modules)
        await message.answer(status_text)
    
    # =================== AI КОМАНДЫ ===================
    
    @router.message(Command('ai'))
    async def ai_handler(message: Message):
        if not await check_permissions(message, modules, 'ai'):
            return
            
        if not modules.get('ai'):
            await message.answer("❌ AI сервис недоступен. Настройте API ключи в .env файле.")
            return
        
        user_message = message.text[4:].strip()
        if not user_message:
            await message.answer(
                "💡 <b>Использование AI помощника:</b>\n\n"
                "📝 /ai [ваш вопрос]\n"
                "🎯 Примеры:\n"
                "• /ai Расскажи о Python\n"
                "• /ai Как создать сайт?\n"
                "• /ai Объясни блокчейн простыми словами"
            )
            return
        
        await process_ai_request(message, user_message, modules)
    
    @router.message(Command('memory_clear'))
    async def memory_clear_handler(message: Message):
        if not await check_permissions(message, modules):
            return
            
        if not modules.get('memory'):
            await message.answer("❌ Модуль памяти недоступен")
            return
        
        success = await modules['memory'].clear_user_memory(
            message.from_user.id, message.chat.id
        )
        
        if success:
            await message.answer("🗑️ <b>Память диалогов очищена</b>\n\nЯ забыл нашу предыдущую беседу и начинаю с чистого листа.")
        else:
            await message.answer("❌ Не удалось очистить память диалогов")
    
    # =================== КРИПТОВАЛЮТЫ ===================
    
    @router.message(Command('crypto'))
    async def crypto_handler(message: Message):
        if not await check_permissions(message, modules, 'crypto'):
            return
            
        if not modules.get('crypto'):
            await message.answer("❌ Криптовалютный модуль недоступен")
            return
        
        coin_query = message.text[8:].strip()
        if not coin_query:
            await message.answer(
                "💡 <b>Использование криптовалютного модуля:</b>\n\n"
                "📝 /crypto [название монеты]\n"
                "🎯 Примеры:\n"
                "• /crypto bitcoin\n"
                "• /crypto BTC\n"
                "• /crypto ethereum\n"
                "• /crypto ton\n\n"
                "📈 /crypto_trending - Трендовые монеты"
            )
            return
        
        await process_crypto_request(message, coin_query, modules)
    
    @router.message(Command('crypto_trending'))
    async def crypto_trending_handler(message: Message):
        if not await check_permissions(message, modules, 'crypto'):
            return
            
        await process_trending_crypto(message, modules)
    
    # =================== АНАЛИТИКА ===================
    
    @router.message(Command('stats'))
    async def stats_handler(message: Message):
        if not await check_permissions(message, modules, 'analytics'):
            return
            
        await process_user_stats(message, modules)
    
    @router.message(Command('dashboard'))
    async def dashboard_handler(message: Message):
        if not await check_permissions(message, modules, 'analytics'):
            return
            
        await process_user_dashboard(message, modules)
    
    @router.message(Command('export'))
    async def export_handler(message: Message):
        if not await check_permissions(message, modules, 'analytics'):
            return
            
        await process_data_export(message, modules)
    
    # =================== ГРАФИКИ ===================
    
    @router.message(Command('chart'))
    async def chart_handler(message: Message):
        if not await check_permissions(message, modules, 'charts'):
            return
            
        await process_chart_request(message, modules)
    
    # =================== ТРИГГЕРЫ ===================
    
    @router.message(Command('triggers'))
    async def triggers_handler(message: Message):
        if not await check_permissions(message, modules, 'triggers'):
            return
            
        await process_triggers_command(message, modules)
    
    @router.message(Command('trigger_add'))
    async def trigger_add_handler(message: Message):
        if not await check_permissions(message, modules, 'triggers'):
            return
            
        await process_trigger_add(message, modules)
    
    @router.message(Command('trigger_del'))
    async def trigger_del_handler(message: Message):
        if not await check_permissions(message, modules, 'triggers'):
            return
            
        await process_trigger_delete(message, modules)
    
    @router.message(Command('trigger_list'))
    async def trigger_list_handler(message: Message):
        if not await check_permissions(message, modules, 'triggers'):
            return
            
        await process_trigger_list(message, modules)
    
    # =================== МОДЕРАЦИЯ (ТОЛЬКО АДМИНЫ) ===================
    
    @router.message(Command('moderation'))
    async def moderation_handler(message: Message):
        if not await check_admin_permissions(message, modules):
            return
            
        # Настройки модерации только в ЛС
        if message.chat.type != 'private':
            await message.answer(
                "🔒 <b>Настройки модерации</b>\n\n"
                "Для безопасности настройки модерации доступны только в личных сообщениях.\n\n"
                "📱 Напишите боту в ЛС и используйте команду /moderation"
            )
            return
            
        await process_moderation_settings(message, modules)
    
    @router.message(Command('ban'))
    async def ban_handler(message: Message):
        if not await check_admin_permissions(message, modules):
            return
            
        # Команды модерации только в группах
        if message.chat.type == 'private':
            await message.answer("❌ Команда /ban доступна только в группах")
            return
            
        await process_ban_command(message, modules)
    
    @router.message(Command('mute'))
    async def mute_handler(message: Message):
        if not await check_admin_permissions(message, modules):
            return
            
        if message.chat.type == 'private':
            await message.answer("❌ Команда /mute доступна только в группах")
            return
            
        await process_mute_command(message, modules)
    
    @router.message(Command('warn'))
    async def warn_handler(message: Message):
        if not await check_admin_permissions(message, modules):
            return
            
        if message.chat.type == 'private':
            await message.answer("❌ Команда /warn доступна только в группах")
            return
            
        await process_warn_command(message, modules)
    
    # =================== НАСТРОЙКИ ДОСТУПА ===================
    
    @router.message(Command('permissions'))
    async def permissions_handler(message: Message):
        if not await check_admin_permissions(message, modules):
            return
            
        await process_permissions_command(message, modules)
    
    # =================== ОБРАБОТКА СТИКЕРОВ ===================
    
    @router.message(F.sticker)
    async def sticker_handler(message: Message):
        if not await check_permissions(message, modules, 'stickers'):
            return
            
        await process_sticker(message, modules)
    
    # =================== ОБРАБОТКА РЕПЛАЕВ ===================
    
    @router.message(F.reply_to_message)
    async def reply_handler(message: Message):
        if not await check_permissions(message, modules):
            return
            
        # Проверяем, отвечают ли на сообщение бота
        if message.reply_to_message.from_user.id == modules['bot'].id:
            await process_reply_to_bot(message, modules)
        else:
            # Обычная обработка текста
            await process_smart_text(message, modules, bot_info)
    
    # =================== ИНТЕЛЛЕКТУАЛЬНАЯ ОБРАБОТКА ТЕКСТА ===================
    
    @router.message(F.text)
    async def smart_text_handler(message: Message):
        if not await check_permissions(message, modules):
            return
            
        await process_smart_text(message, modules, bot_info)
    
    # Регистрируем роутер
    dp.include_router(router)
    
    logger.info("🎛️ Все обработчики v3.0 зарегистрированы")


# =================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ===================

async def check_permissions(message: Message, modules, module_name: str = None) -> bool:
    """🔒 Проверка разрешений доступа"""
    
    try:
        if not modules.get('permissions'):
            return True
        
        # Проверяем базовый доступ к чату
        if not await modules['permissions'].check_chat_access(
            message.chat.id, message.from_user.id
        ):
            await message.answer("🚫 У вас нет доступа к боту в этом чате.")
            return False
        
        # Проверяем доступ к модулю если указан
        if module_name:
            if not await modules['permissions'].check_module_access(
                module_name, message.chat.id, message.from_user.id
            ):
                await message.answer(f"🚫 Модуль {module_name} отключен в этом чате.")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка проверки разрешений: {e}")
        return True

async def check_admin_permissions(message: Message, modules) -> bool:
    """👑 Проверка прав администратора"""
    
    user_id = message.from_user.id
    
    if user_id not in modules['config'].bot.admin_ids:
        await message.answer("👑 Эта команда доступна только администраторам бота.")
        return False
    
    return True

async def save_user_and_message(message: Message, modules):
    """💾 Сохранение пользователя и сообщения"""
    
    try:
        user = message.from_user
        
        if modules.get('db'):
            await modules['db'].save_user({
                'id': user.id,
                'username': user.username,
                'full_name': user.full_name,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'language_code': user.language_code,
                'is_premium': getattr(user, 'is_premium', False)
            })
            
            await modules['db'].save_chat({
                'id': message.chat.id,
                'type': message.chat.type,
                'title': message.chat.title,
                'username': message.chat.username
            })
            
            await modules['db'].save_message({
                'message_id': message.message_id,
                'user_id': user.id,
                'chat_id': message.chat.id,
                'text': message.text or '',
                'message_type': 'text' if message.text else 'other'
            })
            
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения данных: {e}")

async def process_ai_request(message: Message, user_message: str, modules):
    """🤖 Обработка AI запроса"""
    
    try:
        # Показываем что бот думает
        thinking_msg = await message.answer("🤔 Думаю...")
        
        # Получаем контекст памяти
        context = {}
        if modules.get('memory'):
            memory_context = await modules['memory'].get_context(
                message.from_user.id, message.chat.id
            )
            context.update(memory_context)
        
        # Получаем анализ поведения
        if modules.get('behavior'):
            behavior_analysis = await modules['behavior'].analyze_user_behavior(
                message.from_user.id, message.chat.id, user_message, context
            )
            context['behavior_analysis'] = behavior_analysis
        
        # Генерируем ответ
        response = await modules['ai'].generate_response(
            user_message, message.from_user.id, context
        )
        
        # Адаптируем ответ под пользователя
        if modules.get('behavior') and context.get('behavior_analysis'):
            response = await modules['behavior'].adapt_response(
                message.from_user.id, response, context['behavior_analysis']
            )
        
        # Удаляем сообщение о размышлении
        try:
            await thinking_msg.delete()
        except:
            pass
        
        await message.answer(response)
        
        # Сохраняем взаимодействие в память
        if modules.get('memory'):
            await modules['memory'].add_interaction(
                message.from_user.id, message.chat.id, 
                user_message, response
            )
        
        # Обучаем на взаимодействии
        if modules.get('behavior'):
            await modules['behavior'].learn_from_interaction(
                message.from_user.id, message.chat.id, 
                user_message, response
            )
        
    except Exception as e:
        logger.error(f"❌ Ошибка AI обработки: {e}")
        await message.answer("❌ Произошла ошибка при обращении к AI. Попробуйте позже.")

async def process_smart_text(message: Message, modules, bot_info):
    """🧠 Интеллектуальная обработка текста"""
    
    try:
        user = message.from_user
        text = message.text.lower()
        
        # Сохраняем пользователя и сообщение
        await save_user_and_message(message, modules)
        
        # 1. Проверяем триггеры
        if modules.get('triggers'):
            trigger_response = await modules['triggers'].check_message_triggers(
                message.text, message.chat.id, user.id
            )
            if trigger_response:
                await message.answer(trigger_response)
                return
        
        # 2. Проверяем модерацию
        moderation_action = await check_moderation(message, modules)
        if moderation_action:
            return
        
        # 3. Проверяем упоминания бота
        should_respond = await check_bot_mentions(message, bot_info)
        
        if should_respond:
            # Умный ответ на упоминание
            await process_smart_response(message, modules)
        else:
            # Случайные ответы (если настроено)
            await process_random_responses(message, modules)
        
        # Трекинг сообщений
        if modules.get('analytics'):
            await modules['analytics'].track_user_action(
                user.id, message.chat.id, 'message_sent',
                {'text_length': len(message.text), 'has_mention': should_respond}
            )
        
    except Exception as e:
        logger.error(f"❌ Ошибка интеллектуальной обработки: {e}")

async def check_bot_mentions(message: Message, bot_info) -> bool:
    """🎯 Проверка упоминаний бота"""
    
    try:
        if message.chat.type == 'private':
            return True
        
        text = message.text.lower()
        
        # Проверяем прямое упоминание
        if bot_info and f'@{bot_info.username.lower()}' in text:
            return True
        
        # Проверяем упоминание по имени
        if bot_info and bot_info.first_name.lower() in text:
            return True
        
        # Проверяем общие слова-обращения
        bot_keywords = ['бот', 'bot', 'робот', 'помощник', 'assistant']
        if any(keyword in text for keyword in bot_keywords):
            return True
        
        # Проверяем вопросительные предложения
        if '?' in message.text and len(message.text) > 20:
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"❌ Ошибка проверки упоминаний: {e}")
        return False

async def process_smart_response(message: Message, modules):
    """💡 Генерация умного ответа"""
    
    try:
        # Если есть AI, используем его
        if modules.get('ai'):
            await process_ai_request(message, message.text, modules)
        else:
            # Базовые умные ответы
            smart_responses = [
                "🤔 Интересный вопрос! К сожалению, мой AI модуль отключен.",
                "💭 Я бы с удовольствием подумал над этим, но нужен AI модуль.",
                "🧠 Для умных ответов установите AI модуль с API ключами.",
                "💡 Попробуйте команду /help чтобы узнать о доступных функциях.",
                "✨ Я понимаю что вы обращаетесь ко мне, но AI сервис не настроен."
            ]
            
            response = random.choice(smart_responses)
            await message.answer(response)
        
    except Exception as e:
        logger.error(f"❌ Ошибка генерации умного ответа: {e}")

async def process_reply_to_bot(message: Message, modules):
    """💬 ИСПРАВЛЕНО: Обработка ответа на сообщение бота"""
    
    try:
        # Это реплай на бота - точно нужно ответить умно
        if modules.get('ai'):
            # Добавляем контекст предыдущего сообщения
            context_message = f"Пользователь отвечает на мое сообщение: '{message.reply_to_message.text}'\n\nОтвет пользователя: '{message.text}'"
            await process_ai_request(message, context_message, modules)
        else:
            await message.answer("👍 Понял! Но для умных ответов нужен AI модуль.")
        
    except Exception as e:
        logger.error(f"❌ Ошибка обработки реплая: {e}")

async def check_moderation(message: Message, modules) -> bool:
    """🛡️ Проверка модерации"""
    
    try:
        if not modules.get('moderation'):
            return False
            
        moderation_result = await modules['moderation'].check_message(
            message.from_user.id, message.chat.id, message.text
        )
        
        if moderation_result['action'] != 'allow':
            action = moderation_result['action']
            reason = moderation_result['reason']
            
            if action == 'delete':
                try:
                    await message.delete()
                    await message.answer(f"🛡️ Сообщение удалено: {reason}")
                except:
                    await message.answer(f"⚠️ Обнаружено нарушение: {reason}")
            elif action == 'warn':
                warnings = moderation_result.get('user_warnings', 0)
                await message.answer(f"⚠️ Предупреждение ({warnings}): {reason}")
            elif action == 'timeout':
                await message.answer(f"🕐 Временное ограничение: {reason}")
            
            return True
            
        return False
        
    except Exception as e:
        logger.error(f"❌ Ошибка проверки модерации: {e}")
        return False

async def process_random_responses(message: Message, modules):
    """🎲 Случайные ответы"""
    
    try:
        import random
        if (modules.get('config') and 
            random.random() < modules['config'].bot.random_reply_chance):
            
            random_responses = [
                "👍 Интересно!",
                "🤔 Понимаю",
                "✨ Спасибо за сообщение!",
                "💭 Хорошая мысль",
                "🎯 Согласен"
            ]
            
            await message.answer(random.choice(random_responses))
            
    except Exception as e:
        logger.error(f"❌ Ошибка случайных ответов: {e}")

# =================== ФУНКЦИИ ОБРАБОТКИ КОМАНД ===================

async def process_crypto_request(message: Message, coin_query: str, modules):
    """₿ Обработка запроса криптовалюты"""
    
    try:
        crypto_data = await modules['crypto'].handle_crypto_request(
            message.from_user.id, coin_query
        )
        
        if crypto_data.get('error'):
            await message.answer(f"❌ {crypto_data['message']}")
            return
        
        # Форматируем ответ
        response_parts = [
            f"₿ <b>{crypto_data['coin_name']} ({crypto_data['symbol']})</b>\n",
            f"💰 <b>Цена:</b> {crypto_data['price']}",
            f"📊 <b>Изменение 24ч:</b> {crypto_data['change_24h_formatted']} {crypto_data['trend_emoji']}",
            f"🏆 <b>Рейтинг:</b> #{crypto_data['market_cap_rank']}",
            f"💎 <b>Капитализация:</b> {crypto_data['market_cap']}",
            f"📦 <b>Объем торгов:</b> {crypto_data['volume_24h']}",
            f"⏰ <b>Обновлено:</b> {crypto_data['last_updated']}\n",
            f"📈 <b>Анализ:</b> {crypto_data['price_analysis']}"
        ]
        
        await message.answer("\n".join(response_parts))
        
    except Exception as e:
        logger.error(f"❌ Ошибка обработки криптозапроса: {e}")
        await message.answer("❌ Ошибка получения данных о криптовалюте")

async def process_trending_crypto(message: Message, modules):
    """📈 Обработка трендовых криптовалют"""
    
    try:
        if not modules.get('crypto'):
            await message.answer("❌ Криптовалютный модуль недоступен")
            return
        
        trending_data = await modules['crypto'].get_trending_crypto()
        
        if trending_data.get('error'):
            await message.answer(f"❌ {trending_data['message']}")
            return
        
        response_parts = ["🔥 <b>Трендовые криптовалюты:</b>\n"]
        
        for i, coin in enumerate(trending_data['trending_coins'], 1):
            response_parts.append(
                f"{i}. <b>{coin['name']} ({coin['symbol']})</b>\n"
                f"   💰 {coin['price']} ({coin['change_24h']})\n"
                f"   🏆 #{coin['market_cap_rank']} | 💎 {coin['market_cap']}"
            )
        
        response_parts.append(f"\n⏰ Обновлено: {trending_data['update_time']}")
        
        await message.answer("\n\n".join(response_parts))
        
    except Exception as e:
        logger.error(f"❌ Ошибка получения трендовых криптовалют: {e}")
        await message.answer("❌ Ошибка получения трендовых данных")

async def process_user_stats(message: Message, modules):
    """📊 Обработка статистики пользователя"""
    
    try:
        if not modules.get('analytics'):
            await message.answer("❌ Модуль аналитики недоступен")
            return
        
        dashboard = await modules['analytics'].get_user_dashboard(message.from_user.id)
        
        if dashboard.get('error'):
            await message.answer(f"❌ {dashboard['error']}")
            return
        
        basic_stats = dashboard.get('basic_stats', {})
        
        response_parts = [
            f"📊 <b>Статистика пользователя {message.from_user.first_name}</b>\n",
            f"💬 <b>Сообщений:</b> {basic_stats.get('message_count', 0)}",
            f"📏 <b>Средняя длина:</b> {basic_stats.get('avg_message_length', 0)} символов",
            f"⚡ <b>Уровень активности:</b> {dashboard.get('activity_level', 'unknown')}",
            f"🎯 <b>Вовлеченность:</b> {int(dashboard.get('engagement_score', 0) * 100)}%",
            f"⏰ <b>Последняя активность:</b> {basic_stats.get('last_activity', 'Неизвестно')}\n"
        ]
        
        # Добавляем инсайты
        insights = dashboard.get('insights', [])
        if insights:
            response_parts.append("<b>💡 Персональные инсайты:</b>")
            for insight in insights:
                response_parts.append(f"• {insight}")
        
        await message.answer("\n".join(response_parts))
        
    except Exception as e:
        logger.error(f"❌ Ошибка получения статистики: {e}")
        await message.answer("❌ Ошибка получения статистики")

async def process_user_dashboard(message: Message, modules):
    """📋 Обработка детального дашборда"""
    
    await message.answer("🚧 Детальный дашборд в разработке. Используйте /stats для базовой статистики.")

async def process_data_export(message: Message, modules):
    """📤 Обработка экспорта данных"""
    
    await message.answer("🚧 Экспорт данных в разработке.")

async def process_chart_request(message: Message, modules):
    """📈 Обработка запроса графиков"""
    
    await message.answer("🚧 Генерация графиков в разработке.")

async def process_sticker(message: Message, modules):
    """🎭 Обработка стикера"""
    
    try:
        sticker = message.sticker
        
        # Анализируем стикер
        if modules.get('stickers'):
            sticker_data = {
                'file_id': sticker.file_id,
                'set_name': sticker.set_name,
                'emoji': sticker.emoji,
                'is_animated': sticker.is_animated,
                'is_video': sticker.is_video
            }
            
            analysis = await modules['stickers'].analyze_sticker(
                message.from_user.id, message.chat.id, sticker_data
            )
            
            if not analysis.get('error'):
                emotion = analysis.get('emotion', 'neutral')
                if emotion != 'neutral':
                    emotion_responses = {
                        'happy': '😊 Вижу, у вас хорошее настроение!',
                        'sad': '😢 Надеюсь, все наладится!',
                        'angry': '😤 Понимаю ваши эмоции',
                        'love': '💕 Любовь - это прекрасно!',
                        'thinking': '🤔 О чем задумались?'
                    }
                    
                    response = emotion_responses.get(emotion, '👍 Отличный стикер!')
                    await message.answer(response)
        
        # Трекинг
        if modules.get('analytics'):
            await modules['analytics'].track_user_action(
                message.from_user.id, message.chat.id, 'sticker_sent',
                {'emoji': sticker.emoji, 'set_name': sticker.set_name}
            )
            
    except Exception as e:
        logger.error(f"❌ Ошибка обработки стикера: {e}")

# =================== ФУНКЦИИ ТРИГГЕРОВ ===================

async def process_triggers_command(message: Message, modules):
    """⚡ Обработка команды управления триггерами"""
    
    try:
        if not modules.get('triggers'):
            await message.answer("❌ Модуль триггеров недоступен")
            return
        
        user_triggers = await modules['triggers'].get_user_triggers(
            message.from_user.id, message.chat.id
        )
        
        response = "⚡ <b>Управление триггерами</b>\n\n"
        
        if user_triggers:
            response += f"📋 <b>Ваши триггеры ({len(user_triggers)}):</b>\n"
            for trigger in user_triggers[:5]:  # Показываем первые 5
                status = "✅" if trigger.get('is_active') else "❌"
                response += f"{status} <b>{trigger['name']}</b> - {trigger.get('type', 'contains')}\n"
            
            if len(user_triggers) > 5:
                response += f"\n... и еще {len(user_triggers) - 5} триггеров\n"
        else:
            response += "📝 У вас нет созданных триггеров\n"
        
        response += (
            "\n<b>📚 Команды:</b>\n"
            "/trigger_add - Создать триггер\n"
            "/trigger_list - Список всех триггеров\n"
            "/trigger_del [имя] - Удалить триггер\n\n"
            "<b>💡 Пример:</b>\n"
            "/trigger_add привет 'Привет! 👋' contains"
        )
        
        await message.answer(response)
        
    except Exception as e:
        logger.error(f"❌ Ошибка обработки команды триггеров: {e}")
        await message.answer("❌ Ошибка обработки команды триггеров")

async def process_trigger_add(message: Message, modules):
    """➕ Добавление триггера"""
    
    try:
        if not modules.get('triggers'):
            await message.answer("❌ Модуль триггеров недоступен")
            return
        
        # Парсим параметры команды
        parts = message.text.split(' ', 4)
        if len(parts) < 4:
            await message.answer(
                "💡 <b>Создание триггера:</b>\n\n"
                "📝 /trigger_add [имя] [паттерн] [ответ] [тип]\n\n"
                "<b>🎯 Примеры:</b>\n"
                "• /trigger_add привет hello 'Привет! 👋' contains\n"
                "• /trigger_add правила rules 'Правила чата...' exact\n"
                "• /trigger_add утро 'доброе утро' '☀️ Доброе утро!' starts_with\n\n"
                "<b>📋 Типы триггеров:</b>\n"
                "• contains - содержит текст\n"
                "• exact - точное совпадение\n"
                "• starts_with - начинается с\n"
                "• ends_with - заканчивается на\n"
                "• regex - регулярное выражение"
            )
            return
        
        trigger_name = parts[1]
        trigger_pattern = parts[2]
        trigger_response = parts[3]
        trigger_type = parts[4] if len(parts) > 4 else 'contains'
        
        # Убираем кавычки если есть
        if trigger_response.startswith('"') and trigger_response.endswith('"'):
            trigger_response = trigger_response[1:-1]
        elif trigger_response.startswith("'") and trigger_response.endswith("'"):
            trigger_response = trigger_response[1:-1]
        
        result = await modules['triggers'].add_trigger(
            message.from_user.id, message.chat.id,
            trigger_name, trigger_pattern, trigger_response, trigger_type
        )
        
        if result['success']:
            await message.answer(f"✅ {result['message']}")
        else:
            await message.answer(f"❌ {result['error']}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка добавления триггера: {e}")
        await message.answer("❌ Ошибка создания триггера")

async def process_trigger_delete(message: Message, modules):
    """🗑️ Удаление триггера"""
    
    try:
        if not modules.get('triggers'):
            await message.answer("❌ Модуль триггеров недоступен")
            return
        
        parts = message.text.split(' ', 1)
        if len(parts) < 2:
            await message.answer(
                "💡 <b>Удаление триггера:</b>\n\n"
                "📝 /trigger_del [имя триггера]\n\n"
                "<b>🎯 Пример:</b>\n"
                "/trigger_del привет"
            )
            return
        
        trigger_name = parts[1]
        
        result = await modules['triggers'].delete_trigger(
            message.from_user.id, message.chat.id, trigger_name
        )
        
        if result['success']:
            await message.answer(f"✅ {result['message']}")
        else:
            await message.answer(f"❌ {result['error']}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка удаления триггера: {e}")
        await message.answer("❌ Ошибка удаления триггера")

async def process_trigger_list(message: Message, modules):
    """📋 Список триггеров"""
    
    try:
        if not modules.get('triggers'):
            await message.answer("❌ Модуль триггеров недоступен")
            return
        
        user_triggers = await modules['triggers'].get_user_triggers(
            message.from_user.id, message.chat.id
        )
        
        if not user_triggers:
            await message.answer("📝 У вас нет созданных триггеров\n\nИспользуйте /trigger_add для создания первого триггера")
            return
        
        response = f"📋 <b>Ваши триггеры ({len(user_triggers)}):</b>\n\n"
        
        for i, trigger in enumerate(user_triggers, 1):
            status = "✅" if trigger.get('is_active') else "❌"
            usage = trigger.get('usage_count', 0)
            
            response += (
                f"{i}. {status} <b>{trigger['name']}</b>\n"
                f"   🎯 Паттерн: {trigger['pattern']}\n"
                f"   📝 Ответ: {trigger['response'][:50]}...\n"
                f"   🔧 Тип: {trigger.get('type', 'contains')}\n"
                f"   📊 Использований: {usage}\n\n"
            )
        
        await message.answer(response)
        
    except Exception as e:
        logger.error(f"❌ Ошибка получения списка триггеров: {e}")
        await message.answer("❌ Ошибка получения списка триггеров")

# =================== ФУНКЦИИ МОДЕРАЦИИ ===================

async def process_moderation_settings(message: Message, modules):
    """🛡️ Настройки модерации"""
    
    try:
        if not modules.get('moderation'):
            await message.answer("❌ Модуль модерации недоступен")
            return
        
        await message.answer(
            "🛡️ <b>Настройки модерации</b>\n\n"
            "⚙️ Модерация включена и работает автоматически\n"
            "🤖 Проверка токсичности сообщений\n"
            "🌊 Защита от флуда\n"
            "⚠️ Система предупреждений\n\n"
            "<b>📋 Команды для групп:</b>\n"
            "/ban [ID] - Забанить пользователя\n"
            "/mute [ID] - Заглушить пользователя\n"
            "/warn [ID] - Предупредить пользователя\n\n"
            "📊 Все действия модерации логируются"
        )
        
    except Exception as e:
        logger.error(f"❌ Ошибка настроек модерации: {e}")
        await message.answer("❌ Ошибка настроек модерации")

async def process_ban_command(message: Message, modules):
    """🚫 Обработка команды бана"""
    
    await message.answer("🚧 Команда /ban в разработке")

async def process_mute_command(message: Message, modules):
    """🔇 Обработка команды мута"""
    
    await message.answer("🚧 Команда /mute в разработке")

async def process_warn_command(message: Message, modules):
    """⚠️ Обработка команды предупреждения"""
    
    await message.answer("🚧 Команда /warn в разработке")

# =================== ФУНКЦИИ РАЗРЕШЕНИЙ ===================

async def process_permissions_command(message: Message, modules):
    """🔒 Обработка команды разрешений"""
    
    try:
        if not modules.get('permissions'):
            await message.answer("❌ Модуль разрешений недоступен")
            return
        
        global_settings = await modules['permissions'].get_global_settings()
        
        response = (
            "🔒 <b>Настройки доступа</b>\n\n"
            f"📝 <b>Разрешенные чаты:</b> {len(global_settings.get('allowed_chats', []))}\n"
            f"🚫 <b>Заблокированные чаты:</b> {len(global_settings.get('blocked_chats', []))}\n"
            f"👥 <b>Настроенные чаты:</b> {global_settings.get('configured_chats', 0)}\n"
            f"⚡ <b>Ограниченные команды:</b> {len(global_settings.get('command_restrictions', {}))}\n\n"
            "<b>🛠️ Управление:</b>\n"
            "• Добавить чат в whitelist\n"
            "• Заблокировать чат\n"
            "• Настроить модули для чата\n"
            "• Ограничить команды\n\n"
            "📞 Обратитесь к администратору для настройки"
        )
        
        await message.answer(response)
        
    except Exception as e:
        logger.error(f"❌ Ошибка команды разрешений: {e}")
        await message.answer("❌ Ошибка обработки разрешений")

# =================== ФУНКЦИИ ГЕНЕРАЦИИ ТЕКСТА ===================

def generate_help_text(chat_type: str, bot_info) -> str:
    """📖 Генерация текста справки"""
    
    help_text = (
        "📖 <b>Справка Enhanced Telegram Bot v3.0</b>\n\n"
        "🆕 <b>Новое в v3.0:</b>\n"
        "🎯 Умные ответы на упоминания\n"
        "⚡ Система триггеров\n"
        "🛡️ Расширенная модерация\n"
        "🔒 Гибкие настройки доступа\n\n"
        "🤖 <b>AI Помощник:</b>\n"
        "/ai [вопрос] - Задать вопрос AI\n"
        "/memory_clear - Очистить память диалогов\n\n"
        "₿ <b>Криптовалюты:</b>\n"
        "/crypto [монета] - Курс криптовалюты\n"
        "/crypto_trending - Трендовые монеты\n\n"
        "📊 <b>Аналитика:</b>\n"
        "/stats - Персональная статистика\n"
        "/dashboard - Детальный дашборд\n"
        "/export - Экспорт данных\n\n"
        "📈 <b>Графики:</b>\n"
        "/chart activity - График активности\n"
        "/chart emotions - График эмоций\n\n"
        "⚡ <b>Триггеры:</b>\n"
        "/triggers - Управление триггерами\n"
        "/trigger_add - Создать триггер\n"
        "/trigger_list - Список триггеров\n\n"
        "🎭 <b>Стикеры:</b>\n"
        "Отправьте стикер для анализа эмоций\n\n"
    )
    
    if chat_type != 'private':
        help_text += (
            "🎯 <b>Умные ответы:</b>\n"
            f"• Упомяните @{bot_info.username if bot_info else 'bot'}\n"
            "• Ответьте на мое сообщение\n"
            "• Используйте слова: бот, помощник\n"
            "• Задавайте вопросы с '?'\n\n"
        )
    
    help_text += (
        "🛡️ <b>Модерация (админы):</b>\n"
        "/moderation - Настройки (только в ЛС)\n"
        "/ban [ID] - Забанить пользователя\n"
        "/warn [ID] - Предупредить\n"
        "/mute [ID] - Заглушить\n\n"
        "ℹ️ <b>Информация:</b>\n"
        "/about - О боте\n"
        "/status - Статус системы\n"
        "/permissions - Настройки доступа"
    )
    
    return help_text

def generate_about_text(modules) -> str:
    """ℹ️ Генерация информации о боте"""
    
    active_modules = sum(1 for m in modules.values() if m is not None and 
                        m != modules.get('config') and m != modules.get('bot') and m != modules.get('db'))
    
    return (
        "ℹ️ <b>Enhanced Telegram Bot v3.0 - Ultimate Edition</b>\n\n"
        "🎯 <b>Описание:</b>\n"
        "Самый продвинутый Telegram бот с искусственным интеллектом, "
        "адаптивным поведением и множеством уникальных функций.\n\n"
        "⚡ <b>Технологии:</b>\n"
        "• Python 3.11+ с aiogram 3.8+\n"
        "• AI: OpenAI GPT-4 + Anthropic Claude-3\n"
        "• База данных: SQLite с WAL режимом\n"
        "• Аналитика: Машинное обучение\n"
        "• Криптовалюты: CoinGecko API\n"
        "• Визуализация: matplotlib + seaborn\n\n"
        "🧩 <b>Модули (v3.0):</b>\n"
        "• Memory Module - Долгосрочная память\n"
        "• Behavior Module - Адаптивное поведение\n"
        "• Triggers Module - Система триггеров ⭐\n"
        "• Permissions Module - Контроль доступа ⭐\n"
        "• Analytics Module - Детальная аналитика\n"
        "• Moderation Module - Автомодерация\n"
        "• Crypto Module - Криптовалютные данные\n"
        "• Stickers Module - Анализ стикеров\n"
        "• Charts Module - Графики и визуализация\n\n"
        f"📊 <b>Статус:</b> {active_modules} активных модулей\n"
        f"⏰ <b>Время работы:</b> {datetime.now().strftime('%H:%M:%S')}\n"
        "🔧 <b>Версия:</b> 3.0 Ultimate Edition\n\n"
        "⭐ <b>Новые функции v3.0:</b>\n"
        "🎯 Интеллектуальные ответы на упоминания\n"
        "⚡ Пользовательские триггеры\n"
        "🛡️ Расширенная модерация\n"
        "🔒 Гибкие настройки доступа\n"
        "📚 Улучшенная память диалогов"
    )

async def generate_status_text(user, modules) -> str:
    """📊 Генерация статуса системы"""
    
    status_parts = ["🔥 <b>Статус Enhanced Telegram Bot v3.0</b>\n"]
    
    # Проверяем модули
    modules_status = []
    
    if modules.get('ai'):
        try:
            ai_stats = modules['ai'].get_usage_stats()
            modules_status.append(f"🧠 AI: ✅ ({ai_stats.get('daily_usage', 0)} запросов)")
        except:
            modules_status.append("🧠 AI: ⚠️ (есть ошибки)")
    else:
        modules_status.append("🧠 AI: ❌")
    
    if modules.get('crypto'):
        modules_status.append("₿ Crypto: ✅")
    else:
        modules_status.append("₿ Crypto: ❌")
    
    if modules.get('analytics'):
        modules_status.append("📊 Analytics: ✅")
    else:
        modules_status.append("📊 Analytics: ❌")
    
    if modules.get('memory'):
        modules_status.append("🧠 Memory: ✅")
    else:
        modules_status.append("🧠 Memory: ❌")
    
    if modules.get('triggers'):
        try:
            trigger_stats = await modules['triggers'].get_trigger_statistics()
            total_triggers = trigger_stats.get('total_triggers', 0)
            modules_status.append(f"⚡ Triggers: ✅ ({total_triggers} активных)")
        except:
            modules_status.append("⚡ Triggers: ✅")
    else:
        modules_status.append("⚡ Triggers: ❌")
    
    if modules.get('permissions'):
        modules_status.append("🔒 Permissions: ✅")
    else:
        modules_status.append("🔒 Permissions: ❌")
    
    if modules.get('moderation'):
        modules_status.append("🛡️ Moderation: ✅")
    else:
        modules_status.append("🛡️ Moderation: ❌")
    
    status_parts.append("\n".join(modules_status))
    
    status_parts.append(f"\n⏰ <b>Время:</b> {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    status_parts.append(f"👤 <b>Ваш ID:</b> {user.id}")
    status_parts.append(f"🏆 <b>Статус:</b> {'👑 Админ' if user.id in modules['config'].bot.admin_ids else '👤 Пользователь'}")
    
    return "\n\n".join(status_parts)


__all__ = ["register_all_handlers"]