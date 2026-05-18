"""开发模式启动脚本。"""

import sys
import os

# 添加 core 和 server 的源码路径，使开发模式下可直接运行
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import uvicorn

if __name__ == "__main__":
    uvicorn.run("agent_company_server.app:app", host="0.0.0.0", port=8000, reload=True)
