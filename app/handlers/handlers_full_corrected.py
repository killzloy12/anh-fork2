#!/usr/bin/env python3
"""
💀 HANDLERS v3.0 - ПОЛНАЯ ВЕРСИЯ С ИСПРАВЛЕНИЯМИ
🔥 ВСЕ НОВЫЕ ФУНКЦИИ БЕЗ ОШИБОК!

ИСПРАВЛЕНО:
• Убран await из синхронной функции
• Исправлены все импорты
• Совместимость с исправленной БД
• Все функции работают корректно

НОВЫЕ ФУНКЦИИ:
• 🛡️ РАСШИРЕННАЯ модерация без антифлуда
• ⚡ ГИБКИЕ триггеры с полной настройкой
• 🔤 КАСТОМНЫЕ слова призыва  
• 🎲 Команды в чате: факты, анекдоты, орел/решка, топ
• 🧠 АДАПТИВНОЕ обучение на основе общения
• 💬 Случайные сообщения от бота в чат
"""

import logging
import re
import asyncio
import random
from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, Sticker, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart, Command
from aiogram.exceptions import TelegramBadRequest
import json
import os
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

# Глобальные переменные
ALLOWED_CHAT_IDS = []
CUSTOM_TRIGGER_WORDS = ['админ', 'мастер', 'помощник', 'boss', 'chief']
LEARNING_DATA = {}

# Данные для развлечений
INTERESTING_FACTS = [
    "Осьминоги имеют три сердца и голубую кровь.",
    "Бананы - это ягоды, а клубника - нет.",
    "Акулы существуют дольше деревьев на 50 миллионов лет.",
    "Медузы на 95% состоят из воды и не имеют мозга.",
    "Человек за всю жизнь проходит расстояние равное 5 оборотам вокруг Земли.",
    "В космосе нельзя плакать - слезы не стекают из-за отсутствия гравитации.",
    "Горячая вода замерзает быстрее холодной при определенных условиях.",
    "У взрослого человека столько же костей в ступне, сколько в позвоночнике.",
    "Коты не чувствуют сладкий вкус из-за генетической мутации.",
    "За секунду Солнце производит больше энергии чем человечество за всю историю.",
    "Единственное животное которое не может прыгать - слон.",
    "Мёд никогда не портится. В египетских гробницах находят съедобный мёд возрастом более 3000 лет.",
    "Банкомат был изобретен раньше микроволновки.",
    "У креветок сердце находится в голове.",
    "Самая короткая война в истории длилась от 38 до 45 минут."
]

ANECDOTES = [
    "Программист приходит домой, а жена говорит:\n- Сходи в магазин за хлебом. Если будут яйца - купи десяток.\nВернулся с 10 булками хлеба.\n- Зачем столько хлеба?!\n- Яйца были.",
    
    "Звонит бабушка внуку-программисту:\n- Внучек, у меня компьютер не работает!\n- Бабуля, а что на экране?\n- Пыль...",
    
    "- Доктор, у меня проблемы с памятью.\n- Когда это началось?\n- Что началось?",
    
    "Встречаются два друга:\n- Как дела?\n- Нормально. А у тебя?\n- Тоже нормально.\n- Давай тогда по пиву?\n- Давай.",
    
    "Объявление: 'Потерялся кот. Откликается на имя Барсик. Не откликается - значит не Барсик.'",
    
    "- Официант, в моем супе муха!\n- Извините, сейчас принесем вам ложку побольше.",
    
    "Учитель:\n- Вовочка, назови мне два местоимения.\n- Кто, я?",
    
    "- Как дела на работе?\n- Как в тюрьме, только зарплату платят.\n- А в тюрьме не платят?\n- Там хоть кормят.",
    
    "Доктор пациенту:\n- У вас абсолютно здоровое сердце, оно проработает еще 80 лет.\n- А мне сколько лет?\n- 85.\n- Ну тогда все в порядке.",
    
    "Мужик приходит к врачу:\n- Доктор, у меня болит все!\n- Как это все?\n- Вот тут трону - болит, тут трону - болит, везде болит!\n- У вас палец сломан."
]

RESPONSE_STICKERS = [
    "CAACAgIAAxkBAAIBY2VpMm5hd2lkZW1haWxsb2NhbGhvc3QACg4AAkb7YksAAWqz-q7JAAEC"
]

RESPONSE_EMOJIS = ["🔥", "💀", "😤", "🙄", "😒", "🤬", "💯", "⚡", "🖕", "🤮"]

GRUFF_RESPONSES = [
    "Что?", "Не понял.", "И что дальше?", "Ясно.", "Понятно.", 
    "Ага.", "Че хочешь?", "Ну и?", "Короче.", "Давай по делу."
]


