"""檢查資料庫中的使用者"""
import asyncio
from app.database import async_session_maker
from app.models.user import User, UserStatus
from sqlalchemy import select

async def check_users():
    async with async_session_maker() as db:
        # 檢查所有使用者
        result = await db.execute(select(User))
        all_users = result.scalars().all()
        
        print(f'總使用者數: {len(all_users)}')
        for u in all_users:
            print(f'  - Subject: {u.subject}')
            print(f'    Display Name: {u.display_name}')
            print(f'    Status: {u.status}')
            print(f'    Allowed Roles: {u.allowed_roles}')
            print(f'    Is Admin: {u.is_admin}')
            print()
        
        # 檢查待審核使用者
        pending_result = await db.execute(
            select(User).where(User.status == UserStatus.PENDING.value)
        )
        pending_users = pending_result.scalars().all()
        
        print(f'待審核使用者數: {len(pending_users)}')
        for u in pending_users:
            print(f'  - {u.subject} ({u.display_name})')

if __name__ == "__main__":
    asyncio.run(check_users())
