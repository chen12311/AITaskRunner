#!/usr/bin/env python3
"""
启动脚本 - 同时启动后端API和前端开发服务器
"""
import subprocess
import sys
import os
import signal
from pathlib import Path

# 修复 Windows 控制台编码问题
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# 全局进程列表，用于信号处理
_processes = []


def kill_port(port):
    """杀死占用指定端口的进程"""
    try:
        result = subprocess.run(
            ["lsof", "-ti", f":{port}"],
            capture_output=True,
            text=True
        )
        if result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                try:
                    os.kill(int(pid), signal.SIGKILL)
                    print(f"   🔪 已杀死占用端口 {port} 的进程 (PID: {pid})")
                except (ProcessLookupError, ValueError):
                    pass
    except Exception:
        pass


def cleanup_processes(signum=None, frame=None):
    """清理所有子进程"""
    print("\n\n🛑 正在停止所有服务...")
    for name, proc in _processes:
        try:
            # 先尝试优雅终止
            proc.terminate()
            proc.wait(timeout=3)
            print(f"   ✅ {name} 已停止")
        except subprocess.TimeoutExpired:
            proc.kill()
            print(f"   ⚠️  强制停止 {name}")
        except Exception:
            pass

    # 确保端口被释放
    kill_port(8086)
    kill_port(3000)
    print("\n👋 所有服务已停止")
    sys.exit(0)


def main():
    """主函数"""
    global _processes

    # 注册信号处理器
    signal.signal(signal.SIGINT, cleanup_processes)
    signal.signal(signal.SIGTERM, cleanup_processes)

    print("=" * 60)
    print("🚀 Codex Automation Web Dashboard 启动器")
    print("=" * 60)

    # 获取脚本所在目录
    base_dir = Path(__file__).parent

    # 启动前清理可能残留的进程
    print("\n🧹 检查并清理残留进程...")
    kill_port(8086)
    kill_port(3000)

    try:
        # 1. 启动后端服务
        print("\n📡 启动后端API服务 (FastAPI)...")
        backend_dir = base_dir / "backend"

        # 设置环境变量，添加项目根目录到PYTHONPATH
        env = os.environ.copy()
        env['PYTHONPATH'] = str(base_dir)

        backend_process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8086"],
            cwd=str(base_dir),
            env=env,
        )
        _processes.append(("Backend", backend_process))
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
        )
        _processes.append(("Frontend", frontend_process))
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
        for name, proc in _processes:
            proc.wait()

    except KeyboardInterrupt:
        cleanup_processes()

    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        cleanup_processes()


if __name__ == "__main__":
    main()