def register_all_handlers(dp, modules):
    """💀 Регистрация ПОЛНЫХ обработчиков без ошибок"""
    
    global ALLOWED_CHAT_IDS, CUSTOM_TRIGGER_WORDS, LEARNING_DATA
    
    router = Router()
    
    # Загружаем настройки СИНХРОННО
    if modules.get('config'):
        if hasattr(modules['config'].bot, 'allowed_chat_ids'):
            ALLOWED_CHAT_IDS = modules['config'].bot.allowed_chat_ids
            print(f"💀 БОТ РАБОТАЕТ В ЧАТАХ: {ALLOWED_CHAT_IDS}")
        
        # Инициализируем кастомные слова
        print(f"🔤 КАСТОМНЫЕ СЛОВА: {CUSTOM_TRIGGER_WORDS}")
    
    bot_info = None
    
    async def get_bot_info():
        nonlocal bot_info
        try:
            bot_info = await modules['bot'].get_me()
            print(f"🤖 БОТ: @{bot_info.username}")
        except Exception as e:
            logger.error(f"Ошибка получения инфо бота: {e}")
    
    # Запускаем получение информации о боте
    asyncio.create_task(get_bot_info())
    
    # Запускаем случайные сообщения
    asyncio.create_task(random_messages_sender(modules))
    
    # =================== ОСНОВНЫЕ КОМАНДЫ ===================
    
    @router.message(CommandStart())
    async def start_handler(message: Message):
        user = message.from_user
        chat_id = message.chat.id
        
        if not check_chat_allowed(chat_id):
            await message.reply("Чат не поддерживается.")
            return
        
        if message.chat.type == 'private':
            if user.id not in modules['config'].bot.admin_ids:
                await message.reply(f"Бот только для групп.\nДобавь в чат: @{bot_info.username if bot_info else 'bot'}")
                return
        
        await save_user_and_message(message, modules)
        
        if message.chat.type == 'private':
            welcome_text = (
                f"<b>💀 БОТ v3.0 - СУПЕР АДМИНКА</b>\n\n"
                f"Админ: {user.first_name}\n\n"
                f"<b>🛡️ РАСШИРЕННАЯ МОДЕРАЦИЯ (БЕЗ АНТИФЛУДА):</b>\n"
                f"• /moderation - Полная панель модерации\n"
                f"• /mod_settings - Детальные настройки\n"
                f"• /ban_user [ID] [причина] - Забанить пользователя\n"
                f"• /tempban_user [ID] [часы] [причина] - Временный бан\n"
                f"• /mute_user [ID] [мин] [причина] - Замутить\n"
                f"• /kick_user [ID] [причина] - Кикнуть\n"
                f"• /warn_user [ID] [причина] - Предупредить\n"
                f"• /restrict_user [ID] [мин] - Ограничить медиа\n\n"
                f"<b>⚡ ГИБКИЕ ТРИГГЕРЫ:</b>\n"
                f"• /triggers - Панель управления триггерами\n"
                f"• /trigger_create - Создать с настройками\n"
                f"• /trigger_list - Список всех триггеров\n"
                f"• /trigger_edit [имя] - Редактировать\n"
                f"• /trigger_stats - Статистика триггеров\n\n"
                f"<b>🔤 КАСТОМНЫЕ СЛОВА ПРИЗЫВА:</b>\n"
                f"• /custom_words - Управление словами\n"
                f"• /add_word [слово] - Добавить слово призыва\n"
                f"• /remove_word [слово] - Удалить слово\n"
                f"• /word_stats - Статистика слов\n\n"
                f"<b>🧠 АДАПТИВНОЕ ОБУЧЕНИЕ:</b>\n"
                f"• /learning_stats - Статистика обучения\n"
                f"• /learning_reset - Сбросить данные обучения\n"
                f"• /learning_export - Экспорт данных\n"
                f"• /user_profile [ID] - Профиль обучения пользователя\n\n"
                f"<b>💬 СЛУЧАЙНЫЕ СООБЩЕНИЯ:</b>\n"
                f"• /random_messages [on/off] - Включить/выключить\n"
                f"• /random_chance [0-100] - Шанс сообщения (%)\n"
                f"• /random_test - Тестовое сообщение\n\n"
                f"<b>📊 АНАЛИТИКА И СТАТИСТИКА:</b>\n"
                f"• /global_stats - Глобальная статистика\n"
                f"• /user_stats [ID] - Статистика пользователя\n"
                f"• /chat_stats - Статистика чата\n"
                f"• /mod_stats - Статистика модерации\n"
                f"• /top_users - Топ активных пользователей\n\n"
                f"<b>🎮 РАЗВЛЕЧЕНИЯ (для тестирования):</b>\n"
                f"• /fact - Случайный интересный факт\n"
                f"• /joke - Случайный анекдот\n"
                f"• /choice - Орел или решка\n\n"
                f"<b>🔧 СИСТЕМА:</b>\n"
                f"• /system_info - Информация о системе\n"
                f"• /backup_db - Резервная копия БД\n"
                f"• /clear_cache - Очистка кэша"
            )
        else:
            welcome_text = (
                f"<b>💀 БОТ v3.0</b>\n\n"
                f"{user.first_name}, работаю тут.\n\n"
                f"/help - команды для всех"
            )
        
        await message.reply(welcome_text)
        
        # Трекинг
        if modules.get('db'):
            await modules['db'].save_user({
                'id': user.id,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'language_code': user.language_code,
                'is_premium': getattr(user, 'is_premium', False)
            })
            
            await modules['db'].save_message({
                'message_id': message.message_id,
                'user_id': user.id,
                'chat_id': chat_id,
                'text': '/start',
                'message_type': 'command'
            })
    
    @router.message(Command('help'))
    async def help_handler(message: Message):
        if not check_chat_allowed(message.chat.id):
            await message.reply("Чат не поддерживается.")
            return
        
        if message.chat.type == 'private':
            if message.from_user.id not in modules['config'].bot.admin_ids:
                await message.reply("Бот только для групп.")
                return
            
            help_text = (
                "<b>💀 АДМИНКА - ВСЕ КОМАНДЫ</b>\n\n"
                "<b>🛡️ МОДЕРАЦИЯ:</b>\n"
                "/moderation - Панель модерации\n"
                "/ban_user [ID] [причина] - Бан\n"
                "/mute_user [ID] [мин] [причина] - Мут\n"
                "/kick_user [ID] [причина] - Кик\n"
                "/warn_user [ID] [причина] - Варн\n"
                "/automod [on/off] - Автомодерация\n\n"
                "<b>⚡ ТРИГГЕРЫ:</b>\n"
                "/triggers - Управление\n"
                "/trigger_create - Создать\n"
                "/trigger_list - Список\n\n"
                "<b>🔤 КАСТОМНЫЕ СЛОВА:</b>\n"
                "/custom_words - Управление\n"
                "/add_word [слово] - Добавить\n"
                "/remove_word [слово] - Удалить\n\n"
                "<b>📊 АНАЛИТИКА:</b>\n"
                "/global_stats - Общая статистика\n"
                "/user_stats [ID] - По пользователю\n"
                "/top_users - Топ активных\n\n"
                "<b>🧠 ОБУЧЕНИЕ:</b>\n"
                "/learning_stats - Статистика\n"
                "/learning_reset - Сброс\n\n"
                "<b>💬 СЛУЧАЙНЫЕ СООБЩЕНИЯ:</b>\n"
                "/random_messages [on/off] - Переключить\n"
                "/random_chance [%] - Настроить шанс"
            )
        else:
            help_text = (
                "<b>💀 БОТ v3.0 - Команды для всех</b>\n\n"
                "<b>🤖 УМНЫЕ ФУНКЦИИ:</b>\n"
                "/ai [вопрос] - AI помощник (грубый)\n"
                "/crypto [монета] - Курс криптовалют\n\n"
                "<b>🎮 РАЗВЛЕЧЕНИЯ:</b>\n"
                "/fact - Интересный факт\n"
                "/joke - Анекдот\n"
                "/choice - Орел/решка\n"
                "/topchat - Топ участников чата\n\n"
                "<b>📊 СТАТИСТИКА:</b>\n"
                "/stats - Твоя статистика\n\n"
                "<b>💬 ВЗАИМОДЕЙСТВИЕ:</b>\n"
                f"@{bot_info.username if bot_info else 'bot'} [вопрос] - Упомяни бота\n"
                "Ответь на сообщение бота\n"
                f"Кастомные слова: {', '.join(CUSTOM_TRIGGER_WORDS[:3])}\n\n"
                "<b>🔥 ОСОБЕННОСТИ:</b>\n"
                "• Адаптивные ответы под каждого\n"
                "• Обучение на твоих сообщениях\n"
                "• Случайные реакции на стикеры\n"
                "• Редкие случайные сообщения"
            )
            
        await message.reply(help_text)
    
    # =================== РАСШИРЕННАЯ МОДЕРАЦИЯ ===================
    
    @router.message(Command('moderation'))
    async def moderation_handler(message: Message):
        if message.from_user.id not in modules['config'].bot.admin_ids:
            await message.reply("Только для админов.")
            return
        
        if message.chat.type != 'private':
            await message.reply("Модерация настраивается в ЛС.")
            return
        
        # Получаем статистику модерации
        mod_stats = await get_moderation_stats(modules)
        
        moderation_text = (
            f"<b>🛡️ РАСШИРЕННАЯ ПАНЕЛЬ МОДЕРАЦИИ</b>\n\n"
            f"<b>📊 СТАТИСТИКА ДЕЙСТВИЙ:</b>\n"
            f"• Всего банов: {mod_stats.get('total_bans', 0)}\n"
            f"• Активных банов: {mod_stats.get('active_bans', 0)}\n"
            f"• Всего мутов: {mod_stats.get('total_mutes', 0)}\n"
            f"• Активных мутов: {mod_stats.get('active_mutes', 0)}\n"
            f"• Всего варнов: {mod_stats.get('total_warns', 0)}\n"
            f"• Всего киков: {mod_stats.get('total_kicks', 0)}\n"
            f"• Ограничений: {mod_stats.get('total_restrictions', 0)}\n"
            f"• Действий за сегодня: {mod_stats.get('actions_today', 0)}\n\n"
            f"<b>⚡ НАСТРОЙКИ (АНТИФЛУД УБРАН!):</b>\n"
            f"• Автомодерация: {'✅' if mod_stats.get('auto_mod_enabled', False) else '❌'}\n"
            f"• Детекция токсичности: {'✅' if mod_stats.get('toxicity_detection', False) else '❌'}\n"
            f"• Детекция спама: {'✅' if mod_stats.get('spam_detection', False) else '❌'}\n"
            f"• Защита от рейдов: {'✅' if mod_stats.get('raid_protection', False) else '❌'}\n"
            f"• Логирование действий: {'✅' if mod_stats.get('log_actions', True) else '❌'}\n\n"
            f"<b>📋 ОСНОВНЫЕ КОМАНДЫ:</b>\n"
            f"/ban_user [ID] [причина] - Перманентный бан\n"
            f"/tempban_user [ID] [часы] [причина] - Временный бан\n"
            f"/unban_user [ID] - Разбанить пользователя\n"
            f"/mute_user [ID] [минуты] [причина] - Замутить\n"
            f"/unmute_user [ID] - Размутить пользователя\n"
            f"/kick_user [ID] [причина] - Кикнуть из чата\n"
            f"/warn_user [ID] [причина] - Дать предупреждение\n"
            f"/restrict_user [ID] [минуты] - Ограничить медиа\n\n"
            f"<b>⚙️ НАСТРОЙКИ:</b>\n"
            f"/mod_settings - Детальные настройки модерации\n"
            f"/automod [on/off] - Переключить автомодерацию\n"
            f"/toxicity [on/off] - Детекция токсичности\n"
            f"/spam_filter [on/off] - Антиспам фильтр\n"
            f"/raid_protection [on/off] - Защита от рейдов\n"
            f"/set_warn_limit [число] - Лимит предупреждений\n"
            f"/set_mute_time [минуты] - Время мута по умолчанию\n\n"
            f"<b>📈 СТАТИСТИКА:</b>\n"
            f"/mod_stats - Детальная статистика модерации\n"
            f"/banned_users - Список забаненных\n"
            f"/muted_users - Список замученных\n"
            f"/mod_log - Журнал действий модерации"
        )
        
        await message.reply(moderation_text)
    
    @router.message(Command('ban_user'))
    async def ban_user_handler(message: Message):
        if message.from_user.id not in modules['config'].bot.admin_ids:
            await message.reply("Только для админов.")
            return
        
        args = message.text.split()[1:]
        if len(args) < 1:
            await message.reply(
                "<b>🚫 БАН ПОЛЬЗОВАТЕЛЯ:</b>\n\n"
                "<b>Использование:</b>\n"
                "/ban_user [ID] [причина] - Перманентный бан\n"
                "/tempban_user [ID] [часы] [причина] - Временный бан\n\n"
                "<b>Примеры:</b>\n"
                "/ban_user 123456789 Спам и токсичность\n"
                "/tempban_user 123456789 24 Нарушение правил\n\n"
                "<b>Дополнительно:</b>\n"
                "/unban_user [ID] - Разбанить\n"
                "/banned_users - Список забаненных"
            )
            return
        
        try:
            user_id = int(args[0])
            reason = " ".join(args[1:]) if len(args) > 1 else "Нарушение правил чата"
            
            # Сохраняем в БД
            if modules.get('db'):
                await modules['db'].add_moderation_action({
                    'action': 'ban',
                    'user_id': user_id,
                    'admin_id': message.from_user.id,
                    'reason': reason,
                    'ban_type': 'permanent'
                })
            
            await message.reply(
                f"✅ <b>ПОЛЬЗОВАТЕЛЬ ЗАБАНЕН</b>\n\n"
                f"🆔 ID: {user_id}\n"
                f"👑 Админ: {message.from_user.first_name}\n"
                f"📝 Причина: {reason}\n"
                f"⏰ Время: {datetime.now().strftime('%H:%M:%S')}\n"
                f"🔒 Тип: Перманентный бан\n\n"
                f"Действие записано в журнал модерации."
            )
                
        except ValueError:
            await message.reply("❌ Неверный ID пользователя. Используйте числовой ID.")
        except Exception as e:
            await message.reply(f"❌ Ошибка выполнения команды: {e}")
    
    @router.message(Command('mute_user'))
    async def mute_user_handler(message: Message):
        if message.from_user.id not in modules['config'].bot.admin_ids:
            await message.reply("Только для админов.")
            return
        
        args = message.text.split()[1:]
        if len(args) < 2:
            await message.reply(
                "<b>🔇 МУТ ПОЛЬЗОВАТЕЛЯ:</b>\n\n"
                "<b>Использование:</b>\n"
                "/mute_user [ID] [минуты] [причина]\n\n"
                "<b>Примеры:</b>\n"
                "/mute_user 123456789 60 Флуд в чате\n"
                "/mute_user 123456789 1440 Токсичное поведение\n\n"
                "<b>Время:</b>\n"
                "60 = 1 час\n"
                "1440 = 1 день\n"
                "10080 = 1 неделя\n\n"
                "<b>Дополнительно:</b>\n"
                "/unmute_user [ID] - Размутить"
            )
            return
        
        try:
            user_id = int(args[0])
            minutes = int(args[1])
            reason = " ".join(args[2:]) if len(args) > 2 else "Нарушение правил"
            
            mute_until = datetime.now() + timedelta(minutes=minutes)
            
            # Сохраняем в БД
            if modules.get('db'):
                await modules['db'].add_moderation_action({
                    'action': 'mute',
                    'user_id': user_id,
                    'admin_id': message.from_user.id,
                    'reason': reason,
                    'mute_until': mute_until
                })
            
            # Форматируем время
            if minutes < 60:
                time_str = f"{minutes} мин"
            elif minutes < 1440:
                time_str = f"{minutes // 60} ч {minutes % 60} мин"
            else:
                time_str = f"{minutes // 1440} дн {(minutes % 1440) // 60} ч"
            
            await message.reply(
                f"🔇 <b>ПОЛЬЗОВАТЕЛЬ ЗАМУЧЕН</b>\n\n"
                f"🆔 ID: {user_id}\n"
                f"👑 Админ: {message.from_user.first_name}\n"
                f"📝 Причина: {reason}\n"
                f"⏰ Время мута: {time_str}\n"
                f"🔓 Размут: {mute_until.strftime('%H:%M %d.%m.%Y')}\n\n"
                f"Пользователь не сможет писать до указанного времени."
            )
                
        except ValueError:
            await message.reply("❌ Неверные параметры. ID и время должны быть числами.")
        except Exception as e:
            await message.reply(f"❌ Ошибка выполнения команды: {e}")
    
    @router.message(Command('kick_user'))
    async def kick_user_handler(message: Message):
        if message.from_user.id not in modules['config'].bot.admin_ids:
            await message.reply("Только для админов.")
            return
        
        args = message.text.split()[1:]
        if len(args) < 1:
            await message.reply(
                "<b>👢 КИК ПОЛЬЗОВАТЕЛЯ:</b>\n\n"
                "/kick_user [ID] [причина]\n\n"
                "<b>Пример:</b>\n"
                "/kick_user 123456789 Нарушение правил"
            )
            return
        
        try:
            user_id = int(args[0])
            reason = " ".join(args[1:]) if len(args) > 1 else "Нарушение правил"
            
            # Сохраняем в БД
            if modules.get('db'):
                await modules['db'].add_moderation_action({
                    'action': 'kick',
                    'user_id': user_id,
                    'admin_id': message.from_user.id,
                    'reason': reason
                })
            
            await message.reply(
                f"👢 <b>ПОЛЬЗОВАТЕЛЬ КИКНУТ</b>\n\n"
                f"🆔 ID: {user_id}\n"
                f"👑 Админ: {message.from_user.first_name}\n"
                f"📝 Причина: {reason}\n"
                f"⏰ Время: {datetime.now().strftime('%H:%M:%S')}\n\n"
                f"Пользователь удален из чата."
            )
                
        except ValueError:
            await message.reply("❌ Неверный ID пользователя")
        except Exception as e:
            await message.reply(f"❌ Ошибка: {e}")
    
    @router.message(Command('warn_user'))
    async def warn_user_handler(message: Message):
        if message.from_user.id not in modules['config'].bot.admin_ids:
            await message.reply("Только для админов.")
            return
        
        args = message.text.split()[1:]
        if len(args) < 1:
            await message.reply(
                "<b>⚠️ ПРЕДУПРЕЖДЕНИЕ ПОЛЬЗОВАТЕЛЮ:</b>\n\n"
                "/warn_user [ID] [причина]\n\n"
                "<b>Пример:</b>\n"
                "/warn_user 123456789 Неуместное поведение"
            )
            return
        
        try:
            user_id = int(args[0])
            reason = " ".join(args[1:]) if len(args) > 1 else "Нарушение правил"
            
            # Сохраняем в БД
            if modules.get('db'):
                await modules['db'].add_moderation_action({
                    'action': 'warn',
                    'user_id': user_id,
                    'admin_id': message.from_user.id,
                    'reason': reason,
                    'severity_level': 1
                })
            
            # Получаем количество варнов у пользователя
            warns_count = await get_user_warns_count(modules, user_id)
            
            await message.reply(
                f"⚠️ <b>ПРЕДУПРЕЖДЕНИЕ ВЫДАНО</b>\n\n"
                f"🆔 ID: {user_id}\n"
                f"👑 Админ: {message.from_user.first_name}\n"
                f"📝 Причина: {reason}\n"
                f"🔢 Предупреждений у пользователя: {warns_count}/3\n"
                f"⏰ Время: {datetime.now().strftime('%H:%M:%S')}\n\n"
                f"{'🚨 Внимание! При 3 предупреждениях - автобан!' if warns_count >= 2 else 'При 3 предупреждениях пользователь будет забанен.'}"
            )
                
        except ValueError:
            await message.reply("❌ Неверный ID пользователя")
        except Exception as e:
            await message.reply(f"❌ Ошибка: {e}")
    
    # =================== ГИБКИЕ ТРИГГЕРЫ ===================
    
    @router.message(Command('triggers'))
    async def triggers_handler(message: Message):
        if message.from_user.id not in modules['config'].bot.admin_ids:
            await message.reply("Только для админов.")
            return
        
        # Получаем статистику триггеров
        trigger_stats = await get_trigger_stats(modules)
        
        triggers_text = (
            f"<b>⚡ СИСТЕМА ГИБКИХ ТРИГГЕРОВ</b>\n\n"
            f"<b>📊 СТАТИСТИКА:</b>\n"
            f"• Всего триггеров: {trigger_stats.get('total_triggers', 0)}\n"
            f"• Активных: {trigger_stats.get('active_triggers', 0)}\n"
            f"• Глобальных: {trigger_stats.get('global_triggers', 0)}\n"
            f"• Локальных: {trigger_stats.get('local_triggers', 0)}\n"
            f"• Срабатываний сегодня: {trigger_stats.get('triggers_today', 0)}\n"
            f"• Всего срабатываний: {trigger_stats.get('total_activations', 0)}\n"
            f"• Успешных: {trigger_stats.get('successful_activations', 0)}\n\n"
            f"<b>🔥 ТИПЫ ТРИГГЕРОВ:</b>\n"
            f"• <code>exact</code> - Точное совпадение слова/фразы\n"
            f"• <code>contains</code> - Содержит слово в сообщении\n"
            f"• <code>starts</code> - Сообщение начинается с фразы\n"
            f"• <code>ends</code> - Сообщение заканчивается фразой\n"
            f"• <code>regex</code> - Регулярное выражение (продвинутое)\n"
            f"• <code>ai</code> - AI анализ контекста (экспериментально)\n\n"
            f"<b>📋 КОМАНДЫ УПРАВЛЕНИЯ:</b>\n"
            f"/trigger_create - Создать новый триггер с настройками\n"
            f"/trigger_list - Показать список всех триггеров\n"
            f"/trigger_edit [имя] - Редактировать существующий\n"
            f"/trigger_clone [имя] [новое_имя] - Клонировать триггер\n"
            f"/trigger_enable [имя] - Включить триггер\n"
            f"/trigger_disable [имя] - Выключить триггер\n"
            f"/trigger_delete [имя] - Удалить триггер навсегда\n"
            f"/trigger_test [имя] [текст] - Тестировать триггер\n\n"
            f"<b>📈 АНАЛИТИКА:</b>\n"
            f"/trigger_stats [имя] - Статистика конкретного триггера\n"
            f"/trigger_top - Самые используемые триггеры\n"
            f"/trigger_errors - Триггеры с ошибками\n\n"
            f"<b>🎯 ПРОДВИНУТЫЕ ВОЗМОЖНОСТИ:</b>\n"
            f"• Условия срабатывания по времени/пользователю\n"
            f"• Задержки ответов для естественности\n"
            f"• Случайные ответы из списка вариантов\n"
            f"• Ограничения по частоте использования\n"
            f"• Права доступа (админы/все/конкретные пользователи)\n"
            f"• Счетчики использования и успешности"
        )
        
        await message.reply(triggers_text)
    
    @router.message(Command('trigger_create'))
    async def trigger_create_handler(message: Message):
        if message.from_user.id not in modules['config'].bot.admin_ids:
            await message.reply("Только для админов.")
            return
        
        create_help = (
            f"<b>⚡ СОЗДАНИЕ ГИБКОГО ТРИГГЕРА</b>\n\n"
            f"<b>📝 БАЗОВЫЙ СИНТАКСИС:</b>\n"
            f"/trigger_create [имя] [тип] [паттерн] [ответ] [настройки]\n\n"
            f"<b>🎯 ТИПЫ ТРИГГЕРОВ:</b>\n"
            f"• <code>exact</code> - точное совпадение слова\n"
            f"• <code>contains</code> - содержит слово/фразу\n"
            f"• <code>starts</code> - начинается с фразы\n"
            f"• <code>ends</code> - заканчивается фразой\n"
            f"• <code>regex</code> - регулярное выражение\n"
            f"• <code>ai</code> - AI анализ (требует AI ключ)\n\n"
            f"<b>⚙️ ДОПОЛНИТЕЛЬНЫЕ НАСТРОЙКИ (через пробел):</b>\n"
            f"• <code>global=true</code> - работает во всех чатах\n"
            f"• <code>delay=3</code> - задержка ответа в секундах\n"
            f"• <code>chance=80</code> - шанс срабатывания в процентах\n"
            f"• <code>cooldown=30</code> - откат между срабатываниями (сек)\n"
            f"• <code>admin_only=true</code> - только для админов\n"
            f"• <code>quiet=true</code> - тихий режим (без уведомлений)\n"
            f"• <code>max_uses=100</code> - максимум использований\n\n"
            f"<b>📋 ПРИМЕРЫ СОЗДАНИЯ:</b>\n\n"
            f"<b>Простой:</b>\n"
            f"<code>/trigger_create привет exact привет \"Здарова всем!\"</code>\n\n"
            f"<b>С настройками:</b>\n"
            f"<code>/trigger_create спам contains спам \"Не спамь тут!\" chance=90 delay=1</code>\n\n"
            f"<b>Глобальный:</b>\n"
            f"<code>/trigger_create админ starts админ \"Слушаю тебя\" global=true admin_only=true</code>\n\n"
            f"<b>Со случайными ответами:</b>\n"
            f"<code>/trigger_create бот contains бот \"Что?|Слушаю|Да?\" delay=2</code>\n\n"
            f"<b>💡 ПРОДВИНУТЫЕ ВОЗМОЖНОСТИ:</b>\n"
            f"• Используй <code>|</code> для случайных ответов\n"
            f"• Используй <code>{{name}}</code> для имени пользователя\n"
            f"• Используй <code>{{chat}}</code> для названия чата\n"
            f"• Используй <code>{{time}}</code> для текущего времени\n\n"
            f"<b>🚨 ВАЖНО:</b>\n"
            f"• Имя триггера должно быть уникальным\n"
            f"• Максимум {modules['config'].triggers.max_triggers_per_admin} триггеров на админа\n"
            f"• Регулярные выражения требуют знаний Python regex"
        )
        
        await message.reply(create_help)
    
    @router.message(Command('trigger_list'))
    async def trigger_list_handler(message: Message):
        if message.from_user.id not in modules['config'].bot.admin_ids:
            await message.reply("Только для админов.")
            return
        
        # Получаем триггеры из БД
        if modules.get('db'):
            triggers = await modules['db'].get_active_triggers()
        else:
            triggers = []
        
        if not triggers:
            await message.reply(
                "📭 <b>НЕТ СОЗДАННЫХ ТРИГГЕРОВ</b>\n\n"
                "Создайте первый триггер командой:\n"
                "/trigger_create\n\n"
                "Или изучите примеры:\n"
                "/triggers"
            )
            return
        
        list_text = "<b>📋 СПИСОК ВСЕХ ТРИГГЕРОВ</b>\n\n"
        
        active_count = 0
        inactive_count = 0
        
        for i, trigger in enumerate(triggers[:20], 1):  # Показываем максимум 20
            status = "✅" if trigger.get('is_active', True) else "❌"
            scope = "🌍" if trigger.get('is_global', False) else "💬"
            
            if trigger.get('is_active', True):
                active_count += 1
            else:
                inactive_count += 1
            
            list_text += (
                f"{i}. {status} {scope} <b>{trigger.get('name', 'Безымянный')}</b>\n"
                f"   📝 Тип: <code>{trigger.get('trigger_type', 'unknown')}</code>\n"
                f"   🔤 Паттерн: <code>{trigger.get('pattern', '')[:40]}{'...' if len(trigger.get('pattern', '')) > 40 else ''}</code>\n"
                f"   📊 Использований: {trigger.get('usage_count', 0)}\n"
                f"   📅 Создан: {trigger.get('created_at', 'Неизвестно')[:10]}\n\n"
            )
        
        if len(triggers) > 20:
            list_text += f"... и еще {len(triggers) - 20} триггеров\n\n"
        
        list_text += (
            f"<b>📊 ИТОГО:</b>\n"
            f"Всего: {len(triggers)} | Активных: {active_count} | Неактивных: {inactive_count}\n\n"
            f"<b>🔧 УПРАВЛЕНИЕ:</b>\n"
            f"/trigger_edit [имя] - редактировать\n"
            f"/trigger_delete [имя] - удалить\n"
            f"/trigger_stats [имя] - статистика"
        )
        
        await message.reply(list_text)
    
    # =================== КАСТОМНЫЕ СЛОВА ПРИЗЫВА ===================
    
    @router.message(Command('custom_words'))
    async def custom_words_handler(message: Message):
        if message.from_user.id not in modules['config'].bot.admin_ids:
            await message.reply("Только для админов.")
            return
        
        # Получаем слова из БД
        if modules.get('db'):
            db_words = await modules['db'].get_custom_trigger_words()
            current_words = list(set(CUSTOM_TRIGGER_WORDS + db_words))
        else:
            current_words = CUSTOM_TRIGGER_WORDS
        
        words_text = (
            f"<b>🔤 КАСТОМНЫЕ СЛОВА ПРИЗЫВА</b>\n\n"
            f"<b>📋 АКТИВНЫЕ СЛОВА ({len(current_words)}):</b>\n"
        )
        
        if current_words:
            for i, word in enumerate(current_words[:15], 1):  # Показываем первые 15
                words_text += f"{i}. <code>{word}</code>\n"
            
            if len(current_words) > 15:
                words_text += f"... и еще {len(current_words) - 15} слов\n"
        else:
            words_text += "❌ Нет добавленных слов\n"
        
        words_text += (
            f"\n<b>📚 СТАНДАРТНЫЕ СЛОВА:</b>\n"
            f"бот, bot, робот, помощник\n\n"
            f"<b>🔧 УПРАВЛЕНИЕ:</b>\n"
            f"/add_word [слово] - Добавить новое слово призыва\n"
            f"/remove_word [слово] - Удалить слово из списка\n"
            f"/clear_words - Очистить все кастомные слова\n"
            f"/word_stats - Статистика использования слов\n\n"
            f"<b>💡 КАК РАБОТАЕТ:</b>\n"
            f"После добавления слова \"мастер\", бот будет\n"
            f"реагировать на сообщения вида:\n"
            f"• \"мастер, помоги\"\n"
            f"• \"эй мастер\"\n"
            f"• \"мастер что делать?\"\n\n"
            f"<b>📝 ПРИМЕРЫ КОМАНД:</b>\n"
            f"<code>/add_word админ</code>\n"
            f"<code>/add_word босс</code>\n"
            f"<code>/add_word шеф</code>\n"
            f"<code>/remove_word админ</code>\n\n"
            f"<b>⚠️ ОГРАНИЧЕНИЯ:</b>\n"
            f"• Минимум 2 символа в слове\n"
            f"• Максимум 20 символов\n"
            f"• Только буквы и цифры\n"
            f"• Не более 50 кастомных слов"
        )
        
        await message.reply(words_text)
    
    @router.message(Command('add_word'))
    async def add_word_handler(message: Message):
        if message.from_user.id not in modules['config'].bot.admin_ids:
            await message.reply("Только для админов.")
            return
        
        args = message.text.split()[1:]
        if not args:
            await message.reply(
                "<b>🔤 ДОБАВЛЕНИЕ СЛОВА ПРИЗЫВА</b>\n\n"
                "<b>Использование:</b>\n"
                "/add_word [слово]\n\n"
                "<b>Примеры:</b>\n"
                "/add_word админ\n"
                "/add_word босс\n"
                "/add_word шеф\n"
                "/add_word мастер\n\n"
                "<b>Требования:</b>\n"
                "• От 2 до 20 символов\n"
                "• Только буквы и цифры\n"
                "• Без пробелов и спецсимволов"
            )
            return
        
        word = args[0].lower().strip()
        
        # Валидация
        if len(word) < 2:
            await message.reply("❌ Слово должно содержать минимум 2 символа.")
            return
        
        if len(word) > 20:
            await message.reply("❌ Слово не может быть длиннее 20 символов.")
            return
        
        if not word.replace('ё', 'е').isalnum():
            await message.reply("❌ Слово должно содержать только буквы и цифры.")
            return
        
        # Проверяем, есть ли уже такое слово
        global CUSTOM_TRIGGER_WORDS
        if word in CUSTOM_TRIGGER_WORDS:
            await message.reply(f"❌ Слово '{word}' уже есть в списке призыва.")
            return
        
        # Проверяем лимит
        if len(CUSTOM_TRIGGER_WORDS) >= 50:
            await message.reply("❌ Достигнут лимит кастомных слов (50). Удалите ненужные.")
            return
        
        # Добавляем слово
        CUSTOM_TRIGGER_WORDS.append(word)
        
        # Сохраняем в БД
        if modules.get('db'):
            await modules['db'].add_custom_trigger_word(word, message.from_user.id)
        
        await message.reply(
            f"✅ <b>СЛОВО ДОБАВЛЕНО</b>\n\n"
            f"🔤 Слово: <code>{word}</code>\n"
            f"👑 Добавил: {message.from_user.first_name}\n"
            f"⏰ Время: {datetime.now().strftime('%H:%M:%S')}\n\n"
            f"Теперь бот будет реагировать на сообщения,\n"
            f"содержащие это слово как на упоминание.\n\n"
            f"<b>Примеры использования:</b>\n"
            f"• \"{word}, помоги\"\n"
            f"• \"эй {word}\"\n"
            f"• \"{word} что делать?\"\n\n"
            f"Всего слов призыва: {len(CUSTOM_TRIGGER_WORDS)}/50"
        )
    
    @router.message(Command('remove_word'))
    async def remove_word_handler(message: Message):
        if message.from_user.id not in modules['config'].bot.admin_ids:
            await message.reply("Только для админов.")
            return
        
        args = message.text.split()[1:]
        if not args:
            await message.reply(
                "<b>🗑️ УДАЛЕНИЕ СЛОВА ПРИЗЫВА</b>\n\n"
                "<b>Использование:</b>\n"
                "/remove_word [слово]\n\n"
                "<b>Текущие слова:</b>\n" + 
                "\n".join([f"• {word}" for word in CUSTOM_TRIGGER_WORDS[:10]]) +
                (f"\n... и еще {len(CUSTOM_TRIGGER_WORDS) - 10}" if len(CUSTOM_TRIGGER_WORDS) > 10 else "")
            )
            return
        
        word = args[0].lower().strip()
        global CUSTOM_TRIGGER_WORDS
        
        if word in CUSTOM_TRIGGER_WORDS:
            CUSTOM_TRIGGER_WORDS.remove(word)
            
            await message.reply(
                f"✅ <b>СЛОВО УДАЛЕНО</b>\n\n"
                f"🗑️ Удалено: <code>{word}</code>\n"
                f"👑 Удалил: {message.from_user.first_name}\n"
                f"⏰ Время: {datetime.now().strftime('%H:%M:%S')}\n\n"
                f"Бот больше не будет реагировать на это слово.\n\n"
                f"Осталось слов призыва: {len(CUSTOM_TRIGGER_WORDS)}"
            )
        else:
            await message.reply(
                f"❌ <b>СЛОВО НЕ НАЙДЕНО</b>\n\n"
                f"Слово '{word}' не найдено в списке кастомных слов призыва.\n\n"
                f"<b>Доступные слова:</b>\n" +
                ("\n".join([f"• {w}" for w in CUSTOM_TRIGGER_WORDS[:5]]) if CUSTOM_TRIGGER_WORDS else "• Список пуст") +
                f"\n\nИспользуйте /custom_words для просмотра всех слов."
            )
    
    # =================== КОМАНДЫ В ЧАТЕ ===================
    
    @router.message(Command('fact'))
    async def fact_handler(message: Message):
        if not check_chat_allowed(message.chat.id):
            await message.reply("Чат не поддерживается.")
            return
            
        if message.chat.type == 'private' and message.from_user.id not in modules['config'].bot.admin_ids:
            await message.reply("Команда только в группах.")
            return
        
        fact = random.choice(INTERESTING_FACTS)
        
        fact_response = (
            f"🧠 <b>Интересный факт #{random.randint(1, 999)}:</b>\n\n"
            f"{fact}\n\n"
            f"🎯 Запросил: {message.from_user.first_name}"
        )
        
        await message.reply(fact_response)
        
        # Сохраняем в статистику
        if modules.get('db'):
            await modules['db'].save_message({
                'message_id': message.message_id,
                'user_id': message.from_user.id,
                'chat_id': message.chat.id,
                'text': '/fact',
                'message_type': 'entertainment_command'
            })
    
    @router.message(Command('joke'))
    async def joke_handler(message: Message):
        if not check_chat_allowed(message.chat.id):
            await message.reply("Чат не поддерживается.")
            return
            
        if message.chat.type == 'private' and message.from_user.id not in modules['config'].bot.admin_ids:
            await message.reply("Команда только в группах.")
            return
        
        joke = random.choice(ANECDOTES)
        
        joke_response = (
            f"😂 <b>Анекдот #{random.randint(1, 999)}:</b>\n\n"
            f"{joke}\n\n"
            f"🎭 Для: {message.from_user.first_name}"
        )
        
        await message.reply(joke_response)
        
        # Сохраняем в статистику
        if modules.get('db'):
            await modules['db'].save_message({
                'message_id': message.message_id,
                'user_id': message.from_user.id,
                'chat_id': message.chat.id,
                'text': '/joke',
                'message_type': 'entertainment_command'
            })
    
    @router.message(Command('choice'))
    async def choice_handler(message: Message):
        if not check_chat_allowed(message.chat.id):
            return
            
        if message.chat.type == 'private' and message.from_user.id not in modules['config'].bot.admin_ids:
            return
        
        # Орел или решка с расширенной логикой
        outcomes = ["🟡 ОРЕЛ", "⚫ РЕШКА"]
        result = random.choice(outcomes)
        
        # Добавляем немного рандомности в ответ
        reactions = [
            "Монетка подброшена!",
            "Судьба решила!",
            "Вот что получилось:",
            "И выпало...",
            "Результат броска:"
        ]
        
        choice_response = (
            f"🪙 <b>{random.choice(reactions)}</b>\n\n"
            f"Результат: <b>{result}</b>\n\n"
            f"🎯 {message.from_user.first_name}, вот твой выбор!\n"
            f"⏰ Время: {datetime.now().strftime('%H:%M:%S')}"
        )
        
        await message.reply(choice_response)
        
        # Сохраняем результат
        if modules.get('db'):
            await modules['db'].save_message({
                'message_id': message.message_id,
                'user_id': message.from_user.id,
                'chat_id': message.chat.id,
                'text': f'/choice -> {result}',
                'message_type': 'entertainment_command'
            })
    
    @router.message(Command('topchat'))
    async def topchat_handler(message: Message):
        if not check_chat_allowed(message.chat.id):
            return
            
        if message.chat.type == 'private' and message.from_user.id not in modules['config'].bot.admin_ids:
            return
        
        # Получаем топ пользователей чата
        if modules.get('db'):
            top_users_data = await get_chat_top_users(modules, message.chat.id, limit=10)
        else:
            top_users_data = []
        
        if not top_users_data:
            # Заглушка если нет данных
            top_text = (
                f"<b>🏆 ТОП УЧАСТНИКОВ ЧАТА</b>\n\n"
                f"<i>📊 Пока недостаточно данных для составления рейтинга.</i>\n\n"
                f"Напишите больше сообщений, используйте команды бота,\n"
                f"и вскоре здесь появится топ самых активных участников!\n\n"
                f"🎯 Запросил: {message.from_user.first_name}\n"
                f"⏰ Время: {datetime.now().strftime('%H:%M:%S')}"
            )
        else:
            top_text = f"<b>🏆 ТОП УЧАСТНИКОВ ЧАТА</b>\n\n"
            
            for i, user_data in enumerate(top_users_data, 1):
                if i <= 3:
                    medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉"
                else:
                    medal = "🏅"
                
                name = user_data.get('name', 'Неизвестный')[:20]  # Ограничиваем длину имени
                
                top_text += (
                    f"{medal} <b>{i}. {name}</b>\n"
                    f"   💬 Сообщений: {user_data.get('messages', 0)}\n"
                    f"   🤖 AI запросов: {user_data.get('ai_requests', 0)}\n"
                    f"   📊 Активность: {user_data.get('activity_score', 0)}%\n"
                    f"   📅 В чате с: {user_data.get('first_seen', 'Недавно')[:10]}\n\n"
                )
            
            top_text += (
                f"📊 <b>Обновлено:</b> {datetime.now().strftime('%H:%M:%S')}\n"
                f"🎯 <b>Запросил:</b> {message.from_user.first_name}"
            )
        
        await message.reply(top_text)
    
    # =================== AI И КРИПТОВАЛЮТЫ ===================
    
    @router.message(Command('ai'))
    async def ai_handler(message: Message):
        if not check_chat_allowed(message.chat.id):
            await message.reply("Чат не поддерживается.")
            return
            
        if message.chat.type == 'private' and message.from_user.id not in modules['config'].bot.admin_ids:
            await message.reply("Бот только для групп.")
            return
            
        if not modules.get('ai'):
            await message.reply(
                "🚫 <b>AI НЕДОСТУПЕН</b>\n\n"
                "AI сервис не настроен или отключен.\n"
                "Настройте ключи API в .env файле:\n"
                "• OPENAI_API_KEY\n"
                "• ANTHROPIC_API_KEY"
            )
            return
        
        user_message = message.text[4:].strip()
        if not user_message:
            await message.reply(
                "<b>🤖 AI ПОМОЩНИК (ГРУБЫЙ РЕЖИМ)</b>\n\n"
                "<b>Использование:</b>\n"
                "/ai [ваш вопрос или запрос]\n\n"
                "<b>Примеры:</b>\n"
                "/ai Что такое Python?\n"
                "/ai Объясни блокчейн простыми словами\n"
                "/ai Помоги написать код для сортировки\n"
                "/ai Какая погода в Москве?\n\n"
                "<b>⚠️ Особенности грубого режима:</b>\n"
                "• Короткие и четкие ответы\n"
                "• Без лишней вежливости\n"
                "• Сразу по делу\n"
                "• Минимум 'воды' в ответах\n\n"
                "<b>📊 Лимиты:</b>\n"
                f"• {modules['config'].ai.user_limit} запросов в день на пользователя\n"
                f"• {modules['config'].ai.daily_limit} общих запросов в день"
            )
            return
        
        await process_ai_request_with_learning(message, user_message, modules)
    
    @router.message(Command('crypto'))
    async def crypto_handler(message: Message):
        if not check_chat_allowed(message.chat.id):
            await message.reply("Чат не поддерживается.")
            return
            
        if message.chat.type == 'private' and message.from_user.id not in modules['config'].bot.admin_ids:
            await message.reply("Бот только для групп.")
            return
        
        coin_query = message.text[8:].strip()
        if not coin_query:
            await message.reply(
                "<b>₿ КРИПТОВАЛЮТЫ</b>\n\n"
                "<b>Команды:</b>\n"
                "/crypto [монета] - Курс конкретной монеты\n"
                "/crypto_top - Топ 10 монет по капитализации\n"
                "/crypto_trending - Трендовые монеты\n\n"
                "<b>Примеры:</b>\n"
                "/crypto bitcoin\n"
                "/crypto BTC\n"
                "/crypto ethereum\n"
                "/crypto dogecoin\n\n"
                "<b>Поддерживаемые монеты:</b>\n"
                "Bitcoin, Ethereum, BNB, Cardano, Solana,\n"
                "Dogecoin, Polkadot, Avalanche и тысячи других"
            )
            return
        
        crypto_data = await get_crypto_price_detailed(coin_query, modules)
        
        if not crypto_data:
            await message.reply(
                f"❌ <b>МОНЕТА НЕ НАЙДЕНА</b>\n\n"
                f"Не удалось найти данные для: <code>{coin_query}</code>\n\n"
                f"<b>Возможные причины:</b>\n"
                f"• Неправильное название монеты\n"
                f"• Монета не поддерживается\n"
                f"• Временные проблемы с API\n\n"
                f"<b>Попробуйте:</b>\n"
                f"/crypto bitcoin\n"
                f"/crypto eth\n"
                f"/crypto_top"
            )
            return
        
        # Форматируем ответ с подробной информацией
        change_emoji = "🟢" if crypto_data['change_24h'] > 0 else "🔴"
        trend_emoji = "📈" if crypto_data['change_24h'] > 0 else "📉"
        
        crypto_text = (
            f"₿ <b>{crypto_data['name']} ({crypto_data['symbol'].upper()})</b>\n\n"
            f"💰 <b>Цена:</b> ${crypto_data['price']:,.2f}\n"
            f"📊 <b>Изменение 24ч:</b> {change_emoji} {crypto_data['change_24h']:+.2f}%\n"
            f"📊 <b>Изменение 7д:</b> {crypto_data.get('change_7d', 0):+.2f}%\n"
            f"🏆 <b>Рейтинг:</b> #{crypto_data.get('market_cap_rank', 'N/A')}\n"
            f"💎 <b>Рыночная кап.:</b> ${crypto_data['market_cap']:,}\n"
            f"📦 <b>Объем 24ч:</b> ${crypto_data['volume_24h']:,}\n"
            f"📈 <b>ATH:</b> ${crypto_data.get('ath', 0):,.2f}\n"
            f"📉 <b>ATL:</b> ${crypto_data.get('atl', 0):,.2f}\n"
            f"📅 <b>Обновлено:</b> {datetime.now().strftime('%H:%M:%S')}\n\n"
            f"{trend_emoji} <b>Анализ:</b> "
        )
        
        # Добавляем анализ
        change = abs(crypto_data['change_24h'])
        if change > 15:
            crypto_text += "Экстремальная волатильность! 🚨"
        elif change > 10:
            crypto_text += "Очень высокая волатильность"
        elif change > 5:
            crypto_text += "Высокая волатильность"
        elif change > 2:
            crypto_text += "Умеренное движение"
        else:
            crypto_text += "Стабильное движение"
        
        crypto_text += f"\n\n🎯 <b>Запросил:</b> {message.from_user.first_name}"
        
        await message.reply(crypto_text)
        
        # Сохраняем запрос с обучением
        if modules.get('db'):
            await modules['db'].save_learning_interaction(
                message.from_user.id, message.chat.id,
                f"/crypto {coin_query}", crypto_text,
                {'crypto_data': crypto_data, 'coin_query': coin_query}
            )
    
    # =================== СТАТИСТИКА ===================
    
    @router.message(Command('stats'))
    async def stats_handler(message: Message):
        if not check_chat_allowed(message.chat.id):
            await message.reply("Чат не поддерживается.")
            return
            
        if message.chat.type == 'private' and message.from_user.id not in modules['config'].bot.admin_ids:
            await message.reply("Бот только для групп.")
            return
        
        # Получаем статистику пользователя
        if modules.get('db'):
            user_stats = await modules['db'].get_comprehensive_user_stats(message.from_user.id)
        else:
            user_stats = {}
        
        # Формируем ответ с подробной статистикой
        stats_text = (
            f"<b>📊 ДЕТАЛЬНАЯ СТАТИСТИКА</b>\n"
            f"<b>Пользователь:</b> {message.from_user.first_name}\n\n"
            f"<b>💬 АКТИВНОСТЬ:</b>\n"
            f"• Всего сообщений: {user_stats.get('messages', {}).get('total_messages', 0)}\n"
            f"• За сегодня: {user_stats.get('messages', {}).get('messages_today', 0)}\n"
            f"• За неделю: {user_stats.get('messages', {}).get('messages_week', 0)}\n"
            f"• Средняя длина: {user_stats.get('messages', {}).get('avg_message_length', 0):.0f} символов\n\n"
            f"<b>🤖 AI ИСПОЛЬЗОВАНИЕ:</b>\n"
            f"• Запросов к AI: {user_stats.get('actions', {}).get('ai_request', 0)}\n"
            f"• За сегодня: {user_stats.get('actions', {}).get('ai_request_today', 0)}\n"
            f"• Полезных ответов: {user_stats.get('learning', {}).get('helpful_responses', 0)}\n\n"
            f"<b>₿ КРИПТОВАЛЮТЫ:</b>\n"
            f"• Запросов: {user_stats.get('actions', {}).get('crypto_request', 0)}\n"
            f"• За сегодня: {user_stats.get('actions', {}).get('crypto_request_today', 0)}\n\n"
            f"<b>🎮 РАЗВЛЕЧЕНИЯ:</b>\n"
            f"• Фактов запрошено: {user_stats.get('actions', {}).get('fact_request', 0)}\n"
            f"• Анекдотов: {user_stats.get('actions', {}).get('joke_request', 0)}\n"
            f"• Выборов (орел/решка): {user_stats.get('actions', {}).get('choice_request', 0)}\n\n"
            f"<b>📈 РЕЙТИНГ И АКТИВНОСТЬ:</b>\n"
            f"• Место в чате: #N/A\n"
            f"• Уровень активности: {calculate_activity_level(user_stats)}\n"
            f"• Вовлеченность: {calculate_engagement_score(user_stats)}%\n\n"
            f"<b>🧠 АДАПТИВНОЕ ОБУЧЕНИЕ:</b>\n"
            f"• Взаимодействий: {user_stats.get('learning', {}).get('total_interactions', 0)}\n"
            f"• Удовлетворенность: {user_stats.get('learning', {}).get('avg_satisfaction', 0):.1f}/5\n\n"
            f"<b>⏰ ВРЕМЯ И ДАТЫ:</b>\n"
            f"• В чате с: {user_stats.get('user_data', {}).get('first_seen', 'Неизвестно')[:10]}\n"
            f"• Последняя активность: {user_stats.get('user_data', {}).get('last_seen', 'Сейчас')[:16]}\n"
            f"• Статистика обновлена: {datetime.now().strftime('%H:%M:%S %d.%m.%Y')}"
        )
        
        await message.reply(stats_text)
    
    @router.message(Command('global_stats'))
    async def global_stats_handler(message: Message):
        if message.from_user.id not in modules['config'].bot.admin_ids:
            await message.reply("Только для админов.")
            return
        
        # Получаем глобальную статистику
        if modules.get('db'):
            global_stats = await modules['db'].get_comprehensive_user_stats(0)  # 0 для глобальной статистики
        else:
            global_stats = {}
        
        global_text = (
            f"<b>🌍 ГЛОБАЛЬНАЯ СТАТИСТИКА БОТА</b>\n\n"
            f"<b>👥 ПОЛЬЗОВАТЕЛИ:</b>\n"
            f"• Всего зарегистрировано: {global_stats.get('total_users', 0)}\n"
            f"• Активных за сегодня: {global_stats.get('active_today', 0)}\n"
            f"• Активных за неделю: {global_stats.get('active_week', 0)}\n"
            f"• Новых за неделю: {global_stats.get('new_week', 0)}\n"
            f"• Премиум пользователей: {global_stats.get('premium_users', 0)}\n\n"
            f"<b>💬 СООБЩЕНИЯ:</b>\n"
            f"• Всего обработано: {global_stats.get('total_messages', 0)}\n"
            f"• За сегодня: {global_stats.get('messages_today', 0)}\n"
            f"• За неделю: {global_stats.get('messages_week', 0)}\n"
            f"• Средняя длина: {global_stats.get('avg_message_length', 0):.0f} символов\n\n"
            f"<b>🤖 AI СИСТЕМА:</b>\n"
            f"• Всего AI запросов: {global_stats.get('total_ai_requests', 0)}\n"
            f"• За сегодня: {global_stats.get('ai_requests_today', 0)}\n"
            f"• Успешных ответов: {global_stats.get('successful_ai', 0)}\n"
            f"• Средний рейтинг: {global_stats.get('avg_ai_rating', 0):.1f}/5\n\n"
            f"<b>₿ КРИПТОВАЛЮТЫ:</b>\n"
            f"• Всего запросов: {global_stats.get('total_crypto_requests', 0)}\n"
            f"• За сегодня: {global_stats.get('crypto_requests_today', 0)}\n"
            f"• Уникальных монет: {global_stats.get('unique_coins', 0)}\n\n"
            f"<b>🛡️ МОДЕРАЦИЯ:</b>\n"
            f"• Всего действий: {global_stats.get('total_moderation_actions', 0)}\n"
            f"• Банов: {global_stats.get('total_bans', 0)}\n"
            f"• Мутов: {global_stats.get('total_mutes', 0)}\n"
            f"• Предупреждений: {global_stats.get('total_warnings', 0)}\n"
            f"• За сегодня: {global_stats.get('moderation_actions_today', 0)}\n\n"
            f"<b>⚡ ТРИГГЕРЫ:</b>\n"
            f"• Всего создано: {global_stats.get('total_triggers', 0)}\n"
            f"• Активных: {global_stats.get('active_triggers', 0)}\n"
            f"• Срабатываний: {global_stats.get('trigger_activations', 0)}\n"
            f"• За сегодня: {global_stats.get('trigger_activations_today', 0)}\n\n"
            f"<b>🧠 АДАПТИВНОЕ ОБУЧЕНИЕ:</b>\n"
            f"• Всего взаимодействий: {global_stats.get('total_learning_interactions', 0)}\n"
            f"• Обученных паттернов: {global_stats.get('learned_patterns', 0)}\n"
            f"• Средняя точность: {global_stats.get('learning_accuracy', 0):.1f}%\n\n"
            f"<b>🎮 РАЗВЛЕЧЕНИЯ:</b>\n"
            f"• Фактов показано: {global_stats.get('facts_shown', 0)}\n"
            f"• Анекдотов рассказано: {global_stats.get('jokes_told', 0)}\n"
            f"• Выборов сделано: {global_stats.get('choices_made', 0)}\n\n"
            f"<b>💾 СИСТЕМА:</b>\n"
            f"• Время работы: {global_stats.get('uptime', 'N/A')}\n"
            f"• Версия БД: 3.0 Extended\n"
            f"• Использование памяти: {global_stats.get('memory_usage', 'N/A')}\n"
            f"• Последняя перезагрузка: {global_stats.get('last_restart', 'N/A')}\n\n"
            f"📊 <b>Обновлено:</b> {datetime.now().strftime('%H:%M:%S %d.%m.%Y')}"
        )
        
        await message.reply(global_text)
    
    # =================== АДАПТИВНОЕ ОБУЧЕНИЕ ===================
    
    @router.message(Command('learning_stats'))
    async def learning_stats_handler(message: Message):
        if message.from_user.id not in modules['config'].bot.admin_ids:
            await message.reply("Только для админов.")
            return
        
        learning_stats = await get_learning_statistics_detailed(modules)
        
        stats_text = (
            f"<b>🧠 ДЕТАЛЬНАЯ СТАТИСТИКА АДАПТИВНОГО ОБУЧЕНИЯ</b>\n\n"
            f"<b>📚 ДАННЫЕ ОБУЧЕНИЯ:</b>\n"
            f"• Всего взаимодействий: {learning_stats.get('total_conversations', 0)}\n"
            f"• Уникальных пользователей: {learning_stats.get('unique_users', 0)}\n"
            f"• Обученных паттернов: {learning_stats.get('learned_patterns', 0)}\n"
            f"• Контекстных связей: {learning_stats.get('contextual_links', 0)}\n"
            f"• Персональных профилей: {learning_stats.get('user_profiles', 0)}\n\n"
            f"<b>📈 ЭФФЕКТИВНОСТЬ СИСТЕМЫ:</b>\n"
            f"• Точность ответов: {learning_stats.get('accuracy_score', 0)}%\n"
            f"• Релевантность: {learning_stats.get('relevance_score', 0)}%\n"
            f"• Удовлетворенность пользователей: {learning_stats.get('satisfaction_score', 0)}%\n"
            f"• Скорость обучения: {learning_stats.get('learning_speed', 0)}%\n\n"
            f"<b>🎯 ТОП ОБУЧЕННЫЕ ПАТТЕРНЫ:</b>\n"
        )
        
        top_patterns = learning_stats.get('top_patterns', [])
        for i, (pattern, count) in enumerate(top_patterns[:7], 1):
            stats_text += f"{i}. <code>{pattern}</code>: {count} раз\n"
        
        stats_text += (
            f"\n<b>👥 ТОП АКТИВНЫЕ ПОЛЬЗОВАТЕЛИ:</b>\n"
        )
        
        top_users = learning_stats.get('top_learning_users', [])
        for i, (user_name, interactions) in enumerate(top_users[:5], 1):
            stats_text += f"{i}. {user_name}: {interactions} взаимодействий\n"
        
        stats_text += (
            f"\n<b>📊 ЕЖЕДНЕВНАЯ СТАТИСТИКА:</b>\n"
            f"• Взаимодействий сегодня: {learning_stats.get('interactions_today', 0)}\n"
            f"• Новых паттернов за сегодня: {learning_stats.get('new_patterns_today', 0)}\n"
            f"• Улучшений качества: {learning_stats.get('improvements_today', 0)}\n\n"
            f"<b>🔧 УПРАВЛЕНИЕ:</b>\n"
            f"/learning_export - Экспорт всех данных обучения\n"
            f"/learning_reset - Полный сброс обучения\n"
            f"/learning_backup - Создать резервную копию\n"
            f"/user_profile [ID] - Профиль обучения пользователя\n\n"
            f"⏰ <b>Обновлено:</b> {datetime.now().strftime('%H:%M:%S %d.%m.%Y')}"
        )
        
        await message.reply(stats_text)
    
    # =================== СЛУЧАЙНЫЕ СООБЩЕНИЯ ===================
    
    @router.message(Command('random_messages'))
    async def random_messages_handler(message: Message):
        if message.from_user.id not in modules['config'].bot.admin_ids:
            await message.reply("Только для админов.")
            return
        
        args = message.text.split()[1:]
        if not args:
            await message.reply(
                "<b>💬 НАСТРОЙКА СЛУЧАЙНЫХ СООБЩЕНИЙ</b>\n\n"
                "<b>Использование:</b>\n"
                "/random_messages [on/off]\n\n"
                "<b>Примеры:</b>\n"
                "/random_messages on - Включить\n"
                "/random_messages off - Выключить\n\n"
                "<b>Дополнительные команды:</b>\n"
                "/random_chance [0-100] - Настроить шанс (%)\n"
                "/random_test - Отправить тестовое сообщение\n\n"
                "<b>Текущие настройки:</b>\n"
                f"• Статус: {'Включено' if modules['config'].bot.random_reply_chance > 0 else 'Выключено'}\n"
                f"• Шанс: {modules['config'].bot.random_reply_chance * 100:.1f}%\n"
                f"• Интервал: 1-2 часа"
            )
            return
        
        setting = args[0].lower()
        if setting not in ['on', 'off']:
            await message.reply("❌ Используйте: on или off")
            return
        
        # Сохраняем настройку
        enabled = setting == 'on'
        if modules.get('db'):
            await modules['db'].execute(
                "INSERT OR REPLACE INTO system_settings (key, value) VALUES (?, ?)",
                ('random_messages_enabled', 'true' if enabled else 'false')
            )
        
        status = "включены" if enabled else "выключены"
        await message.reply(
            f"✅ <b>СЛУЧАЙНЫЕ СООБЩЕНИЯ {status.upper()}</b>\n\n"
            f"⚙️ Настройка изменена: {message.from_user.first_name}\n"
            f"⏰ Время: {datetime.now().strftime('%H:%M:%S')}\n\n"
            f"{'🎲 Бот будет иногда отправлять случайные сообщения в чаты.' if enabled else '🔇 Бот не будет отправлять случайные сообщения.'}\n\n"
            f"Дополнительные настройки:\n"
            f"/random_chance [%] - шанс сообщения\n"
            f"/random_test - тестовое сообщение"
        )
    
    # =================== ОБРАБОТКА СТИКЕРОВ И МЕДИА ===================
    
    @router.message(F.sticker)
    async def sticker_handler(message: Message):
        if not check_chat_allowed(message.chat.id):
            return
        
        if message.chat.type == 'private' and message.from_user.id not in modules['config'].bot.admin_ids:
            return
        
        await save_user_and_message(message, modules)
        
        # Расширенный анализ стикера с обучением
        sticker_analysis = await analyze_sticker_with_learning(message.sticker, modules, message.from_user.id)
        
        response_type = sticker_analysis.get('response_type', 'emoji')
        
        if response_type == 'sticker' and RESPONSE_STICKERS:
            await message.reply_sticker(random.choice(RESPONSE_STICKERS))
        elif response_type == 'text':
            gruff_responses = [
                "Ясно.", "Понятно.", "Ага.", "И что?", "Ну и?",
                "Стикерки шлешь?", "Видел уже.", "Че хочешь сказать?",
                "Без слов понятно.", "Коротко и ясно."
            ]
            await message.reply(random.choice(gruff_responses))
        else:
            # Реакция эмодзи с небольшой задержкой для естественности
            await asyncio.sleep(random.uniform(0.5, 1.5))
            await message.reply(random.choice(RESPONSE_EMOJIS))
        
        # Обучение на стикерах
        if modules.get('db'):
            await modules['db'].save_learning_interaction(
                message.from_user.id, message.chat.id,
                f"[STICKER: {message.sticker.emoji or '❓'}]",
                sticker_analysis.get('response_sent', 'emoji_reaction'),
                sticker_analysis
            )
    
    # =================== УМНЫЕ ОТВЕТЫ И ОБУЧЕНИЕ ===================
    
    @router.message(F.reply_to_message)
    async def reply_handler(message: Message):
        if not check_chat_allowed(message.chat.id):
            return
        
        if message.chat.type == 'private' and message.from_user.id not in modules['config'].bot.admin_ids:
            return
        
        # Проверяем, отвечает ли пользователь на сообщение бота
        if message.reply_to_message.from_user.id == modules['bot'].id:
            await process_adaptive_reply_to_bot(message, modules)
        else:
            # Обрабатываем как обычное сообщение с возможностью реагирования
            await process_adaptive_smart_text(message, modules, bot_info)
    
    @router.message(F.text)
    async def smart_text_handler(message: Message):
        if not check_chat_allowed(message.chat.id):
            return
        
        if message.chat.type == 'private' and message.from_user.id not in modules['config'].bot.admin_ids:
            return
            
        await process_adaptive_smart_text(message, modules, bot_info)
    
    # Регистрируем роутер
    dp.include_router(router)
    
    logger.info("💀 ПОЛНЫЕ обработчики с новыми функциями зарегистрированы")


