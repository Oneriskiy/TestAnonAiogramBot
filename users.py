
import aiosqlite

async def create_user_table():
    async with aiosqlite.connect('users.db') as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                name TEXT,
                age INTEGER,
                gender TEXT,
                interests TEXT
            )
        """)
        await db.commit()

async def add_or_update_user(user_id, name, age, gender, interests):
    async with aiosqlite.connect('users.db') as db:
        await db.execute("""
            INSERT OR REPLACE INTO users (user_id, name, age, gender, interests)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, name, age, gender, interests))
        await db.commit()

async def get_all_users():
    async with aiosqlite.connect('users.db') as db:
        cursor = await db.execute("SELECT * FROM users")
        users = await cursor.fetchall()
    return users

async def get_user_by_id(user_id):
    async with aiosqlite.connect('users.db') as db:
        cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = await cursor.fetchone()
    return user

async def get_user_profile(user_id):
    async with aiosqlite.connect("users.db") as db:
        cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        profile = await cursor.fetchone()
        if profile:
            return {
                "user_id": profile[0],
                "name": profile[1],
                "age": profile[2],
                "gender": profile[3],
                "interests": profile[4]
            }
        return None