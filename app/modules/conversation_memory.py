#!/usr/bin/env python3
"""
🧠 CONVERSATION MEMORY MODULE v3.0 - ДОЛГОСРОЧНАЯ ПАМЯТЬ ДИАЛОГОВ
💭 Система запоминания и использования контекста разговоров

ВОЗМОЖНОСТИ:
• Долгосрочная память о пользователях
• Запоминание предпочтений и интересов
• История тем разговоров
• Личные факты о пользователях
• Эмоциональные паттерны
• Связи между пользователями
• Адаптивное поведение на основе памяти
"""

import logging
import asyncio
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, asdict
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class UserProfile:
    """👤 Профиль пользователя"""
    user_id: int
    name: str = ""
    interests: List[str] = None
    personality_traits: List[str] = None
    preferred_topics: Dict[str, float] = None
    communication_style: str = "casual"
    relationship_level: str = "stranger"
    last_interaction: datetime = None
    total_messages: int = 0
    favorite_emojis: List[str] = None
    time_zone: str = ""
    language_preference: str = "ru"
    
    def __post_init__(self):
        if self.interests is None:
            self.interests = []
        if self.personality_traits is None:
            self.personality_traits = []
        if self.preferred_topics is None:
            self.preferred_topics = {}
        if self.favorite_emojis is None:
            self.favorite_emojis = []
        if self.last_interaction is None:
            self.last_interaction = datetime.now()


@dataclass
class ConversationMemory:
    """💭 Память о разговоре"""
    user_id: int
    chat_id: int
    topic: str
    summary: str
    key_facts: List[str]
    emotional_tone: str
    importance_score: float
    timestamp: datetime
    related_users: List[int] = None
    
    def __post_init__(self):
        if self.related_users is None:
            self.related_users = []


@dataclass  
class PersonalFact:
    """📝 Личный факт о пользователе"""
    user_id: int
    category: str  # work, family, hobbies, etc.
    fact: str
    confidence: float
    source: str  # direct, inferred, context
    timestamp: datetime
    relevance_score: float = 1.0


