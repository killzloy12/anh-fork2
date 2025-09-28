#!/usr/bin/env python3
"""
🎭 CUSTOM AI PERSONALITY v2.0 - Произвольное задание персонажей
🚀 Прописывай любого персонажа текстом: "/be ты крутой хакер из киберпанка"

НОВЫЕ ВОЗМОЖНОСТИ:
• Произвольное описание персонажа текстом
• Временные и постоянные персонажи
• AI-анализ описания и генерация системного промпта
• История персонажей пользователя
• Быстрая смена между персонажами
"""

import logging
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import asyncio
import openai

logger = logging.getLogger(__name__)


@dataclass
class CustomPersonality:
    """🎭 Произвольный персонаж"""
    id: str
    description: str  # Произвольное описание от пользователя
    system_prompt: str  # Сгенерированный системный промпт
    chat_id: int
    user_id: int
    created_at: datetime
    is_active: bool = True
    is_temporary: bool = False  # Временный персонаж
    usage_count: int = 0
    last_used: Optional[datetime] = None


class CustomPersonalityManager:
    """🎭 Менеджер произвольных персонажей"""
    
    def __init__(self, db_service, config, ai_service=None):
        self.db = db_service
        self.config = config
        self.ai_service = ai_service
        self.active_personalities = {}  # chat_id -> CustomPersonality
        self.user_personalities_history = {}  # user_id -> List[CustomPersonality]
        
        # Примеры для AI генерации промптов
        self.prompt_templates = {
            "personality": """Создай системный промпт для AI ассистента на основе описания: "{description}"

ТРЕБОВАНИЯ:
• Промпт должен быть на русском языке
• Максимум 300 символов
• Включи возраст, черты характера, стиль речи
• Добавь эмоциональность и живость
• Используй "Ты" обращение
• Укажи конкретные особенности поведения

ФОРМАТ ОТВЕТА:
Только системный промпт, без дополнительного текста.""",
            
            "analysis": """Проанализируй описание персонажа: "{description}"

Выдели:
1. Профессию/роль
2. Возраст (примерно)
3. Черты характера
4. Стиль общения
5. Интересы

Формат: JSON с ключами: profession, age, traits, speech_style, interests"""
        }
        
        logger.info("🎭 Менеджер произвольных персонажей инициализирован")
    
    async def initialize(self):
        """🚀 Инициализация системы"""
        await self._create_custom_personality_tables()
        await self._load_active_personalities()
        await self._load_user_histories()
        logger.info("🎭 Система произвольных персонажей загружена")
    
    async def _create_custom_personality_tables(self):
        """📋 Создание таблиц"""
        tables = [
            """
            CREATE TABLE IF NOT EXISTS custom_personalities (
                id TEXT PRIMARY KEY,
                description TEXT NOT NULL,
                system_prompt TEXT NOT NULL,
                chat_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                is_temporary BOOLEAN DEFAULT FALSE,
                usage_count INTEGER DEFAULT 0,
                last_used DATETIME
            )
            """,
            
            """
            CREATE TABLE IF NOT EXISTS personality_usage_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                personality_id TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                chat_id INTEGER NOT NULL,
                message_count INTEGER DEFAULT 1,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (personality_id) REFERENCES custom_personalities (id)
            )
            """
        ]
        
        for table_sql in tables:
            await self.db.execute(table_sql)
    
    async def create_personality_from_description(self, description: str, chat_id: int, user_id: int, is_temporary: bool = False) -> Optional[CustomPersonality]:
        """🎭 Создание персонажа из произвольного описания"""
        try:
            # Генерируем системный промпт через AI
            system_prompt = await self._generate_system_prompt(description)
            
            if not system_prompt:
                # Fallback - простой промпт
                system_prompt = f"Ты {description}. Отвечай в соответствии с этой ролью, будь живым и эмоциональным."
            
            # Создаем ID
            personality_id = f"custom_{user_id}_{int(datetime.now().timestamp())}"
            
            personality = CustomPersonality(
                id=personality_id,
                description=description,
                system_prompt=system_prompt,
                chat_id=chat_id,
                user_id=user_id,
                created_at=datetime.now(),
                is_temporary=is_temporary
            )
            
            # Сохраняем в БД
            await self.db.execute("""
                INSERT INTO custom_personalities 
                (id, description, system_prompt, chat_id, user_id, is_temporary)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                personality.id,
                personality.description,
                personality.system_prompt,
                personality.chat_id,
                personality.user_id,
                personality.is_temporary
            ))
            
            # Активируем
            self.active_personalities[chat_id] = personality
            
            # Добавляем в историю пользователя
            if user_id not in self.user_personalities_history:
                self.user_personalities_history[user_id] = []
            self.user_personalities_history[user_id].append(personality)
            
            logger.info(f"🎭 Создан персонаж: {description[:50]}... для чата {chat_id}")
            return personality
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания персонажа: {e}")
            return None
    
    async def _generate_system_prompt(self, description: str) -> Optional[str]:
        """🧠 Генерация системного промпта через AI"""
        if not self.ai_service or not hasattr(self.ai_service, 'openai_client') or not self.ai_service.openai_client:
            return None
        
        try:
            prompt = self.prompt_templates["personality"].format(description=description)
            
            response = await asyncio.to_thread(
                self.ai_service.openai_client.chat.completions.create,
                model="gpt-4o-mini",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=300
            )
            
            system_prompt = response.choices[0].message.content.strip()
            
            # Валидация и очистка
            if len(system_prompt) > 500:
                system_prompt = system_prompt[:500] + "..."
            
            logger.info(f"🧠 Сгенерирован промпт для: {description[:30]}...")
            return system_prompt
            
        except Exception as e:
            logger.error(f"❌ Ошибка генерации промпта: {e}")
            return None
    
    async def set_active_personality(self, chat_id: int, personality_id: str) -> bool:
        """🎭 Активация существующего персонажа"""
        try:
            # Загружаем из БД
            personality_data = await self.db.fetch_one(
                "SELECT * FROM custom_personalities WHERE id = ?", 
                (personality_id,)
            )
            
            if not personality_data:
                return False
            
            personality = CustomPersonality(
                id=personality_data['id'],
                description=personality_data['description'],
                system_prompt=personality_data['system_prompt'],
                chat_id=personality_data['chat_id'],
                user_id=personality_data['user_id'],
                created_at=datetime.fromisoformat(personality_data['created_at']),
                is_temporary=personality_data['is_temporary'],
                usage_count=personality_data['usage_count'],
                last_used=datetime.fromisoformat(personality_data['last_used']) if personality_data['last_used'] else None
            )
            
            self.active_personalities[chat_id] = personality
            
            # Обновляем статистику
            await self.db.execute("""
                UPDATE custom_personalities 
                SET usage_count = usage_count + 1, last_used = ?
                WHERE id = ?
            """, (datetime.now().isoformat(), personality_id))
            
            logger.info(f"🎭 Активирован персонаж: {personality.description[:30]}...")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка активации персонажа: {e}")
            return False
    
    def get_active_personality(self, chat_id: int) -> Optional[CustomPersonality]:
        """🎭 Получение активного персонажа"""
        return self.active_personalities.get(chat_id)
    
    async def get_user_personalities(self, user_id: int, limit: int = 10) -> List[Dict]:
        """👤 История персонажей пользователя"""
        try:
            personalities_data = await self.db.fetch_all("""
                SELECT * FROM custom_personalities 
                WHERE user_id = ? 
                ORDER BY last_used DESC, created_at DESC
                LIMIT ?
            """, (user_id, limit))
            
            result = []
            for row in personalities_data:
                result.append({
                    'id': row['id'],
                    'description': row['description'],
                    'created_at': row['created_at'],
                    'usage_count': row['usage_count'],
                    'last_used': row['last_used'],
                    'is_temporary': row['is_temporary']
                })
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения истории персонажей: {e}")
            return []
    
    async def delete_personality(self, personality_id: str, user_id: int) -> bool:
        """🗑️ Удаление персонажа"""
        try:
            # Проверяем права
            personality_data = await self.db.fetch_one(
                "SELECT user_id FROM custom_personalities WHERE id = ?", 
                (personality_id,)
            )
            
            if not personality_data or personality_data['user_id'] != user_id:
                return False
            
            # Удаляем
            await self.db.execute("DELETE FROM custom_personalities WHERE id = ?", (personality_id,))
            
            # Убираем из активных если был активен
            for chat_id, personality in self.active_personalities.items():
                if personality.id == personality_id:
                    del self.active_personalities[chat_id]
                    break
            
            logger.info(f"🗑️ Удален персонаж: {personality_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка удаления персонажа: {e}")
            return False
    
    async def clear_active_personality(self, chat_id: int) -> bool:
        """🔄 Сброс активного персонажа"""
        if chat_id in self.active_personalities:
            del self.active_personalities[chat_id]
            logger.info(f"🔄 Сброшен персонаж для чата {chat_id}")
            return True
        return False
    
    async def _load_active_personalities(self):
        """📥 Загрузка активных персонажей"""
        try:
            # Загружаем только недавно использованные (последние 7 дней)
            week_ago = (datetime.now() - timedelta(days=7)).isoformat()
            
            personalities_data = await self.db.fetch_all("""
                SELECT * FROM custom_personalities 
                WHERE last_used > ? OR created_at > ?
                ORDER BY last_used DESC
            """, (week_ago, week_ago))
            
            for row in personalities_data:
                personality = CustomPersonality(
                    id=row['id'],
                    description=row['description'],
                    system_prompt=row['system_prompt'],
                    chat_id=row['chat_id'],
                    user_id=row['user_id'],
                    created_at=datetime.fromisoformat(row['created_at']),
                    is_temporary=row['is_temporary'],
                    usage_count=row['usage_count'],
                    last_used=datetime.fromisoformat(row['last_used']) if row['last_used'] else None
                )
                
                # Активируем для соответствующего чата
                self.active_personalities[personality.chat_id] = personality
            
            logger.info(f"📥 Загружено {len(personalities_data)} активных персонажей")
            
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки персонажей: {e}")
    
    async def _load_user_histories(self):
        """📥 Загрузка истории пользователей"""
        try:
            personalities_data = await self.db.fetch_all("""
                SELECT * FROM custom_personalities 
                ORDER BY user_id, created_at DESC
            """)
            
            for row in personalities_data:
                user_id = row['user_id']
                
                personality = CustomPersonality(
                    id=row['id'],
                    description=row['description'],
                    system_prompt=row['system_prompt'],
                    chat_id=row['chat_id'],
                    user_id=row['user_id'],
                    created_at=datetime.fromisoformat(row['created_at']),
                    is_temporary=row['is_temporary'],
                    usage_count=row['usage_count'],
                    last_used=datetime.fromisoformat(row['last_used']) if row['last_used'] else None
                )
                
                if user_id not in self.user_personalities_history:
                    self.user_personalities_history[user_id] = []
                
                self.user_personalities_history[user_id].append(personality)
            
            logger.info(f"📥 Загружена история для {len(self.user_personalities_history)} пользователей")
            
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки истории: {e}")
    
    async def get_personality_stats(self) -> Dict[str, Any]:
        """📊 Статистика персонажей"""
        try:
            stats = await self.db.fetch_one("""
                SELECT 
                    COUNT(*) as total_personalities,
                    COUNT(CASE WHEN is_temporary = 1 THEN 1 END) as temporary_count,
                    AVG(usage_count) as avg_usage,
                    MAX(usage_count) as max_usage
                FROM custom_personalities
            """)
            
            active_count = len(self.active_personalities)
            users_count = len(self.user_personalities_history)
            
            return {
                'total_personalities': stats['total_personalities'],
                'active_personalities': active_count,
                'temporary_personalities': stats['temporary_count'],
                'users_with_personalities': users_count,
                'average_usage': round(stats['avg_usage'] or 0, 1),
                'max_usage': stats['max_usage'] or 0
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения статистики: {e}")
            return {}


# =================== ЭКСПОРТ ===================

__all__ = [
    "CustomPersonalityManager",
    "CustomPersonality"
]