import asyncio
from notebooklm import NotebookLMClient

async def test():
    try:
        client = await NotebookLMClient.from_storage()
        print("連線成功！")
    except Exception as e:
        print(f"連線失敗: {e}")

if __name__ == "__main__":
    asyncio.run(test())
