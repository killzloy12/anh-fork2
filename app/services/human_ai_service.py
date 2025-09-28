#!/usr/bin/env python3
"""
🧠 HUMAN-LIKE AI SERVICE v4.0 - С ПРОИЗВОЛЬНЫМИ ПЕРСОНАЖАМИ
🚀 Интегрирован с кастомными персонажами и системой кармы

ВОЗМОЖНОСТИ:
• Обычные AI ответы (GPT-4o-mini)
• Произвольные персонажи от пользователей
• Предустановленные персонажи
• Эмоциональный анализ
• Fallback без OpenAI
"""

import logging
import asyncio
import openai
import random
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ConversationContext:
    """💬 Контекст разговора"""
    user_id: int
    chat_id: int
    messages_history: List[Dict] = None
    user_name: str = ""
    chat_type: str = "private"
    topic: str = "общение"
    mood: str = "нейтральная"
    formality_level: float = 0.5
    last_interaction: datetime = None
    
    def __post_init__(self):
        if self.messages_history is None:
            self.messages_history = []
        if self.last_interaction is None:
            self.last_interaction = datetime.now()


def create_conversation_context(user_id: int, chat_id: int, user_name: str = "") -> ConversationContext:
    """🆕 Создание нового контекста"""
    return ConversationContext(
        user_id=user_id,
        chat_id=chat_id,
        user_name=user_name,
        last_interaction=datetime.now()
    )


class EmotionAnalyzer:
    """😊 Анализатор эмоций"""
    
    def __init__(self):
        self.emotion_keywords = {
            "радость": ["рад", "счастлив", "отлично", "супер", "круто", "ура", "😊", "😄", "🎉", "👍"],
            "грусть": ["грустно", "печально", "плохо", "расстроен", "😢", "😞", "💔", "грущу"],
            "злость": ["злой", "бесит", "раздражает", "ненавижу", "😠", "😡", "🤬", "ярость"],
            "удивление": ["вау", "ого", "неожиданно", "удивлен", "😲", "😮", "🤯"],
            "страх": ["боюсь", "страшно", "пугает", "тревожно", "😨", "😰", "😱"],
            "интерес": ["интересно", "любопытно", "хочу знать", "расскажи", "🤔", "💭"]
        }
    
    def analyze(self, text: str) -> Tuple[str, float]:
        """🎯 Анализ эмоции в тексте"""
        text_lower = text.lower()
        emotion_scores = {}
        
        for emotion, keywords in self.emotion_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in text_lower:
                    score += 1
            emotion_scores[emotion] = score
        
        if not any(emotion_scores.values()):
            return "нейтральная", 0.5
        
        best_emotion = max(emotion_scores.keys(), key=lambda k: emotion_scores[k])
        confidence = min(1.0, emotion_scores[best_emotion] / 3)
        
        return best_emotion, confidence


class TopicClassifier:
    """📚 Классификатор тем"""
    
    def __init__(self):
        self.topic_keywords = {
            "программирование": ["код", "python", "javascript", "программа", "алгоритм", "баг", "функция"],
            "технологии": ["компьютер", "интернет", "приложение", "софт", "железо", "гаджет"],
            "работа": ["работа", "карьера", "офис", "начальник", "зарплата", "проект"],
            "отношения": ["любовь", "семья", "друзья", "отношения", "свидание", "парень", "девушка"],
            "учеба": ["учеба", "университет", "экзамен", "лекция", "студент", "школа"],
            "развлечения": ["фильм", "игра", "музыка", "книга", "сериал", "концерт"],
            "здоровье": ["здоровье", "болезнь", "врач", "лечение", "спорт", "диета"],
            "философия": ["жизнь", "смысл", "счастье", "мудрость", "духовность", "цель"]
        }
    
    def classify(self, text: str) -> Tuple[str, float]:
        """🎯 Классификация темы"""
        text_lower = text.lower()
        topic_scores = {}
        
        for topic, keywords in self.topic_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in text_lower:
                    score += 1
            topic_scores[topic] = score
        
        if not any(topic_scores.values()):
            return "общение", 0.5
        
        best_topic = max(topic_scores.keys(), key=lambda k: topic_scores[k])
        confidence = min(1.0, topic_scores[best_topic] / 2)
        
        return best_topic, confidence


