#!/usr/bin/env python3
"""
🧠 UPDATED HANDLERS v3.0 - ИНТЕГРАЦИЯ ЧЕЛОВЕКОПОДОБНОГО AI И МЕДИА
🚀 Обновленные обработчики с интеграцией всех новых модулей

ИНТЕГРИРОВАННЫЕ МОДУЛИ:
• Human-like AI для максимально естественного общения
• Долгосрочная память диалогов
• Расширенные триггеры с AI-анализом намерений
• Мультимедийные триггеры (стикеры, GIF, аудио)
• Эмоциональный анализ и адаптация
• Контекстные ответы на любые темы
"""

import logging
import asyncio
import random
from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import Message, Sticker
from aiogram.filters import CommandStart, Command
from aiogram.exceptions import TelegramBadRequest

# Импорты новых модулей
from human_ai_service import HumanLikeAI, create_conversation_context
from conversation_memory import ConversationMemoryModule
from advanced_triggers import AdvancedTriggersModule
from media_triggers import MediaTriggersModule

logger = logging.getLogger(__name__)

# Глобальные переменные для управления активностью
last_activity_time = {}
conversation_contexts = {}
bot_trigger_words = ["бот", "bot", "робот", "помощник", "assistant", "эй", "слушай", "макс"]


def register_all_handlers(dp, modules):
    """🎛️ Регистрация ВСЕХ обработчиков с новыми AI модулями"""
    
    router = Router()
    
    # Инициализация новых модулей
    human_ai = None
    memory_module = None
    advanced_triggers = None
    media_triggers = None
    
    # Получаем информацию о боте для упоминаний
    bot_info = None
    
    async def get_bot_info():
        nonlocal bot_info
        try:
            bot_info = await modules['bot'].get_me()
            logger.info(f"🤖 Бот: @{bot_info.username} ({bot_info.first_name})")
        except Exception as e:
            logger.error(f"❌ Не удалось получить информацию о боте: {e}")
    
    async def initialize_ai_modules():
        """🚀 Инициализация AI модулей"""
        nonlocal human_ai, memory_module, advanced_triggers, media_triggers
        
        try:
            # Human-like AI
            if modules.get('ai'):
                human_ai = HumanLikeAI(modules['config'])
                logger.info("🧠 Human-like AI инициализирован")
            
            # Память диалогов
            if modules.get('db'):
                memory_module = ConversationMemoryModule(modules['db'])
                await memory_module.initialize()
                logger.info("💭 Модуль памяти диалогов инициализирован")
            
            # Расширенные триггеры
            if modules.get('db'):
                advanced_triggers = AdvancedTriggersModule(
                    modules['db'], 
                    modules['config'], 
                    modules.get('ai')
                )
                await advanced_triggers.initialize()
                logger.info("⚡ Модуль расширенных триггеров инициализирован")
            
            # Медиа триггеры
            if modules.get('db') and modules.get('bot'):
                media_triggers = MediaTriggersModule(
                    modules['db'],
                    modules['config'],
                    modules['bot']
                )
                await media_triggers.initialize()
                logger.info("🎭 Модуль медиа триггеров инициализирован")
                
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации AI модулей: {e}")
    
    asyncio.create_task(get_bot_info())
    asyncio.create_task(initialize_ai_modules())
    
    # ================= ФИЛЬТР ДОСТУПА К ЧАТАМ =================
    
    async def check_chat_access(message: Message) -> bool:
        """🔒 Проверка доступа к чату"""
        config = modules['config']
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        # Админы имеют доступ везде
        if user_id in config.bot.admin_ids:
            return True
            
        # Если список разрешенных чатов пуст - разрешаем все
        if not config.bot.allowed_chat_ids:
            return True
            
        # Проверяем, есть ли чат в списке разрешенных
        if chat_id not in config.bot.allowed_chat_ids:
            logger.info(f"🚫 Доступ запрещен: чат {chat_id} не в списке разрешенных")
            return False
            
        return True
    
    # ================= ЛОГИРОВАНИЕ И ОБУЧЕНИЕ =================
    
    async def log_and_learn(message: Message):
        """📝 Логирование и обучение на сообщениях"""
        try:
            # Логируем в БД
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
            
            # Обновляем память пользователя
            if memory_module:
                await memory_module.update_user_interaction(
                    message.from_user.id,
                    message.text or '',
                    "general",  # Тема будет определена позже
                    "neutral"   # Эмоция будет определена позже
                )
            
            # Извлекаем факты о пользователе
            if memory_module and message.text:
                facts = await memory_module.extract_facts_from_message(
                    message.from_user.id, 
                    message.text
                )
                for fact in facts:
                    await memory_module.add_personal_fact(
                        fact.user_id, 
                        fact.category, 
                        fact.fact, 
                        fact.confidence
                    )
                        
        except Exception as e:
            logger.error(f"❌ Ошибка логирования: {e}")
    
    # ================= ОСНОВНЫЕ КОМАНДЫ =================
    
    @router.message(CommandStart())
    async def start_handler(message: Message):
        """🚀 Команда /start с AI приветствием"""
        if not await check_chat_access(message):
            return
            
        await log_and_learn(message)
        
        user = message.from_user
        user_name = user.first_name or "друг"
        
        # Создаем контекст разговора
        context = create_conversation_context(user.id, message.chat.id)
        
        # Получаем память о пользователе
        if memory_module:
            user_context = await memory_module.get_user_context(user.id, message.chat.id)
            context.last_messages = user_context.get('memories', [])
            
            # Обновляем уровень отношений
            profile = user_context.get('profile', {})
            context.relationship_level = profile.get('relationship_level', 'stranger')
        
        # Генерируем персонализированное приветствие
        if human_ai:
            greeting_prompt = f"Пользователь {user_name} запустил команду /start. Поприветствуй его тепло и дружелюбно, представься как Макс. Учитывай уровень знакомства: {context.relationship_level}"
            
            try:
                greeting = await human_ai.generate_human_response(greeting_prompt, context)
            except Exception as e:
                logger.error(f"❌ Ошибка AI приветствия: {e}")
                greeting = f"Привет, {user_name}! 👋 Я Макс, твой AI-помощник. Готов болтать на любые темы!"
        else:
            greeting = f"Привет, {user_name}! 👋 Я Макс, готов к общению!"
        
        await message.reply(greeting)
        
        # Сохраняем контекст
        conversation_contexts[f"{user.id}_{message.chat.id}"] = context
        
        logger.info(f"✅ /start: {user.id} в чате {message.chat.id}")
    
    @router.message(Command('help'))
    async def help_handler(message: Message):
        """📖 Справка с AI объяснением"""
        if not await check_chat_access(message):
            return
            
        await log_and_learn(message)
        
        # Базовая справка
        help_text = (
            "🧠 **Макс - Умный AI помощник**\n\n"
            "✨ **Новые возможности:**\n"
            "• Естественное человеческое общение\n"
            "• Память диалогов и личных фактов\n"
            "• Умные реакции на стикеры и GIF\n"
            "• Анализ эмоций и настроения\n"
            "• Адаптация под твой стиль общения\n\n"
            "💬 **Как общаться:**\n"
            "• Просто говори со мной как с другом\n"
            "• Используй команды: /ai, /stats, /about\n"
            "• Отправляй стикеры - отвечу по настроению\n"
            "• Задавай любые вопросы\n\n"
            "🎯 **Обращения ко мне:**\n"
            "• Напиши 'Макс' или 'бот'\n"
            "• Ответь на мое сообщение\n"
            "• Или просто общайся - я понимаю контекст!"
        )
        
        await message.reply(help_text)
    
    @router.message(Command('ai'))
    async def ai_handler(message: Message):
        """🧠 AI помощник с улучшенным интеллектом"""
        if not await check_chat_access(message):
            return
            
        await log_and_learn(message)
        
        user_message = message.text[4:].strip()
        if not user_message:
            await message.reply(
                "💡 **Умный AI помощник готов!**\n\n"
                "Просто напиши свой вопрос или мысль:\n"
                "• /ai Как дела с искусственным интеллектом?\n"
                "• /ai Что думаешь о жизни?\n"
                "• /ai Помоги разобраться с Python\n\n"
                "Я отвечу максимально по-человечески! 🤖➡️👨"
            )
            return
        
        try:
            # Получаем или создаем контекст разговора
            context_key = f"{message.from_user.id}_{message.chat.id}"
            context = conversation_contexts.get(context_key)
            
            if not context:
                context = create_conversation_context(message.from_user.id, message.chat.id)
                conversation_contexts[context_key] = context
            
            # Обогащаем контекст памятью
            if memory_module:
                user_context = await memory_module.get_user_context(
                    message.from_user.id, 
                    message.chat.id
                )
                
                # Добавляем информацию из памяти в контекст
                context.user_preferences = user_context.get('profile', {})
                context.last_messages.extend([
                    {'role': 'user', 'content': memory['summary']} 
                    for memory in user_context.get('memories', [])[-3:]
                ])
            
            # Генерируем ответ через Human-like AI
            if human_ai:
                response = await human_ai.generate_human_response(user_message, context)
                
                # Обновляем контекст
                await human_ai.update_context(context, user_message, response)
                
                # Сохраняем в долгосрочную память
                if memory_module:
                    await memory_module.save_conversation_memory(
                        message.from_user.id,
                        message.chat.id,
                        context.topic or "general",
                        f"Пользователь: {user_message}\nОтвет: {response}",
                        [user_message],
                        context.mood,
                        0.8  # Высокая важность для AI взаимодействий
                    )
            else:
                response = "AI модуль недоступен, но я все равно рад общению! 😊"
            
            await message.reply(response)
            
        except Exception as e:
            logger.error(f"❌ Ошибка AI: {e}")
            await message.reply("Что-то пошло не так с мозгом... Попробуй еще раз! 🤯")
    
    # ================= ОБРАБОТКА СТИКЕРОВ =================
    
    @router.message(F.sticker)
    async def sticker_handler(message: Message):
        """🎭 Умная обработка стикеров"""
        if not await check_chat_access(message):
            return
        
        await log_and_learn(message)
        
        try:
            # Создаем контекст
            context = {
                'user_id': message.from_user.id,
                'chat_id': message.chat.id,
                'user_name': message.from_user.first_name,
                'chat_type': message.chat.type
            }
            
            # Обрабатываем стикер через медиа модуль
            if media_triggers:
                media_responses = await media_triggers.process_sticker(
                    message.sticker,
                    message.from_user.id,
                    message.chat.id,
                    context
                )
                
                # Отправляем медиа ответы
                for media_response in media_responses:
                    await media_triggers.send_media_response(message.chat.id, media_response)
            
            # Случайный текстовый ответ на стикер
            elif random.random() < 0.1:  # 10% шанс
                sticker_responses = [
                    "Классный стикер! 👍",
                    "Понял твое настроение 😊",
                    "🎭",
                    "Интересно!",
                    "😄"
                ]
                await message.reply(random.choice(sticker_responses))
                
        except Exception as e:
            logger.error(f"❌ Ошибка обработки стикера: {e}")
    
    # ================= ИНТЕЛЛЕКТУАЛЬНАЯ ОБРАБОТКА ТЕКСТА =================
    
    @router.message(F.text)
    async def smart_text_handler(message: Message):
        """🧠 Интеллектуальная обработка текста с AI"""
        
        # ВСЕГДА логируем сообщение для обучения
        await log_and_learn(message)
        
        # Проверяем доступ к чату
        if not await check_chat_access(message):
            return
        
        # Пропускаем команды (они обрабатываются отдельно)
        if message.text.startswith('/'):
            return
            
        text_lower = message.text.lower()
        should_respond = False
        response_type = "none"
        
        # Получаем или создаем контекст разговора
        context_key = f"{message.from_user.id}_{message.chat.id}"
        context = conversation_contexts.get(context_key)
        
        if not context:
            context = create_conversation_context(message.from_user.id, message.chat.id)
            conversation_contexts[context_key] = context
        
        # Обогащаем контекст
        enriched_context = {
            'user_id': message.from_user.id,
            'chat_id': message.chat.id,
            'user_name': message.from_user.first_name or 'друг',
            'chat_type': message.chat.type,
            'original_message': message.text,
            'timestamp': datetime.now()
        }
        
        # 1. Проверяем, это реплай на сообщение бота
        if message.reply_to_message and message.reply_to_message.from_user.id == modules['bot'].id:
            should_respond = True
            response_type = "reply"
        
        # 2. Проверяем обращение к боту по ключевым словам
        elif any(trigger_word in text_lower for trigger_word in bot_trigger_words):
            should_respond = True
            response_type = "mention"
        
        # 3. Проверяем упоминание бота (@username)
        elif bot_info and f'@{bot_info.username.lower()}' in text_lower:
            should_respond = True
            response_type = "username_mention"
        
        # 4. В личных сообщениях всегда отвечаем
        elif message.chat.type == 'private':
            should_respond = True
            response_type = "private"
        
        # 5. Проверяем расширенные триггеры
        elif advanced_triggers:
            try:
                trigger_responses = await advanced_triggers.process_message(
                    message.text,
                    message.from_user.id,
                    message.chat.id,
                    enriched_context
                )
                
                if trigger_responses:
                    should_respond = True
                    response_type = "advanced_trigger"
                    
                    # Отправляем все ответы от триггеров
                    for trigger_response in trigger_responses:
                        await message.reply(trigger_response)
                        await asyncio.sleep(0.5)  # Небольшая задержка между ответами
                    
                    return  # Выходим, так как уже ответили
                    
            except Exception as e:
                logger.error(f"❌ Ошибка обработки триггеров: {e}")
        
        # Обрабатываем медиа триггеры
        if media_triggers:
            try:
                # Определяем эмоцию из контекста или анализируем
                emotion = enriched_context.get('detected_emotion', 'neutral')
                
                media_responses = await media_triggers.process_text_for_media(
                    message.text,
                    emotion,
                    enriched_context
                )
                
                # Отправляем медиа ответы
                for media_response in media_responses:
                    await media_triggers.send_media_response(message.chat.id, media_response)
                    
            except Exception as e:
                logger.error(f"❌ Ошибка медиа триггеров: {e}")
        
        # Генерируем умный ответ если нужно
        if should_respond:
            await handle_intelligent_response(message, context, response_type, enriched_context)
        
        # Очень редкая самостоятельная активность
        elif random.random() < 0.001:  # 0.1% шанс
            await handle_random_activity(message, modules)
    
    async def handle_intelligent_response(message: Message, context, response_type: str, enriched_context: Dict):
        """🧠 Обработка умного ответа"""
        try:
            logger.info(f"🧠 Генерируем умный ответ: тип={response_type}, пользователь={message.from_user.id}")
            
            # Обогащаем контекст памятью пользователя
            if memory_module:
                user_context = await memory_module.get_user_context(
                    message.from_user.id, 
                    message.chat.id
                )
                enriched_context.update(user_context.get('profile', {}))
                
                # Добавляем личные факты
                personal_facts = user_context.get('personal_facts', [])
                if personal_facts:
                    enriched_context['personal_facts'] = personal_facts[:5]  # Последние 5 фактов
            
            response = None
            
            # Генерируем ответ через Human-like AI
            if human_ai:
                try:
                    # Адаптируем промпт под тип ответа
                    if response_type == "reply":
                        prompt = f"Пользователь ответил на мое сообщение: {message.text}. Продолжи диалог естественно."
                    elif response_type in ["mention", "username_mention"]:
                        prompt = f"Пользователь обратился ко мне: {message.text}. Ответь дружелюбно и по существу."
                    elif response_type == "private":
                        prompt = message.text
                    else:
                        prompt = message.text
                    
                    response = await human_ai.generate_human_response(prompt, context)
                    
                    # Обновляем контекст
                    await human_ai.update_context(context, message.text, response)
                    
                except Exception as e:
                    logger.error(f"❌ Ошибка Human-like AI: {e}")
            
            # Fallback ответы если нет AI
            if not response:
                fallback_responses = {
                    "reply": [
                        "Интересная мысль!",
                        "Понимаю тебя",
                        "Да, согласен",
                        "А что ты еще об этом думаешь?",
                        "Хороший момент!"
                    ],
                    "mention": [
                        "Слушаю тебя!",
                        "Что хотел сказать?",
                        "Да, я здесь 👋",
                        "О чем поговорим?",
                        "Че надо? 😄"
                    ],
                    "private": [
                        "Расскажи подробнее!",
                        "Интересно... Продолжай",
                        "И как тебе это?",
                        "Понял, что дальше?",
                        "Хм, любопытно 🤔"
                    ]
                }
                
                responses_list = fallback_responses.get(response_type, fallback_responses["mention"])
                response = random.choice(responses_list)
            
            # Отправляем ответ
            await message.reply(response)
            
            # Сохраняем в долгосрочную память
            if memory_module:
                await memory_module.save_conversation_memory(
                    message.from_user.id,
                    message.chat.id,
                    context.topic or "general",
                    f"Пользователь ({response_type}): {message.text}\nОтвет: {response}",
                    [message.text],
                    context.mood,
                    0.7  # Важность обычного диалога
                )
                
        except Exception as e:
            logger.error(f"❌ Ошибка генерации умного ответа: {e}")
    
    async def handle_random_activity(message: Message, modules):
        """🎲 Очень редкая самостоятельная активность"""
        try:
            chat_id = message.chat.id
            
            # Проверяем, не было ли недавно активности в этом чате
            now = datetime.now()
            if chat_id in last_activity_time:
                if now - last_activity_time[chat_id] < timedelta(hours=3):
                    return  # Слишком рано для активности
            
            last_activity_time[chat_id] = now
            
            random_responses = [
                "Кстати...",
                "А что вы думаете о том, что...",
                "Интересно наблюдать за вашей беседой 🤔",
                "Тишина... 👀",
                "Есть кто живой?",
                "Что-то тихо стало",
                "М-да..."
            ]
            
            response = random.choice(random_responses)
            
            # Задержка перед отправкой
            await asyncio.sleep(random.randint(10, 60))
            
            await modules['bot'].send_message(chat_id, response)
            logger.info(f"🎲 Самостоятельная активность в чате {chat_id}: {response}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка самостоятельной активности: {e}")
    
    # ================= АДМИНСКИЕ КОМАНДЫ =================
    
    @router.message(Command('memory_stats'))
    async def memory_stats_handler(message: Message):
        """📊 Статистика памяти (только админы)"""
        if message.from_user.id not in modules['config'].bot.admin_ids:
            return
            
        if not memory_module:
            await message.reply("❌ Модуль памяти не активен")
            return
        
        try:
            # Получаем статистику памяти
            user_count = len(memory_module.user_profiles)
            memory_count = len(memory_module.conversation_memories)
            facts_count = sum(len(facts) for facts in memory_module.personal_facts.values())
            
            stats_text = (
                f"📊 **Статистика памяти**\n\n"
                f"👤 **Пользователей в памяти:** {user_count}\n"
                f"💭 **Воспоминаний:** {memory_count}\n"
                f"📝 **Личных фактов:** {facts_count}\n\n"
                f"🧠 **Память работает и обучается!**"
            )
            
            await message.reply(stats_text)
            
        except Exception as e:
            logger.error(f"❌ Ошибка статистики памяти: {e}")
            await message.reply("❌ Ошибка получения статистики памяти")
    
    @router.message(Command('triggers_stats'))
    async def triggers_stats_handler(message: Message):
        """⚡ Статистика триггеров (только админы)"""
        if message.from_user.id not in modules['config'].bot.admin_ids:
            return
            
        if not advanced_triggers:
            await message.reply("❌ Модуль триггеров не активен")
            return
        
        try:
            stats = await advanced_triggers.get_triggers_stats()
            
            stats_text = (
                f"⚡ **Статистика триггеров**\n\n"
                f"📊 **Общая информация:**\n"
                f"• Всего триггеров: {stats['total_triggers']}\n"
                f"• Активных: {stats['active_triggers']}\n"
                f"• Общих срабатываний: {stats['total_usage']}\n"
                f"• Средний успех: {stats['average_success_rate']:.1%}\n\n"
                f"🏆 **Топ триггеров:**\n"
            )
            
            for i, trigger in enumerate(stats['top_triggers'], 1):
                stats_text += f"{i}. {trigger['name']}: {trigger['usage_count']} ({trigger['success_rate']:.1%})\n"
            
            await message.reply(stats_text)
            
        except Exception as e:
            logger.error(f"❌ Ошибка статистики триггеров: {e}")
            await message.reply("❌ Ошибка получения статистики триггеров")
    
    # Регистрируем роутер
    dp.include_router(router)
    
    logger.info("🎛️ Обновленные обработчики с AI модулями зарегистрированы")


def register_basic_handlers(dp, modules):
    """🔧 Базовые обработчики (если модули недоступны)"""
    register_all_handlers(dp, modules)


# ================= ЭКСПОРТ =================

__all__ = ["register_all_handlers", "register_basic_handlers"]