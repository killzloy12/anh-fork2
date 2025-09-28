#!/usr/bin/env python3
"""
🎭 MEDIA TRIGGERS MODULE v3.0 - МУЛЬТИМЕДИЙНЫЕ ТРИГГЕРЫ
🎨 Расширенные триггеры с поддержкой стикеров, GIF, эмодзи и аудио

НОВЫЕ ВОЗМОЖНОСТИ:
• Отправка стикеров по триггерам
• Автоматические GIF-реакции
• Умные эмодзи ответы
• Голосовые сообщения
• Анализ полученных стикеров
• Реакции на аудио сообщения
• Контекстные медиа-ответы
• Коллекции стикеров по темам
• Генерация голосовых ответов через TTS
"""

import logging
import asyncio
import random
import re
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import aiofiles
import aiohttp

logger = logging.getLogger(__name__)


@dataclass
class MediaContent:
    """🎨 Медиа контент"""
    type: str  # sticker, gif, emoji, audio, voice
    content: str  # file_id для telegram или путь к файлу
    description: str = ""
    tags: List[str] = field(default_factory=list)
    emotion: str = "neutral"
    context: str = "general"
    usage_count: int = 0
    success_rate: float = 0.0


@dataclass
class MediaTriggerAction:
    """🎬 Медиа-действие триггера"""
    type: str  # send_sticker, send_gif, send_emoji, send_audio, send_voice, react_emoji
    content: str  # ID медиа или текст для генерации
    probability: float = 1.0
    delay: float = 0.0
    context_filters: List[str] = field(default_factory=list)
    emotion_match: str = "any"


class StickerAnalyzer:
    """🎭 Анализатор стикеров"""
    
    def __init__(self):
        # Эмоциональные категории стикеров
        self.sticker_emotions = {
            'радость': ['😄', '😊', '🎉', '👍', '❤️', '🥰', '😍'],
            'грусть': ['😢', '😭', '💔', '😔', '☹️', '😿'],
            'злость': ['😠', '😡', '🤬', '💢', '👿', '🖕'],
            'удивление': ['😮', '😲', '🤯', '😱', '🙀'],
            'смех': ['😂', '🤣', '😆', '🤪', '😋'],
            'любовь': ['❤️', '💕', '💖', '😍', '🥰', '😘'],
            'усталость': ['😴', '🥱', '😪', '💤'],
            'думаю': ['🤔', '🧐', '💭', '🤨'],
            'привет': ['👋', '🙋', '👍'],
            'пока': ['👋', '✋', '🖐️'],
            'ок': ['👌', '👍', '✅', '🆗'],
            'нет': ['❌', '🚫', '👎', '🙅'],
            'да': ['✅', '👍', '👌', '💯'],
            'вопрос': ['❓', '❔', '🤷']
        }
        
        # Контекстные стикеры
        self.context_stickers = {
            'работа': ['💼', '⚡', '💪', '🔥', '📈'],
            'учеба': ['📚', '🎓', '✏️', '📝', '🤓'],
            'спорт': ['⚽', '🏀', '🏈', '🎾', '🏃', '💪'],
            'еда': ['🍕', '🍔', '🍰', '☕', '🍺', '🥳'],
            'погода': ['☀️', '🌧️', '❄️', '⛈️', '🌈'],
            'время': ['⏰', '🕐', '🌅', '🌙', '⭐'],
            'праздник': ['🎉', '🎂', '🎁', '🥳', '🎊'],
            'путешествие': ['✈️', '🚗', '🏖️', '🏔️', '🌍']
        }
    
    def analyze_sticker_emotion(self, sticker_emoji: str) -> Tuple[str, float]:
        """🔍 Анализ эмоции стикера"""
        for emotion, emojis in self.sticker_emotions.items():
            if sticker_emoji in emojis:
                return emotion, 0.8
        
        return 'нейтральная', 0.3
    
    def get_response_sticker(self, input_emotion: str, context: str = "general") -> Optional[str]:
        """🎭 Подбор ответного стикера"""
        
        # Эмоциональные ответы
        emotion_responses = {
            'радость': ['😄', '🎉', '👍', '🥳'],
            'грусть': ['🤗', '😊', '💪', '❤️'],  # Поддерживающие
            'злость': ['😌', '🤷', '☮️'],       # Успокаивающие
            'удивление': ['😮', '🤯', '😲'],
            'смех': ['😂', '🤣', '😆'],
            'любовь': ['❤️', '😍', '🥰'],
            'привет': ['👋', '😊', '🙋'],
            'пока': ['👋', '😊', '🤗'],
            'вопрос': ['🤔', '💭', '🧐'],
            'ок': ['👌', '✅', '👍'],
            'нет': ['🤷', '😔', '👎'],
            'да': ['👍', '✅', '💯']
        }
        
        if input_emotion in emotion_responses:
            return random.choice(emotion_responses[input_emotion])
        
        # Контекстные ответы
        if context in self.context_stickers:
            return random.choice(self.context_stickers[context])
        
        # Общие дружелюбные стикеры
        general_stickers = ['😊', '👍', '🙂', '😌', '👌']
        return random.choice(general_stickers)


