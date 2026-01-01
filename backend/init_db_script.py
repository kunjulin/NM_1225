"""初始化資料庫腳本"""
import asyncio
from app.database import init_db

async def main():
    print("正在初始化資料庫...")
    await init_db()
    print("資料庫初始化完成！")

if __name__ == "__main__":
    asyncio.run(main())

