#!/usr/bin/env python3
"""
🧠 AI ИНТЕГРАЦИЯ С ПЕРСОНАЖАМИ v3.2
🚀 Логика использования персонажей в AI ответах

НОВОЕ В v3.2:
• Персонажи работают только в группах
• Обычные пользователи в ЛС получают отказ
• Интеграция с основными обработчиками
"""

import logging
from aiogram.types import Message

logger = logging.getLogger(__name__)

async def process_ai_request_with_personality(message: Message, modules: dict) -> bool:
    """🎭 Обработка AI запроса с учетом персонажей"""
    
    personality_manager = modules.get('custom_personality_manager')
    ai_service = modules.get('ai') or modules.get('human_ai')
    
    if not personality_manager or not ai_service:
        return False
    
    # Проверяем есть ли активный персонаж
    personality = await personality_manager.get_active_personality(message.chat.id)
    
    if personality:
        try:
            # Генерируем ответ в роли персонажа
            response = await ai_service.generate_response(
                message.text,
                system_prompt=personality['system_prompt'],
                max_tokens=500,
                temperature=0.8  # Больше креативности для персонажа
            )
            
            if response:
                # Добавляем индикатор персонажа
                persona_response = f"🎭 **{personality['name']}:**\n{response}"
                await message.reply(persona_response)
                
                logger.info(f"🎭 Ответ персонажа: {personality['name']} в чате {message.chat.id}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Ошибка генерации ответа персонажа: {e}")
    
    return False

async def handle_personality_access_denied(message: Message, modules: dict):
    """🚫 Обработка отказа в доступе к персонажам"""
    
    # Проверяем является ли это личный чат
    if message.chat.id > 0:  # Личный чат
        # Проверяем является ли пользователь админом
        is_admin = message.from_user.id in modules['config'].bot.admin_ids
        
        if not is_admin:
            # Обычный пользователь в ЛС - отказываем в AI ответах с персонажами
            await message.reply(
                "🤖 **Я работаю по-разному в группах и личных чатах**\n\n"
                "📍 **В личных чатах:** Базовые функции\n"
                "🌍 **В групповых чатах:** Полный функционал + персонажи\n\n"
                "💡 **Совет:** Добавьте меня в группу для полного функционала!"
            )
            return True
    
    return False

# Интеграция в основной AI обработчик
async def enhanced_ai_handler(message: Message, modules: dict):
    """🧠 Улучшенный AI обработчик с поддержкой персонажей v3.2"""
    
    # Сначала проверяем персонажи
    personality_used = await process_ai_request_with_personality(message, modules)
    if personality_used:
        return  # Персонаж ответил, больше ничего не нужно
    
    # Проверяем доступ для обычных пользователей в ЛС
    access_denied = await handle_personality_access_denied(message, modules)
    if access_denied:
        return  # Отказ обработан
    
    # Обычный AI ответ (если персонаж не активен)
    ai_service = modules.get('ai') or modules.get('human_ai')
    if ai_service:
        try:
            response = await ai_service.generate_response(
                message.text,
                max_tokens=300,
                temperature=0.7
            )
            
            if response:
                await message.reply(f"🤖 {response}")
                
        except Exception as e:
            logger.error(f"❌ Ошибка AI ответа: {e}")
            await message.reply("❌ Произошла ошибка при генерации ответа")

# Функция для интеграции в handlers_v3_fixed.py
def integrate_personality_ai_logic(router, modules):
    """🔧 Интеграция логики персонажей в AI обработчики"""
    
    # Пример интеграции в обработчик AI команд
    @router.message(Command("ai"))
    async def cmd_ai_with_personality(message: Message):
        """🧠 Команда /ai с поддержкой персонажей"""
        
        # Получаем вопрос
        command_args = message.text.split(' ', 1)
        if len(command_args) < 2:
            await message.reply(
                "🧠 **Команда /ai**\n\n"
                "**Использование:** `/ai ваш вопрос`\n\n"
                "**Пример:** `/ai расскажи о программировании`\n\n"
                "🎭 **Персонажи:** Если установлен персонаж, отвечу в его роли"
            )
            return
        
        question = command_args[1].strip()
        
        # Обрабатываем с учетом персонажей
        await enhanced_ai_handler(message, modules)
    
    logger.info("🔧 Интеграция персонажей в AI логику завершена")