class GifManager:
    """🎬 Менеджер GIF"""
    
    def __init__(self):
        self.gif_collections = {
            'привет': [
                'CAACAgIAAxkBAAIBYmJ1h2fXYe...',  # Примерные file_id
                'CAACAgIAAxkBAAIBY2J1h2fXYf...'
            ],
            'пока': [
                'CAACAgIAAxkBAAIBZGJ1h2fXYg...',
                'CAACAgIAAxkBAAIBZWJ1h2fXYh...'
            ],
            'да': [
                'CAACAgIAAxkBAAIBZmJ1h2fXYi...',
                'CAACAgIAAxkBAAIBZ2J1h2fXYj...'
            ],
            'нет': [
                'CAACAgIAAxkBAAIBaGJ1h2fXYk...',
                'CAACAgIAAxkBAAIBaWJ1h2fXYl...'
            ],
            'смех': [
                'CAACAgIAAxkBAAIBamJ1h2fXYm...',
                'CAACAgIAAxkBAAIBa2J1h2fXYn...'
            ],
            'танец': [
                'CAACAgIAAxkBAAIBbGJ1h2fXYo...',
                'CAACAgIAAxkBAAIBbWJ1h2fXYp...'
            ],
            'аплодисменты': [
                'CAACAgIAAxkBAAIBbmJ1h2fXYq...',
                'CAACAgIAAxkBAAIBb2J1h2fXYr...'
            ],
            'поцелуй': [
                'CAACAgIAAxkBAAIBcGJ1h2fXYs...',
                'CAACAgIAAxkBAAIBcWJ1h2fXYt...'
            ],
            'удивление': [
                'CAACAgIAAxkBAAIBcmJ1h2fXYu...',
                'CAACAgIAAxkBAAIBc2J1h2fXYv...'
            ],
            'грустно': [
                'CAACAgIAAxkBAAIBdGJ1h2fXYw...',
                'CAACAgIAAxkBAAIBdWJ1h2fXYx...'
            ]
        }
    
    def get_gif_by_emotion(self, emotion: str) -> Optional[str]:
        """🎬 Получить GIF по эмоции"""
        emotion_mapping = {
            'радость': 'танец',
            'смех': 'смех',
            'грусть': 'грустно',
            'удивление': 'удивление',
            'любовь': 'поцелуй',
            'привет': 'привет',
            'пока': 'пока',
            'да': 'аплодисменты',
            'нет': 'грустно'
        }
        
        gif_type = emotion_mapping.get(emotion)
        if gif_type and gif_type in self.gif_collections:
            return random.choice(self.gif_collections[gif_type])
        
        return None
    
    def get_random_gif(self, category: str = None) -> Optional[str]:
        """🎲 Случайный GIF"""
        if category and category in self.gif_collections:
            return random.choice(self.gif_collections[category])
        
        # Случайный GIF из любой категории
        all_gifs = []
        for gifs in self.gif_collections.values():
            all_gifs.extend(gifs)
        
        return random.choice(all_gifs) if all_gifs else None


