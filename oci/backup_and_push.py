#!/usr/bin/env python3
"""
完整備份流程：OCI備份 + GitHub同步
"""

import subprocess
import sys
import os
from datetime import datetime

def run_command(cmd, description):
    """執行命令並顯示結果"""
    print(f"\n🔄 {description}...")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        if result.stdout:
            print(result.stdout)
        return True
    else:
        print(f"❌ 失敗: {result.stderr}")
        return False

def main():
    """執行完整備份流程"""
    
    print("🚀 開始完整備份流程")
    print("=" * 60)
    
    # 步驟 1: 備份到 OCI
    print("\n📦 步驟 1: 備份當前資料到 OCI")
    if not run_command(
        "cd '/mnt/c/claude code/建照爬蟲/oci' && python3 backup_current_data.py",
        "執行 OCI 備份"
    ):
        print("❌ OCI 備份失敗，流程中止")
        return
    
    # 步驟 2: 備份到 GitHub 備份目錄
    print("\n📦 步驟 2: 備份資料到本地 GitHub 備份目錄")
    if not run_command(
        "cd '/mnt/c/claude code/建照爬蟲/oci' && python3 backup-to-github.py",
        "執行 GitHub 備份"
    ):
        print("❌ GitHub 備份失敗，流程中止")
        return
    
    # 步驟 3: 同步到 GitHub 資料目錄
    print("\n📦 步驟 3: 同步資料到 GitHub 資料目錄")
    if not run_command(
        "cd '/mnt/c/claude code/建照爬蟲/oci' && python3 sync_to_github.py",
        "同步到 GitHub 目錄"
    ):
        print("❌ 同步失敗，流程中止")
        return
    
    print("\n" + "=" * 60)
    print("✅ 完整備份流程執行完成！")
    print("\n📊 備份摘要:")
    print(f"   - OCI 備份: ✅ 完成")
    print(f"   - 本地備份: ✅ 完成")
    print(f"   - GitHub 同步: ✅ 完成")
    print(f"   - 執行時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    print("\n💡 GitHub 推送說明:")
    print("   由於此目錄尚未初始化為 Git 倉庫，請手動執行以下步驟：")
    print("   1. 按照 DEPLOY_TO_GITHUB.md 的說明在 GitHub 創建倉庫")
    print("   2. 將 /github 目錄的內容上傳到 GitHub")
    print("   3. 啟用 GitHub Actions 和 GitHub Pages")
    
    print("\n📁 備份檔案位置:")
    print(f"   - OCI: oci://taichung-building-permits/backups/")
    print(f"   - 本地: /mnt/c/claude code/建照爬蟲/backups/")
    print(f"   - GitHub: /mnt/c/claude code/建照爬蟲/github/data/")

if __name__ == "__main__":
    main()