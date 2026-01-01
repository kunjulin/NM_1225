"""
查詢特定 LLM 分析記錄的詳細錯誤資訊
用法: python check_llm_error.py <analysis_id>
"""
import asyncio
import sys
import io
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# 設置 UTF-8 編碼以支援中文和特殊字符
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from app.database import async_session_maker
from app.models import LLMAnalysis


async def check_llm_error(analysis_id: str):
    """查詢特定分析 ID 的詳細資訊"""
    async with async_session_maker() as db:
        result = await db.execute(
            select(LLMAnalysis).where(LLMAnalysis.id == analysis_id)
        )
        analysis = result.scalar_one_or_none()
        
        if not analysis:
            print(f"❌ 找不到分析記錄: {analysis_id}")
            return
        
        print("=" * 80)
        print(f"LLM 分析錯誤記錄")
        print("=" * 80)
        print(f"\n📋 基本資訊:")
        print(f"  分析 ID: {analysis.id}")
        print(f"  案件 ID: {analysis.case_id}")
        print(f"  狀態: {analysis.status}")
        print(f"  模型名稱: {analysis.model_name or 'N/A'}")
        print(f"  觸發者: {analysis.triggered_by or 'N/A'}")
        print(f"  觸發方式: {analysis.trigger_type}")
        print(f"  建立時間: {analysis.created_at}")
        print(f"  更新時間: {analysis.updated_at}")
        
        if analysis.latency_ms:
            print(f"  執行時間: {analysis.latency_ms} ms ({analysis.latency_ms/1000:.2f} 秒)")
        
        if analysis.prompt_tokens:
            print(f"\n📊 Token 使用量:")
            print(f"  Prompt Tokens: {analysis.prompt_tokens}")
            print(f"  Completion Tokens: {analysis.completion_tokens or 0}")
            print(f"  Total Tokens: {analysis.total_tokens or 0}")
        
        if analysis.error_message:
            print(f"\n❌ 錯誤訊息:")
            print("-" * 80)
            print(analysis.error_message)
            print("-" * 80)
        
        if analysis.prompt_used:
            print(f"\n📝 使用的 Prompt (前 500 字元):")
            print("-" * 80)
            prompt_preview = analysis.prompt_used[:500]
            print(prompt_preview)
            if len(analysis.prompt_used) > 500:
                print(f"... (總共 {len(analysis.prompt_used)} 字元)")
            print("-" * 80)
        
        if analysis.raw_response:
            print(f"\n📨 LLM 原始回應 (前 1000 字元):")
            print("-" * 80)
            response_preview = analysis.raw_response[:1000]
            print(response_preview)
            if len(analysis.raw_response) > 1000:
                print(f"... (總共 {len(analysis.raw_response)} 字元)")
            print("-" * 80)
        
        if analysis.result_json:
            print(f"\n✅ 解析結果:")
            print("-" * 80)
            print(analysis.result_json[:500])
            if len(analysis.result_json) > 500:
                print(f"... (總共 {len(analysis.result_json)} 字元)")
            print("-" * 80)
        
        print("\n" + "=" * 80)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python check_llm_error.py <analysis_id>")
        print("\n範例:")
        print("  python check_llm_error.py 567a1421-abd4-459c-bd47-93cec43c1602")
        sys.exit(1)
    
    analysis_id = sys.argv[1]
    asyncio.run(check_llm_error(analysis_id))

