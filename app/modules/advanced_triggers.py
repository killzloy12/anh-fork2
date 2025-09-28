#!/usr/bin/env python3
"""
⚡ ADVANCED TRIGGERS v3.1 - УЛУЧШЕННЫЕ ТРИГГЕРЫ
🚀 Расширенные возможности: добавление, редактирование, статистика

НОВЫЕ ВОЗМОЖНОСТИ:
• Создание пользовательских триггеров
• Редактирование существующих триггеров
• Детальная статистика использования
• Временные триггеры
• Контекстные триггеры
• Администрирование триггеров
"""

import logging
import asyncio
import random
import re
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
import aiofiles

logger = logging.getLogger(__name__)


@dataclass
class TriggerAction:
    """🎬 Действие триггера"""
    type: str  # text, emoji, sticker, gif, audio, chain
    content: str
    probability: float = 1.0
    delay: float = 0.0
    context_filters: List[str] = field(default_factory=list)
    success_count: int = 0
    total_attempts: int = 0


@dataclass
class CustomTrigger:
    """🎯 Пользовательский триггер"""
    id: str
    name: str
    description: str
    trigger_type: str  # keyword, emotion, time, context, regex, user_specific
    trigger_pattern: str
    actions: List[TriggerAction]
    probability: float = 1.0
    cooldown: float = 0.0
    allowed_chats: List[int] = field(default_factory=list)
    allowed_users: List[int] = field(default_factory=list)
    is_active: bool = True
    created_by: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    usage_count: int = 0
    success_rate: float = 0.0
    last_used: Optional[datetime] = None


class TriggerStats:
    """📊 Статистика триггеров"""
    
    def __init__(self):
        self.daily_stats = {}
        self.user_stats = {}
        self.chat_stats = {}
        self.trigger_performance = {}
    
    def record_trigger_use(self, trigger_id: str, user_id: int, chat_id: int, success: bool):
        """📈 Запись использования триггера"""
        today = datetime.now().date().isoformat()
        
        # Дневная статистика
        if today not in self.daily_stats:
            self.daily_stats[today] = {'total': 0, 'successful': 0, 'triggers': {}}
        
        self.daily_stats[today]['total'] += 1
        if success:
            self.daily_stats[today]['successful'] += 1
        
        if trigger_id not in self.daily_stats[today]['triggers']:
            self.daily_stats[today]['triggers'][trigger_id] = {'total': 0, 'successful': 0}
        
        self.daily_stats[today]['triggers'][trigger_id]['total'] += 1
        if success:
            self.daily_stats[today]['triggers'][trigger_id]['successful'] += 1
        
        # Статистика пользователя
        if user_id not in self.user_stats:
            self.user_stats[user_id] = {'triggers_activated': 0, 'successful_activations': 0}
        
        self.user_stats[user_id]['triggers_activated'] += 1
        if success:
            self.user_stats[user_id]['successful_activations'] += 1
        
        # Статистика чата
        if chat_id not in self.chat_stats:
            self.chat_stats[chat_id] = {'triggers_activated': 0, 'successful_activations': 0}
        
        self.chat_stats[chat_id]['triggers_activated'] += 1
        if success:
            self.chat_stats[chat_id]['successful_activations'] += 1


