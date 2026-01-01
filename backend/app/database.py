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
    from app.models import order_case, review_event, outbox, user, settings, llm_analysis  # noqa: F401
    
    async with engine.begin() as conn:
        # 啟用 WAL mode 以提升並發效能
        await conn.run_sync(lambda sync_conn: sync_conn.execute(
            __import__('sqlalchemy').text("PRAGMA journal_mode=WAL")
        ))
        await conn.run_sync(Base.metadata.create_all)
    
    # 建立預設管理員帳號（如果不存在）
    await create_default_admin()


async def create_default_admin():
    """建立預設管理員帳號"""
    import uuid
    from datetime import datetime, timezone
    from sqlalchemy import select
    from app.models.user import User, UserStatus
    
    async with async_session_maker() as session:
        # 檢查是否已存在管理員
        result = await session.execute(
            select(User).where(User.subject == "admin")
        )
        existing = result.scalar_one_or_none()
        
        if not existing:
            now = datetime.now(timezone.utc).isoformat()
            admin_user = User(
                id=str(uuid.uuid4()),
                subject="admin",
                practitioner_ref=None,
                display_name="系統管理員",
                email=None,
                allowed_roles='["ADMIN"]',
                status=UserStatus.ACTIVE.value,
                is_admin=True,
                last_login_at=None,
                created_at=now,
                updated_at=now,
            )
            session.add(admin_user)
            await session.commit()


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


