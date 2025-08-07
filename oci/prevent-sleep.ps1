# PowerShell 腳本防止 Windows 休眠
# 在 Windows PowerShell 中執行此腳本

Write-Host "防止電腦休眠中...按 Ctrl+C 結束"

while ($true) {
    # 模擬按鍵防止休眠
    Add-Type -TypeDefinition @"
        using System;
        using System.Runtime.InteropServices;
        public class PreventSleep {
            [DllImport("kernel32.dll")]
            public static extern uint SetThreadExecutionState(uint esFlags);
        }
"@
    
    # ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
    [PreventSleep]::SetThreadExecutionState(0x80000003)
    
    Start-Sleep -Seconds 60
}