class CasualResponseGenerator:
    """😎 Генератор обычных ответов"""
    
    def __init__(self):
        self.casual_responses = {
            "greeting": ["Привет!", "Дарова!", "Хай!", "Йо!", "Салют!"],
            "agreement": ["Да", "Точно", "Согласен", "Угу", "Ага"],
            "neutral": ["Понятно", "Ясно", "Хм", "Интересно", "И что дальше?"],
            "questions": ["А ты что думаешь?", "Расскажи больше", "Интересно, а почему?"],
            "goodbye": ["Пока!", "До встречи!", "Увидимся!", "Бай!"]
        }
    
    def generate_casual_response(self, message: str, emotion: str, topic: str, context: ConversationContext) -> str:
        """💬 Генерация обычного ответа"""
        message_lower = message.lower()
        
        # Приветствия
        if any(word in message_lower for word in ['привет', 'дарова', 'хай', 'hello']):
            return random.choice(self.casual_responses["greeting"])
        
        # Прощания
        if any(word in message_lower for word in ['пока', 'до встречи', 'goodbye', 'bye']):
            return random.choice(self.casual_responses["goodbye"])
        
        # Вопросы
        if '?' in message:
            return random.choice(self.casual_responses["questions"])
        
        # Эмоциональные ответы
        if emotion == "радость":
            return "Отлично! 😊"
        elif emotion == "грусть":
            return "Не расстраивайся 😔"
        elif emotion == "злость":
            return "Понимаю, бесит..."
        
        # Тематические ответы
        if topic == "программирование":
            return "Код рулит! 💻"
        elif topic == "работа":
            return "Работа есть работа 🏢"
        
        # Обычные ответы
        return random.choice(self.casual_responses["neutral"])


