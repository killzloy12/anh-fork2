#!/usr/bin/env python3
"""
⚖️ KARMA SYSTEM v1.0 - Система кармы пользователей
🚀 Полноценная система репутации с гибкими настройками

ВОЗМОЖНОСТИ:
• Карма за активность, помощь, вклад в сообщество
• Штрафы за нарушения, спам, токсичность
• Уровни и достижения на основе кармы
• Модификаторы кармы для разных действий
• Автоматические и ручные изменения кармы
• Детальная статистика и история
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import asyncio

logger = logging.getLogger(__name__)


class KarmaActionType(Enum):
    """🎯 Типы действий для кармы"""
    # Положительные действия
    MESSAGE = "message"                  # Сообщение (+1)
    HELPFUL_REPLY = "helpful_reply"      # Полезный ответ (+3)
    QUESTION_ANSWER = "question_answer"  # Ответ на вопрос (+5)
    WELCOME_NEWCOMER = "welcome_newcomer" # Приветствие новичка (+2)
    SHARE_KNOWLEDGE = "share_knowledge"  # Деление знаниями (+4)
    POSITIVE_REACTION = "positive_reaction" # Позитивная реакция (+1)
    
    # Отрицательные действия
    SPAM = "spam"                       # Спам (-5)
    TOXICITY = "toxicity"               # Токсичность (-10)
    FLOOD = "flood"                     # Флуд (-3)
    OFF_TOPIC = "off_topic"             # Оффтоп (-2)
    RULE_VIOLATION = "rule_violation"   # Нарушение правил (-8)
    REPEATED_VIOLATION = "repeated_violation" # Повторное нарушение (-15)
    
    # Модераторские действия
    MANUAL_BONUS = "manual_bonus"       # Ручной бонус (переменный)
    MANUAL_PENALTY = "manual_penalty"   # Ручной штраф (переменный)
    ACHIEVEMENT_BONUS = "achievement"   # Бонус за достижение (+20)


@dataclass
class KarmaLevel:
    """📊 Уровень кармы"""
    level: int
    name: str
    min_karma: int
    max_karma: int
    emoji: str
    description: str
    benefits: List[str]


@dataclass
class KarmaAction:
    """📋 Действие кармы"""
    id: str
    user_id: int
    chat_id: int
    action_type: KarmaActionType
    karma_change: int
    reason: str
    moderator_id: Optional[int]
    timestamp: datetime
    message_id: Optional[int] = None


@dataclass
class UserKarma:
    """👤 Карма пользователя"""
    user_id: int
    chat_id: int
    karma: int
    level: int
    total_positive: int
    total_negative: int
    message_count: int
    last_activity: datetime
    created_at: datetime


class KarmaSettings:
    """⚙️ Настройки системы кармы"""
    
    def __init__(self):
        # Базовые значения кармы за действия
        self.karma_values = {
            KarmaActionType.MESSAGE: 1,
            KarmaActionType.HELPFUL_REPLY: 3,
            KarmaActionType.QUESTION_ANSWER: 5,
            KarmaActionType.WELCOME_NEWCOMER: 2,
            KarmaActionType.SHARE_KNOWLEDGE: 4,
            KarmaActionType.POSITIVE_REACTION: 1,
            
            KarmaActionType.SPAM: -5,
            KarmaActionType.TOXICITY: -10,
            KarmaActionType.FLOOD: -3,
            KarmaActionType.OFF_TOPIC: -2,
            KarmaActionType.RULE_VIOLATION: -8,
            KarmaActionType.REPEATED_VIOLATION: -15,
        }
        
        # Лимиты кармы
        self.daily_message_karma_limit = 50  # Макс кармы за сообщения в день
        self.karma_decay_enabled = False      # Включить затухание кармы
        self.karma_decay_rate = 0.1          # Процент затухания в месяц
        self.min_karma = -1000               # Минимальная карма
        self.max_karma = 10000               # Максимальная карма
        
        # Модификаторы
        self.newcomer_bonus = 1.5            # Бонус новичкам (первые 7 дней)
        self.veteran_penalty = 0.8           # Штраф ветеранам (уже высокая карма)
        self.weekend_bonus = 1.2             # Бонус в выходные
        
        # Детекция действий
        self.auto_detect_helpful = True       # Автоматически определять полезные ответы
        self.auto_detect_spam = True         # Автоматически определять спам
        self.auto_detect_toxicity = True     # Автоматически определять токсичность
        
        # Уровни кармы
        self.levels = [
            KarmaLevel(0, "Новичок", -1000, 0, "🔰", "Только начинающий путь", ["Базовый доступ"]),
            KarmaLevel(1, "Участник", 1, 50, "👤", "Активный участник сообщества", ["Создание опросов"]),
            KarmaLevel(2, "Активист", 51, 150, "⭐", "Полезный член сообщества", ["Приглашение пользователей"]),
            KarmaLevel(3, "Эксперт", 151, 300, "🎓", "Знающий и опытный", ["Модерация контента"]),
            KarmaLevel(4, "Мастер", 301, 600, "🔥", "Мастер своего дела", ["Особые привилегии"]),
            KarmaLevel(5, "Гуру", 601, 1000, "🏆", "Признанный авторитет", ["VIP статус"]),
            KarmaLevel(6, "Легенда", 1001, 10000, "👑", "Легендарный участник", ["Все привилегии"])
        ]


class KarmaManager:
    """⚖️ Менеджер системы кармы"""
    
    def __init__(self, db_service, config):
        self.db = db_service
        self.config = config
        self.settings = KarmaSettings()
        self.user_karma_cache = {}  # Кэш кармы пользователей
        self.daily_limits = {}      # Дневные лимиты по пользователям
        
        logger.info("⚖️ Система кармы инициализирована")
    
    async def initialize(self):
        """🚀 Инициализация системы"""
        await self._create_karma_tables()
        await self._load_karma_cache()
        await self._load_settings()
        logger.info("⚖️ Система кармы загружена")
    
    async def _create_karma_tables(self):
        """📋 Создание таблиц кармы"""
        tables = [
            """
            CREATE TABLE IF NOT EXISTS user_karma (
                user_id INTEGER NOT NULL,
                chat_id INTEGER NOT NULL,
                karma INTEGER DEFAULT 0,
                level INTEGER DEFAULT 0,
                total_positive INTEGER DEFAULT 0,
                total_negative INTEGER DEFAULT 0,
                message_count INTEGER DEFAULT 0,
                last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, chat_id)
            )
            """,
            
            """
            CREATE TABLE IF NOT EXISTS karma_actions (
                id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                chat_id INTEGER NOT NULL,
                action_type TEXT NOT NULL,
                karma_change INTEGER NOT NULL,
                reason TEXT,
                moderator_id INTEGER,
                message_id INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """,
            
            """
            CREATE TABLE IF NOT EXISTS karma_settings (
                chat_id INTEGER PRIMARY KEY,
                settings_json TEXT NOT NULL,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """,
            
            """
            CREATE TABLE IF NOT EXISTS karma_achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                chat_id INTEGER NOT NULL,
                achievement_type TEXT NOT NULL,
                achieved_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                karma_bonus INTEGER DEFAULT 0
            )
            """
        ]
        
        for table_sql in tables:
            await self.db.execute(table_sql)
        
        # Индексы
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_karma_user_chat ON user_karma (user_id, chat_id)",
            "CREATE INDEX IF NOT EXISTS idx_karma_actions_user ON karma_actions (user_id, timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_karma_actions_chat ON karma_actions (chat_id, timestamp)"
        ]
        
        for index_sql in indexes:
            await self.db.execute(index_sql)
    
    async def add_karma(self, user_id: int, chat_id: int, action_type: KarmaActionType, 
                       reason: str = "", moderator_id: Optional[int] = None, 
                       message_id: Optional[int] = None, custom_value: Optional[int] = None) -> Tuple[bool, int, int]:
        """➕ Добавление кармы"""
        try:
            # Определяем значение кармы
            karma_change = custom_value or self.settings.karma_values.get(action_type, 0)
            
            # Применяем модификаторы
            karma_change = await self._apply_karma_modifiers(user_id, chat_id, karma_change, action_type)
            
            # Проверяем лимиты
            if not await self._check_karma_limits(user_id, chat_id, karma_change, action_type):
                return False, 0, 0
            
            # Получаем текущую карму
            current_karma = await self.get_user_karma(user_id, chat_id)
            new_karma = max(self.settings.min_karma, min(self.settings.max_karma, current_karma.karma + karma_change))
            actual_change = new_karma - current_karma.karma
            
            # Обновляем карму
            await self.db.execute("""
                INSERT OR REPLACE INTO user_karma 
                (user_id, chat_id, karma, level, total_positive, total_negative, message_count, last_activity)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id, chat_id, new_karma,
                self._get_level_by_karma(new_karma),
                current_karma.total_positive + max(0, actual_change),
                current_karma.total_negative + abs(min(0, actual_change)),
                current_karma.message_count + (1 if action_type == KarmaActionType.MESSAGE else 0),
                datetime.now().isoformat()
            ))
            
            # Записываем действие
            action_id = f"karma_{user_id}_{chat_id}_{int(datetime.now().timestamp())}"
            await self.db.execute("""
                INSERT INTO karma_actions 
                (id, user_id, chat_id, action_type, karma_change, reason, moderator_id, message_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (action_id, user_id, chat_id, action_type.value, actual_change, reason, moderator_id, message_id))
            
            # Обновляем кэш
            if (user_id, chat_id) in self.user_karma_cache:
                self.user_karma_cache[(user_id, chat_id)].karma = new_karma
                self.user_karma_cache[(user_id, chat_id)].level = self._get_level_by_karma(new_karma)
            
            # Проверяем достижения
            await self._check_achievements(user_id, chat_id, new_karma, action_type)
            
            logger.info(f"⚖️ Карма изменена: пользователь {user_id}, чат {chat_id}, {actual_change:+d} ({action_type.value})")
            return True, actual_change, new_karma
            
        except Exception as e:
            logger.error(f"❌ Ошибка добавления кармы: {e}")
            return False, 0, 0
    
    async def get_user_karma(self, user_id: int, chat_id: int) -> UserKarma:
        """👤 Получение кармы пользователя"""
        # Проверяем кэш
        cache_key = (user_id, chat_id)
        if cache_key in self.user_karma_cache:
            return self.user_karma_cache[cache_key]
        
        try:
            karma_data = await self.db.fetch_one("""
                SELECT * FROM user_karma WHERE user_id = ? AND chat_id = ?
            """, (user_id, chat_id))
            
            if karma_data:
                user_karma = UserKarma(
                    user_id=karma_data['user_id'],
                    chat_id=karma_data['chat_id'],
                    karma=karma_data['karma'],
                    level=karma_data['level'],
                    total_positive=karma_data['total_positive'],
                    total_negative=karma_data['total_negative'],
                    message_count=karma_data['message_count'],
                    last_activity=datetime.fromisoformat(karma_data['last_activity']),
                    created_at=datetime.fromisoformat(karma_data['created_at'])
                )
            else:
                # Создаем новую запись
                user_karma = UserKarma(
                    user_id=user_id,
                    chat_id=chat_id,
                    karma=0,
                    level=0,
                    total_positive=0,
                    total_negative=0,
                    message_count=0,
                    last_activity=datetime.now(),
                    created_at=datetime.now()
                )
                
                await self.db.execute("""
                    INSERT INTO user_karma (user_id, chat_id, karma, level)
                    VALUES (?, ?, ?, ?)
                """, (user_id, chat_id, 0, 0))
            
            # Кэшируем
            self.user_karma_cache[cache_key] = user_karma
            return user_karma
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения кармы: {e}")
            return UserKarma(user_id, chat_id, 0, 0, 0, 0, 0, datetime.now(), datetime.now())
    
    async def get_karma_leaderboard(self, chat_id: int, limit: int = 10) -> List[Dict]:
        """🏆 Топ по карме"""
        try:
            leaderboard_data = await self.db.fetch_all("""
                SELECT user_id, karma, level, message_count, last_activity
                FROM user_karma 
                WHERE chat_id = ? AND karma > 0
                ORDER BY karma DESC, last_activity DESC
                LIMIT ?
            """, (chat_id, limit))
            
            result = []
            for i, row in enumerate(leaderboard_data, 1):
                level_info = self.settings.levels[min(row['level'], len(self.settings.levels) - 1)]
                result.append({
                    'rank': i,
                    'user_id': row['user_id'],
                    'karma': row['karma'],
                    'level': row['level'],
                    'level_name': level_info.name,
                    'level_emoji': level_info.emoji,
                    'message_count': row['message_count']
                })
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения топа: {e}")
            return []
    
    async def get_user_karma_history(self, user_id: int, chat_id: int, limit: int = 20) -> List[Dict]:
        """📜 История кармы пользователя"""
        try:
            history_data = await self.db.fetch_all("""
                SELECT action_type, karma_change, reason, timestamp, moderator_id
                FROM karma_actions 
                WHERE user_id = ? AND chat_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (user_id, chat_id, limit))
            
            result = []
            for row in history_data:
                result.append({
                    'action_type': row['action_type'],
                    'karma_change': row['karma_change'],
                    'reason': row['reason'],
                    'timestamp': row['timestamp'],
                    'moderator_id': row['moderator_id']
                })
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения истории: {e}")
            return []
    
    def _get_level_by_karma(self, karma: int) -> int:
        """📊 Определение уровня по карме"""
        for i, level in enumerate(reversed(self.settings.levels)):
            if karma >= level.min_karma:
                return len(self.settings.levels) - 1 - i
        return 0
    
    def get_level_info(self, level: int) -> KarmaLevel:
        """ℹ️ Информация об уровне"""
        return self.settings.levels[min(level, len(self.settings.levels) - 1)]
    
    async def _apply_karma_modifiers(self, user_id: int, chat_id: int, karma_change: int, action_type: KarmaActionType) -> int:
        """🔧 Применение модификаторов кармы"""
        if karma_change == 0:
            return 0
        
        modifier = 1.0
        
        # Бонус новичкам
        user_karma = await self.get_user_karma(user_id, chat_id)
        if (datetime.now() - user_karma.created_at).days <= 7:
            modifier *= self.settings.newcomer_bonus
        
        # Штраф ветеранам
        if user_karma.karma > 500:
            modifier *= self.settings.veteran_penalty
        
        # Бонус в выходные
        if datetime.now().weekday() >= 5:  # Суббота/Воскресенье
            modifier *= self.settings.weekend_bonus
        
        return int(karma_change * modifier)
    
    async def _check_karma_limits(self, user_id: int, chat_id: int, karma_change: int, action_type: KarmaActionType) -> bool:
        """🚫 Проверка лимитов кармы"""
        # Лимит кармы за сообщения в день
        if action_type == KarmaActionType.MESSAGE and karma_change > 0:
            today = datetime.now().date().isoformat()
            limit_key = f"{user_id}_{chat_id}_{today}"
            
            current_daily = self.daily_limits.get(limit_key, 0)
            if current_daily >= self.settings.daily_message_karma_limit:
                return False
            
            self.daily_limits[limit_key] = current_daily + karma_change
        
        return True
    
    async def _check_achievements(self, user_id: int, chat_id: int, new_karma: int, action_type: KarmaActionType):
        """🏆 Проверка достижений"""
        # Достижения по уровням кармы
        milestones = [50, 100, 250, 500, 1000]
        for milestone in milestones:
            if new_karma >= milestone:
                # Проверяем, не получал ли уже
                existing = await self.db.fetch_one("""
                    SELECT id FROM karma_achievements 
                    WHERE user_id = ? AND chat_id = ? AND achievement_type = ?
                """, (user_id, chat_id, f"karma_{milestone}"))
                
                if not existing:
                    # Выдаем достижение
                    await self.db.execute("""
                        INSERT INTO karma_achievements 
                        (user_id, chat_id, achievement_type, karma_bonus)
                        VALUES (?, ?, ?, ?)
                    """, (user_id, chat_id, f"karma_{milestone}", 20))
                    
                    # Добавляем бонусную карму
                    await self.add_karma(user_id, chat_id, KarmaActionType.ACHIEVEMENT_BONUS, 
                                       f"Достижение: {milestone} кармы", custom_value=20)
    
    async def _load_karma_cache(self):
        """📥 Загрузка кэша кармы"""
        try:
            karma_data = await self.db.fetch_all("SELECT * FROM user_karma")
            
            for row in karma_data:
                user_karma = UserKarma(
                    user_id=row['user_id'],
                    chat_id=row['chat_id'],
                    karma=row['karma'],
                    level=row['level'],
                    total_positive=row['total_positive'],
                    total_negative=row['total_negative'],
                    message_count=row['message_count'],
                    last_activity=datetime.fromisoformat(row['last_activity']),
                    created_at=datetime.fromisoformat(row['created_at'])
                )
                
                self.user_karma_cache[(row['user_id'], row['chat_id'])] = user_karma
            
            logger.info(f"📥 Загружено {len(karma_data)} записей кармы")
            
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки кэша кармы: {e}")
    
    async def _load_settings(self):
        """⚙️ Загрузка настроек"""
        # В будущем можно загружать индивидуальные настройки для чатов
        pass
    
    async def get_karma_stats(self, chat_id: Optional[int] = None) -> Dict[str, Any]:
        """📊 Статистика кармы"""
        try:
            if chat_id:
                stats = await self.db.fetch_one("""
                    SELECT 
                        COUNT(*) as total_users,
                        AVG(karma) as avg_karma,
                        MAX(karma) as max_karma,
                        MIN(karma) as min_karma,
                        SUM(message_count) as total_messages
                    FROM user_karma 
                    WHERE chat_id = ?
                """, (chat_id,))
            else:
                stats = await self.db.fetch_one("""
                    SELECT 
                        COUNT(*) as total_users,
                        AVG(karma) as avg_karma,
                        MAX(karma) as max_karma,
                        MIN(karma) as min_karma,
                        SUM(message_count) as total_messages
                    FROM user_karma
                """)
            
            return {
                'total_users': stats['total_users'],
                'average_karma': round(stats['avg_karma'] or 0, 1),
                'max_karma': stats['max_karma'] or 0,
                'min_karma': stats['min_karma'] or 0,
                'total_messages': stats['total_messages'] or 0,
                'cached_users': len(self.user_karma_cache)
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения статистики кармы: {e}")
            return {}


# =================== ЭКСПОРТ ===================

__all__ = [
    "KarmaManager",
    "KarmaActionType", 
    "KarmaLevel",
    "KarmaSettings",
    "UserKarma"
]