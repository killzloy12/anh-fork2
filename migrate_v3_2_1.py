#!/usr/bin/env python3
"""
🔧 МИГРАЦИЯ v3.2.1 - Добавляем недостающие столбцы
"""

import asyncio
import aiosqlite
import os

async def migrate_personality_table():
    """🔄 Добавляем недостающие столбцы для v3.2"""
    
    db_path = "data/bot.db"
    
    if not os.path.exists(db_path):
        print("❌ База данных не найдена")
        return
    
    try:
        async with aiosqlite.connect(db_path) as db:
            print("🔧 Проверяем столбцы таблицы custom_personalities...")
            
            # Проверяем структуру таблицы
            cursor = await db.execute("PRAGMA table_info(custom_personalities)")
            columns = await cursor.fetchall()
            
            column_names = [col[1] for col in columns]
            print(f"📋 Найдены столбцы: {column_names}")
            
            # Добавляем недостающие столбцы для v3.2
            missing_columns = []
            
            if 'personality_name' not in column_names:
                missing_columns.append(('personality_name', 'TEXT DEFAULT ""'))
                
            if 'personality_description' not in column_names:
                missing_columns.append(('personality_description', 'TEXT DEFAULT ""'))
                
            if 'is_group_personality' not in column_names:
                missing_columns.append(('is_group_personality', 'BOOLEAN DEFAULT FALSE'))
            
            if 'updated_at' not in column_names:
                missing_columns.append(('updated_at', 'DATETIME DEFAULT CURRENT_TIMESTAMP'))
            
            # Добавляем недостающие столбцы
            for column_name, column_type in missing_columns:
                print(f"➕ Добавляем столбец {column_name}...")
                await db.execute(f"""
                    ALTER TABLE custom_personalities 
                    ADD COLUMN {column_name} {column_type}
                """)
                print(f"✅ Столбец {column_name} добавлен")
            
            if missing_columns:
                await db.commit()
                
                # Обновляем существующие записи
                print("🔄 Обновляем существующие записи...")
                
                await db.execute("""
                    UPDATE custom_personalities 
                    SET personality_name = SUBSTR(description, 1, 50),
                        personality_description = description,
                        is_group_personality = (chat_id < 0),
                        updated_at = CURRENT_TIMESTAMP
                    WHERE personality_name = '' OR personality_name IS NULL
                """)
                
                await db.commit()
                print("✅ Существующие записи обновлены")
                
            else:
                print("ℹ️ Все столбцы уже существуют")
            
            # Показываем финальную структуру
            cursor = await db.execute("PRAGMA table_info(custom_personalities)")
            columns = await cursor.fetchall()
            
            print("\n📋 Финальная структура custom_personalities:")
            for col in columns:
                print(f"  • {col[1]} ({col[2]})")
            
            print("\n✅ Миграция v3.2.1 завершена!")
            
    except Exception as e:
        print(f"❌ Ошибка миграции: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(migrate_personality_table())