class HumanLikeAI:
    """🧠 Human-like AI с поддержкой произвольных персонажей"""
    
    def __init__(self, config):
        self.config = config
        self.openai_client = None
        self.emotion_analyzer = EmotionAnalyzer()
        self.topic_classifier = TopicClassifier()
        self.response_generator = CasualResponseGenerator()
        
        self._initialize_openai()
        logger.info("🧠 Human-like AI инициализирован")
    
    def _initialize_openai(self):
        """🔧 Инициализация OpenAI"""
        if hasattr(self.config.ai, 'openai_api_key') and self.config.ai.openai_api_key:
            try:
                self.openai_client = openai.OpenAI(api_key=self.config.ai.openai_api_key)
                logger.info("🧠 OpenAI клиент инициализирован")
            except Exception as e:
                logger.warning(f"⚠️ OpenAI недоступен: {e}")
                self.openai_client = None
        else:
            logger.info("🧠 OpenAI API ключ не найден - работаем в режиме fallback")
    
    def analyze_emotion(self, message: str) -> Tuple[str, float]:
        """😊 Анализ эмоции"""
        return self.emotion_analyzer.analyze(message)
    
    def classify_topic(self, message: str) -> Tuple[str, float]:
        """📚 Классификация темы"""
        return self.topic_classifier.classify(message)
    
    async def generate_human_response(self, message: str, context: ConversationContext) -> str:
        """🤖 Генерация обычного человеческого ответа"""
        try:
            emotion, emotion_confidence = self.analyze_emotion(message)
            topic, topic_confidence = self.classify_topic(message)
            
            context.topic = topic
            context.mood = emotion
            
            logger.info(f"🧠 Анализ: эмоция={emotion}, тема={topic}")
            
            if self.openai_client:
                try:
                    response = await self._generate_openai_response(message, context, emotion, topic)
                    if response:
                        return response
                except Exception as e:
                    logger.warning(f"⚠️ OpenAI ошибка: {e}")
            
            # Fallback
            response = self.response_generator.generate_casual_response(message, emotion, topic, context)
            logger.info(f"🧠 Fallback ответ: тема={topic}, эмоция={emotion}")
            return response
            
        except Exception as e:
            logger.error(f"❌ Ошибка генерации ответа: {e}")
            return self._generate_error_response()
    
    async def generate_response_with_custom_personality(self, message: str, context: ConversationContext, chat_id: int) -> str:
        """🎭 Генерация ответа с произвольным персонажем"""
        try:
            # Пытаемся получить активного персонажа
            custom_personality = None
            
            # Ищем в глобальных модулях
            import sys
            if 'modules' in globals():
                modules = globals()['modules']
            elif hasattr(sys.modules.get('__main__'), 'modules'):
                modules = sys.modules.get('__main__').modules
            else:
                modules = None
            
            if modules and hasattr(modules, 'custom_personality_manager'):
                custom_pm = modules.custom_personality_manager
                custom_personality = custom_pm.get_active_personality(chat_id)
            elif modules and 'custom_personality_manager' in modules:
                custom_pm = modules['custom_personality_manager']
                custom_personality = custom_pm.get_active_personality(chat_id)
            
            # Если есть кастомный персонаж - используем его
            if custom_personality:
                return await self._generate_custom_personality_response(message, context, custom_personality)
            
            # Fallback на обычную генерацию
            return await self.generate_human_response(message, context)
            
        except Exception as e:
            logger.error(f"❌ Ошибка генерации с персонажем: {e}")
            return await self.generate_human_response(message, context)
    
    async def _generate_custom_personality_response(self, message: str, context: ConversationContext, custom_personality) -> str:
        """🎭 Генерация ответа для произвольного персонажа"""
        try:
            emotion, emotion_confidence = self.analyze_emotion(message)
            topic, topic_confidence = self.classify_topic(message)
            
            context.topic = topic
            context.mood = emotion
            
            logger.info(f"🎭 Кастомный персонаж: {custom_personality.description[:30]}... (эмоция={emotion}, тема={topic})")
            
            # Если OpenAI доступно
            if self.openai_client:
                try:
                    response = await self._generate_custom_openai_response(message, context, emotion, topic, custom_personality)
                    if response:
                        # Обновляем статистику использования
                        try:
                            import sys
                            if 'modules' in globals():
                                modules = globals()['modules']
                            elif hasattr(sys.modules.get('__main__'), 'modules'):
                                modules = sys.modules.get('__main__').modules
                            
                            if modules and hasattr(modules, 'custom_personality_manager'):
                                custom_pm = modules.custom_personality_manager
                                await custom_pm.db.execute("""
                                    UPDATE custom_personalities 
                                    SET usage_count = usage_count + 1, last_used = ?
                                    WHERE id = ?
                                """, (datetime.now().isoformat(), custom_personality.id))
                        except Exception as e:
                            logger.warning(f"⚠️ Ошибка обновления статистики персонажа: {e}")
                        
                        return response
                except Exception as e:
                    logger.warning(f"⚠️ OpenAI ошибка для кастомного персонажа: {e}")
            
            # Fallback для кастомного персонажа
            return self._generate_custom_personality_fallback(message, emotion, topic, custom_personality)
            
        except Exception as e:
            logger.error(f"❌ Ошибка кастомного персонажа: {e}")
            return self._generate_error_response()
    
    async def _generate_custom_openai_response(self, message: str, context: ConversationContext, emotion: str, topic: str, custom_personality) -> Optional[str]:
        """🎭 OpenAI ответ для произвольного персонажа"""
        try:
            # Используем системный промпт персонажа напрямую
            system_prompt = custom_personality.system_prompt
            
            # Добавляем эмоциональный контекст
            emotion_context = ""
            if emotion != "нейтральная":
                emotion_context = f"\n\nПользователь сейчас испытывает {emotion}. Учти это в своем ответе."
            
            # Добавляем контекст темы
            topic_context = ""
            if topic != "общение":
                topic_context = f"\nТема разговора: {topic}."
            
            final_prompt = f"{system_prompt}{emotion_context}{topic_context}\n\nОтвечай коротко (1-2 предложения), естественно, в характере персонажа."
            
            response = await asyncio.to_thread(
                self.openai_client.chat.completions.create,
                model=self.config.ai.default_model,
                messages=[
                    {"role": "system", "content": final_prompt},
                    {"role": "user", "content": message}
                ],
                temperature=0.9,
                max_tokens=150
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"❌ Ошибка OpenAI кастомного персонажа: {e}")
            return None
    
    def _generate_custom_personality_fallback(self, message: str, emotion: str, topic: str, custom_personality) -> str:
        """🎭 Fallback ответы для произвольного персонажа"""
        message_lower = message.lower()
        
        # Базовые ответы на основе описания персонажа
        description = custom_personality.description.lower()
        
        # 1. Приветствия
        if any(word in message_lower for word in ['привет', 'здрав', 'дарова', 'хай', 'hello']):
            if 'хакер' in description:
                return "Привет! Готов взломать систему? 💻"
            elif 'бабушка' in description:
                return "Здравствуй, милый! Чаю хочешь? 👵🍵"
            elif 'пират' in description:
                return "Йо-хо-хо! Приветствую, матрос! ⚓"
            elif 'учитель' in description:
                return "Здравствуйте! Садитесь, начинаем урок 📚"
            elif 'врач' in description:
                return "Добро пожаловать! Что вас беспокоит? 👨‍⚕️"
            elif 'повар' in description:
                return "Добро пожаловать на кухню! Что готовим? 👨‍🍳"
            else:
                return f"Привет! Я {custom_personality.description} 😊"
        
        # 2. Вопросы
        if '?' in message:
            if 'хакер' in description:
                return "Интересный вопрос... Дай-ка подумаю в терминале 🖥️"
            elif 'философ' in description:
                return "А что ты сам думаешь об этом? 🤔"
            elif 'учитель' in description:
                return "Отличный вопрос! Разберем пошагово 📝"
            else:
                return "Хм, интересно... Дай подумаю 💭"
        
        # 3. Эмоциональные реакции
        if emotion == "радость":
            if 'серьезный' in description or 'строгий' in description:
                return "Хорошо видеть вашу радость, хотя и сдержанно 😐"
            else:
                return "Отлично! Разделяю твою радость! 😄"
        elif emotion == "грусть":
            if 'добрый' in description or 'заботливый' in description:
                return "Не грусти, все будет хорошо ❤️"
            elif 'строгий' in description:
                return "Соберитесь. Трудности закаляют характер 💪"
            else:
                return "Понимаю твои чувства... 😔"
        
        # 4. Тематические ответы
        if 'программирование' in topic or 'код' in message_lower:
            if 'хакер' in description:
                return "Код - это поэзия! Какой язык используешь? 💻"
            elif 'учитель' in description:
                return "Программирование - важный навык! Изучаем? 📚"
        
        # 5. Ключевые слова из описания
        description_words = description.split()
        for word in description_words:
            if word in message_lower and len(word) > 3:
                return f"О, {word}! Это моя стихия! ✨"
        
        # 6. Универсальные ответы в стиле персонажа
        if 'крутой' in description or 'крутая' in description:
            return "Да, я крут! А ты как дела? 😎"
        elif 'добрый' in description or 'добрая' in description:
            return "Я здесь, чтобы помочь! Что нужно? 🤗"
        elif 'умный' in description or 'умная' in description:
            return "Интересная мысль! Развиваем дальше? 🧠"
        elif 'веселый' in description or 'веселая' in description:
            return "Хаха! Развлекаемся? 😄"
        elif 'серьезный' in description or 'серьезная' in description:
            return "Это требует серьезного подхода 🤔"
        
        # 7. Fallback на основе промпта
        if len(custom_personality.system_prompt) > 20:
            # Берем ключевые слова из промпта
            prompt_words = custom_personality.system_prompt.lower().split()
            relevant_words = [w for w in prompt_words if len(w) > 4 and w.isalpha()]
            if relevant_words:
                return f"Понимаю! Это связано с {relevant_words[0]} ✨"
        
        # 8. Последний fallback
        return f"Как {custom_personality.description[:30]}..., скажу: интересно! 🤔"
    
    async def _generate_openai_response(self, message: str, context: ConversationContext, emotion: str, topic: str) -> Optional[str]:
        """🤖 OpenAI ответ"""
        try:
            system_prompt = f"""Ты дружелюбный AI-помощник. Общаешься неформально, как друг. 
Используй короткие ответы (1-2 предложения). 
Текущая эмоция пользователя: {emotion}
Тема разговора: {topic}
Будь живым и эмоциональным, но не слишком навязчивым."""
            
            response = await asyncio.to_thread(
                self.openai_client.chat.completions.create,
                model=self.config.ai.default_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                temperature=0.8,
                max_tokens=100
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"❌ Ошибка OpenAI: {e}")
            return None
    
    def _generate_error_response(self) -> str:
        """❌ Ответ при ошибке"""
        error_responses = [
            "Что-то пошло не так... 🤔",
            "Хм, ошибочка вышла 😅",
            "Сейчас подумаю... 💭",
            "Дай секунду разобраться 🔄"
        ]
        return random.choice(error_responses)


# =================== ЭКСПОРТ ===================

__all__ = [
    "HumanLikeAI",
    "ConversationContext",
    "create_conversation_context"
]