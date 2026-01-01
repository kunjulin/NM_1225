"""
檢查 LLM 分析記錄是否使用了 thinking mode
用法: python check_thinking_mode.py <analysis_id>
"""
import asyncio
import sys
import io
import json
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# 設置 UTF-8 編碼
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from app.database import async_session_maker
from app.models import LLMAnalysis
from app.services.llm_service import LLMService


async def check_thinking_mode(analysis_id: str):
    """檢查特定分析 ID 是否使用了 thinking mode"""
    async with async_session_maker() as db:
        # 查詢分析記錄
        result = await db.execute(
            select(LLMAnalysis).where(LLMAnalysis.id == analysis_id)
        )
        analysis = result.scalar_one_or_none()
        
        if not analysis:
            print(f"❌ 找不到分析記錄: {analysis_id}")
            return
        
        print("=" * 80)
        print("Thinking Mode 檢查")
        print("=" * 80)
        print(f"\n📋 分析記錄資訊:")
        print(f"  分析 ID: {analysis.id}")
        print(f"  案件 ID: {analysis.case_id}")
        print(f"  模型: {analysis.model_name}")
        print(f"  狀態: {analysis.status}")
        print(f"  建立時間: {analysis.created_at}")
        
        # 檢查當前的 LLM 設定
        llm_service = LLMService(db)
        current_settings = await llm_service.get_settings()
        
        print(f"\n⚙️  當前 LLM 設定:")
        print(f"  disable_thinking_mode: {current_settings.disable_thinking_mode}")
        
        # 判斷是否使用 thinking mode
        # 如果 disable_thinking_mode = True，則沒有使用 thinking mode
        # 如果 disable_thinking_mode = False，則使用 thinking mode（預設）
        using_thinking_mode = not current_settings.disable_thinking_mode
        
        print(f"\n🔍 Thinking Mode 狀態:")
        if using_thinking_mode:
            print(f"  ✅ 使用 Thinking Mode（disable_thinking_mode = False）")
        else:
            print(f"  ❌ 未使用 Thinking Mode（disable_thinking_mode = True）")
        
        # 檢查 prompt 中是否有相關內容
        if analysis.prompt_used:
            prompt_lower = analysis.prompt_used.lower()
            has_thinking_keywords = any(keyword in prompt_lower for keyword in ['thinking', 'reasoning', 'thought'])
            print(f"\n📝 Prompt 檢查:")
            print(f"  包含 thinking/reasoning 相關關鍵字: {has_thinking_keywords}")
            if has_thinking_keywords:
                print(f"  （注意：這只是檢查關鍵字，不代表實際啟用了 thinking mode）")
        
        # 檢查 raw_response 中是否有 thinking 標記
        if analysis.raw_response:
            try:
                response_data = json.loads(analysis.raw_response)
                # 某些 API 會在回應中包含 thinking 相關的欄位
                has_thinking_in_response = any(keyword in str(response_data).lower() for keyword in ['thinking', 'reasoning'])
                print(f"\n📨 回應檢查:")
                print(f"  回應中包含 thinking 相關內容: {has_thinking_in_response}")
            except:
                pass
        
        print("\n" + "=" * 80)
        print(f"\n💡 說明:")
        print(f"  - Thinking Mode 的啟用/禁用是由 LLM 設定的 'disable_thinking_mode' 參數控制")
        print(f"  - 如果 disable_thinking_mode = False（預設），則啟用 Thinking Mode")
        print(f"  - 如果 disable_thinking_mode = True，則禁用 Thinking Mode")
        print(f"  - 注意：此檢查基於當前的設定值，可能與分析時的設定不同")
        print(f"  - 模型 '{analysis.model_name}' 屬於支援 thinking mode 的模型（如 Qwen 系列）")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python check_thinking_mode.py <analysis_id>")
        print("\n範例:")
        print("  python check_thinking_mode.py 2fb6f9d6-f736-4a66-84d4-8e4871ae9696")
        sys.exit(1)
    
    analysis_id = sys.argv[1]
    asyncio.run(check_thinking_mode(analysis_id))

