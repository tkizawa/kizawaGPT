import tkinter as tk
from tkinter import scrolledtext, ttk
from openai import AzureOpenAI
import json
import os
import datetime
import threading

class ChatApp:
    def __init__(self, master):
        self.master = master
        master.title("KizawaGPT")
        
        self.load_settings()
        self.load_window_state()
        
        self.setup_ui()
        self.setup_openai()
        
        self.conversation_history = [
            {"role": "system", "content": "You are a helpful assistant."}
        ]
        
        # 処理中フラグ
        self.is_processing = False
        
        # 最後に保存したメッセージのインデックス
        self.last_saved_index = 0

    def load_settings(self):
        default_settings = {
            "AZURE_OPENAI_KEY": "your_default_key",
            "AZURE_OPENAI_ENDPOINT": "your_default_endpoint",
            "DEPLOYMENT_NAME": "your_default_deployment_name"
        }
        try:
            with open('setting.json', 'r') as f:
                self.settings = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            print("Error: setting.json file not found or invalid format. Using default settings.")
            self.settings = default_settings

    def load_window_state(self):
        try:
            with open('work.json', 'r') as f:
                self.window_state = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.window_state = {
                "geometry": "600x400+100+100"
            }

    def save_window_state(self):
        self.window_state["geometry"] = self.master.geometry()
        with open('work.json', 'w') as f:
            json.dump(self.window_state, f)

    def setup_ui(self):
        self.master.geometry(self.window_state["geometry"])
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)

        main_frame = tk.Frame(self.master)
        main_frame.pack(fill=tk.BOTH, expand=True)

        self.chat_history = scrolledtext.ScrolledText(main_frame, state='disabled', height=20)
        self.chat_history.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        bottom_frame = tk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        self.input_field = scrolledtext.ScrolledText(bottom_frame, height=5)
        self.input_field.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.input_field.bind("<Control-Return>", self.send_message_event)

        button_frame = tk.Frame(bottom_frame)
        button_frame.pack(side=tk.RIGHT, padx=(10, 0))

        self.send_button = tk.Button(button_frame, text="送信", command=self.send_message)
        self.send_button.pack(fill=tk.X)

        self.continue_button = tk.Button(button_frame, text="続き", command=self.send_continue_message)
        self.continue_button.pack(fill=tk.X, pady=(10, 0))

        self.clear_button = tk.Button(button_frame, text="会話をクリア", command=self.clear_conversation)
        self.clear_button.pack(fill=tk.X, pady=(10, 0))

        self.exit_button = tk.Button(button_frame, text="終了", command=self.on_closing)
        self.exit_button.pack(fill=tk.X, pady=(10, 0))

        self.progress_bar = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress_bar.pack(fill=tk.X, padx=10, pady=(0, 10))

    def setup_openai(self):
        self.client = AzureOpenAI(
            api_key=self.settings["AZURE_OPENAI_KEY"],
            api_version="2023-05-15",
            azure_endpoint=self.settings["AZURE_OPENAI_ENDPOINT"]
        )

    def send_message_event(self, event):
        self.send_message()

    def send_message(self):
        if self.is_processing:
            return

        user_input = self.input_field.get("1.0", tk.END).strip()
        if user_input:
            self.update_chat_history(f"あなた: {user_input}\n", "user")
            self.input_field.delete("1.0", tk.END)
            self.conversation_history.append({"role": "user", "content": user_input})

            self.is_processing = True
            self.progress_bar.start()
            
            threading.Thread(target=self.process_message).start()

    def process_message(self):
        try:
            response = self.client.chat.completions.create(
                model=self.settings["DEPLOYMENT_NAME"],
                messages=self.conversation_history,
                max_tokens=1000
            )
            ai_response = response.choices[0].message.content
            self.master.after(0, self.update_chat_history, f"AI: {ai_response}\n", "assistant")

            self.conversation_history.append({"role": "assistant", "content": ai_response})
            self.save_conversation()  # 自動保存
        except Exception as e:
            self.master.after(0, self.update_chat_history, f"エラーが発生しました: {str(e)}\n", "error")
        finally:
            self.is_processing = False
            self.master.after(0, self.progress_bar.stop)

    def send_continue_message(self):
        if not self.is_processing:
            continue_message = "続きをお願いします"
            self.update_chat_history(f"あなた: {continue_message}\n", "user")
            self.conversation_history.append({"role": "user", "content": continue_message})
            self.send_message()

    def update_chat_history(self, message, role):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        divider = "-" * 50 + "\n"

        self.chat_history.configure(state='normal')
        self.chat_history.insert(tk.END, f"{timestamp} - {role}\n")
        self.chat_history.insert(tk.END, message)
        self.chat_history.insert(tk.END, divider)
        self.chat_history.configure(state='disabled')
        self.chat_history.see(tk.END)

    def clear_conversation(self):
        self.conversation_history = [
            {"role": "system", "content": "You are a helpful assistant."}
        ]
        self.chat_history.configure(state='normal')
        self.chat_history.delete("1.0", tk.END)
        self.chat_history.configure(state='disabled')
        self.update_chat_history("会話がクリアされました。新しい会話を開始します。\n", "system")
        self.last_saved_index = 0  # 最後に保存したインデックスをリセット
        self.save_conversation()  # 自動保存

    def save_conversation(self):
        filename = "会話履歴.md"
        
        # 新しいメッセージのみを保存
        new_messages = self.conversation_history[self.last_saved_index:]
        if not new_messages:
            return  # 新しいメッセージがない場合は保存しない
        
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        markdown_content = f"# 会話履歴 - {timestamp}\n\n"
        
        for entry in new_messages:
            role = entry["role"]
            content = entry["content"]
            if role == "system":
                markdown_content += f"**システム**: {content}\n\n"
            elif role == "user":
                markdown_content += f"**あなた**: {content}\n\n"
            elif role == "assistant":
                markdown_content += f"**AI**: {content}\n\n"
            markdown_content += "---\n\n"
        
        mode = 'a' if os.path.exists(filename) else 'w'
        with open(filename, mode, encoding="utf-8") as f:
            f.write(markdown_content)
        
        self.last_saved_index = len(self.conversation_history)  # 保存したインデックスを更新

    def on_closing(self):
        self.save_window_state()
        self.master.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ChatApp(root)
    root.mainloop()
    