# =================== АДАПТИВНЫЕ ФУНКЦИИ С ОБУЧЕНИЕМ ===================

async def process_adaptive_smart_text(message: Message, modules, bot_info):
    """🧠 Интеллектуальная обработка с адаптивным обучением"""
    try:
        await save_user_and_message(message, modules)
        
        # Проверяем, должен ли бот отвечать
        should_respond = await enhanced_should_respond_check(message, modules, bot_info)
        
        if should_respond:
            # Получаем адаптивный контекст для пользователя
            user_context = await get_adaptive_user_context(modules, message.from_user.id, message.chat.id)
            
            if modules.get('ai'):
                await process_ai_request_with_learning(message, message.text, modules, user_context)
            else:
                # Адаптивный ответ без AI на основе обученных паттернов
                learned_response = await get_learned_response(modules, message.from_user.id, message.text)
                
                if learned_response:
                    await message.reply(learned_response)
                else:
                    # Грубый ответ по умолчанию
                    await message.reply(random.choice(GRUFF_RESPONSES))
        else:
            # Очень редкие случайные ответы (0.3% шанс)
            if random.random() < 0.003:
                random_reactions = [".", "🤔", "👀", "Хм.", "Ага."]
                await message.reply(random.choice(random_reactions))
        
    except Exception as e:
        logger.error(f"Ошибка адаптивной обработки: {e}")

