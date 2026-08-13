import customtkinter as ctk
import sqlite3
import hashlib
import re
import os
import sys
import threading
import requests


# ============================================================
# FINN'S AI APP
# ============================================================

APP_NAME = "Finn's AI App"

# ============================================================
# APP DATA LOCATION
# ============================================================

APP_FOLDER = os.path.join(
    os.getenv("APPDATA", os.getcwd()),
    "FinnsAI"
)

os.makedirs(
    APP_FOLDER,
    exist_ok=True
)

DB_FILE = os.path.join(
    APP_FOLDER,
    "finns_ai.db"
)

LOGIN_FILE = os.path.join(
    APP_FOLDER,
    "remembered_login.txt"
)

# ============================================================
# AI SERVER
# ============================================================

# LOCAL TEST SERVER
# Later, when you publish the server, change this to:
# https://your-server-domain.com/chat

AI_SERVER_URL = "https://finns-ai-service.onrender.com/chat"


# ============================================================
# APPEARANCE
# ============================================================

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


# ============================================================
# DATABASE
# ============================================================

def setup_database():

    conn = sqlite3.connect(
        DB_FILE
    )

    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    conn.commit()

    conn.close()


def hash_password(password):

    return hashlib.sha256(
        password.encode("utf-8")
    ).hexdigest()


def valid_email(email):

    return re.match(
        r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
        email
    ) is not None


def create_account(
    email,
    password
):

    try:

        conn = sqlite3.connect(
            DB_FILE
        )

        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO users
            (email, password)
            VALUES (?, ?)
            """,
            (
                email.lower(),
                hash_password(password)
            )
        )

        conn.commit()

        conn.close()

        return True

    except sqlite3.IntegrityError:

        return False

    except Exception:

        return False


def check_login(
    email,
    password
):

    conn = sqlite3.connect(
        DB_FILE
    )

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id
        FROM users
        WHERE email = ?
        AND password = ?
        """,
        (
            email.lower(),
            hash_password(password)
        )
    )

    result = cursor.fetchone()

    conn.close()

    return result is not None


# ============================================================
# FINN'S AI
# ============================================================

