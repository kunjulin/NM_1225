"""
除錯 LLM 分析記錄的腳本

用法:
    python debug_llm_analysis.py <case_id>          # 查看特定案件的分析記錄
    python debug_llm_analysis.py --recent 10        # 查看最近 10 筆失敗的分析
    python debug_llm_analysis.py --failed          # 查看所有失敗的分析
    python debug_llm_analysis.py --all             # 查看所有分析記錄
"""
import asyncio
import sys
import json
from datetime import datetime
from sqlalchemy import select, desc, and_
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.database import get_database_url
from app.models.llm_analysis import LLMAnalysis


async def debug_case_analysis(case_id: str):
    """查看特定案件的分析記錄"""
    engine = create_async_engine(get_database_url(), echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        result = await db.execute(
            select(LLMAnalysis)
            .where(LLMAnalysis.case_id == case_id)
            .order_by(desc(LLMAnalysis.created_at))
        )
        analyses = result.scalars().all()
        
        if not analyses:
            print(f"案件 {case_id} 沒有分析記錄")
            return
        
        print(f"\n=== 案件 {case_id} 的分析記錄 ===\n")
        
        for i, analysis in enumerate(analyses, 1):
            print(f"--- 記錄 #{i} ---")
            print(f"ID: {analysis.id}")
            print(f"狀態: {analysis.status}")
            print(f"模型: {analysis.model_name}")
            print(f"觸發者: {analysis.triggered_by}")
            print(f"觸發方式: {analysis.trigger_type}")
            print(f"建立時間: {analysis.created_at}")
            print(f"更新時間: {analysis.updated_at}")
            print(f"執行時間: {analysis.latency_ms} ms" if analysis.latency_ms else "執行時間: N/A")
            
            if analysis.prompt_tokens:
                print(f"Token 使用: {analysis.prompt_tokens} (prompt) + {analysis.completion_tokens} (completion) = {analysis.total_tokens} (total)")
            
            if analysis.error_message:
                print(f"\n❌ 錯誤訊息:")
                print(f"{analysis.error_message}")
            
            if analysis.raw_response:
                try:
                    raw_data = json.loads(analysis.raw_response)
                    print(f"\n📥 LLM 原始回應 (前 500 字):")
                    response_text = json.dumps(raw_data, ensure_ascii=False, indent=2)
                    print(response_text[:500])
                    if len(response_text) > 500:
                        print("... (已截斷)")
                except:
                    print(f"\n📥 LLM 原始回應 (前 500 字):")
                    print(analysis.raw_response[:500])
                    if len(analysis.raw_response) > 500:
                        print("... (已截斷)")
            
            if analysis.result_json:
                try:
                    result_data = json.loads(analysis.result_json)
                    print(f"\n✅ 解析結果:")
                    print(json.dumps(result_data, ensure_ascii=False, indent=2)[:1000])
                    if len(json.dumps(result_data, ensure_ascii=False)) > 1000:
                        print("... (已截斷)")
                except:
                    print(f"\n✅ 解析結果 (原始):")
                    print(analysis.result_json[:500])
            
            if analysis.prompt_used:
                print(f"\n📝 使用的 Prompt (前 500 字):")
                print(analysis.prompt_used[:500])
                if len(analysis.prompt_used) > 500:
                    print("... (已截斷)")
            
            print("\n" + "="*60 + "\n")
    
    await engine.dispose()


async def debug_recent_failed(limit: int = 10):
    """查看最近失敗的分析記錄"""
    engine = create_async_engine(get_database_url(), echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        result = await db.execute(
            select(LLMAnalysis)
            .where(LLMAnalysis.status == "FAILED")
            .order_by(desc(LLMAnalysis.created_at))
            .limit(limit)
        )
        analyses = result.scalars().all()
        
        if not analyses:
            print("沒有失敗的分析記錄")
            return
        
        print(f"\n=== 最近 {len(analyses)} 筆失敗的分析記錄 ===\n")
        
        for i, analysis in enumerate(analyses, 1):
            print(f"--- 記錄 #{i} ---")
            print(f"案件 ID: {analysis.case_id}")
            print(f"分析 ID: {analysis.id}")
            print(f"模型: {analysis.model_name}")
            print(f"建立時間: {analysis.created_at}")
            print(f"執行時間: {analysis.latency_ms} ms" if analysis.latency_ms else "執行時間: N/A")
            
            if analysis.error_message:
                print(f"\n❌ 錯誤訊息:")
                print(f"{analysis.error_message}")
            
            print("\n" + "="*60 + "\n")
    
    await engine.dispose()


async def debug_all_failed():
    """查看所有失敗的分析記錄"""
    engine = create_async_engine(get_database_url(), echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        result = await db.execute(
            select(LLMAnalysis)
            .where(LLMAnalysis.status == "FAILED")
            .order_by(desc(LLMAnalysis.created_at))
        )
        analyses = result.scalars().all()
        
        if not analyses:
            print("沒有失敗的分析記錄")
            return
        
        print(f"\n=== 所有失敗的分析記錄 (共 {len(analyses)} 筆) ===\n")
        
        for i, analysis in enumerate(analyses, 1):
            print(f"--- 記錄 #{i} ---")
            print(f"案件 ID: {analysis.case_id}")
            print(f"分析 ID: {analysis.id}")
            print(f"模型: {analysis.model_name}")
            print(f"建立時間: {analysis.created_at}")
            print(f"執行時間: {analysis.latency_ms} ms" if analysis.latency_ms else "執行時間: N/A")
            
            if analysis.error_message:
                print(f"\n❌ 錯誤訊息:")
                print(f"{analysis.error_message[:500]}")
                if len(analysis.error_message) > 500:
                    print("... (已截斷)")
            
            print("\n" + "="*60 + "\n")
    
    await engine.dispose()


async def debug_all(limit: int = 20):
    """查看所有分析記錄"""
    engine = create_async_engine(get_database_url(), echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        result = await db.execute(
            select(LLMAnalysis)
            .order_by(desc(LLMAnalysis.created_at))
            .limit(limit)
        )
        analyses = result.scalars().all()
        
        if not analyses:
            print("沒有分析記錄")
            return
        
        print(f"\n=== 最近 {len(analyses)} 筆分析記錄 ===\n")
        
        for i, analysis in enumerate(analyses, 1):
            status_icon = "✅" if analysis.status == "COMPLETED" else "❌" if analysis.status == "FAILED" else "⏳"
            print(f"{status_icon} 記錄 #{i} - {analysis.status}")
            print(f"  案件 ID: {analysis.case_id}")
            print(f"  分析 ID: {analysis.id}")
            print(f"  模型: {analysis.model_name}")
            print(f"  建立時間: {analysis.created_at}")
            if analysis.error_message:
                print(f"  錯誤: {analysis.error_message[:100]}")
            print()
    
    await engine.dispose()


async def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    arg = sys.argv[1]
    
    if arg == "--recent":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        await debug_recent_failed(limit)
    elif arg == "--failed":
        await debug_all_failed()
    elif arg == "--all":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
        await debug_all(limit)
    else:
        # 假設是 case_id
        case_id = arg
        await debug_case_analysis(case_id)


if __name__ == "__main__":
    asyncio.run(main())

