#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::process::Command;

pub fn run() {
    tauri::Builder::default()
        .setup(|_app| {
            let home = dirs::home_dir()
                .expect("无法获取 HOME 目录")
                .to_string_lossy()
                .to_string();
            
            let venv_python = format!("{}/.hermes/hermes-agent/venv/bin/python3", home);
            let bridge_script = format!("{}/.hermes/hermes-agent/server/chat_bridge.py", home);
            
            // 选择 Bridge 脚本路径
            let bridge_path = if std::path::Path::new(&bridge_script).exists() {
                bridge_script
            } else {
                std::env::current_dir()
                    .expect("无法获取当前目录")
                    .join("server/chat_bridge.py")
                    .to_string_lossy()
                    .to_string()
            };
            
            println!("[Hermes] Bridge 脚本: {}", bridge_path);
            
            // 启动 Bridge
            let mut cmd = Command::new(&venv_python);
            cmd.arg(&bridge_path)
                .env("PATH", format!("{}/.hermes/hermes-agent/venv/bin:/usr/local/bin:/usr/bin:/bin", home))
                .env("VIRTUAL_ENV", format!("{}/.hermes/hermes-agent/venv", home))
                .env("HERMES_BRIDGE_PORT", "9120");
            
            match cmd.spawn() {
                Ok(child) => {
                    println!("[Hermes] Bridge 已启动, PID: {}", child.id());
                }
                Err(e) => {
                    eprintln!("[Hermes] 启动 Bridge 失败: {}", e);
                }
            };
            
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
