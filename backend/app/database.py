"""
資料庫連線與會話管理模組
使用 SQLAlchemy 2.x async 模式
"""
from typing import AsyncGenerator

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings


class Base(DeclarativeBase):
    """SQLAlchemy 基礎模型類別"""
    pass


# 取得設定
settings = get_settings()

# 將 sqlite:/// 轉換為 sqlite+aiosqlite:///
database_url = settings.database_url.replace("sqlite:///", "sqlite+aiosqlite:///")

# 建立非同步引擎
engine = create_async_engine(
    database_url,
    echo=settings.debug,
    future=True,
)

# 建立非同步會話工廠
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db():
    """初始化資料庫（建立所有資料表）"""
    # 匯入所有模型以確保它們被註冊
    from app.models import order_case, review_event, outbox  # noqa: F401
    
    async with engine.begin() as conn:
        # 啟用 WAL mode 以提升並發效能
        await conn.run_sync(lambda sync_conn: sync_conn.execute(
            __import__('sqlalchemy').text("PRAGMA journal_mode=WAL")
        ))
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """取得資料庫會話（依賴注入用）"""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


