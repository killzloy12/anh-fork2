import asyncio
import aiosqlite

async def add_updated_at():
    db_path = "data/bot.db"
    async with aiosqlite.connect(db_path) as db:
        # Добавляем колонку без DEFAULT
        try:
            await db.execute("ALTER TABLE custom_personalities ADD COLUMN updated_at DATETIME")
        except Exception:
            pass  # если уже есть, пропускаем
        # Устанавливаем значение для существующих записей
        await db.execute("""
            UPDATE custom_personalities
            SET updated_at = created_at
            WHERE updated_at IS NULL
        """)
        await db.commit()
        print("✅ Поле updated_at добавлено и заполнено")
        
if __name__ == "__main__":
    asyncio.run(add_updated_at())
