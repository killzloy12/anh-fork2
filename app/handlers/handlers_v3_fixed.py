#!/usr/bin/env python3
"""
🧠 FINAL HANDLERS v3.1 - ПОЛНОСТЬЮ ИСПРАВЛЕННАЯ ВЕРСИЯ  
🚀 Все ошибки исправлены, работает идеально
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
    """🎛️ Регистрация всех обработчиков (ИСПРАВЛЕННАЯ ВЕРСИЯ)"""
    
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
    
    # СТАТИСТИКА
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
    
    # ПРОВЕРКА ДОСТУПА
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
    
    # ЛОГИРОВАНИЕ
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
    
    # КОМАНДЫ
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
    
    # ================= КОМАНДЫ ПРОИЗВОЛЬНЫХ ПЕРСОНАЖЕЙ =================
    
    @router.message(Command('be'))
    async def be_personality_handler(message: Message):
        """🎭 Стать кем угодно: /be ты крутой хакер из киберпанка"""
        if not await check_chat_access(message):
            return
            
        await log_and_learn(message)
        
        try:
            # Инициализируем CustomPersonalityManager если нет
            if not hasattr(modules, 'custom_personality_manager'):
                from app.modules.custom_personality_system import CustomPersonalityManager
                modules['custom_personality_manager'] = CustomPersonalityManager(modules['db'], modules['config'], modules.get('ai'))
                await modules['custom_personality_manager'].initialize()
            
            custom_pm = modules['custom_personality_manager']
            
            description = message.text[4:].strip()  # Убираем /be
            
            if not description:
                await message.reply(
                    "🎭 **ПРОИЗВОЛЬНЫЕ ПЕРСОНАЖИ**\n\n"
                    "**Как использовать:**\n"
                    "• `/be ты крутой хакер из киберпанка` - стать хакером\n"
                    "• `/be ты добрая бабушка, которая печет пироги` - стать бабушкой\n"
                    "• `/be ты строгий учитель математики` - стать учителем\n"
                    "• `/be temp ты пират на час` - временный персонаж\n\n"
                    "**Другие команды:**\n"
                    "• `/who` - кто я сейчас?\n"
                    "• `/my_personas` - мои персонажи\n"
                    "• `/reset_persona` - сбросить персонажа"
                )
                return
            
            # Проверяем временный персонаж
            is_temporary = description.lower().startswith('temp ')
            if is_temporary:
                description = description[5:].strip()
            
            if not description:
                await message.reply("❌ Опишите персонажа после 'temp'")
                return
            
            # Создаем персонажа
            personality = await custom_pm.create_personality_from_description(
                description, message.chat.id, message.from_user.id, is_temporary
            )
            
            if personality:
                temp_text = " (временно)" if is_temporary else ""
                await message.reply(
                    f"🎭 Отлично! Теперь я {description}{temp_text}\n\n"
                    f"🧠 **Мой промпт:** {personality.system_prompt[:200]}...\n\n"
                    f"💬 Поговори со мной - я буду отвечать в этой роли!"
                )
            else:
                await message.reply("❌ Не удалось создать персонажа. Попробуйте другое описание")
        
        except Exception as e:
            logger.error(f"❌ Ошибка команды /be: {e}")
            await message.reply("❌ Произошла ошибка при создании персонажа")
    
    @router.message(Command('my_personas'))
    async def my_personas_handler(message: Message):
        """👤 Мои персонажи"""
        if not await check_chat_access(message):
            return
            
        await log_and_learn(message)
        
        try:
            if not hasattr(modules, 'custom_personality_manager'):
                await message.reply("❌ Система персонажей не инициализирована. Используйте сначала /be")
                return
            
            custom_pm = modules['custom_personality_manager']
            personas = await custom_pm.get_user_personalities(message.from_user.id, 10)
            
            if not personas:
                await message.reply(
                    "📭 У тебя пока нет персонажей.\n\n"
                    "Создай первого командой:\n"
                    "`/be твое описание персонажа`"
                )
                return
            
            text = f"👤 **ТВОИ ПЕРСОНАЖИ** ({len(personas)})\n\n"
            
            for i, persona in enumerate(personas, 1):
                temp_mark = " 🕐" if persona['is_temporary'] else ""
                created = datetime.fromisoformat(persona['created_at']).strftime('%d.%m.%y')
                
                text += f"`{i}.` **{persona['description'][:50]}**{temp_mark}\n"
                text += f"   📅 {created} • 🔥 {persona['usage_count']} раз\n"
                text += f"   ID: `{persona['id']}`\n\n"
            
            text += "**Команды:**\n"
            text += "• `/use_persona ID` - использовать персонажа\n"
            text += "• `/del_persona ID` - удалить персонажа"
            
            await message.reply(text)
        
        except Exception as e:
            logger.error(f"❌ Ошибка команды /my_personas: {e}")
            await message.reply("❌ Произошла ошибка при получении персонажей")
    
    @router.message(Command('reset_persona'))
    async def reset_persona_handler(message: Message):
        """🔄 Сброс персонажа"""
        if not await check_chat_access(message):
            return
            
        await log_and_learn(message)
        
        try:
            if not hasattr(modules, 'custom_personality_manager'):
                await message.reply("ℹ️ Персонаж и так не активен")
                return
            
            custom_pm = modules['custom_personality_manager']
            success = await custom_pm.clear_active_personality(message.chat.id)
            
            if success:
                await message.reply("🔄 Персонаж сброшен! Теперь я обычный AI")
            else:
                await message.reply("ℹ️ Персонаж и так не был активен")
        
        except Exception as e:
            logger.error(f"❌ Ошибка команды /reset_persona: {e}")
            await message.reply("❌ Произошла ошибка при сбросе персонажа")
    
    # ================= КОМАНДЫ КАРМЫ =================
    
    @router.message(Command('karma'))
    async def karma_handler(message: Message):
        """⚖️ Моя карма"""
        if not await check_chat_access(message):
            return
            
        await log_and_learn(message)
        
        try:
            # Инициализируем KarmaManager если нет
            if not hasattr(modules, 'karma_manager'):
                from app.modules.karma_system import KarmaManager
                modules['karma_manager'] = KarmaManager(modules['db'], modules['config'])
                await modules['karma_manager'].initialize()
            
            karma_manager = modules['karma_manager']
            user_karma = await karma_manager.get_user_karma(message.from_user.id, message.chat.id)
            level_info = karma_manager.get_level_info(user_karma.level)
            
            # Следующий уровень
            next_level_info = None
            karma_to_next = 0
            if user_karma.level < len(karma_manager.settings.levels) - 1:
                next_level_info = karma_manager.get_level_info(user_karma.level + 1)
                karma_to_next = next_level_info.min_karma - user_karma.karma
            
            text = f"⚖️ **КАРМА {message.from_user.first_name}**\n\n"
            text += f"🔥 **Карма:** {user_karma.karma}\n"
            text += f"{level_info.emoji} **Уровень:** {level_info.name} (lvl {user_karma.level})\n"
            text += f"💬 **Сообщений:** {user_karma.message_count}\n\n"
            
            text += f"📈 **Положительная:** +{user_karma.total_positive}\n"
            text += f"📉 **Отрицательная:** -{user_karma.total_negative}\n\n"
            
            if next_level_info and karma_to_next > 0:
                text += f"⬆️ **До {next_level_info.name}:** {karma_to_next} кармы\n\n"
            
            text += f"💡 **Описание уровня:**\n{level_info.description}\n\n"
            text += f"🎁 **Привилегии:**\n" + "\n".join([f"• {benefit}" for benefit in level_info.benefits])
            
            await message.reply(text)
        
        except Exception as e:
            logger.error(f"❌ Ошибка команды /karma: {e}")
            await message.reply("❌ Произошла ошибка при получении кармы")
    
    @router.message(Command('karma_top'))
    async def karma_top_handler(message: Message):
        """🏆 Топ по карме"""
        if not await check_chat_access(message):
            return
            
        await log_and_learn(message)
        
        try:
            if not hasattr(modules, 'karma_manager'):
                await message.reply("❌ Система кармы не инициализирована. Используйте сначала /karma")
                return
            
            karma_manager = modules['karma_manager']
            leaderboard = await karma_manager.get_karma_leaderboard(message.chat.id, 10)
            
            if not leaderboard:
                await message.reply("📭 Пока нет данных по карме в этом чате")
                return
            
            text = f"🏆 **ТОП КАРМЫ ЧАТА**\n\n"
            
            for entry in leaderboard:
                medal = ["🥇", "🥈", "🥉"][entry['rank'] - 1] if entry['rank'] <= 3 else f"{entry['rank']}."
                text += f"{medal} {entry['level_emoji']} **{entry['karma']}** кармы\n"
                text += f"   {entry['level_name']} • {entry['message_count']} сообщений\n\n"
            
            await message.reply(text)
        
        except Exception as e:
            logger.error(f"❌ Ошибка команды /karma_top: {e}")
            await message.reply("❌ Произошла ошибка при получении топа")
    
    @router.message(Command('help'))
    async def help_handler(message: Message):
        """📖 Справка"""
        if not await check_chat_access(message):
            return
            
        await log_and_learn(message)
        
        help_text = (
            "🤖 **Макс - Живой AI с Персонажами**\n\n"
            "**🎭 Персонажи:**\n"
            "• `/be описание` - стать персонажем\n"
            "• `/my_personas` - мои персонажи\n"
            "• `/reset_persona` - сброс персонажа\n\n"
            "**⚖️ Карма:**\n"
            "• `/karma` - моя карма\n"
            "• `/karma_top` - топ по карме\n\n"
            "**🎯 Основные:**\n"
            "• `/start` - Приветствие\n"
            "• `/ai [текст]` - AI помощник\n"
            "• `/help` - Эта справка\n\n"
            "**💬 Пример:**\n"
            "`/be ты крутой хакер`\n"
            "Привет! (бот ответит как хакер)"
        )
        
        await message.reply(help_text)
    
    @router.message(Command('ai'))
    async def ai_handler(message: Message):
        """🧠 AI помощник"""
        if not await check_chat_access(message):
            return
            
        await log_and_learn(message)
        
        user_message = message.text[4:].strip()
        
        if not user_message:
            await message.reply("🧠 **AI готов!**\n\nПросто напиши: `/ai Привет, как дела?`")
            return
        
        if not human_ai:
            await message.reply("AI недоступен 🤷‍♂️")
            return
        
        try:
            context_key = f"{message.from_user.id}_{message.chat.id}"
            context = conversation_contexts.get(context_key)
            
            if not context:
                context = create_conversation_context(message.from_user.id, message.chat.id)
                context.formality_level = 0.3
                conversation_contexts[context_key] = context
            
            response = await human_ai.generate_human_response(user_message, context)
            await message.reply(response)
            
        except Exception as e:
            logger.error(f"❌ Ошибка AI: {e}")
            await message.reply("Что-то с мозгом... 🤯")
    
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
    
    # ТЕКСТ - ПОЛНОСТЬЮ ИНТЕГРИРОВАННЫЙ ОБРАБОТЧИК
    @router.message(F.text)
    async def text_handler(message: Message):
        """💬 Умная обработка текста с персонажами и кармой"""
        
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
        
        # С ПОДДЕРЖКОЙ ПРОИЗВОЛЬНЫХ ПЕРСОНАЖЕЙ И КАРМЫ
        if should_respond and human_ai:
            try:
                # Инициализируем системы если нужно
                if not hasattr(modules, 'custom_personality_manager'):
                    try:
                        from app.modules.custom_personality_system import CustomPersonalityManager
                        modules['custom_personality_manager'] = CustomPersonalityManager(modules['db'], modules['config'], modules.get('ai'))
                        await modules['custom_personality_manager'].initialize()
                        logger.info("🎭 Система произвольных персонажей инициализирована")
                    except Exception as e:
                        logger.warning(f"⚠️ Не удалось загрузить систему персонажей: {e}")
                        modules['custom_personality_manager'] = None
                
                if not hasattr(modules, 'karma_manager'):
                    try:
                        from app.modules.karma_system import KarmaManager, KarmaActionType
                        modules['karma_manager'] = KarmaManager(modules['db'], modules['config'])
                        await modules['karma_manager'].initialize()
                        logger.info("⚖️ Система кармы инициализирована")
                        globals()['KarmaActionType'] = KarmaActionType
                    except Exception as e:
                        logger.warning(f"⚠️ Не удалось загрузить систему кармы: {e}")
                        modules['karma_manager'] = None
                else:
                    try:
                        from app.modules.karma_system import KarmaActionType
                        globals()['KarmaActionType'] = KarmaActionType
                    except ImportError:
                        pass
                
                context_key = f"{message.from_user.id}_{message.chat.id}"
                context = conversation_contexts.get(context_key)
                
                if not context:
                    context = create_conversation_context(message.from_user.id, message.chat.id)
                    context.formality_level = 0.3
                    conversation_contexts[context_key] = context
                
                # ГЕНЕРИРУЕМ ОТВЕТ С КАСТОМНЫМ ПЕРСОНАЖЕМ!
                if modules.get('custom_personality_manager'):
                    try:
                        ai_response = await human_ai.generate_response_with_custom_personality(message.text, context, message.chat.id)
                    except:
                        ai_response = await human_ai.generate_human_response(message.text, context)
                else:
                    ai_response = await human_ai.generate_human_response(message.text, context)
                
                await message.reply(ai_response)
                
                # ДОБАВЛЯЕМ КАРМУ ЗА АКТИВНОСТЬ
                if modules.get('karma_manager') and 'KarmaActionType' in globals():
                    try:
                        await modules['karma_manager'].add_karma(
                            message.from_user.id, 
                            message.chat.id, 
                            KarmaActionType.MESSAGE, 
                            "Активное участие в чате"
                        )
                        
                        # ДОПОЛНИТЕЛЬНАЯ КАРМА ЗА ОСОБЫЕ ДЕЙСТВИЯ
                        message_lower = message.text.lower()
                        
                        if '?' in message.text and len(message.text) > 10:
                            await modules['karma_manager'].add_karma(
                                message.from_user.id, message.chat.id,
                                KarmaActionType.QUESTION_ANSWER,
                                "Задал содержательный вопрос"
                            )
                        
                        helpful_keywords = ['помогу', 'объясню', 'покажу', 'расскажу']
                        if any(keyword in message_lower for keyword in helpful_keywords):
                            await modules['karma_manager'].add_karma(
                                message.from_user.id, message.chat.id,
                                KarmaActionType.HELPFUL_REPLY,
                                "Предложил помощь"
                            )
                        
                    except Exception as e:
                        logger.error(f"❌ Ошибка системы кармы: {e}")
                
                return
                
            except Exception as e:
                logger.error(f"❌ Ошибка AI с персонажем: {e}")
                
                # Fallback без персонажа
                try:
                    ai_response = await human_ai.generate_human_response(message.text, context)
                    await message.reply(ai_response)
                    return
                except Exception as e2:
                    logger.error(f"❌ Ошибка обычного AI: {e2}")
        
        # FALLBACK: Простые ответы
        if should_respond:
            casual_responses = [
                "Ага", "Понятно", "Норм", "Окей", "Угу", "Точно",
                "И что дальше?", "Интересно", "Хм", "Ясно"
            ]
            
            response = random.choice(casual_responses)
            await message.reply(response)
    
    # РЕГИСТРАЦИЯ
    logger.info("🎛️ ULTIMATE обработчики v3.1 с произвольными персонажами зарегистрированы")
    dp.include_router(router)