class AudioManager:
    """🎵 Менеджер аудио"""
    
    def __init__(self):
        self.audio_clips = {
            'привет': [
                'AwACAgIAAxkBAAIBfGJ1h2fXY0...',  # Примерные voice file_id
                'AwACAgIAAxkBAAIBfWJ1h2fXY1...'
            ],
            'пока': [
                'AwACAgIAAxkBAAIBfmJ1h2fXY2...',
                'AwACAgIAAxkBAAIBf2J1h2fXY3...'
            ],
            'спасибо': [
                'AwACAgIAAxkBAAIBgGJ1h2fXY4...',
                'AwACAgIAAxkBAAIBgWJ1h2fXY5...'
            ],
            'смех': [
                'AwACAgIAAxkBAAIBgmJ1h2fXY6...',
                'AwACAgIAAxkBAAIBg2J1h2fXY7...'
            ]
        }
        
        # TTS настройки (если доступно)
        self.tts_available = False
    
    def get_audio_by_emotion(self, emotion: str) -> Optional[str]:
        """🎵 Получить аудио по эмоции"""
        emotion_mapping = {
            'радость': 'смех',
            'благодарность': 'спасибо',
            'привет': 'привет',
            'пока': 'пока'
        }
        
        audio_type = emotion_mapping.get(emotion)
        if audio_type and audio_type in self.audio_clips:
            return random.choice(self.audio_clips[audio_type])
        
        return None
    
    async def generate_tts_audio(self, text: str, emotion: str = "neutral") -> Optional[str]:
        """🗣️ Генерация TTS аудио"""
        if not self.tts_available:
            return None
        
        try:
            # Здесь будет интеграция с TTS сервисом
            # Например, с Google TTS, Amazon Polly, или локальным TTS
            
            # Пока возвращаем None
            return None
            
        except Exception as e:
            logger.error(f"❌ Ошибка генерации TTS: {e}")
            return None