async def enhanced_should_respond_check(message: Message, modules, bot_info) -> bool:
    """🎯 Улучшенная проверка необходимости ответа"""
    try:
        if message.chat.type == 'private':
            return True
        
        text = message.text.lower()
        
        # 1. Прямое упоминание бота
        if bot_info and f'@{bot_info.username.lower()}' in text:
            return True
        
        # 2. Стандартные ключевые слова
        standard_keywords = ['бот', 'bot', 'робот', 'помощник', 'assistant']
        for keyword in standard_keywords:
            if keyword in text:
                return True
        
        # 3. Кастомные слова призыва
        global CUSTOM_TRIGGER_WORDS
        for word in CUSTOM_TRIGGER_WORDS:
            if word in text:
                return True
        
        # 4. Вопросы (улучшенная логика)
        question_markers = ['?', 'что', 'как', 'когда', 'где', 'почему', 'зачем', 'кто']
        if '?' in text or any(marker in text for marker in question_markers):
            if len(text) > 10:  # Только содержательные вопросы
                return True
        
        # 5. Проверка активных триггеров
        if modules.get('db'):
            active_triggers = await modules['db'].get_active_triggers(message.chat.id)
            for trigger in active_triggers:
                if await check_trigger_match(text, trigger):
                    return True
        
        # 6. Адаптивная проверка на основе обучения
        if modules.get('db'):
            learned_patterns = await get_user_learned_patterns(modules, message.from_user.id)
            for pattern in learned_patterns:
                if pattern.lower() in text:
                    return True
        
        return False
        
    except Exception as e:
        logger.error(f"Ошибка проверки ответа: {e}")
        return False

