#!/usr/bin/env python3
"""
🎭 CUSTOM PERSONALITY SYSTEM v3.2 - ТОЛЬКО ГРУППЫ И АДМИНЫ
🚀 Система произвольных персонажей с жестким контролем доступа

НОВОЕ В v3.2:
• Персонажи работают ТОЛЬКО в групповых чатах
• В группах персонажа может установить только админ бота
• В личных чатах обычные пользователи получают отказ
• Админы могут тестировать персонажи в личных чатах
"""

import asyncio
import logging
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import aiosqlite

logger = logging.getLogger(__name__)

class CustomPersonalityManager:
    """🎭 Менеджер произвольных персонажей"""
    
    def __init__(self, db_service, config, ai_service=None):
        self.db = db_service
        self.config = config
        self.ai_service = ai_service
        
        # Кэш активных персонажей
        self.active_personalities = {}
        
        # Ограничения
        self.max_personality_length = 500
        self.groups_only = True  # НОВОЕ: только группы
        self.admin_exception = True  # НОВОЕ: исключение для админов
        
        logger.info("🎭 CustomPersonalityManager v3.2 инициализирован (только группы)")
    
    async def initialize(self):
        """🚀 Инициализация системы"""
        try:
            # Создаем таблицы для персонажей
            await self._create_tables()
            
            # Загружаем активные персонажи в кэш
            await self._load_active_personalities()
            
            logger.info("✅ Система персонажей v3.2 инициализирована")
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации персонажей: {e}")
            raise
    
    async def _create_tables(self):
        """📋 Создание таблиц для персонажей"""
        try:
            # Таблица персонажей - оптимизирована для групп
            await self.db.execute("""
                CREATE TABLE IF NOT EXISTS custom_personalities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL,
                    admin_id INTEGER NOT NULL,
                    personality_name TEXT NOT NULL,
                    personality_description TEXT NOT NULL,
                    system_prompt TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT FALSE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Индексы для быстрого поиска
            await self.db.execute("""
                CREATE INDEX IF NOT EXISTS idx_personalities_chat_active 
                ON custom_personalities(chat_id, is_active)
            """)
            
            await self.db.execute("""
                CREATE INDEX IF NOT EXISTS idx_personalities_admin 
                ON custom_personalities(admin_id, chat_id)
            """)
            
            logger.info("📋 Таблицы персонажей созданы (v3.2)")
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания таблиц персонажей: {e}")
            raise
    
    async def _load_active_personalities(self):
        """💾 Загрузка активных персонажей в кэш"""
        try:
            # Загружаем все активные персонажи
            results = await self.db.fetch_all("""
                SELECT chat_id, admin_id, personality_name, personality_description, 
                       system_prompt
                FROM custom_personalities 
                WHERE is_active = TRUE
            """)
            
            for row in results:
                chat_id = row['chat_id']
                
                personality_data = {
                    'id': personality_id,
                    'name': name,
                    'description': description,  # <--- Обязательно передать!
                    'system_prompt': system_prompt,
                    'chat_id': chat_id,
                    'user_id': user_id,
                    'admin_id': admin_id,
                    'created_at': datetime.utcnow().isoformat(),
                    'updated_at': datetime.utcnow().isoformat(),
                    'is_active': True,
                    'is_temporary': is_temporary,
                    'usage_count': 0,
                    'last_used': datetime.utcnow().isoformat(),
                    'is_group_personality': chat_id < 0
                }

                
                # Ключ только по chat_id (групповые персонажи)
                key = f"chat_{chat_id}"
                self.active_personalities[key] = personality_data
            
            logger.info(f"💾 Загружено {len(self.active_personalities)} активных персонажей")
            
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки персонажей: {e}")
    
    def _is_admin(self, user_id: int) -> bool:
        """👑 Проверка является ли пользователь админом бота"""
        return user_id in self.config.bot.admin_ids
    
    def _is_group_chat(self, chat_id: int) -> bool:
        """👥 Проверка является ли чат групповым"""
        return chat_id < 0
    
    async def can_use_personalities(self, user_id: int, chat_id: int) -> tuple[bool, str]:
        """🔐 НОВАЯ ЛОГИКА: Проверка доступа к системе персонажей"""
        
        # Проверяем является ли пользователь админом
        is_admin = self._is_admin(user_id)
        is_group = self._is_group_chat(chat_id)
        
        if is_admin:
            # Админы могут использовать везде (для тестирования)
            if is_group:
                return True, "Админ бота в группе - полный доступ"
            else:
                return True, "Админ бота в ЛС - тестовый режим"
        
        if is_group:
            # В группах обычные пользователи НЕ могут устанавливать персонажи
            return False, "В групповых чатах персонажа может установить только админ бота"
        else:
            # В личных чатах обычные пользователи НЕ могут использовать персонажи
            return False, "Система персонажей работает только в групповых чатах"
    
    async def set_personality(self, user_id: int, chat_id: int, description: str) -> tuple[bool, str]:
        """🎭 Установка персонажа"""
        
        # Проверяем права доступа
        can_use, access_reason = await self.can_use_personalities(user_id, chat_id)
        if not can_use:
            return False, f"🚫 {access_reason}"
        
        # Валидация описания
        if not description or len(description.strip()) < 5:
            return False, "❌ Описание персонажа слишком короткое (минимум 5 символов)"
        
        if len(description) > self.max_personality_length:
            return False, f"❌ Описание слишком длинное (максимум {self.max_personality_length} символов)"
        
        description = description.strip()
        
        try:
            # Генерируем системный промпт
            system_prompt = await self._generate_system_prompt(description)
            
            # Деактивируем предыдущий персонаж в этом чате
            await self.db.execute("""
                UPDATE custom_personalities 
                SET is_active = FALSE 
                WHERE chat_id = ?
            """, (chat_id,))
            
            # Удаляем из кэша
            cache_key = f"chat_{chat_id}"
            if cache_key in self.active_personalities:
                del self.active_personalities[cache_key]
            
            # Создаем имя персонажа из первых слов описания
            personality_name = self._extract_personality_name(description)
            
            # Сохраняем новый персонаж
            await self.db.execute("""
                INSERT INTO custom_personalities 
                (chat_id, admin_id, personality_name, personality_description, 
                 system_prompt, is_active)
                VALUES (?, ?, ?, ?, ?, TRUE)
            """, (chat_id, user_id, personality_name, description, system_prompt))
            
            # Добавляем в кэш
            personality_data = {
                'name': personality_name,
                'description': description,
                'system_prompt': system_prompt,
                'admin_id': user_id
            }
            
            self.active_personalities[cache_key] = personality_data
            
            # Формируем сообщение успеха
            if self._is_group_chat(chat_id):
                success_msg = f"🎭 Групповой персонаж установлен!\n\n"
                success_msg += f"Персонаж: {personality_name}\n"
                success_msg += f"Описание: {description}\n\n"
                success_msg += f"🎯 Теперь бот будет отвечать всем участникам в роли этого персонажа"
            else:
                success_msg = f"🎭 Тестовый персонаж установлен!\n\n"
                success_msg += f"Персонаж: {personality_name}\n"
                success_msg += f"Описание: {description}\n\n"
                success_msg += f"🧪 Режим тестирования для админа"
            
            # Логируем событие
            await self.db.track_user_action(
                user_id, chat_id, 
                "personality_set", 
                {"name": personality_name, "chat_type": "group" if self._is_group_chat(chat_id) else "private"}
            )
            
            logger.info(f"🎭 Персонаж установлен: {personality_name} в чате {chat_id}")
            
            return True, success_msg
            
        except Exception as e:
            logger.error(f"❌ Ошибка установки персонажа: {e}")
            return False, f"❌ Ошибка установки персонажа: {str(e)}"
    
    def _extract_personality_name(self, description: str) -> str:
        """📝 Извлечение имени персонажа из описания"""
        # Берем первые 3-4 значимых слова
        words = description.split()[:4]
        name = " ".join(words)
        
        # Ограничиваем длину
        if len(name) > 50:
            name = name[:47] + "..."
        
        return name
    
    async def _generate_system_prompt(self, description: str) -> str:
        """🧠 Генерация системного промпта для персонажа"""
        
        # Если есть AI сервис, используем его для генерации
        if self.ai_service:
            try:
                prompt = f"""
                Создай системный промпт для чат-бота на основе этого описания персонажа:
                "{description}"
                
                Промпт должен быть:
                - На русском языке
                - Четким и конкретным
                - Не более 200 слов
                - Включать стиль общения, манеру речи, особенности
                
                Отвечай ТОЛЬКО системным промптом без дополнительных объяснений.
                """
                
                response = await self.ai_service.generate_response(
                    prompt, 
                    max_tokens=300,
                    temperature=0.7
                )
                
                if response and len(response.strip()) > 10:
                    return response.strip()
                    
            except Exception as e:
                logger.warning(f"⚠️ Ошибка генерации промпта через AI: {e}")
        
        # Fallback - создаем базовый промпт
        return f"""Ты играешь роль персонажа с такими характеристиками: {description}

Важно:
- Полностью вживайся в эту роль
- Отвечай в характере персонажа
- Используй соответствующий стиль речи
- Будь последовательным в поведении
- Отвечай на русском языке
- Будь дружелюбным и интересным собеседником"""
    
    async def get_active_personality(self, chat_id: int) -> Optional[Dict]:
        """🎭 Получение активного персонажа для чата"""
        
        cache_key = f"chat_{chat_id}"
        return self.active_personalities.get(cache_key)
    
    async def reset_personality(self, user_id: int, chat_id: int) -> tuple[bool, str]:
        """🔄 Сброс персонажа"""
        
        # Проверяем права доступа
        can_use, access_reason = await self.can_use_personalities(user_id, chat_id)
        if not can_use:
            return False, f"🚫 {access_reason}"
        
        try:
            # Проверяем есть ли активный персонаж
            cache_key = f"chat_{chat_id}"
            if cache_key not in self.active_personalities:
                return False, "🤷‍♂️ Персонаж не установлен в этом чате"
            
            # Деактивируем персонаж
            await self.db.execute("""
                UPDATE custom_personalities 
                SET is_active = FALSE 
                WHERE chat_id = ? AND is_active = TRUE
            """, (chat_id,))
            
            # Удаляем из кэша
            del self.active_personalities[cache_key]
            
            if self._is_group_chat(chat_id):
                return True, "🔄 Групповой персонаж сброшен\n\n🤖 Бот вернулся к обычному режиму"
            else:
                return True, "🔄 Тестовый персонаж сброшен\n\n🤖 Админ-режим: обычные ответы"
            
        except Exception as e:
            logger.error(f"❌ Ошибка сброса персонажа: {e}")
            return False, f"❌ Ошибка сброса персонажа: {str(e)}"
    
    async def get_admin_personalities(self, admin_id: int) -> List[Dict]:
        """👑 Получение всех персонажей созданных админом"""
        try:
            results = await self.db.fetch_all("""
                SELECT personality_name, personality_description, chat_id,
                       is_active, created_at
                FROM custom_personalities 
                WHERE admin_id = ? 
                ORDER BY created_at DESC
                LIMIT 20
            """, (admin_id,))
            
            return results if results else []
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения персонажей админа: {e}")
            return []
    
    async def get_chat_personality_info(self, chat_id: int) -> Optional[Dict]:
        """💬 Получение информации о персонаже чата"""
        try:
            result = await self.db.fetch_one("""
                SELECT personality_name, personality_description, 
                       admin_id, created_at
                FROM custom_personalities 
                WHERE chat_id = ? AND is_active = TRUE
            """, (chat_id,))
            
            if result:
                return {
                    'name': result['personality_name'],
                    'description': result['personality_description'],
                    'admin_id': result['admin_id'],
                    'created_at': result['created_at']
                }
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения информации о персонаже: {e}")
            return None
    
    async def get_statistics(self) -> Dict:
        """📊 Статистика системы персонажей"""
        try:
            stats = {}
            
            # Общее количество персонажей
            total_result = await self.db.fetch_one("""
                SELECT COUNT(*) as count FROM custom_personalities
            """)
            stats['total_personalities'] = total_result['count'] if total_result else 0
            
            # Активные персонажи
            active_result = await self.db.fetch_one("""
                SELECT COUNT(*) as count FROM custom_personalities WHERE is_active = TRUE
            """)
            stats['active_personalities'] = active_result['count'] if active_result else 0
            
            # Групповые чаты с персонажами
            group_result = await self.db.fetch_one("""
                SELECT COUNT(*) as count FROM custom_personalities 
                WHERE is_active = TRUE AND chat_id < 0
            """)
            stats['group_chats'] = group_result['count'] if group_result else 0
            
            # Тестовые персонажи (в ЛС)
            test_result = await self.db.fetch_one("""
                SELECT COUNT(*) as count FROM custom_personalities 
                WHERE is_active = TRUE AND chat_id > 0
            """)
            stats['test_personalities'] = test_result['count'] if test_result else 0
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения статистики: {e}")
            return {}
    
    def is_personality_active(self, chat_id: int) -> bool:
        """❓ Проверка активности персонажа в чате"""
        cache_key = f"chat_{chat_id}"
        return cache_key in self.active_personalities
    
    async def cleanup_old_personalities(self, days: int = 30):
        """🧹 Очистка старых неактивных персонажей"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            await self.db.execute("""
                DELETE FROM custom_personalities 
                WHERE is_active = FALSE AND created_at < ?
            """, (cutoff_date,))
            
            logger.info(f"🧹 Очищены персонажи старше {days} дней")
            
        except Exception as e:
            logger.error(f"❌ Ошибка очистки персонажей: {e}")

# Вспомогательная функция для создания менеджера
async def create_personality_manager(db_service, config, ai_service=None) -> CustomPersonalityManager:
    """🚀 Создание и инициализация менеджера персонажей"""
    manager = CustomPersonalityManager(db_service, config, ai_service)
    await manager.initialize()
    return manager