class MediaTriggersModule:
    """🎭 Модуль мультимедийных триггеров"""
    
    def __init__(self, db_service, config, bot):
        self.db = db_service
        self.config = config
        self.bot = bot
        
        self.sticker_analyzer = StickerAnalyzer()
        self.gif_manager = GifManager()
        self.audio_manager = AudioManager()
        
        # Коллекции медиа
        self.media_collections = {
            'stickers': {},
            'gifs': {},
            'audio': {}
        }
        
        logger.info("🎭 Модуль мультимедийных триггеров инициализирован")
    
    async def initialize(self):
        """🚀 Инициализация модуля"""
        await self._create_media_tables()
        await self._load_media_collections()
        await self._setup_default_media_triggers()
        logger.info("🎭 Мультимедийные триггеры загружены")
    
    async def _create_media_tables(self):
        """📋 Создание таблиц для медиа"""
        tables = [
            """
            CREATE TABLE IF NOT EXISTS media_content (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,  -- sticker, gif, emoji, audio, voice
                content TEXT NOT NULL,  -- file_id или путь
                description TEXT,
                tags TEXT,  -- JSON
                emotion TEXT DEFAULT 'neutral',
                context TEXT DEFAULT 'general',
                usage_count INTEGER DEFAULT 0,
                success_rate REAL DEFAULT 0.0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """,
            
            """
            CREATE TABLE IF NOT EXISTS media_triggers (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                trigger_type TEXT NOT NULL,  -- emotion, keyword, context, time
                trigger_pattern TEXT NOT NULL,
                media_type TEXT NOT NULL,
                media_content TEXT NOT NULL,
                probability REAL DEFAULT 1.0,
                cooldown REAL DEFAULT 0.0,
                allowed_chats TEXT,  -- JSON
                allowed_users TEXT,  -- JSON
                is_active BOOLEAN DEFAULT TRUE,
                usage_count INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """,
            
            """
            CREATE TABLE IF NOT EXISTS sticker_responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                input_sticker_id TEXT,
                input_emotion TEXT,
                response_type TEXT,  -- sticker, gif, emoji
                response_content TEXT,
                confidence REAL DEFAULT 0.8,
                usage_count INTEGER DEFAULT 0,
                success_rate REAL DEFAULT 0.0
            )
            """
        ]
        
        for table_sql in tables:
            await self.db.execute(table_sql)
    
    async def _load_media_collections(self):
        """📥 Загрузка медиа коллекций"""
        try:
            media_items = await self.db.fetch_all("SELECT * FROM media_content")
            
            for item in media_items:
                media_content = MediaContent(
                    type=item['type'],
                    content=item['content'],
                    description=item['description'] or '',
                    tags=json.loads(item['tags'] or '[]'),
                    emotion=item['emotion'],
                    context=item['context'],
                    usage_count=item['usage_count'],
                    success_rate=item['success_rate']
                )
                
                if item['type'] not in self.media_collections:
                    self.media_collections[item['type']] = {}
                
                self.media_collections[item['type']][item['content']] = media_content
                
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки медиа: {e}")
    
    async def _setup_default_media_triggers(self):
        """🎯 Настройка триггеров по умолчанию"""
        
        default_triggers = [
            {
                'id': 'happy_sticker_response',
                'name': 'Ответ на радостный стикер',
                'trigger_type': 'emotion',
                'trigger_pattern': 'радость',
                'media_type': 'emoji',
                'media_content': '😊|🎉|👍|❤️',
                'probability': 0.8
            },
            {
                'id': 'sad_sticker_support',
                'name': 'Поддержка при грусти',
                'trigger_type': 'emotion', 
                'trigger_pattern': 'грусть',
                'media_type': 'emoji',
                'media_content': '🤗|💪|😊|❤️',
                'probability': 0.9
            },
            {
                'id': 'hello_gif_response',
                'name': 'GIF приветствие',
                'trigger_type': 'keyword',
                'trigger_pattern': 'привет|дарова|здрав',
                'media_type': 'gif',
                'media_content': 'привет',
                'probability': 0.3,
                'cooldown': 300  # 5 минут
            },
            {
                'id': 'laugh_reaction',
                'name': 'Реакция на смех',
                'trigger_type': 'emotion',
                'trigger_pattern': 'смех',
                'media_type': 'gif',
                'media_content': 'смех',
                'probability': 0.6
            },
            {
                'id': 'thanks_audio',
                'name': 'Аудио благодарность',
                'trigger_type': 'keyword',
                'trigger_pattern': 'спасибо|благодар|сенк',
                'media_type': 'audio',
                'media_content': 'спасибо',
                'probability': 0.4
            },
            {
                'id': 'question_thinking',
                'name': 'Думающий смайлик на вопросы',
                'trigger_type': 'keyword',
                'trigger_pattern': '\\?',
                'media_type': 'emoji',
                'media_content': '🤔|💭|🧐',
                'probability': 0.2
            }
        ]
        
        for trigger_data in default_triggers:
            # Проверяем, есть ли уже такой триггер
            existing = await self.db.fetch_one(
                "SELECT id FROM media_triggers WHERE id = ?",
                (trigger_data['id'],)
            )
            
            if not existing:
                await self._save_media_trigger(trigger_data)
    
    async def _save_media_trigger(self, trigger_data: Dict):
        """💾 Сохранение медиа триггера"""
        try:
            await self.db.execute("""
                INSERT INTO media_triggers 
                (id, name, description, trigger_type, trigger_pattern, media_type, 
                 media_content, probability, cooldown, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                trigger_data['id'],
                trigger_data['name'],
                trigger_data.get('description', ''),
                trigger_data['trigger_type'],
                trigger_data['trigger_pattern'],
                trigger_data['media_type'],
                trigger_data['media_content'],
                trigger_data.get('probability', 1.0),
                trigger_data.get('cooldown', 0.0),
                True
            ))
            
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения медиа триггера: {e}")
    
    async def process_sticker(self, sticker, user_id: int, chat_id: int, context: Dict = None) -> List[Dict]:
        """🎭 Обработка полученного стикера"""
        responses = []
        
        try:
            # Анализируем эмоцию стикера
            sticker_emoji = sticker.emoji if hasattr(sticker, 'emoji') and sticker.emoji else '🙂'
            emotion, confidence = self.sticker_analyzer.analyze_sticker_emotion(sticker_emoji)
            
            logger.info(f"🎭 Стикер проанализирован: эмоция={emotion}, уверенность={confidence}")
            
            # Ищем подходящие медиа триггеры
            media_triggers = await self.db.fetch_all("""
                SELECT * FROM media_triggers 
                WHERE is_active = TRUE AND (trigger_type = 'emotion' OR trigger_type = 'sticker')
                ORDER BY probability DESC
            """)
            
            for trigger in media_triggers:
                should_respond = False
                
                if trigger['trigger_type'] == 'emotion':
                    should_respond = (emotion == trigger['trigger_pattern'] and 
                                    confidence >= 0.5)
                elif trigger['trigger_type'] == 'sticker':
                    should_respond = sticker_emoji in trigger['trigger_pattern']
                
                if should_respond and random.random() < trigger['probability']:
                    # Генерируем медиа ответ
                    media_response = await self._generate_media_response(
                        trigger['media_type'], 
                        trigger['media_content'],
                        emotion,
                        context
                    )
                    
                    if media_response:
                        responses.append(media_response)
                        
                        # Обновляем статистику
                        await self._update_trigger_stats(trigger['id'])
                        
                        # Если сработал высокоприоритетный триггер, прерываем
                        if trigger['probability'] > 0.7:
                            break
            
            # Если нет специальных триггеров, используем базовую логику
            if not responses and random.random() < 0.3:  # 30% шанс
                response_emoji = self.sticker_analyzer.get_response_sticker(emotion)
                if response_emoji:
                    responses.append({
                        'type': 'emoji',
                        'content': response_emoji
                    })
            
            return responses
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки стикера: {e}")
            return []
    
    async def process_text_for_media(self, message: str, emotion: str, context: Dict) -> List[Dict]:
        """📝 Обработка текста для медиа триггеров"""
        responses = []
        
        try:
            # Получаем активные медиа триггеры
            media_triggers = await self.db.fetch_all("""
                SELECT * FROM media_triggers 
                WHERE is_active = TRUE 
                ORDER BY probability DESC
            """)
            
            message_lower = message.lower()
            
            for trigger in media_triggers:
                should_respond = False
                
                if trigger['trigger_type'] == 'keyword':
                    # Проверяем ключевые слова
                    pattern = trigger['trigger_pattern']
                    if '|' in pattern:
                        keywords = pattern.split('|')
                        should_respond = any(keyword in message_lower for keyword in keywords)
                    else:
                        should_respond = re.search(pattern, message_lower) is not None
                
                elif trigger['trigger_type'] == 'emotion':
                    should_respond = emotion == trigger['trigger_pattern']
                
                elif trigger['trigger_type'] == 'context':
                    context_value = context.get('topic', 'general')
                    should_respond = context_value == trigger['trigger_pattern']
                
                if should_respond and random.random() < trigger['probability']:
                    # Проверяем кулдаун
                    if await self._check_trigger_cooldown(trigger['id'], context.get('chat_id')):
                        media_response = await self._generate_media_response(
                            trigger['media_type'],
                            trigger['media_content'],
                            emotion,
                            context
                        )
                        
                        if media_response:
                            responses.append(media_response)
                            await self._update_trigger_stats(trigger['id'])
                            
                            # Устанавливаем кулдаун
                            await self._set_trigger_cooldown(trigger['id'], context.get('chat_id'), trigger['cooldown'])
                            
                            break  # Один медиа ответ за раз
            
            return responses
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки медиа триггеров: {e}")
            return []
    
    async def _generate_media_response(self, media_type: str, content: str, emotion: str, context: Dict) -> Optional[Dict]:
        """🎨 Генерация медиа ответа"""
        
        try:
            if media_type == 'emoji':
                # Случайный выбор из вариантов
                if '|' in content:
                    emojis = content.split('|')
                    selected_emoji = random.choice(emojis)
                else:
                    selected_emoji = content
                
                return {
                    'type': 'emoji',
                    'content': selected_emoji
                }
            
            elif media_type == 'sticker':
                # Получаем стикер по эмоции
                sticker_id = self.sticker_analyzer.get_response_sticker(emotion)
                if sticker_id:
                    return {
                        'type': 'sticker',
                        'content': sticker_id
                    }
            
            elif media_type == 'gif':
                # Получаем GIF
                if content in self.gif_manager.gif_collections:
                    gif_id = random.choice(self.gif_manager.gif_collections[content])
                    return {
                        'type': 'animation',  # Telegram тип для GIF
                        'content': gif_id
                    }
                else:
                    # Пробуем по эмоции
                    gif_id = self.gif_manager.get_gif_by_emotion(emotion)
                    if gif_id:
                        return {
                            'type': 'animation',
                            'content': gif_id
                        }
            
            elif media_type == 'audio':
                # Получаем аудио
                if content in self.audio_manager.audio_clips:
                    audio_id = random.choice(self.audio_manager.audio_clips[content])
                    return {
                        'type': 'voice',
                        'content': audio_id
                    }
                else:
                    # Пробуем по эмоции
                    audio_id = self.audio_manager.get_audio_by_emotion(emotion)
                    if audio_id:
                        return {
                            'type': 'voice',
                            'content': audio_id
                        }
            
            elif media_type == 'voice':
                # Генерируем голосовое сообщение
                voice_id = await self.audio_manager.generate_tts_audio(content, emotion)
                if voice_id:
                    return {
                        'type': 'voice',
                        'content': voice_id
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Ошибка генерации медиа ответа: {e}")
            return None
    
    async def _check_trigger_cooldown(self, trigger_id: str, chat_id: int) -> bool:
        """⏰ Проверка кулдауна триггера"""
        try:
            cooldown_key = f"{trigger_id}_{chat_id}"
            
            # Проверяем последнее использование из БД или кеша
            last_used = await self.db.fetch_one("""
                SELECT MAX(created_at) as last_used FROM media_triggers 
                WHERE id = ?
            """, (trigger_id,))
            
            if last_used and last_used['last_used']:
                last_time = datetime.fromisoformat(last_used['last_used'])
                cooldown_seconds = 300  # По умолчанию 5 минут
                
                if (datetime.now() - last_time).total_seconds() < cooldown_seconds:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки кулдауна: {e}")
            return True
    
    async def _set_trigger_cooldown(self, trigger_id: str, chat_id: int, cooldown: float):
        """🕐 Установка кулдауна триггера"""
        # Здесь можно реализовать более сложную логику кулдаунов
        pass
    
    async def _update_trigger_stats(self, trigger_id: str):
        """📊 Обновление статистики триггера"""
        try:
            await self.db.execute("""
                UPDATE media_triggers 
                SET usage_count = usage_count + 1
                WHERE id = ?
            """, (trigger_id,))
            
        except Exception as e:
            logger.error(f"❌ Ошибка обновления статистики: {e}")
    
    async def add_custom_media(self, media_type: str, content: str, tags: List[str], 
                              emotion: str = "neutral", context: str = "general") -> bool:
        """➕ Добавление пользовательского медиа"""
        try:
            await self.db.execute("""
                INSERT INTO media_content 
                (type, content, tags, emotion, context)
                VALUES (?, ?, ?, ?, ?)
            """, (media_type, content, json.dumps(tags), emotion, context))
            
            # Добавляем в память
            media_content = MediaContent(
                type=media_type,
                content=content,
                tags=tags,
                emotion=emotion,
                context=context
            )
            
            if media_type not in self.media_collections:
                self.media_collections[media_type] = {}
            
            self.media_collections[media_type][content] = media_content
            
            logger.info(f"➕ Добавлен медиа контент: {media_type} - {emotion}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка добавления медиа: {e}")
            return False
    
    async def get_media_stats(self) -> Dict[str, Any]:
        """📊 Статистика медиа"""
        try:
            # Статистика по типам медиа
            media_stats = await self.db.fetch_all("""
                SELECT type, COUNT(*) as count, AVG(success_rate) as avg_success
                FROM media_content
                GROUP BY type
            """)
            
            # Статистика триггеров
            trigger_stats = await self.db.fetch_all("""
                SELECT media_type, COUNT(*) as count, SUM(usage_count) as total_usage
                FROM media_triggers
                WHERE is_active = TRUE
                GROUP BY media_type
            """)
            
            return {
                'media_content': [dict(row) for row in media_stats],
                'triggers': [dict(row) for row in trigger_stats],
                'total_media': sum(row['count'] for row in media_stats),
                'total_triggers': len(trigger_stats)
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения статистики: {e}")
            return {}
    
    # Методы для отправки медиа через бота
    async def send_media_response(self, chat_id: int, media_response: Dict):
        """📤 Отправка медиа ответа"""
        try:
            media_type = media_response['type']
            content = media_response['content']
            
            if media_type == 'emoji':
                await self.bot.send_message(chat_id, content)
            
            elif media_type == 'sticker':
                await self.bot.send_sticker(chat_id, content)
            
            elif media_type == 'animation':  # GIF
                await self.bot.send_animation(chat_id, content)
            
            elif media_type == 'voice':
                await self.bot.send_voice(chat_id, content)
            
            elif media_type == 'audio':
                await self.bot.send_audio(chat_id, content)
            
        except Exception as e:
            logger.error(f"❌ Ошибка отправки медиа: {e}")


# =================== ЭКСПОРТ ===================

__all__ = [
    "MediaTriggersModule",
    "StickerAnalyzer", 
    "GifManager",
    "AudioManager",
    "MediaContent",
    "MediaTriggerAction"
]