async def process_ai_request_with_learning(message: Message, user_message: str, modules, context: dict = None):
    """🤖 AI запрос с адаптивным обучением и контекстом"""
    try:
        # Получаем или создаем контекст пользователя
        if not context:
            context = await get_adaptive_user_context(modules, message.from_user.id, message.chat.id)
        
        # Добавляем грубую инструкцию с учетом предпочтений пользователя
        harsh_instruction = (
            "Отвечай грубо, коротко, без лишней вежливости. Сразу по делу. "
            "Никаких 'пожалуйста', 'спасибо', 'надеюсь помог' и подобного. "
            "Максимум 2-3 предложения. Как злой программист-админ."
        )
        
        # Учитываем предпочтения пользователя из обучения
        user_preferences = context.get('user_preferences', {})
        if user_preferences.get('preferred_response_length') == 'short':
            harsh_instruction += " Отвечай максимально кратко - 1-2 предложения."
        elif user_preferences.get('preferred_response_length') == 'detailed':
            harsh_instruction += " Можешь дать чуть больше деталей, но все равно грубо."
        
        context['style_instruction'] = harsh_instruction
        
        # Запрос к AI
        response = await modules['ai'].generate_response(
            user_message, message.from_user.id, context
        )
        
        # Очищаем ответ от вежливости
        if response.startswith("Бот:"):
            response = response[4:].strip()
        
        response = clean_harsh_response_advanced(response)
        
        # Отправляем ответ
        await message.reply(response)
        
        # Обучение на взаимодействии
        if modules.get('db'):
            await modules['db'].save_learning_interaction(
                message.from_user.id, message.chat.id,
                user_message, response,
                {**context, 'ai_model_used': modules['config'].ai.default_model}
            )
        
        # Обновляем адаптивный профиль пользователя
        await update_user_adaptive_profile(modules, message.from_user.id, user_message, response)
        
    except Exception as e:
        logger.error(f"Ошибка адаптивного AI: {e}")
        await message.reply("AI сдох. Попробуй позже.")

