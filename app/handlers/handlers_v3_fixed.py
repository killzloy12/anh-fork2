#!/usr/bin/env python3
"""
🧠 HANDLERS v3.2 - ВСТРОЕННАЯ СИСТЕМА ПЕРСОНАЖЕЙ
🚀 Система персонажей встроена прямо в обработчики
"""

import logging
import asyncio
import random
import re
from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import Message, Sticker
from aiogram.filters import CommandStart, Command
from aiogram.exceptions import TelegramBadRequest

logger = logging.getLogger(__name__)

# AI МОДУЛИ
human_ai = None
memory_module = None
advanced_triggers = None
media_triggers = None

try:
    from app.services.human_ai_service import HumanLikeAI, create_conversation_context
    AI_AVAILABLE = True
    logger.info("✅ Human-like AI импортирован")
except ImportError as e:
    logger.warning(f"⚠️ Human AI недоступен: {e}")
    AI_AVAILABLE = False

try:
    from app.modules.conversation_memory import ConversationMemoryModule
    MEMORY_AVAILABLE = True
    logger.info("✅ Память диалогов импортирована")
except ImportError as e:
    logger.warning(f"⚠️ Память недоступна: {e}")
    MEMORY_AVAILABLE = False

try:
    from app.modules.advanced_triggers import AdvancedTriggersModule
    TRIGGERS_AVAILABLE = True
    logger.info("✅ Расширенные триггеры импортированы")
except ImportError as e:
    logger.warning(f"⚠️ Триггеры недоступны: {e}")
    TRIGGERS_AVAILABLE = False

try:
    from app.modules.media_triggers import MediaTriggersModule
    MEDIA_AVAILABLE = True
    logger.info("✅ Медиа триггеры импортированы")
except ImportError as e:
    logger.warning(f"⚠️ Медиа триггеры недоступны: {e}")
    MEDIA_AVAILABLE = False

# ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ
last_activity_time = {}
conversation_contexts = {}
bot_trigger_words = ["бот", "bot", "робот", "помощник", "assistant", "эй", "слушай", "макс"]
chat_stats = {}
user_stats = {}


