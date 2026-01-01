"""
檢查資料庫中的所有 LLM 分析記錄
用法: python check_llm_logs.py
"""
import asyncio
import sys
import io
import json
from datetime import datetime
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# 設置 UTF-8 編碼以支援中文和特殊字符
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from app.config import get_settings
from app.models.llm_analysis import LLMAnalysis


def get_database_url() -> str:
    """取得資料庫 URL（轉換為 async 格式）"""
    settings = get_settings()
    return settings.database_url.replace("sqlite:///", "sqlite+aiosqlite:///")


async def check_all_logs():
    """檢查所有 LLM 分析記錄"""
    engine = create_async_engine(get_database_url(), echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        # 統計總數
        total_result = await db.execute(select(func.count()).select_from(LLMAnalysis))
        total_count = total_result.scalar()
        
        print("=" * 80)
        print("LLM 分析記錄統計")
        print("=" * 80)
        print(f"\n總記錄數: {total_count}")
        
        if total_count == 0:
            print("\n資料庫中沒有任何 LLM 分析記錄。")
            await engine.dispose()
            return
        
        # 按狀態統計
        status_result = await db.execute(
            select(LLMAnalysis.status, func.count(LLMAnalysis.id))
            .group_by(LLMAnalysis.status)
        )
        status_counts = status_result.all()
        
        print("\n按狀態統計:")
        for status, count in status_counts:
            print(f"  {status}: {count}")
        
        # 最近 10 筆記錄摘要
        recent_result = await db.execute(
            select(LLMAnalysis)
            .order_by(desc(LLMAnalysis.created_at))
            .limit(10)
        )
        recent_analyses = recent_result.scalars().all()
        
        print(f"\n最近 {len(recent_analyses)} 筆記錄:")
        print("-" * 80)
        for i, analysis in enumerate(recent_analyses, 1):
            status_icon = "✅" if analysis.status == "COMPLETED" else "❌" if analysis.status == "FAILED" else "⏳"
            print(f"\n{i}. {status_icon} {analysis.status}")
            print(f"   分析 ID: {analysis.id}")
            print(f"   案件 ID: {analysis.case_id}")
            print(f"   模型: {analysis.model_name or 'N/A'}")
            print(f"   建立時間: {analysis.created_at}")
            if analysis.latency_ms:
                print(f"   執行時間: {analysis.latency_ms} ms ({analysis.latency_ms/1000:.2f} 秒)")
            if analysis.error_message:
                error_preview = analysis.error_message[:100].replace('\n', ' ')
                print(f"   錯誤: {error_preview}...")
        
        # 失敗記錄詳情
        failed_result = await db.execute(
            select(LLMAnalysis)
            .where(LLMAnalysis.status == "FAILED")
            .order_by(desc(LLMAnalysis.created_at))
            .limit(5)
        )
        failed_analyses = failed_result.scalars().all()
        
        if failed_analyses:
            print("\n" + "=" * 80)
            print(f"最近 {len(failed_analyses)} 筆失敗記錄詳情")
            print("=" * 80)
            for i, analysis in enumerate(failed_analyses, 1):
                print(f"\n--- 失敗記錄 #{i} ---")
                print(f"分析 ID: {analysis.id}")
                print(f"案件 ID: {analysis.case_id}")
                print(f"模型: {analysis.model_name or 'N/A'}")
                print(f"觸發者: {analysis.triggered_by or 'N/A'}")
                print(f"觸發方式: {analysis.trigger_type}")
                print(f"建立時間: {analysis.created_at}")
                if analysis.latency_ms:
                    print(f"執行時間: {analysis.latency_ms} ms ({analysis.latency_ms/1000:.2f} 秒)")
                if analysis.error_message:
                    print(f"\n錯誤訊息:")
                    print("-" * 80)
                    print(analysis.error_message)
                    print("-" * 80)
                if analysis.prompt_tokens:
                    print(f"\nToken 使用量: {analysis.prompt_tokens} (prompt) + {analysis.completion_tokens or 0} (completion)")
        
        # 檢查特定 ID（如果需要的話）
        target_id = "7f22e7de-7f3b-43f8-a277-41db070c5a53"
        target_result = await db.execute(
            select(LLMAnalysis).where(LLMAnalysis.id == target_id)
        )
        target_analysis = target_result.scalar_one_or_none()
        
        if target_analysis:
            print("\n" + "=" * 80)
            print("找到目標分析記錄")
            print("=" * 80)
            print(f"分析 ID: {target_analysis.id}")
            print(f"案件 ID: {target_analysis.case_id}")
            print(f"狀態: {target_analysis.status}")
            print(f"模型: {target_analysis.model_name or 'N/A'}")
            print(f"建立時間: {target_analysis.created_at}")
            if target_analysis.error_message:
                print(f"\n錯誤訊息:")
                print("-" * 80)
                print(target_analysis.error_message)
                print("-" * 80)
        else:
            print(f"\n注意: 未找到分析 ID {target_id}")
        
        print("\n" + "=" * 80)
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(check_all_logs())