class ConversationMemoryModule:
    """💭 Модуль долгосрочной памяти диалогов"""
    
    def __init__(self, db_service):
        self.db = db_service
        self.user_profiles: Dict[int, UserProfile] = {}
        self.conversation_memories: List[ConversationMemory] = []
        self.personal_facts: Dict[int, List[PersonalFact]] = defaultdict(list)
        
        logger.info("💭 Модуль памяти диалогов инициализирован")
    
    async def initialize(self):
        """🚀 Инициализация модуля"""
        await self._create_memory_tables()
        await self._load_user_profiles()
        await self._load_conversation_memories()
        logger.info("💭 Память диалогов загружена")
    
    async def _create_memory_tables(self):
        """📋 Создание таблиц для памяти"""
        tables = [
            """
            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id INTEGER PRIMARY KEY,
                name TEXT,
                interests TEXT,  -- JSON
                personality_traits TEXT,  -- JSON
                preferred_topics TEXT,  -- JSON
                communication_style TEXT,
                relationship_level TEXT,
                last_interaction DATETIME,
                total_messages INTEGER DEFAULT 0,
                favorite_emojis TEXT,  -- JSON
                time_zone TEXT,
                language_preference TEXT DEFAULT 'ru',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """,
            
            """
            CREATE TABLE IF NOT EXISTS conversation_memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                chat_id INTEGER,
                topic TEXT,
                summary TEXT,
                key_facts TEXT,  -- JSON
                emotional_tone TEXT,
                importance_score REAL,
                related_users TEXT,  -- JSON
                timestamp DATETIME,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            """,
            
            """
            CREATE TABLE IF NOT EXISTS personal_facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                category TEXT,
                fact TEXT,
                confidence REAL,
                source TEXT,
                relevance_score REAL DEFAULT 1.0,
                timestamp DATETIME,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            """,
            
            """
            CREATE TABLE IF NOT EXISTS user_relationships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user1_id INTEGER,
                user2_id INTEGER,
                relationship_type TEXT,
                strength REAL DEFAULT 0.5,
                context TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user1_id) REFERENCES users (id),
                FOREIGN KEY (user2_id) REFERENCES users (id)
            )
            """
        ]
        
        for table_sql in tables:
            await self.db.execute(table_sql)
        
        # Индексы
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_conversation_memories_user ON conversation_memories(user_id, timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_personal_facts_user ON personal_facts(user_id, category)",
            "CREATE INDEX IF NOT EXISTS idx_user_relationships ON user_relationships(user1_id, user2_id)"
        ]
        
        for index_sql in indexes:
            await self.db.execute(index_sql)
    
    async def _load_user_profiles(self):
        """👤 Загрузка профилей пользователей"""
        try:
            profiles = await self.db.fetch_all("SELECT * FROM user_profiles")
            
            for profile_data in profiles:
                profile = UserProfile(
                    user_id=profile_data['user_id'],
                    name=profile_data['name'] or "",
                    interests=json.loads(profile_data['interests'] or '[]'),
                    personality_traits=json.loads(profile_data['personality_traits'] or '[]'),
                    preferred_topics=json.loads(profile_data['preferred_topics'] or '{}'),
                    communication_style=profile_data['communication_style'],
                    relationship_level=profile_data['relationship_level'],
                    last_interaction=datetime.fromisoformat(profile_data['last_interaction']) if profile_data['last_interaction'] else datetime.now(),
                    total_messages=profile_data['total_messages'],
                    favorite_emojis=json.loads(profile_data['favorite_emojis'] or '[]'),
                    time_zone=profile_data['time_zone'] or "",
                    language_preference=profile_data['language_preference']
                )
                
                self.user_profiles[profile.user_id] = profile
                
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки профилей: {e}")
    
    async def _load_conversation_memories(self):
        """💭 Загрузка памяти разговоров"""
        try:
            memories = await self.db.fetch_all("""
                SELECT * FROM conversation_memories 
                ORDER BY timestamp DESC LIMIT 1000
            """)
            
            for memory_data in memories:
                memory = ConversationMemory(
                    user_id=memory_data['user_id'],
                    chat_id=memory_data['chat_id'],
                    topic=memory_data['topic'],
                    summary=memory_data['summary'],
                    key_facts=json.loads(memory_data['key_facts'] or '[]'),
                    emotional_tone=memory_data['emotional_tone'],
                    importance_score=memory_data['importance_score'],
                    timestamp=datetime.fromisoformat(memory_data['timestamp']),
                    related_users=json.loads(memory_data['related_users'] or '[]')
                )
                
                self.conversation_memories.append(memory)
                
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки памяти разговоров: {e}")
    
    async def get_or_create_user_profile(self, user_id: int, name: str = "") -> UserProfile:
        """👤 Получить или создать профиль пользователя"""
        if user_id not in self.user_profiles:
            profile = UserProfile(user_id=user_id, name=name)
            self.user_profiles[user_id] = profile
            await self._save_user_profile(profile)
        
        return self.user_profiles[user_id]
    
    async def _save_user_profile(self, profile: UserProfile):
        """💾 Сохранение профиля пользователя"""
        try:
            await self.db.execute("""
                INSERT OR REPLACE INTO user_profiles 
                (user_id, name, interests, personality_traits, preferred_topics, 
                 communication_style, relationship_level, last_interaction, total_messages,
                 favorite_emojis, time_zone, language_preference, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                profile.user_id,
                profile.name,
                json.dumps(profile.interests, ensure_ascii=False),
                json.dumps(profile.personality_traits, ensure_ascii=False),
                json.dumps(profile.preferred_topics, ensure_ascii=False),
                profile.communication_style,
                profile.relationship_level,
                profile.last_interaction.isoformat(),
                profile.total_messages,
                json.dumps(profile.favorite_emojis, ensure_ascii=False),
                profile.time_zone,
                profile.language_preference,
                datetime.now().isoformat()
            ))
            
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения профиля: {e}")
    
    async def update_user_interaction(self, user_id: int, message: str, topic: str, emotion: str):
        """📝 Обновление данных о взаимодействии с пользователем"""
        profile = await self.get_or_create_user_profile(user_id)
        
        # Обновляем базовые данные
        profile.last_interaction = datetime.now()
        profile.total_messages += 1
        
        # Анализируем и обновляем предпочтения по темам
        if topic in profile.preferred_topics:
            profile.preferred_topics[topic] += 0.1
        else:
            profile.preferred_topics[topic] = 0.5
        
        # Нормализуем веса тем
        total_weight = sum(profile.preferred_topics.values())
        if total_weight > 10:  # Если слишком много накопилось
            for t in profile.preferred_topics:
                profile.preferred_topics[t] *= 0.9
        
        # Обновляем уровень отношений
        if profile.total_messages > 50:
            profile.relationship_level = "friend"
        elif profile.total_messages > 10:
            profile.relationship_level = "acquaintance"
        
        # Анализируем эмодзи
        emojis = re.findall(r'[😀-🙏]', message)
        for emoji in emojis:
            if emoji not in profile.favorite_emojis:
                profile.favorite_emojis.append(emoji)
            if len(profile.favorite_emojis) > 10:
                profile.favorite_emojis = profile.favorite_emojis[-10:]
        
        await self._save_user_profile(profile)
    
    async def save_conversation_memory(self, user_id: int, chat_id: int, topic: str, 
                                      summary: str, key_facts: List[str], emotional_tone: str,
                                      importance_score: float = 0.5):
        """💭 Сохранение памяти о разговоре"""
        memory = ConversationMemory(
            user_id=user_id,
            chat_id=chat_id,
            topic=topic,
            summary=summary,
            key_facts=key_facts,
            emotional_tone=emotional_tone,
            importance_score=importance_score,
            timestamp=datetime.now()
        )
        
        self.conversation_memories.append(memory)
        
        # Ограничиваем количество воспоминаний в памяти
        if len(self.conversation_memories) > 1000:
            self.conversation_memories = sorted(self.conversation_memories, 
                                              key=lambda x: x.importance_score, reverse=True)[:800]
        
        # Сохраняем в БД
        try:
            await self.db.execute("""
                INSERT INTO conversation_memories 
                (user_id, chat_id, topic, summary, key_facts, emotional_tone, 
                 importance_score, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                memory.user_id, memory.chat_id, memory.topic, memory.summary,
                json.dumps(memory.key_facts, ensure_ascii=False), memory.emotional_tone,
                memory.importance_score, memory.timestamp.isoformat()
            ))
            
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения памяти: {e}")
    
    async def add_personal_fact(self, user_id: int, category: str, fact: str, 
                               confidence: float = 0.8, source: str = "direct"):
        """📝 Добавление личного факта о пользователе"""
        personal_fact = PersonalFact(
            user_id=user_id,
            category=category,
            fact=fact,
            confidence=confidence,
            source=source,
            timestamp=datetime.now()
        )
        
        self.personal_facts[user_id].append(personal_fact)
        
        # Ограничиваем количество фактов
        if len(self.personal_facts[user_id]) > 50:
            self.personal_facts[user_id] = sorted(
                self.personal_facts[user_id], 
                key=lambda x: x.confidence * x.relevance_score, 
                reverse=True
            )[:40]
        
        # Сохраняем в БД
        try:
            await self.db.execute("""
                INSERT INTO personal_facts 
                (user_id, category, fact, confidence, source, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                personal_fact.user_id, personal_fact.category, personal_fact.fact,
                personal_fact.confidence, personal_fact.source, 
                personal_fact.timestamp.isoformat()
            ))
            
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения факта: {e}")
    
    async def get_user_context(self, user_id: int, chat_id: int, limit: int = 5) -> Dict[str, Any]:
        """🔍 Получение контекста для пользователя"""
        profile = await self.get_or_create_user_profile(user_id)
        
        # Получаем релевантные воспоминания
        relevant_memories = [
            memory for memory in self.conversation_memories
            if memory.user_id == user_id and memory.chat_id == chat_id
        ]
        
        # Сортируем по важности и времени
        relevant_memories = sorted(
            relevant_memories,
            key=lambda x: (x.importance_score, x.timestamp),
            reverse=True
        )[:limit]
        
        # Получаем личные факты
        personal_facts = self.personal_facts.get(user_id, [])
        personal_facts = sorted(personal_facts, 
                              key=lambda x: x.confidence * x.relevance_score,
                              reverse=True)[:10]
        
        # Формируем контекст
        context = {
            'profile': {
                'name': profile.name,
                'relationship_level': profile.relationship_level,
                'total_messages': profile.total_messages,
                'interests': profile.interests,
                'personality_traits': profile.personality_traits,
                'preferred_topics': profile.preferred_topics,
                'communication_style': profile.communication_style,
                'favorite_emojis': profile.favorite_emojis,
                'last_interaction': profile.last_interaction
            },
            'memories': [
                {
                    'topic': memory.topic,
                    'summary': memory.summary,
                    'key_facts': memory.key_facts,
                    'emotional_tone': memory.emotional_tone,
                    'timestamp': memory.timestamp
                }
                for memory in relevant_memories
            ],
            'personal_facts': [
                {
                    'category': fact.category,
                    'fact': fact.fact,
                    'confidence': fact.confidence
                }
                for fact in personal_facts
            ]
        }
        
        return context
    
    async def extract_facts_from_message(self, user_id: int, message: str) -> List[PersonalFact]:
        """🔍 Извлечение фактов из сообщения"""
        facts = []
        message_lower = message.lower()
        
        # Паттерны для извлечения фактов
        fact_patterns = {
            'work': [
                r'работаю (.*)', r'моя работа (.*)', r'я (программист|врач|учитель|менеджер)',
                r'в офисе (.*)', r'мой начальник (.*)', r'коллеги (.*)'
            ],
            'family': [
                r'моя (мама|папа|жена|муж) (.*)', r'у меня есть (сын|дочь|брат|сестра)',
                r'мои родители (.*)', r'семья (.*)'
            ],
            'hobbies': [
                r'люблю (.*)', r'увлекаюсь (.*)', r'хобби (.*)', r'играю в (.*)',
                r'читаю (.*)', r'смотрю (.*)'
            ],
            'personal': [
                r'мне (\d+) (лет|года|год)', r'я из (.*)', r'живу в (.*)',
                r'учился в (.*)', r'окончил (.*)'
            ],
            'preferences': [
                r'не люблю (.*)', r'ненавижу (.*)', r'обожаю (.*)', 
                r'предпочитаю (.*)', r'мой любимый (.*)'
            ]
        }
        
        for category, patterns in fact_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, message_lower)
                for match in matches:
                    fact_text = match if isinstance(match, str) else ' '.join(match)
                    if len(fact_text.strip()) > 2:  # Минимальная длина факта
                        fact = PersonalFact(
                            user_id=user_id,
                            category=category,
                            fact=f"{pattern.split('(')[0]} {fact_text}".strip(),
                            confidence=0.7,
                            source="inferred",
                            timestamp=datetime.now()
                        )
                        facts.append(fact)
        
        return facts
    
    async def get_conversation_suggestions(self, user_id: int) -> List[str]:
        """💡 Предложения для продолжения разговора"""
        profile = await self.get_or_create_user_profile(user_id)
        suggestions = []
        
        # На основе интересов
        if profile.interests:
            interest = random.choice(profile.interests)
            suggestions.append(f"Кстати, что думаешь о {interest}?")
        
        # На основе предыдущих тем
        if profile.preferred_topics:
            top_topic = max(profile.preferred_topics, key=profile.preferred_topics.get)
            suggestions.append(f"Помню, ты интересуешься {top_topic}")
        
        # На основе личных фактов
        user_facts = self.personal_facts.get(user_id, [])
        if user_facts:
            fact = random.choice(user_facts)
            if fact.category == 'work':
                suggestions.append("Как дела на работе?")
            elif fact.category == 'hobbies':
                suggestions.append("Чем занимаешься в свободное время?")
        
        return suggestions[:3]  # Максимум 3 предложения
    
    async def cleanup_old_memories(self, days: int = 30):
        """🧹 Очистка старых воспоминаний"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Удаляем из памяти
        self.conversation_memories = [
            memory for memory in self.conversation_memories
            if memory.timestamp > cutoff_date or memory.importance_score > 0.8
        ]
        
        # Удаляем из БД
        try:
            await self.db.execute("""
                DELETE FROM conversation_memories 
                WHERE timestamp < ? AND importance_score < 0.8
            """, (cutoff_date.isoformat(),))
            
            logger.info(f"🧹 Очищены воспоминания старше {days} дней")
            
        except Exception as e:
            logger.error(f"❌ Ошибка очистки памяти: {e}")


# =================== ЭКСПОРТ ===================

__all__ = [
    "ConversationMemoryModule",
    "UserProfile", 
    "ConversationMemory",
    "PersonalFact"
]