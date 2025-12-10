#!/usr/bin/env python3
"""
启动脚本 - 同时启动后端API和前端开发服务器
"""
import subprocess
import sys
import os
import signal
from pathlib import Path


def main():
    """主函数"""
    print("=" * 60)
    print("🚀 Codex Automation Web Dashboard 启动器")
    print("=" * 60)

    # 获取脚本所在目录
    base_dir = Path(__file__).parent

    processes = []

    try:
        # 1. 启动后端服务
        print("\n📡 启动后端API服务 (FastAPI)...")
        backend_dir = base_dir / "backend"

        # 设置环境变量，添加项目根目录到PYTHONPATH
        env = os.environ.copy()
        env['PYTHONPATH'] = str(base_dir)

        backend_process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8086"],
            cwd=str(base_dir),  # 改为在项目根目录运行
            env=env,
            start_new_session=True,  # 创建新进程组，便于统一关闭
        )
        processes.append(("Backend", backend_process))
        print(f"   ✅ 后端服务已启动 (PID: {backend_process.pid})")
        print(f"   📍 API地址: http://127.0.0.1:8086")
        print(f"   📖 API文档: http://127.0.0.1:8086/docs")

        # 2. 启动前端开发服务器
        print("\n🎨 启动前端开发服务器 (Vite)...")
        frontend_dir = base_dir / "frontend"

        # 检查是否已安装依赖
        if not (frontend_dir / "node_modules").exists():
            print("   ⚠️  未检测到 node_modules，正在安装依赖...")
            install_process = subprocess.run(
                ["npm", "install"],
                cwd=str(frontend_dir),
                capture_output=True
            )
            if install_process.returncode != 0:
                print("   ❌ 安装前端依赖失败")
                return

        frontend_process = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=str(frontend_dir),
            start_new_session=True,  # 创建新进程组，便于统一关闭
        )
        processes.append(("Frontend", frontend_process))
        print(f"   ✅ 前端服务已启动 (PID: {frontend_process.pid})")
        print(f"   🌐 前端地址: http://localhost:3000")

        print("\n" + "=" * 60)
        print("✨ 所有服务已启动!")
        print("   - 后端API: http://127.0.0.1:8086")
        print("   - 前端界面: http://localhost:3000")
        print("   - API文档: http://127.0.0.1:8086/docs")
        print("=" * 60)
        print("\n按 Ctrl+C 停止所有服务...\n")

        # 等待进程
        for name, proc in processes:
            proc.wait()

    except KeyboardInterrupt:
        print("\n\n🛑 正在停止所有服务...")

    finally:
        # 清理进程组
        for name, proc in processes:
            try:
                # 发送 SIGTERM 到整个进程组
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
                proc.wait(timeout=5)
                print(f"   ✅ {name} 已停止")
            except Exception as e:
                try:
                    # 强制杀死整个进程组
                    os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                except Exception:
                    proc.kill()
                print(f"   ⚠️  强制停止 {name}")

        print("\n👋 所有服务已停止")


if __name__ == "__main__":
    main()
