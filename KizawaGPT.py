import tkinter as tk
from tkinter import scrolledtext
from openai import AzureOpenAI
import json
import os
import datetime

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

        # メインフレームの作成
        main_frame = tk.Frame(self.master)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # チャット履歴
        self.chat_history = scrolledtext.ScrolledText(main_frame, state='disabled', height=20)
        self.chat_history.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # 入力欄とボタンを含む下部フレーム
        bottom_frame = tk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        # 入力欄（サイズ変更可能）
        self.input_field = scrolledtext.ScrolledText(bottom_frame, height=5)
        self.input_field.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Ctrl+Enterでメッセージを送信
        self.input_field.bind("<Control-Return>", self.send_message_event)

        # ボタンフレーム
        button_frame = tk.Frame(bottom_frame)
        button_frame.pack(side=tk.RIGHT, padx=(10, 0))

        # 送信ボタン
        self.send_button = tk.Button(button_frame, text="送信", command=self.send_message)
        self.send_button.pack(fill=tk.X)

        # 続きボタン
        self.continue_button = tk.Button(button_frame, text="続き", command=self.send_continue_message)
        self.continue_button.pack(fill=tk.X, pady=(10, 0))

        # クリアボタン
        self.clear_button = tk.Button(button_frame, text="会話をクリア", command=self.clear_conversation)
        self.clear_button.pack(fill=tk.X, pady=(10, 0))

    def setup_openai(self):
        self.client = AzureOpenAI(
            api_key=self.settings["AZURE_OPENAI_KEY"],
            api_version="2023-05-15",
            azure_endpoint=self.settings["AZURE_OPENAI_ENDPOINT"]
        )

    def send_message_event(self, event):
        """Ctrl+Enterキーのイベントハンドラ"""
        self.send_message()

    def send_message(self):
        user_input = self.input_field.get("1.0", tk.END).strip()
        if user_input:
            self.update_chat_history(f"あなた: {user_input}\n", "user")
            self.input_field.delete("1.0", tk.END)
            # Send user message to the conversation history
            self.conversation_history.append({"role": "user", "content": user_input})

            try:
                response = self.client.chat.completions.create(
                    model=self.settings["DEPLOYMENT_NAME"],
                    messages=self.conversation_history,
                    max_tokens=1000
                )
                ai_response = response.choices[0].message.content
                self.update_chat_history(f"AI: {ai_response}\n", "assistant")

                # Add AI response to conversation history
                self.conversation_history.append({"role": "assistant", "content": ai_response})
            except Exception as e:
                self.update_chat_history(f"エラーが発生しました: {str(e)}\n", "error")

    def send_continue_message(self):
        continue_message = "続きをお願いします"
        self.update_chat_history(f"あなた: {continue_message}\n", "user")

        # Add continue message to conversation history
        self.conversation_history.append({"role": "user", "content": continue_message})

        try:
            response = self.client.chat.completions.create(
                model=self.settings["DEPLOYMENT_NAME"],
                messages=self.conversation_history,
                max_tokens=1000
            )
            ai_response = response.choices[0].message.content
            self.update_chat_history(f"AI: {ai_response}\n", "assistant")

            # Add AI response to conversation history
            self.conversation_history.append({"role": "assistant", "content": ai_response})
        except Exception as e:
            self.update_chat_history(f"エラーが発生しました: {str(e)}\n", "error")

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

    def on_closing(self):
        self.save_window_state()
        self.master.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ChatApp(root)
    root.mainloop()