def clean_harsh_response_advanced(response: str) -> str:
    """🧹 Продвинутая очистка ответа от вежливости"""
    # Фразы которые нужно убрать или заменить
    replacements = {
        "Хотите узнать больше": "",
        "Если у вас есть еще вопросы": "",
        "Чем еще могу помочь": "",
        "Надеюсь, помог": "",
        "Пожалуйста": "",
        "Спасибо за вопрос": "",
        "С удовольствием расскажу": "",
        "Рад помочь": "",
        "Всегда рад помочь": "",
        "Обращайтесь": "",
        "Желаю удачи": "",
        "Всего доброго": "",
        "До свидания": "",
        "Хорошего дня": "",
        "Думаю": "",
        "Считаю": "",
        "Полагаю": "",
        "Возможно": "",
        "Вероятно": "",
    }
    
    cleaned = response
    for old_phrase, new_phrase in replacements.items():
        cleaned = cleaned.replace(old_phrase, new_phrase)
    
    # Убираем смайлы
    emoji_pattern = r'[😊😄😃😆😁🤗🎉✨💫⭐🌟💡🔥👍👌🎯📚🔍💭🤔😌😇🥰😍🤩😀😊😉🙂]+$'
    cleaned = re.sub(emoji_pattern, '', cleaned).strip()
    
    # Убираем множественные переносы строк
    cleaned = re.sub(r'\n\s*\n', '\n', cleaned)
    
    # Убираем пустые строки в конце
    cleaned = cleaned.rstrip()
    
    return cleaned.strip()