class FinnsAI(ctk.CTk):

    def __init__(self):

        super().__init__()

        self.title(
            APP_NAME
        )

        self.geometry(
            "1200x750"
        )

        self.minsize(
            950,
            600
        )

        self.current_email = None

        self.messages = []

        self.protocol(
            "WM_DELETE_WINDOW",
            self.close_app
        )

        self.load_saved_login()


    # ========================================================
    # COLORS
    # ========================================================

    def text_color(self):

        if ctk.get_appearance_mode().lower() == "light":

            return "black"

        return "white"


    def secondary_text_color(self):

        if ctk.get_appearance_mode().lower() == "light":

            return "#555555"

        return "#AAAAAA"


    # ========================================================
    # SAVED LOGIN
    # ========================================================

    def save_login(
        self,
        email
    ):

        try:

            with open(
                LOGIN_FILE,
                "w",
                encoding="utf-8"
            ) as file:

                file.write(
                    email.lower()
                )

        except Exception:

            pass


    def load_saved_login(self):

        if not os.path.exists(
            LOGIN_FILE
        ):

            self.show_login()

            return

        try:

            with open(
                LOGIN_FILE,
                "r",
                encoding="utf-8"
            ) as file:

                email = file.read().strip()

            if email and valid_email(email):

                conn = sqlite3.connect(
                    DB_FILE
                )

                cursor = conn.cursor()

                cursor.execute(
                    "SELECT id FROM users WHERE email = ?",
                    (
                        email.lower(),
                    )
                )

                result = cursor.fetchone()

                conn.close()

                if result:

                    self.current_email = email.lower()

                    self.show_main_app()

                    return

        except Exception:

            pass

        self.show_login()


    # ========================================================
    # CLEAR SCREEN
    # ========================================================

    def clear_screen(self):

        for widget in self.winfo_children():

            widget.destroy()


    # ========================================================
    # LOGIN SCREEN
    # ========================================================

    def show_login(self):

        self.clear_screen()

        container = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )

        container.pack(
            expand=True,
            fill="both"
        )

        card = ctk.CTkFrame(
            container,
            width=430,
            height=500,
            corner_radius=20
        )

        card.place(
            relx=0.5,
            rely=0.5,
            anchor="center"
        )

        title = ctk.CTkLabel(
            card,
            text="Finn's AI",
            text_color=self.text_color(),
            font=ctk.CTkFont(
                size=34,
                weight="bold"
            )
        )

        title.pack(
            pady=(55, 5)
        )

        subtitle = ctk.CTkLabel(
            card,
            text="Log in to continue",
            text_color=self.secondary_text_color()
        )

        subtitle.pack(
            pady=(0, 30)
        )

        self.login_email = ctk.CTkEntry(
            card,
            width=320,
            height=45,
            placeholder_text="Email address"
        )

        self.login_email.pack(
            pady=10
        )

        self.login_password = ctk.CTkEntry(
            card,
            width=320,
            height=45,
            placeholder_text="Password",
            show="*"
        )

        self.login_password.pack(
            pady=10
        )

        login_button = ctk.CTkButton(
            card,
            text="Log In",
            width=320,
            height=45,
            command=self.login
        )

        login_button.pack(
            pady=(20, 10)
        )

        signup_button = ctk.CTkButton(
            card,
            text="Create Account",
            width=320,
            height=45,
            fg_color="transparent",
            border_width=1,
            text_color=self.text_color(),
            command=self.show_signup
        )

        signup_button.pack(
            pady=10
        )

        self.login_status = ctk.CTkLabel(
            card,
            text=""
        )

        self.login_status.pack(
            pady=10
        )

        self.login_password.bind(
            "<Return>",
            lambda event: self.login()
        )


    # ========================================================
    # LOGIN
    # ========================================================

    def login(self):

        email = self.login_email.get().strip()

        password = self.login_password.get()

        if not email or not password:

            self.login_status.configure(
                text="Enter your email and password.",
                text_color="#ff5555"
            )

            return

        if not valid_email(email):

            self.login_status.configure(
                text="Enter a valid email address.",
                text_color="#ff5555"
            )

            return

        if check_login(
            email,
            password
        ):

            self.current_email = email.lower()

            self.save_login(
                self.current_email
            )

            self.show_main_app()

        else:

            self.login_status.configure(
                text="Incorrect email or password.",
                text_color="#ff5555"
            )


    # ========================================================
    # SIGNUP SCREEN
    # ========================================================

    def show_signup(self):

        self.clear_screen()

        container = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )

        container.pack(
            expand=True,
            fill="both"
        )

        card = ctk.CTkFrame(
            container,
            width=430,
            height=570,
            corner_radius=20
        )

        card.place(
            relx=0.5,
            rely=0.5,
            anchor="center"
        )

        title = ctk.CTkLabel(
            card,
            text="Create Account",
            text_color=self.text_color(),
            font=ctk.CTkFont(
                size=30,
                weight="bold"
            )
        )

        title.pack(
            pady=(50, 5)
        )

        subtitle = ctk.CTkLabel(
            card,
            text="Create your Finn's AI account",
            text_color=self.secondary_text_color()
        )

        subtitle.pack(
            pady=(0, 25)
        )

        self.signup_email = ctk.CTkEntry(
            card,
            width=320,
            height=45,
            placeholder_text="Email address"
        )

        self.signup_email.pack(
            pady=10
        )

        self.signup_password = ctk.CTkEntry(
            card,
            width=320,
            height=45,
            placeholder_text="Password",
            show="*"
        )

        self.signup_password.pack(
            pady=10
        )

        self.signup_confirm = ctk.CTkEntry(
            card,
            width=320,
            height=45,
            placeholder_text="Confirm password",
            show="*"
        )

        self.signup_confirm.pack(
            pady=10
        )

        create_button = ctk.CTkButton(
            card,
            text="Create Account",
            width=320,
            height=45,
            command=self.signup
        )

        create_button.pack(
            pady=(20, 10)
        )

        back_button = ctk.CTkButton(
            card,
            text="Back to Login",
            width=320,
            height=40,
            fg_color="transparent",
            border_width=1,
            text_color=self.text_color(),
            command=self.show_login
        )

        back_button.pack(
            pady=10
        )

        self.signup_status = ctk.CTkLabel(
            card,
            text=""
        )

        self.signup_status.pack(
            pady=10
        )


    # ========================================================
    # SIGNUP
    # ========================================================

    def signup(self):

        email = self.signup_email.get().strip()

        password = self.signup_password.get()

        confirm = self.signup_confirm.get()

        if not email or not password or not confirm:

            self.signup_status.configure(
                text="Please fill in every field.",
                text_color="#ff5555"
            )

            return

        if not valid_email(email):

            self.signup_status.configure(
                text="Enter a valid email address.",
                text_color="#ff5555"
            )

            return

        if len(password) < 6:

            self.signup_status.configure(
                text="Password must be at least 6 characters.",
                text_color="#ff5555"
            )

            return

        if password != confirm:

            self.signup_status.configure(
                text="Passwords do not match.",
                text_color="#ff5555"
            )

            return

        if create_account(
            email,
            password
        ):

            self.show_login()

            self.login_status.configure(
                text="Account created! Log in below.",
                text_color="#55dd77"
            )

        else:

            self.signup_status.configure(
                text="An account with that email already exists.",
                text_color="#ff5555"
            )


    # ========================================================
    # MAIN APP
    # ========================================================

    def show_main_app(self):

        self.clear_screen()

        self.messages = []

        # ====================================================
        # SIDEBAR
        # ====================================================

        sidebar = ctk.CTkFrame(
            self,
            width=250,
            corner_radius=0
        )

        sidebar.pack(
            side="left",
            fill="y"
        )

        sidebar.pack_propagate(False)

        logo = ctk.CTkLabel(
            sidebar,
            text="Finn's AI",
            text_color=self.text_color(),
            font=ctk.CTkFont(
                size=25,
                weight="bold"
            )
        )

        logo.pack(
            padx=20,
            pady=(25, 20),
            anchor="w"
        )

        new_chat = ctk.CTkButton(
            sidebar,
            text="+  New Chat",
            height=45,
            command=self.new_chat
        )

        new_chat.pack(
            padx=15,
            pady=5,
            fill="x"
        )

        projects_label = ctk.CTkLabel(
            sidebar,
            text="PROJECTS",
            text_color=self.secondary_text_color(),
            font=ctk.CTkFont(
                size=12,
                weight="bold"
            )
        )

        projects_label.pack(
            padx=20,
            pady=(30, 10),
            anchor="w"
        )

        projects = [
            "📁 General",
            "📁 Coding",
            "📁 Fortnite",
            "📁 School"
        ]

        for project in projects:

            button = ctk.CTkButton(
                sidebar,
                text=project,
                anchor="w",
                fg_color="transparent",
                text_color=self.text_color()
            )

            button.pack(
                padx=10,
                pady=2,
                fill="x"
            )

        # ====================================================
        # BOTTOM SIDEBAR
        # ====================================================

        bottom = ctk.CTkFrame(
            sidebar,
            fg_color="transparent"
        )

        bottom.pack(
            side="bottom",
            fill="x",
            padx=10,
            pady=15
        )

        account = ctk.CTkLabel(
            bottom,
            text=self.current_email,
            text_color=self.text_color(),
            anchor="w"
        )

        account.pack(
            fill="x",
            pady=5
        )

        settings_button = ctk.CTkButton(
            bottom,
            text="⚙  Settings",
            fg_color="transparent",
            text_color=self.text_color(),
            anchor="w",
            command=self.open_settings
        )

        settings_button.pack(
            fill="x"
        )

        # ====================================================
        # MAIN CHAT
        # ====================================================

        main = ctk.CTkFrame(
            self,
            corner_radius=0
        )

        main.pack(
            side="right",
            fill="both",
            expand=True
        )

        self.chat_title = ctk.CTkLabel(
            main,
            text="New Chat",
            text_color=self.text_color(),
            font=ctk.CTkFont(
                size=20,
                weight="bold"
            )
        )

        self.chat_title.pack(
            pady=20
        )

        self.chat_area = ctk.CTkScrollableFrame(
            main,
            fg_color="transparent"
        )

        self.chat_area.pack(
            fill="both",
            expand=True,
            padx=30,
            pady=10
        )

        self.welcome_label = ctk.CTkLabel(
            self.chat_area,
            text="What can I help you with?",
            text_color=self.text_color(),
            font=ctk.CTkFont(
                size=28,
                weight="bold"
            )
        )

        self.welcome_label.pack(
            pady=(150, 10)
        )

        # ====================================================
        # INPUT
        # ====================================================

        input_frame = ctk.CTkFrame(
            main,
            fg_color="transparent"
        )

        input_frame.pack(
            fill="x",
            padx=30,
            pady=25
        )

        self.message_entry = ctk.CTkEntry(
            input_frame,
            height=50,
            placeholder_text="Message Finn's AI..."
        )

        self.message_entry.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(0, 10)
        )

        self.send_button = ctk.CTkButton(
            input_frame,
            text="Send",
            width=90,
            height=50,
            command=self.send_message
        )

        self.send_button.pack(
            side="right"
        )

        self.message_entry.bind(
            "<Return>",
            lambda event: self.send_message()
        )


    # ========================================================
    # SETTINGS
    # ========================================================

    def open_settings(self):

        settings = ctk.CTkToplevel(
            self
        )

        settings.title(
            "Settings"
        )

        settings.geometry(
            "430x420"
        )

        settings.resizable(
            False,
            False
        )

        settings.transient(
            self
        )

        title = ctk.CTkLabel(
            settings,
            text="Settings",
            text_color=self.text_color(),
            font=ctk.CTkFont(
                size=28,
                weight="bold"
            )
        )

        title.pack(
            pady=(30, 25)
        )

        appearance_label = ctk.CTkLabel(
            settings,
            text="Appearance",
            text_color=self.text_color(),
            font=ctk.CTkFont(
                size=15,
                weight="bold"
            )
        )

        appearance_label.pack(
            pady=(5, 8)
        )

        appearance_menu = ctk.CTkOptionMenu(
            settings,
            width=260,
            height=40,
            values=[
                "Dark",
                "Light",
                "System"
            ],
            command=lambda mode:
                self.change_appearance(
                    mode,
                    settings
                )
        )

        current_mode = ctk.get_appearance_mode().lower()

        if current_mode == "dark":

            appearance_menu.set(
                "Dark"
            )

        elif current_mode == "light":

            appearance_menu.set(
                "Light"
            )

        else:

            appearance_menu.set(
                "System"
            )

        appearance_menu.pack(
            pady=(0, 25)
        )

        account_label = ctk.CTkLabel(
            settings,
            text="Account",
            text_color=self.text_color(),
            font=ctk.CTkFont(
                size=15,
                weight="bold"
            )
        )

        account_label.pack(
            pady=(5, 8)
        )

        email_label = ctk.CTkLabel(
            settings,
            text=self.current_email,
            text_color=self.secondary_text_color()
        )

        email_label.pack(
            pady=(0, 20)
        )

        logout_button = ctk.CTkButton(
            settings,
            text="Log Out",
            width=260,
            height=45,
            fg_color="#d33",
            hover_color="#b22",
            command=lambda:
                self.logout(settings)
        )

        logout_button.pack(
            pady=10
        )

        close_button = ctk.CTkButton(
            settings,
            text="Close",
            width=260,
            height=40,
            fg_color="transparent",
            border_width=1,
            text_color=self.text_color(),
            command=settings.destroy
        )

        close_button.pack(
            pady=5
        )


    # ========================================================
    # CHANGE APPEARANCE
    # ========================================================

    def change_appearance(
        self,
        mode,
        settings_window=None
    ):

        if mode == "Dark":

            ctk.set_appearance_mode(
                "dark"
            )

        elif mode == "Light":

            ctk.set_appearance_mode(
                "light"
            )

        else:

            ctk.set_appearance_mode(
                "system"
            )

        if settings_window:

            settings_window.destroy()

        self.show_main_app()


    # ========================================================
    # LOGOUT
    # ========================================================

    def logout(
        self,
        settings_window=None
    ):

        if settings_window:

            settings_window.destroy()

        if os.path.exists(
            LOGIN_FILE
        ):

            try:

                os.remove(
                    LOGIN_FILE
                )

            except Exception:

                pass

        self.current_email = None

        self.messages = []

        self.show_login()


    # ========================================================
    # NEW CHAT
    # ========================================================

    def new_chat(self):

        self.messages = []

        for widget in self.chat_area.winfo_children():

            widget.destroy()

        self.chat_title.configure(
            text="New Chat",
            text_color=self.text_color()
        )

        self.welcome_label = ctk.CTkLabel(
            self.chat_area,
            text="What can I help you with?",
            text_color=self.text_color(),
            font=ctk.CTkFont(
                size=28,
                weight="bold"
            )
        )

        self.welcome_label.pack(
            pady=(150, 10)
        )


    # ========================================================
    # ADD MESSAGE
    # ========================================================

    def add_message(
        self,
        sender,
        message
    ):

        label = ctk.CTkLabel(
            self.chat_area,
            text=f"{sender}\n{message}",
            text_color=self.text_color(),
            anchor=(
                "w"
                if sender == "Finn's AI"
                else "e"
            ),
            justify=(
                "left"
                if sender == "Finn's AI"
                else "right"
            ),
            wraplength=750
        )

        label.pack(
            fill="x",
            padx=20,
            pady=10
        )

        self.chat_area.update_idletasks()

        try:

            self.chat_area._parent_canvas.yview_moveto(
                1.0
            )

        except Exception:

            pass


    # ========================================================
    # SEND MESSAGE
    # ========================================================

    def send_message(self):

        message = self.message_entry.get().strip()

        if not message:

            return

        self.message_entry.delete(
            0,
            "end"
        )

        for widget in self.chat_area.winfo_children():

            try:

                if (
                    "What can I help you with?"
                    in widget.cget("text")
                ):

                    widget.destroy()

            except Exception:

                pass

        self.add_message(
            "You",
            message
        )

        self.messages.append(
            {
                "role": "user",
                "content": message
            }
        )

        self.message_entry.configure(
            state="disabled"
        )

        self.send_button.configure(
            state="disabled"
        )

        self.add_message(
            "Finn's AI",
            "Thinking..."
        )

        thread = threading.Thread(
            target=self.get_ai_response,
            daemon=True
        )

        thread.start()


    # ========================================================
    # CONNECT TO AI SERVER
    # ========================================================

    def get_ai_response(self):

        try:

            response = requests.post(
                AI_SERVER_URL,
                json={
                    "message": self.messages[-1]["content"],
                    "messages": self.messages[:-1]
                },
                timeout=120
            )

            if response.status_code != 200:

                try:

                    error_data = response.json()

                    error_message = error_data.get(
                        "error",
                        f"Server returned HTTP {response.status_code}"
                    )

                except Exception:

                    error_message = (
                        f"Server returned HTTP "
                        f"{response.status_code}"
                    )

                raise Exception(
                    error_message
                )

            data = response.json()

            if not data.get("success"):

                raise Exception(
                    data.get(
                        "error",
                        "Unknown server error."
                    )
                )

            answer = data.get(
                "response",
                ""
            )

            if not answer:

                raise Exception(
                    "The server returned an empty response."
                )

            self.messages.append(
                {
                    "role": "assistant",
                    "content": answer
                }
            )

            self.after(
                0,
                lambda:
                self.display_ai_response(
                    answer
                )
            )

        except requests.exceptions.ConnectionError:

            self.after(
                0,
                lambda:
                self.display_ai_error(
                    "Couldn't connect to Finn's AI Server.\n\n"
                    "Make sure server.py is running."
                )
            )

        except requests.exceptions.Timeout:

            self.after(
                0,
                lambda:
                self.display_ai_error(
                    "The AI server took too long to respond."
                )
            )

        except Exception as error:

            error_text = str(
                error
            )

            self.after(
                0,
                lambda:
                self.display_ai_error(
                    error_text
                )
            )


    # ========================================================
    # DISPLAY RESPONSE
    # ========================================================

    def display_ai_response(
        self,
        answer
    ):

        self.remove_thinking_message()

        self.add_message(
            "Finn's AI",
            answer
        )

        self.message_entry.configure(
            state="normal"
        )

        self.send_button.configure(
            state="normal"
        )

        self.message_entry.focus()


    # ========================================================
    # DISPLAY ERROR
    # ========================================================

    def display_ai_error(
        self,
        error
    ):

        self.remove_thinking_message()

        self.add_message(
            "Finn's AI",
            error
        )

        self.message_entry.configure(
            state="normal"
        )

        self.send_button.configure(
            state="normal"
        )

        self.message_entry.focus()


    # ========================================================
    # REMOVE THINKING MESSAGE
    # ========================================================

    def remove_thinking_message(self):

        for widget in self.chat_area.winfo_children():

            try:

                if widget.cget("text") == (
                    "Finn's AI\nThinking..."
                ):

                    widget.destroy()

                    return

            except Exception:

                pass


    # ========================================================
    # CLOSE APP
    # ========================================================

    def close_app(self):

        self.destroy()


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    setup_database()

    app = FinnsAI()

    app.mainloop()
