#!/usr/bin/env python3
"""
🔧 МИГРАЦИЯ БАЗЫ ДАННЫХ v3.2
Добавляет отсутствующий столбец admin_id в таблицу custom_personalities
"""

import asyncio
import aiosqlite
import os

async def migrate_database():
    """🔄 Миграция базы данных"""
    
    db_path = "data/bot.db"
    
    if not os.path.exists(db_path):
        print("❌ База данных не найдена")
        return
    
    try:
        async with aiosqlite.connect(db_path) as db:
            print("🔧 Проверяем структуру таблицы custom_personalities...")
            
            # Проверяем существует ли столбец admin_id
            cursor = await db.execute("PRAGMA table_info(custom_personalities)")
            columns = await cursor.fetchall()
            
            column_names = [col[1] for col in columns]
            
            if 'admin_id' not in column_names:
                print("➕ Добавляем столбец admin_id...")
                
                # Добавляем столбец admin_id
                await db.execute("""
                    ALTER TABLE custom_personalities 
                    ADD COLUMN admin_id INTEGER DEFAULT 0
                """)
                
                await db.commit()
                print("✅ Столбец admin_id добавлен")
                
                # Обновляем существующие записи (если есть)
                await db.execute("""
                    UPDATE custom_personalities 
                    SET admin_id = user_id 
                    WHERE admin_id = 0
                """)
                
                await db.commit()
                print("✅ Существующие записи обновлены")
                
            else:
                print("ℹ️ Столбец admin_id уже существует")
            
            # Проверяем финальную структуру
            cursor = await db.execute("PRAGMA table_info(custom_personalities)")
            columns = await cursor.fetchall()
            
            print("\n📋 Структура таблицы custom_personalities:")
            for col in columns:
                print(f"  • {col[1]} ({col[2]})")
            
            print("\n✅ Миграция завершена успешно!")
            
    except Exception as e:
        print(f"❌ Ошибка миграции: {e}")

if __name__ == "__main__":
    asyncio.run(migrate_database())