def register_all_handlers(dp, modules):
    """🎛️ ИСПРАВЛЕННАЯ регистрация всех обработчиков v3.2"""
    
    global human_ai, memory_module, advanced_triggers, media_triggers
    
    router = Router()
    bot_info = None
    
    async def get_bot_info():
        nonlocal bot_info
        try:
            bot_info = await modules['bot'].get_me()
            logger.info(f"🤖 Бот: @{bot_info.username} ({bot_info.first_name})")
        except Exception as e:
            logger.error(f"❌ Ошибка получения информации о боте: {e}")
    
    async def initialize_ai_modules():
        """🚀 Инициализация AI модулей"""
        global human_ai, memory_module, advanced_triggers, media_triggers
        
        try:
            if AI_AVAILABLE and modules.get('ai'):
                human_ai = HumanLikeAI(modules['config'])
                logger.info("🧠 Ultimate Human-like AI инициализирован (живой стиль)")
            
            if MEMORY_AVAILABLE and modules.get('db'):
                memory_module = ConversationMemoryModule(modules['db'])
                await memory_module.initialize()
                logger.info("💭 Ultimate память диалогов инициализирована")
            
            if TRIGGERS_AVAILABLE and modules.get('db'):
                advanced_triggers = AdvancedTriggersModule(modules['db'], modules['config'], modules.get('ai'))
                await advanced_triggers.initialize()
                logger.info("⚡ Ultimate расширенные триггеры инициализированы")
            
            if MEDIA_AVAILABLE and modules.get('db') and modules.get('bot'):
                media_triggers = MediaTriggersModule(modules['db'], modules['config'], modules['bot'])
                await media_triggers.initialize()
                logger.info("🎭 Ultimate медиа триггеры инициализированы")
                
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации AI модулей: {e}")
    
    asyncio.create_task(get_bot_info())
    asyncio.create_task(initialize_ai_modules())
    
    # СЛУЖЕБНЫЕ ФУНКЦИИ
    async def update_stats(message: Message):
        """📊 Обновление статистики"""
        try:
            chat_id = message.chat.id
            user_id = message.from_user.id
            now = datetime.now()
            
            # Статистика чата
            if chat_id not in chat_stats:
                chat_stats[chat_id] = {
                    'messages_count': 0,
                    'unique_users': set(),
                    'first_message': now,
                    'last_activity': now,
                    'chat_type': message.chat.type,
                    'chat_title': message.chat.title or message.chat.first_name or 'Личные сообщения'
                }
            
            chat_stats[chat_id]['messages_count'] += 1
            chat_stats[chat_id]['unique_users'].add(user_id)
            chat_stats[chat_id]['last_activity'] = now
            
            # Статистика пользователя
            if user_id not in user_stats:
                user_stats[user_id] = {
                    'messages_count': 0,
                    'first_seen': now,
                    'last_seen': now,
                    'name': message.from_user.first_name or 'Аноним',
                    'username': message.from_user.username,
                    'chats': set()
                }
            
            user_stats[user_id]['messages_count'] += 1
            user_stats[user_id]['last_seen'] = now
            user_stats[user_id]['chats'].add(chat_id)
            
        except Exception as e:
            logger.error(f"❌ Ошибка обновления статистики: {e}")
    
    async def check_chat_access(message: Message) -> bool:
        """🔒 Проверка доступа к чату"""
        config = modules['config']
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        if user_id in config.bot.admin_ids:
            return True
            
        if not config.bot.allowed_chat_ids:
            return True
            
        if chat_id not in config.bot.allowed_chat_ids:
            return False
            
        return True
    
    async def log_and_learn(message: Message):
        """📝 Логирование"""
        try:
            await update_stats(message)
            
            if modules.get('db'):
                await modules['db'].log_message(
                    chat_id=message.chat.id,
                    user_id=message.from_user.id,
                    username=message.from_user.username or '',
                    full_name=message.from_user.full_name or '',
                    text=message.text or '',
                    message_type='text',
                    timestamp=datetime.now()
                )
            
            if memory_module:
                await memory_module.update_user_interaction(
                    message.from_user.id,
                    message.text or '',
                    "general",
                    "neutral"
                )
                
        except Exception as e:
            logger.error(f"❌ Ultimate: Ошибка логирования: {e}")
    
    # =========================== ВСТРОЕННЫЕ КОМАНДЫ ПЕРСОНАЖЕЙ v3.2 ===========================
    
    @router.message(Command('be'))
    async def cmd_be_personality(message: Message):
        """🎭 Команда /be - установка персонажа (v3.2: только группы и админы)"""
        
        if not await check_chat_access(message):
            return
            
        await log_and_learn(message)
        
        try:
            personality_manager = modules.get('custom_personality_manager')
            
            if not personality_manager:
                await message.reply("❌ Система персонажей не инициализирована")
                return
            
            # Проверяем может ли пользователь использовать персонажи
            can_use, access_reason = await personality_manager.can_use_personalities(
                message.from_user.id, message.chat.id
            )
            
            if not can_use:
                # Разные сообщения для групп и ЛС
                if message.chat.id < 0:  # Группа
                    await message.reply(
                        f"🚫 Доступ запрещен\n\n"
                        f"{access_reason}\n\n"
                        f"👑 Только админы бота могут:\n"
                        f"• Устанавливать персонажи в группах\n"
                        f"• Управлять поведением бота\n"
                        f"• Сбрасывать персонажи"
                    )
                else:  # Личный чат
                    await message.reply(
                        "🚫 Система персонажей недоступна\n\n"
                        "📍 Персонажи работают только в групповых чатах\n\n"
                        "🔄 Что делать:\n"
                        "1. Добавьте бота в групповой чат\n"
                        "2. Попросите админа бота установить персонажа\n"
                        "3. Наслаждайтесь общением с персонажем!\n\n"
                        "💡 Зачем так: Персонажи созданы для развлечения участников групп"
                    )
                return
            
            # Получаем описание персонажа
            command_args = message.text.split(' ', 1)
            if len(command_args) < 2:
                chat_type = "группе" if message.chat.id < 0 else "тестовом режиме"
                
                await message.reply(
                    f"🎭 Команда /be - стать персонажем\n\n"
                    f"Использование:\n"
                    f"`/be описание персонажа`\n\n"
                    f"Пример:\n"
                    f"`/be ты крутой хакер из киберпанка, говоришь сленгом`\n\n"
                    f"Действие: В {chat_type} бот будет отвечать как этот персонаж\n\n"
                    f"📏 Ограничения:\n"
                    f"• Описание: 5-500 символов\n"
                    f"• Только админы бота\n"
                    f"• Работает в группах"
                )
                return
            
            description = command_args[1].strip()
            
            # Устанавливаем персонажа через систему v3.2
            success, result_message = await personality_manager.set_personality(
                message.from_user.id, message.chat.id, description
            )
            
            if success:
                result_message += f"\n\n👑 Установил: {message.from_user.first_name}"
                
                if message.chat.id < 0:  # Группа
                    result_message += f"\n🌍 Охват: Все участники группы"
                else:  # ЛС админа
                    result_message += f"\n🧪 Режим: Тестирование для админа"
                
                await message.reply(result_message)
            else:
                await message.reply(result_message)
                
        except Exception as e:
            logger.error(f"❌ Ошибка команды /be: {e}")
            await message.reply("❌ Произошла ошибка при установке персонажа")
    
    @router.message(Command('reset_persona'))
    async def cmd_reset_persona(message: Message):
        """🔄 Команда /reset_persona - сброс персонажа (v3.2)"""
        
        if not await check_chat_access(message):
            return
            
        await log_and_learn(message)
        
        try:
            personality_manager = modules.get('custom_personality_manager')
            
            if not personality_manager:
                await message.reply("❌ Система персонажей не инициализирована")
                return
            
            # Проверяем права доступа
            can_use, access_reason = await personality_manager.can_use_personalities(
                message.from_user.id, message.chat.id
            )
            
            if not can_use:
                if message.chat.id < 0:  # Группа
                    await message.reply(
                        f"🚫 Доступ запрещен\n\n"
                        f"{access_reason}\n\n"
                        f"👑 Только админы бота могут:\n"
                        f"• Устанавливать персонажи в группах\n"
                        f"• Управлять поведением бота\n"
                        f"• Сбрасывать персонажи"
                    )
                else:  # Личный чат
                    await message.reply(
                        f"🚫 Система персонажей недоступна\n\n"
                        f"📍 Персонажи работают только в групповых чатах"
                    )
                return
            
            # Проверяем есть ли активный персонаж
            active_personality = await personality_manager.get_active_personality(message.chat.id)
            
            if not active_personality:
                chat_location = "группе" if message.chat.id < 0 else "чате"
                await message.reply(
                    f"🤷‍♂️ Персонаж не установлен\n\n"
                    f"В этом {chat_location} нет активного персонажа"
                )
                return
            
            # Сбрасываем персонажа
            success, result_message = await personality_manager.reset_personality(
                message.from_user.id, message.chat.id
            )
            
            if success:
                result_message += f"\n\n👑 Сбросил: {message.from_user.first_name}"
                await message.reply(result_message)
            else:
                await message.reply(result_message)
                
        except Exception as e:
            logger.error(f"❌ Ошибка команды /reset_persona: {e}")
            await message.reply("❌ Произошла ошибка при сбросе персонажа")
    
    @router.message(Command('current_persona'))
    async def cmd_current_persona(message: Message):
        """🎭 Команда /current_persona - информация о текущем персонаже"""
        
        if not await check_chat_access(message):
            return
            
        await log_and_learn(message)
        
        try:
            personality_manager = modules.get('custom_personality_manager')
            
            if not personality_manager:
                await message.reply("❌ Система персонажей не инициализирована")
                return
            
            # Получаем активный персонаж
            active_personality = await personality_manager.get_active_personality(message.chat.id)
            
            if not active_personality:
                if message.chat.id > 0 and message.from_user.id not in modules['config'].bot.admin_ids:
                    # Обычный пользователь в ЛС
                    await message.reply(
                        f"📍 Персонажи работают только в групповых чатах\n\n"
                        f"🔄 Добавьте бота в группу и попросите админа установить персонажа!"
                    )
                else:
                    # Админ или группа без персонажа
                    chat_location = "группе" if message.chat.id < 0 else "чате"
                    await message.reply(
                        f"🤷‍♂️ Персонаж не установлен\n\n"
                        f"В этом {chat_location} нет активного персонажа"
                    )
                return
            
            # Показываем информацию о персонаже
            response = f"🎭 Активный персонаж\n\n"
            response += f"Имя: {active_personality['name']}\n"
            response += f"Описание: {active_personality['description']}\n\n"
            
            if message.chat.id < 0:  # Группа
                response += f"🌍 Тип: Групповой персонаж\n"
                response += f"🎯 Охват: Все участники группы"
            else:  # ЛС админа
                response += f"🧪 Тип: Тестовый режим\n"
                response += f"🎯 Охват: Только этот чат"
            
            await message.reply(response)
            
        except Exception as e:
            logger.error(f"❌ Ошибка команды /current_persona: {e}")
            await message.reply("❌ Произошла ошибка при получении информации о персонаже")
    
    # =========================== ОСТАЛЬНЫЕ КОМАНДЫ ===========================
    
    @router.message(CommandStart())
    async def start_handler(message: Message):
        """🚀 Команда /start"""
        if not await check_chat_access(message):
            return
            
        await log_and_learn(message)
        
        user_name = message.from_user.first_name or "друг"
        
        casual_greetings = [
            f"Йо, {user_name}! 👋 Че как?",
            f"Дарова, {user_name}! 😄 Что нового?", 
            f"Привет, {user_name}! Рад видеть 👍",
            f"Хай, {user_name}! Как дела? 😊",
            f"Салют, {user_name}! Что происходит?"
        ]
        
        greeting = random.choice(casual_greetings)
        await message.reply(greeting)
        
        logger.info(f"✅ Ultimate /start: {message.from_user.id}")
    
    @router.message(Command('karma'))
    async def karma_handler(message: Message):
        """⚖️ Моя карма"""
        if not await check_chat_access(message):
            return
            
        await log_and_learn(message)
        
        try:
            karma_manager = modules.get('karma_manager')
            
            if not karma_manager:
                await message.reply("❌ Система кармы не инициализирована")
                return
            
            user_karma = await karma_manager.get_user_karma(message.from_user.id, message.chat.id)
            level_info = karma_manager.get_level_info(user_karma.level)
            
            text = f"⚖️ КАРМА {message.from_user.first_name}\n\n"
            text += f"🔥 Карма: {user_karma.karma}\n"
            text += f"{level_info.emoji} Уровень: {level_info.name} (lvl {user_karma.level})\n"
            text += f"💬 Сообщений: {user_karma.message_count}\n\n"
            
            await message.reply(text)
        
        except Exception as e:
            logger.error(f"❌ Ошибка команды /karma: {e}")
            await message.reply("❌ Произошла ошибка при получении кармы")
    
    @router.message(Command('help'))
    async def help_handler(message: Message):
        """📖 Справка v3.2"""
        if not await check_chat_access(message):
            return
            
        await log_and_learn(message)
        
        is_admin = message.from_user.id in modules['config'].bot.admin_ids
        is_group = message.chat.id < 0
        
        if is_admin:
            help_text = (
                "🤖 Макс - AI с Персонажами v3.2\n\n"
                "🎭 Персонажи (Админ):\n"
                "• `/be описание` - установить персонажа\n"
                "• `/reset_persona` - сбросить персонажа\n"
                "• `/current_persona` - текущий персонаж\n\n"
                "⚖️ Карма:\n"
                "• `/karma` - моя карма\n\n"
                "🎯 Основные:\n"
                "• `/start` - Приветствие\n"
                "• `/help` - Эта справка\n\n"
                "💡 v3.2: Персонажи только в группах, управление - только админы"
            )
        elif is_group:
            help_text = (
                "🤖 Макс - AI с Персонажами\n\n"
                "🎭 Персонажи:\n"
                "• Только админы могут устанавливать\n"
                "• `/current_persona` - текущий персонаж\n\n"
                "⚖️ Карма:\n"
                "• `/karma` - моя карма\n\n"
                "🎯 Основные:\n"
                "• `/start` - Приветствие\n"
                "• `/help` - Эта справка"
            )
        else:
            help_text = (
                "🤖 Макс - AI Бот\n\n"
                "📍 Персонажи работают только в группах\n\n"
                "🔄 Что делать:\n"
                "1. Добавьте бота в групповой чат\n"
                "2. Попросите админа установить персонажа\n"
                "3. Наслаждайтесь общением!\n\n"
                "⚖️ Карма:\n"
                "• `/karma` - моя карма\n\n"
                "🎯 Основные:\n"
                "• `/start` - Приветствие"
            )
        
        await message.reply(help_text)
    
    # ТЕКСТ - ОБРАБОТЧИК С ПЕРСОНАЖАМИ v3.2
    @router.message(F.text)
    async def text_handler(message: Message):
        """💬 Умная обработка текста с персонажами v3.2"""
        
        await log_and_learn(message)
        
        if not await check_chat_access(message):
            return
        
        if message.text.startswith('/'):
            return
            
        text_lower = message.text.lower()
        should_respond = False
        
        # Проверка нужно ли отвечать
        if message.reply_to_message and message.reply_to_message.from_user.id == modules['bot'].id:
            should_respond = True
        elif any(word in text_lower for word in bot_trigger_words):
            should_respond = True
        elif bot_info and f'@{bot_info.username.lower()}' in text_lower:
            should_respond = True
        elif message.chat.type == 'private':
            should_respond = True
        
        # ИНТЕГРАЦИЯ С ПЕРСОНАЖАМИ v3.2
        if should_respond:
            try:
                personality_manager = modules.get('custom_personality_manager')
                
                if personality_manager:
                    # Проверяем есть ли активный персонаж
                    personality = await personality_manager.get_active_personality(message.chat.id)
                    
                    if personality:
                        # ОТВЕЧАЕМ В РОЛИ ПЕРСОНАЖА
                        if modules.get('ai'):
                            try:
                                ai_service = modules['ai']
                                
                                response = await ai_service.generate_response(
                                    f"Отвечай как персонаж: {personality['system_prompt']}\n\nВопрос: {message.text}",
                                    user_id=message.from_user.id,
                                    context={'personality': personality['name']}
                                )
                                
                                if response:
                                    # Индикатор персонажа
                                    persona_response = f"🎭 {personality['name']}: {response}"
                                    await message.reply(persona_response)
                                    
                                    logger.info(f"🎭 Ответ персонажа: {personality['name']} в чате {message.chat.id}")
                                    return
                                    
                            except Exception as e:
                                logger.error(f"❌ Ошибка генерации ответа персонажа: {e}")
                
                # ОБЫЧНЫЙ AI ОТВЕТ (если нет персонажа)
                if modules.get('ai'):
                    try:
                        ai_service = modules['ai']
                        
                        response = await ai_service.generate_response(
                            message.text,
                            user_id=message.from_user.id
                        )

                        if response:
                            await message.reply(f"🤖 {response}")
                            return
                            
                    except Exception as e:
                        logger.error(f"❌ Ошибка AI ответа: {e}")
                
                # FALLBACK: Простые ответы
                casual_responses = [
                    "Ага", "Понятно", "Норм", "Окей", "Угу", "Точно",
                    "И что дальше?", "Интересно", "Хм", "Ясно"
                ]
                
                response = random.choice(casual_responses)
                await message.reply(response)
                
            except Exception as e:
                logger.error(f"❌ Ошибка обработки текста: {e}")
    
    # СТИКЕРЫ
    @router.message(F.sticker)
    async def sticker_handler(message: Message):
        """🎭 Стикеры"""
        if not await check_chat_access(message):
            return
        
        await log_and_learn(message)
        
        if random.random() < 0.15:
            reactions = ["👍", "😄", "🤷‍♂️", "Норм!", "Ок"]
            await message.reply(random.choice(reactions))
    
    # РЕГИСТРАЦИЯ ROUTER
    dp.include_router(router)
    logger.info("🎛️ Все обработчики v3.2 зарегистрированы (встроенные персонажи)")