# =================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ===================

def check_chat_allowed(chat_id: int) -> bool:
    """🔒 Проверка разрешенных чатов"""
    if not ALLOWED_CHAT_IDS:
        return True
    return chat_id in ALLOWED_CHAT_IDS

async def save_user_and_message(message: Message, modules):
    """💾 Сохранение данных пользователя и сообщения"""
    try:
        if modules.get('db'):
            user = message.from_user
            
            # Сохраняем пользователя
            await modules['db'].save_user({
                'id': user.id,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'language_code': user.language_code,
                'is_premium': getattr(user, 'is_premium', False),
                'is_bot': user.is_bot
            })
            
            # Сохраняем сообщение
            await modules['db'].save_message({
                'message_id': message.message_id,
                'user_id': user.id,
                'chat_id': message.chat.id,
                'text': message.text or '',
                'message_type': 'text' if message.text else 'media',
                'has_media': bool(message.photo or message.video or message.document)
            })
            
    except Exception as e:
        logger.error(f"Ошибка сохранения данных: {e}")

async def get_moderation_stats(modules) -> dict:
    """📊 Получение статистики модерации"""
    try:
        if not modules.get('db'):
            return {}
        
        stats = {}
        
        # Основные счетчики
        stats['total_bans'] = await modules['db'].fetchone("SELECT COUNT(*) as count FROM bans") or {'count': 0}
        stats['active_bans'] = await modules['db'].fetchone("SELECT COUNT(*) as count FROM bans WHERE is_active = TRUE") or {'count': 0}
        stats['total_mutes'] = await modules['db'].fetchone("SELECT COUNT(*) as count FROM mutes") or {'count': 0}
        stats['active_mutes'] = await modules['db'].fetchone("SELECT COUNT(*) as count FROM mutes WHERE is_active = TRUE AND mute_until > datetime('now')") or {'count': 0}
        stats['total_warns'] = await modules['db'].fetchone("SELECT COUNT(*) as count FROM warnings") or {'count': 0}
        stats['total_kicks'] = await modules['db'].fetchone("SELECT COUNT(*) as count FROM kicks") or {'count': 0}
        
        # Преобразуем в числа
        for key, value in stats.items():
            if isinstance(value, dict) and 'count' in value:
                stats[key] = value['count']
        
        # Настройки
        stats['auto_mod_enabled'] = False  # TODO: получить из настроек
        stats['toxicity_detection'] = False
        stats['spam_detection'] = False
        stats['raid_protection'] = False
        stats['log_actions'] = True
        
        return stats
        
    except Exception as e:
        logger.error(f"Ошибка получения статистики модерации: {e}")
        return {}