class AdvancedTriggersModule:
    """⚡ Модуль расширенных триггеров (улучшенная версия)"""
    
    def __init__(self, db_service, config, ai_service=None):
        self.db = db_service
        self.config = config
        self.ai = ai_service
        
        # Хранилища
        self.custom_triggers = {}
        self.trigger_cooldowns = {}
        self.stats = TriggerStats()
        
        # Предустановленные триггеры
        self.default_triggers = []
        
        logger.info("⚡ Модуль расширенных триггеров инициализирован")
    
    async def initialize(self):
        """🚀 Инициализация модуля"""
        await self._create_triggers_tables()
        await self._load_custom_triggers()
        await self._setup_default_triggers()
        logger.info("⚡ Расширенные триггеры загружены")
    
    async def _create_triggers_tables(self):
        """📋 Создание таблиц триггеров"""
        tables = [
            """
            CREATE TABLE IF NOT EXISTS custom_triggers (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                trigger_type TEXT NOT NULL,
                trigger_pattern TEXT NOT NULL,
                actions TEXT NOT NULL,  -- JSON
                probability REAL DEFAULT 1.0,
                cooldown REAL DEFAULT 0.0,
                allowed_chats TEXT,  -- JSON
                allowed_users TEXT,  -- JSON
                is_active BOOLEAN DEFAULT TRUE,
                created_by INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                usage_count INTEGER DEFAULT 0,
                success_rate REAL DEFAULT 0.0,
                last_used DATETIME
            )
            """,
            
            """
            CREATE TABLE IF NOT EXISTS trigger_usage_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trigger_id TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                chat_id INTEGER NOT NULL,
                message_text TEXT,
                success BOOLEAN DEFAULT FALSE,
                response_text TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (trigger_id) REFERENCES custom_triggers (id)
            )
            """,
            
            """
            CREATE TABLE IF NOT EXISTS trigger_stats_daily (
                date DATE PRIMARY KEY,
                total_activations INTEGER DEFAULT 0,
                successful_activations INTEGER DEFAULT 0,
                unique_users INTEGER DEFAULT 0,
                unique_chats INTEGER DEFAULT 0,
                stats_data TEXT  -- JSON
            )
            """
        ]
        
        for table_sql in tables:
            await self.db.execute(table_sql)
    
    async def _load_custom_triggers(self):
        """📥 Загрузка пользовательских триггеров"""
        try:
            triggers_data = await self.db.fetch_all("SELECT * FROM custom_triggers WHERE is_active = TRUE")
            
            for trigger_row in triggers_data:
                # Парсим действия из JSON
                actions_json = json.loads(trigger_row['actions'])
                actions = []
                
                for action_data in actions_json:
                    action = TriggerAction(
                        type=action_data['type'],
                        content=action_data['content'],
                        probability=action_data.get('probability', 1.0),
                        delay=action_data.get('delay', 0.0),
                        context_filters=action_data.get('context_filters', []),
                        success_count=action_data.get('success_count', 0),
                        total_attempts=action_data.get('total_attempts', 0)
                    )
                    actions.append(action)
                
                # Создаем объект триггера
                trigger = CustomTrigger(
                    id=trigger_row['id'],
                    name=trigger_row['name'],
                    description=trigger_row['description'] or '',
                    trigger_type=trigger_row['trigger_type'],
                    trigger_pattern=trigger_row['trigger_pattern'],
                    actions=actions,
                    probability=trigger_row['probability'],
                    cooldown=trigger_row['cooldown'],
                    allowed_chats=json.loads(trigger_row['allowed_chats'] or '[]'),
                    allowed_users=json.loads(trigger_row['allowed_users'] or '[]'),
                    is_active=trigger_row['is_active'],
                    created_by=trigger_row['created_by'],
                    created_at=datetime.fromisoformat(trigger_row['created_at']) if trigger_row['created_at'] else datetime.now(),
                    usage_count=trigger_row['usage_count'],
                    success_rate=trigger_row['success_rate'],
                    last_used=datetime.fromisoformat(trigger_row['last_used']) if trigger_row['last_used'] else None
                )
                
                self.custom_triggers[trigger.id] = trigger
            
            logger.info(f"📥 Загружено {len(self.custom_triggers)} пользовательских триггеров")
            
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки триггеров: {e}")
    
    async def _setup_default_triggers(self):
        """🎯 Настройка триггеров по умолчанию"""
        
        default_triggers_data = [
            {
                'id': 'greeting_morning',
                'name': 'Утреннее приветствие',
                'trigger_type': 'time_keyword',
                'trigger_pattern': 'утр|morning',
                'actions': [{'type': 'text', 'content': 'Доброе утро! ☀️ Как спалось?'}],
                'probability': 0.7
            },
            {
                'id': 'help_request',
                'name': 'Запрос помощи',
                'trigger_type': 'keyword',
                'trigger_pattern': 'помоги|помощь|help',
                'actions': [{'type': 'text', 'content': 'Помогу! 💪 В чем дело?'}],
                'probability': 0.9
            },
            {
                'id': 'programming_topic',
                'name': 'Тема программирования',
                'trigger_type': 'keyword',
                'trigger_pattern': 'программ|код|python|javascript',
                'actions': [{'type': 'text', 'content': 'Программинг! 👨‍💻 Какие вопросы?'}],
                'probability': 0.6
            },
            {
                'id': 'goodbye',
                'name': 'Прощание',
                'trigger_type': 'keyword',
                'trigger_pattern': 'пока|до свидания|bye|увидимся',
                'actions': [{'type': 'text', 'content': 'Пока! 👋 Заходи еще!'}],
                'probability': 0.8
            },
            {
                'id': 'thanks_response',
                'name': 'Ответ на благодарность',
                'trigger_type': 'keyword',
                'trigger_pattern': 'спасибо|благодар|thanks|thx',
                'actions': [{'type': 'text', 'content': 'Пожалуйста! 😊 Всегда рад помочь!'}],
                'probability': 0.9
            },
            {
                'id': 'sad_emotion',
                'name': 'Поддержка при грусти',
                'trigger_type': 'emotion',
                'trigger_pattern': 'грустн|печальн|расстроен|плохо',
                'actions': [{'type': 'text', 'content': 'Не грусти! 🤗 Все будет хорошо'}],
                'probability': 0.8
            },
            {
                'id': 'excited_emotion',
                'name': 'Реакция на радость',
                'trigger_type': 'emotion',
                'trigger_pattern': 'круто|супер|отлично|ура|🎉',
                'actions': [{'type': 'text', 'content': 'Да! 🎉 Классно!'}],
                'probability': 0.7
            },
            {
                'id': 'question_mark',
                'name': 'Реакция на вопросы',
                'trigger_type': 'regex',
                'trigger_pattern': r'\?$',
                'actions': [{'type': 'text', 'content': 'Интересный вопрос! 🤔'}],
                'probability': 0.3
            }
        ]
        
        # Добавляем триггеры по умолчанию если их нет
        for trigger_data in default_triggers_data:
            if trigger_data['id'] not in self.custom_triggers:
                await self.create_custom_trigger(trigger_data)
        
        logger.info(f"🎯 Настроено {len(default_triggers_data)} триггеров по умолчанию")
    
    async def create_custom_trigger(self, trigger_data: Dict) -> bool:
        """➕ Создание пользовательского триггера"""
        try:
            # Создаем уникальный ID если не указан
            if 'id' not in trigger_data:
                trigger_data['id'] = f"custom_{uuid.uuid4().hex[:8]}"
            
            # Парсим действия
            actions = []
            for action_data in trigger_data.get('actions', []):
                action = TriggerAction(
                    type=action_data['type'],
                    content=action_data['content'],
                    probability=action_data.get('probability', 1.0),
                    delay=action_data.get('delay', 0.0),
                    context_filters=action_data.get('context_filters', [])
                )
                actions.append(action)
            
            # Создаем объект триггера
            trigger = CustomTrigger(
                id=trigger_data['id'],
                name=trigger_data['name'],
                description=trigger_data.get('description', ''),
                trigger_type=trigger_data['trigger_type'],
                trigger_pattern=trigger_data['trigger_pattern'],
                actions=actions,
                probability=trigger_data.get('probability', 1.0),
                cooldown=trigger_data.get('cooldown', 0.0),
                allowed_chats=trigger_data.get('allowed_chats', []),
                allowed_users=trigger_data.get('allowed_users', []),
                created_by=trigger_data.get('created_by', 0)
            )
            
            # Сохраняем в БД
            actions_json = json.dumps([
                {
                    'type': action.type,
                    'content': action.content,
                    'probability': action.probability,
                    'delay': action.delay,
                    'context_filters': action.context_filters,
                    'success_count': action.success_count,
                    'total_attempts': action.total_attempts
                }
                for action in actions
            ])
            
            await self.db.execute("""
                INSERT OR REPLACE INTO custom_triggers 
                (id, name, description, trigger_type, trigger_pattern, actions, 
                 probability, cooldown, allowed_chats, allowed_users, is_active, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                trigger.id,
                trigger.name,
                trigger.description,
                trigger.trigger_type,
                trigger.trigger_pattern,
                actions_json,
                trigger.probability,
                trigger.cooldown,
                json.dumps(trigger.allowed_chats),
                json.dumps(trigger.allowed_users),
                trigger.is_active,
                trigger.created_by
            ))
            
            # Добавляем в память
            self.custom_triggers[trigger.id] = trigger
            
            logger.info(f"➕ Создан триггер: {trigger.name} ({trigger.id})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания триггера: {e}")
            return False
    
    async def process_message(self, message: str, user_id: int, chat_id: int, context: Dict) -> List[str]:
        """🔄 Обработка сообщения триггерами"""
        responses = []
        
        try:
            message_lower = message.lower()
            
            # Перебираем все активные триггеры
            for trigger in self.custom_triggers.values():
                if not trigger.is_active:
                    continue
                
                # Проверяем права доступа
                if trigger.allowed_chats and chat_id not in trigger.allowed_chats:
                    continue
                
                if trigger.allowed_users and user_id not in trigger.allowed_users:
                    continue
                
                # Проверяем кулдаун
                cooldown_key = f"{trigger.id}_{chat_id}"
                if await self._check_cooldown(cooldown_key, trigger.cooldown):
                    continue
                
                # Проверяем соответствие триггеру
                if await self._matches_trigger(message, message_lower, trigger):
                    # Проверяем вероятность
                    if random.random() < trigger.probability:
                        # Выполняем действия триггера
                        trigger_responses = await self._execute_trigger_actions(trigger, message, context)
                        responses.extend(trigger_responses)
                        
                        # Обновляем статистику
                        await self._update_trigger_usage(trigger.id, user_id, chat_id, message, True)
                        
                        # Устанавливаем кулдаун
                        await self._set_cooldown(cooldown_key, trigger.cooldown)
                        
                        # Если высокоприоритетный триггер, прекращаем обработку
                        if trigger.probability > 0.8:
                            break
            
            return responses
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки триггеров: {e}")
            return []
    
    async def _matches_trigger(self, message: str, message_lower: str, trigger: CustomTrigger) -> bool:
        """🎯 Проверка соответствия триггеру"""
        
        pattern = trigger.trigger_pattern.lower()
        
        if trigger.trigger_type == 'keyword':
            # Ключевые слова (через |)
            keywords = pattern.split('|')
            return any(keyword.strip() in message_lower for keyword in keywords)
        
        elif trigger.trigger_type == 'regex':
            # Регулярное выражение
            try:
                return bool(re.search(pattern, message, re.IGNORECASE))
            except re.error:
                logger.error(f"❌ Неверное регулярное выражение в триггере {trigger.id}: {pattern}")
                return False
        
        elif trigger.trigger_type == 'emotion':
            # Эмоциональные ключевые слова
            emotion_keywords = pattern.split('|')
            return any(keyword.strip() in message_lower for keyword in emotion_keywords)
        
        elif trigger.trigger_type == 'time_keyword':
            # Проверка времени + ключевые слова
            hour = datetime.now().hour
            keywords = pattern.split('|')
            
            # Утро (5-12)
            if 5 <= hour < 12 and any('утр' in keyword or 'morning' in keyword for keyword in keywords):
                return any(keyword.strip() in message_lower for keyword in keywords)
            
            # День (12-18)
            if 12 <= hour < 18 and any('день' in keyword or 'day' in keyword for keyword in keywords):
                return any(keyword.strip() in message_lower for keyword in keywords)
            
            # Вечер (18-22)
            if 18 <= hour < 22 and any('вечер' in keyword or 'evening' in keyword for keyword in keywords):
                return any(keyword.strip() in message_lower for keyword in keywords)
            
            # Ночь (22-5)
            if hour >= 22 or hour < 5 and any('ноч' in keyword or 'night' in keyword for keyword in keywords):
                return any(keyword.strip() in message_lower for keyword in keywords)
            
            # Обычная проверка ключевых слов
            return any(keyword.strip() in message_lower for keyword in keywords)
        
        return False
    
    async def _execute_trigger_actions(self, trigger: CustomTrigger, message: str, context: Dict) -> List[str]:
        """🎬 Выполнение действий триггера"""
        responses = []
        
        for action in trigger.actions:
            if random.random() < action.probability:
                if action.delay > 0:
                    await asyncio.sleep(action.delay)
                
                if action.type == 'text':
                    responses.append(action.content)
                
                elif action.type == 'emoji':
                    responses.append(action.content)
                
                # Другие типы действий можно добавить позже
                
                action.total_attempts += 1
                action.success_count += 1
        
        return responses
    
    async def _check_cooldown(self, cooldown_key: str, cooldown_seconds: float) -> bool:
        """⏰ Проверка кулдауна"""
        if cooldown_seconds <= 0:
            return False
        
        if cooldown_key in self.trigger_cooldowns:
            last_used = self.trigger_cooldowns[cooldown_key]
            if datetime.now() - last_used < timedelta(seconds=cooldown_seconds):
                return True
        
        return False
    
    async def _set_cooldown(self, cooldown_key: str, cooldown_seconds: float):
        """🕐 Установка кулдауна"""
        if cooldown_seconds > 0:
            self.trigger_cooldowns[cooldown_key] = datetime.now()
    
    async def _update_trigger_usage(self, trigger_id: str, user_id: int, chat_id: int, message: str, success: bool):
        """📊 Обновление статистики триггера"""
        try:
            # Обновляем в БД
            await self.db.execute("""
                UPDATE custom_triggers 
                SET usage_count = usage_count + 1, last_used = ?
                WHERE id = ?
            """, (datetime.now().isoformat(), trigger_id))
            
            # Логируем использование
            await self.db.execute("""
                INSERT INTO trigger_usage_log 
                (trigger_id, user_id, chat_id, message_text, success)
                VALUES (?, ?, ?, ?, ?)
            """, (trigger_id, user_id, chat_id, message[:200], success))
            
            # Обновляем статистику
            self.stats.record_trigger_use(trigger_id, user_id, chat_id, success)
            
            # Обновляем в памяти
            if trigger_id in self.custom_triggers:
                self.custom_triggers[trigger_id].usage_count += 1
                self.custom_triggers[trigger_id].last_used = datetime.now()
                
        except Exception as e:
            logger.error(f"❌ Ошибка обновления статистики триггера: {e}")
    
    async def get_triggers_stats(self) -> Dict[str, Any]:
        """📊 Получение статистики триггеров"""
        try:
            total_triggers = len(self.custom_triggers)
            active_triggers = len([t for t in self.custom_triggers.values() if t.is_active])
            total_usage = sum(t.usage_count for t in self.custom_triggers.values())
            
            # Топ триггеров по использованию
            top_triggers = sorted(
                self.custom_triggers.values(),
                key=lambda x: x.usage_count,
                reverse=True
            )[:10]
            
            # Средний успех
            total_attempts = sum(
                sum(action.total_attempts for action in trigger.actions)
                for trigger in self.custom_triggers.values()
            )
            
            total_successes = sum(
                sum(action.success_count for action in trigger.actions)
                for trigger in self.custom_triggers.values()
            )
            
            avg_success_rate = total_successes / total_attempts if total_attempts > 0 else 0
            
            return {
                'total_triggers': total_triggers,
                'active_triggers': active_triggers,
                'total_usage': total_usage,
                'average_success_rate': avg_success_rate,
                'top_triggers': [
                    {
                        'name': trigger.name,
                        'usage_count': trigger.usage_count,
                        'success_rate': trigger.success_rate,
                        'created_by': trigger.created_by
                    }
                    for trigger in top_triggers
                ]
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения статистики: {e}")
            return {}
    
    async def delete_trigger(self, trigger_id: str, user_id: int) -> bool:
        """🗑️ Удаление триггера"""
        try:
            if trigger_id not in self.custom_triggers:
                return False
            
            trigger = self.custom_triggers[trigger_id]
            
            # Проверяем права (только создатель или админ может удалить)
            if trigger.created_by != user_id and user_id not in self.config.bot.admin_ids:
                return False
            
            # Деактивируем триггер
            await self.db.execute("UPDATE custom_triggers SET is_active = FALSE WHERE id = ?", (trigger_id,))
            
            # Удаляем из памяти
            del self.custom_triggers[trigger_id]
            
            logger.info(f"🗑️ Удален триггер: {trigger.name} ({trigger_id})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка удаления триггера: {e}")
            return False


# =================== ЭКСПОРТ ===================

__all__ = [
    "AdvancedTriggersModule",
    "CustomTrigger",
    "TriggerAction",
    "TriggerStats"
]