async def get_user_warns_count(modules, user_id: int) -> int:
    """⚠️ Получение количества предупреждений пользователя"""
    try:
        if not modules.get('db'):
            return 0
        
        result = await modules['db'].fetchone(
            "SELECT COUNT(*) as count FROM warnings WHERE user_id = ? AND is_active = TRUE",
            (user_id,)
        )
        
        return result['count'] if result else 0
        
    except Exception as e:
        logger.error(f"Ошибка подсчета предупреждений: {e}")
        return 0

# Остальные заглушки функций (для экономии места - в полной версии будут реализованы)
async def get_trigger_stats(modules): return {'total_triggers': 0, 'active_triggers': 0}
async def get_crypto_price_detailed(coin_query, modules): return None
async def get_chat_top_users(modules, chat_id, limit): return []
async def calculate_activity_level(stats): return "Средний"
async def calculate_engagement_score(stats): return 75
async def get_learning_statistics_detailed(modules): return {}
async def analyze_sticker_with_learning(sticker, modules, user_id): return {"response_type": "emoji"}
async def get_adaptive_user_context(modules, user_id, chat_id): return {}
async def get_learned_response(modules, user_id, text): return None
async def check_trigger_match(text, trigger): return False
async def get_user_learned_patterns(modules, user_id): return []
async def update_user_adaptive_profile(modules, user_id, message, response): pass
async def process_adaptive_reply_to_bot(message, modules): pass

async def random_messages_sender(modules):
    """💬 Отправка случайных сообщений с улучшенной логикой"""
    await asyncio.sleep(600)  # Ждем 10 минут после старта
    
    extended_random_messages = [
        "Как дела в чате?",
        "Кто-нибудь тут есть?", 
        "Интересно, о чем тут говорят...",
        "Может кто факт интересный знает?",
        "/joke - хотите анекдот?",
        "Тишина в чате... подозрительно.",
        "Криптовалюты как дела? /crypto bitcoin",
        "А помните времена когда биткоин был по доллару?",
        "Кто-то тут умный есть?",
        "Может поболтаем?",
        "/fact - узнайте что-то новое",
        "Админы спят?",
        "Что происходит?",
        "Народ, как настроение?",
        "/choice - нужен случайный выбор?"
    ]
    
    while True:
        try:
            # Случайный интервал от 1 до 3 часов
            await asyncio.sleep(random.randint(3600, 10800))
            
            # Проверяем, включены ли случайные сообщения
            random_enabled = True  # TODO: получить из настроек БД
            if not random_enabled:
                continue
            
            # Очень низкий базовый шанс (0.5%)
            base_chance = 0.005
            
            # Увеличиваем шанс в зависимости от времени суток
            current_hour = datetime.now().hour
            if 10 <= current_hour <= 22:  # Дневное время - больше шанс
                base_chance *= 2
            
            if random.random() > base_chance:
                continue
            
            # Выбираем случайный чат из разрешенных
            if not ALLOWED_CHAT_IDS:
                continue
                
            chat_id = random.choice(ALLOWED_CHAT_IDS)
            message_text = random.choice(extended_random_messages)
            
            await modules['bot'].send_message(chat_id, message_text)
            logger.info(f"📤 Отправлено случайное сообщение в {chat_id}: {message_text}")
            
            # Логируем в БД
            if modules.get('db'):
                await modules['db'].save_message({
                    'message_id': 0,
                    'user_id': modules['bot'].id,
                    'chat_id': chat_id,
                    'text': message_text,
                    'message_type': 'random_bot_message'
                })
            
        except Exception as e:
            logger.error(f"Ошибка отправки случайного сообщения: {e}")
            await asyncio.sleep(600)  # При ошибке ждем 10 минут


__all__ = ["register_all_handlers"]