import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from atm_backend import (ATMAccount, CURRENCY, DAILY_LIMIT, DENOMINATIONS,
                         ACCOUNT_NUMBER_LENGTH, PIN_LENGTH)
# coloring for app
NAVY = "#0A1128"          
PANEL = "#12204A"       
PANEL_LIGHT = "#1B2E63"   
BLUE = "#2F80ED"          
BLUE_HOVER = "#5599F5"
CYAN = "#38BDF8"         
GREEN = "#22C55E"
RED = "#EF4444"
RED_HOVER = "#F87171"
AMBER = "#F59E0B"
WHITE = "#FFFFFF"
TEXT = "#E6EEF9"
MUTED = "#8FA3C7"
PAPER = "#F8FAFC"        
INK = "#1E293B"

FONT = "Segoe UI"         
TITLE_FONT = (FONT, 26, "bold")
HEADING_FONT = (FONT, 18, "bold")
BODY_FONT = (FONT, 12)
SMALL_FONT = (FONT, 10)
BUTTON_FONT = (FONT, 13, "bold")
RECEIPT_FONT = ("Courier New", 12)
NUMBER_FONT = ("Courier New", 28, "bold")   # account number display
# Colors used to draw each type of note
NOTE_COLORS = {5000: "#7C3AED", 1000: "#0EA5E9", 500: "#16A34A", 100: "#D97706"}

DIGITS = "0123456789"


def money(amount):
    """Format a number like  PKR 25,000"""
    return CURRENCY + " " + format(amount, ",")
# resuable widgets
class FlatButton(tk.Label):
    """A flat colored button made from a Label.
    (Normal tk.Button ignores colors on macOS, a Label looks the same
    on every computer.)"""

    def __init__(self, parent, text, command, bg=BLUE, hover=BLUE_HOVER,
                 fg=WHITE, font=BUTTON_FONT, width=14, height=2):
        tk.Label.__init__(self, parent, text=text, bg=bg, fg=fg, font=font,
                          width=width, height=height, cursor="hand2")
        self.normal_color = bg
        self.hover_color = hover
        self.command = command
        self.bind("<Button-1>", self.on_click)
        self.bind("<Enter>", self.on_hover)
        self.bind("<Leave>", self.on_leave)

    def on_click(self, event):
        self.command()

    def on_hover(self, event):
        self.config(bg=self.hover_color)

    def on_leave(self, event):
        self.config(bg=self.normal_color)
class Keypad(tk.Frame):
    """ATM numeric keypad: 1-9, CLEAR, 0, ENTER.
    It does not know what the numbers are for. It just calls the three
    functions it is given."""

    def __init__(self, parent, on_digit, on_clear, on_enter):
        tk.Frame.__init__(self, parent, bg=NAVY)
        keys = [["1", "2", "3"],
                ["4", "5", "6"],
                ["7", "8", "9"],
                ["CLEAR", "0", "ENTER"]]
        for row_number in range(4):
            for column_number in range(3):
                label = keys[row_number][column_number]
                if label == "CLEAR":
                    key = FlatButton(self, label, on_clear, bg=AMBER,
                                     hover="#FBBF24", fg=NAVY, width=7, height=2)
                elif label == "ENTER":
                    key = FlatButton(self, label, on_enter, bg=GREEN,
                                     hover="#4ADE80", fg=NAVY, width=7, height=2)
                else:
                    # lambda remembers which digit this key belongs to
                    key = FlatButton(self, label,
                                     lambda digit=label: on_digit(digit),
                                     bg=PANEL_LIGHT, hover=BLUE, width=7, height=2)
                key.grid(row=row_number, column=column_number, padx=5, pady=5)

class ATMApp(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.title("Iqra Islamic BANK - ATM Simulation")
        self.configure(bg=NAVY)
        self.resizable(False, False)
        self.center_window(980, 680)

        self.atm = ATMAccount()        
        self.login_stage = "account"   
        self.login_text = ""           
        self.amount_entered = ""       
        self.amount_mode = ""          
        self.pin_text = ""             
        self.pin_values = []           
        self.key_handler = None        

        self.setup_table_style()
        self.build_header()
        self.build_footer()
        self.content = tk.Frame(self, bg=NAVY)
        self.content.pack(fill="both", expand=True, padx=30, pady=10)

        self.bind_all("<Key>", self.on_key_press)
        self.protocol("WM_DELETE_WINDOW", self.exit_atm)   # window X button
        self.show_login_screen()
    def center_window(self, width, height):
        x = (self.winfo_screenwidth() - width) // 2
        y = (self.winfo_screenheight() - height) // 2
        self.geometry(str(width) + "x" + str(height) + "+" + str(x) + "+" + str(y))

    def setup_table_style(self):
        """Dark theme for the transaction table (ttk.Treeview)."""
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background=PANEL, foreground=TEXT,
                        fieldbackground=PANEL, rowheight=40, font=BODY_FONT,
                        borderwidth=0)
        style.configure("Treeview.Heading", background=BLUE, foreground=WHITE,
                        font=(FONT, 11, "bold"), relief="flat")
        style.map("Treeview", background=[("selected", PANEL_LIGHT)])

    def build_header(self):
        header = tk.Frame(self, bg=PANEL, height=64)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="Iqra Islamic BANK", bg=PANEL, fg=WHITE,
                 font=(FONT, 20, "bold")).pack(side="left", padx=30)
        tk.Label(header, text="ATM", bg=BLUE, fg=WHITE, font=(FONT, 11, "bold"),
                 padx=10, pady=2).pack(side="left")
        self.clock_label = tk.Label(header, text="", bg=PANEL, fg=CYAN,
                                    font=(FONT, 12, "bold"))
        self.clock_label.pack(side="right", padx=30)
        self.update_clock()

    def update_clock(self):
        """Show the date and time. after() runs this again every second."""
        self.clock_label.config(text=datetime.now().strftime("%d %b %Y   %H:%M:%S"))
        self.after(1000, self.update_clock)

    def build_footer(self):
        tk.Label(self, text="Educational simulation  |  Fictional demo data only  |  "
                 "Not a real banking application",
                 bg=NAVY, fg=MUTED, font=SMALL_FONT).pack(side="bottom", pady=8)

    def clear_screen(self):
        """Remove the old screen so a new one can be drawn."""
        for widget in self.content.winfo_children():
            widget.destroy()
        self.key_handler = None

    def on_key_press(self, event):
        """Pass computer-keyboard keys to the current screen (if it wants them)."""
        if self.key_handler is not None:
            self.key_handler(event)

    def handle_keyboard(self, event, add_digit, backspace, clear, submit):
        """Shared keyboard logic: digits, Backspace, Esc and Enter."""
        if event.char != "" and event.char in DIGITS:
            add_digit(event.char)
        elif event.keysym == "BackSpace":
            backspace()
        elif event.keysym == "Escape":
            clear()
        elif event.keysym == "Return":
            submit()

    def show_message(self, label, text, kind):
        """Put colored text in a message label. kind = error / success / info"""
        colors = {"error": RED, "success": GREEN, "info": CYAN}
        label.config(text=text, fg=colors[kind])

    def make_card(self, parent, **options):
        return tk.Frame(parent, bg=PANEL, **options)

    def make_dots(self, text):
        """Mask a PIN: a filled dot per typed digit, an empty dot for the rest."""
        dots = ""
        for position in range(PIN_LENGTH):
            if position < len(text):
                dots = dots + "●  "
            else:
                dots = dots + "○  "
        return dots.strip()

    def make_detail_rows(self, parent, rows):
        """Draw a list of (label, value) pairs as two neat columns."""
        table = tk.Frame(parent, bg=PANEL)
        table.pack(pady=10)
        for row_number in range(len(rows)):
            tk.Label(table, text=rows[row_number][0], bg=PANEL, fg=MUTED,
                     font=BODY_FONT, anchor="w", width=20).grid(
                         row=row_number, column=0, pady=3)
            tk.Label(table, text=rows[row_number][1], bg=PANEL, fg=WHITE,
                     font=(FONT, 12, "bold"), anchor="e", width=26).grid(
                         row=row_number, column=1, pady=3)
# login screen
    def show_login_screen(self):
        self.clear_screen()
        self.login_stage = "account"
        self.login_text = ""
        self.key_handler = lambda event: self.handle_keyboard(
            event, self.login_add_digit, self.login_backspace,
            self.login_clear, self.login_submit)

        left = self.make_card(self.content, padx=40, pady=30)
        left.pack(side="left", fill="both", expand=True, padx=(0, 20), pady=10)
        right = tk.Frame(self.content, bg=NAVY)
        right.pack(side="right", padx=(0, 10))

        tk.Label(left, text="WELCOME", bg=PANEL, fg=WHITE,
                 font=TITLE_FONT).pack(anchor="w")
        self.login_prompt = tk.Label(left, text="", bg=PANEL, fg=MUTED,
                                     font=BODY_FONT, justify="left")
        self.login_prompt.pack(anchor="w", pady=(4, 24))

        # Shows the account number digits, or the masked PIN dots
        self.login_display = tk.Label(left, text="", bg=NAVY, fg=CYAN,
                                      padx=25, pady=10)
        self.login_display.pack(anchor="w")

        self.login_message = tk.Label(left, text="Insert card simulated.",
                                      bg=PANEL, fg=CYAN, font=(FONT, 12, "bold"),
                                      wraplength=400, justify="left")
        self.login_message.pack(anchor="w", pady=20)

        button_row = tk.Frame(left, bg=PANEL)
        button_row.pack(anchor="w", pady=(10, 0))
        FlatButton(button_row, "EXIT", self.exit_atm, bg=RED, hover=RED_HOVER,
                   width=10, height=1).pack(side="left")
        # This button is only shown on the PIN step (see refresh_login_display)
        self.back_button = FlatButton(button_row, "CHANGE ACCOUNT", self.login_go_back,
                                      bg=PANEL_LIGHT, hover=BLUE, width=16, height=1)

        Keypad(right, self.login_add_digit, self.login_clear,
               self.login_submit).pack(pady=20)
        self.refresh_login_display()

    def refresh_login_display(self):
        """Update the prompt and the digits for the current login step."""
        if self.login_stage == "account":
            self.login_prompt.config(text="Please enter your 10-digit account number")
            padded = self.login_text + "_" * (ACCOUNT_NUMBER_LENGTH - len(self.login_text))
            grouped = padded[0:4] + "   " + padded[4:7] + "   " + padded[7:10]
            self.login_display.config(text=grouped, font=NUMBER_FONT)
            self.back_button.pack_forget()
        else:
            masked = self.atm.mask_account_number(self.atm.selected_number)
            self.login_prompt.config(text="Account " + masked + "\nPlease enter your 4-digit PIN")
            self.login_display.config(text=self.make_dots(self.login_text),
                                      font=(FONT, 34, "bold"))
            self.back_button.pack(side="left", padx=12)

    def login_add_digit(self, digit):
        if self.login_stage == "account":
            max_length = ACCOUNT_NUMBER_LENGTH
        else:
            max_length = PIN_LENGTH
        if len(self.login_text) < max_length:
            self.login_text = self.login_text + digit
            self.refresh_login_display()

    def login_backspace(self):
        self.login_text = self.login_text[:-1]
        self.refresh_login_display()

    def login_clear(self):
        self.login_text = ""
        self.refresh_login_display()

    def login_go_back(self):
        """Go back from the PIN step to the account number step."""
        self.login_stage = "account"
        self.login_text = ""
        self.refresh_login_display()
        self.show_message(self.login_message, "Enter your account number.", "info")

    def login_submit(self):
        if self.login_stage == "account":
            self.login_submit_account()
        else:
            self.login_submit_pin()

    def login_submit_account(self):
        """Step 1: ask the backend if the account number exists."""
        found, message = self.atm.check_account_number(self.login_text)
        if found:
            self.login_stage = "pin"
            self.login_text = ""
            self.refresh_login_display()
            self.show_message(self.login_message, "Account found. Enter your PIN.", "info")
        elif self.atm.locked:
            self.show_locked_screen()
        else:
            self.show_message(self.login_message, message, "error")
            self.login_clear()

    def login_submit_pin(self):
        """Step 2: ask the backend to check the PIN."""
        if len(self.login_text) < PIN_LENGTH:
            self.show_message(self.login_message, "PIN must have 4 digits.", "error")
            return
        success, message = self.atm.check_pin(self.login_text)
        if success:
            self.show_dashboard()
        elif self.atm.locked:
            self.show_locked_screen()
        else:
            self.show_message(self.login_message, message, "error")
            self.login_clear()
# screen locked after three wrong pin attempts
    def show_locked_screen(self):
        self.clear_screen()
        card = self.make_card(self.content, padx=60, pady=50)
        card.pack(expand=True)
        tk.Label(card, text="SESSION LOCKED", bg=PANEL, fg=RED,
                 font=TITLE_FONT).pack()
        tk.Label(card, text="Three incorrect PIN attempts.\n"
                 "Your card has been blocked (simulation).\n\n"
                 "Please close and restart the program to try again.",
                 bg=PANEL, fg=TEXT, font=BODY_FONT, justify="center").pack(pady=25)
        FlatButton(card, "EXIT", self.exit_atm, bg=RED, hover=RED_HOVER,
                   width=14).pack()
# deshboard main menu
    def show_dashboard(self):
        self.clear_screen()
        details = self.atm.get_account_details()

        tk.Label(self.content, text="Welcome, " + details["holder_name"], bg=NAVY,
                 fg=WHITE, font=HEADING_FONT).pack(anchor="w")
        tk.Label(self.content, text="Please select a transaction", bg=NAVY,
                 fg=MUTED, font=BODY_FONT).pack(anchor="w", pady=(0, 14))

        info_row = tk.Frame(self.content, bg=NAVY)
        info_row.pack(fill="x", pady=(0, 10))
        masked = self.atm.mask_account_number(details["account_number"])
        cards = [("ACCOUNT", masked + "  (" + details["account_type"] + ")"),
                 ("BRANCH", details["branch"]),
                 ("DAILY LIMIT LEFT", money(details["remaining_today"]))]
        for title, value in cards:
            self.make_info_card(info_row, title, value).pack(
                side="left", expand=True, fill="both", padx=5)
        grid = tk.Frame(self.content, bg=NAVY)
        grid.pack(expand=True)
        tiles = [
            ("Balance Inquiry", self.show_balance_screen, BLUE, BLUE_HOVER),
            ("Cash Withdrawal", lambda: self.show_amount_screen("withdraw"), BLUE, BLUE_HOVER),
            ("Cash Deposit", lambda: self.show_amount_screen("deposit"), BLUE, BLUE_HOVER),
            ("Mini Statement", self.show_statement_screen, BLUE, BLUE_HOVER),
            ("Account Details", self.show_details_screen, BLUE, BLUE_HOVER),
            ("Change PIN", self.show_change_pin_screen, BLUE, BLUE_HOVER),
            ("Logout", self.logout, AMBER, "#FBBF24"),
            ("Exit", self.exit_atm, RED, RED_HOVER),
        ]
        for index in range(len(tiles)):
            title, command, color, hover = tiles[index]
            text_color = NAVY if color == AMBER else WHITE
            tile = FlatButton(grid, title, command, bg=color, hover=hover,
                              fg=text_color, font=(FONT, 14, "bold"),
                              width=16, height=3)
            tile.grid(row=index // 4, column=index % 4, padx=8, pady=8)

    def make_info_card(self, parent, title, value):
        card = tk.Frame(parent, bg=PANEL, padx=18, pady=10)
        tk.Label(card, text=title, bg=PANEL, fg=MUTED, font=SMALL_FONT).pack(anchor="w")
        tk.Label(card, text=value, bg=PANEL, fg=CYAN,
                 font=(FONT, 13, "bold")).pack(anchor="w")
        return card
# Balance inquiry
    def show_balance_screen(self):
        self.clear_screen()
        card = self.make_card(self.content, padx=60, pady=35)
        card.pack(expand=True)

        tk.Label(card, text="BALANCE INQUIRY", bg=PANEL, fg=MUTED,
                 font=(FONT, 13, "bold")).pack()
        tk.Label(card, text="Available Balance", bg=PANEL, fg=TEXT,
                 font=BODY_FONT).pack(pady=(20, 0))
        # get_balance() always returns the latest saved balance
        tk.Label(card, text=money(self.atm.get_balance()), bg=PANEL, fg=GREEN,
                 font=(FONT, 40, "bold")).pack(pady=(0, 20))

        self.make_detail_rows(card, [
            ("Withdrawn today", money(self.atm.get_withdrawn_today())),
            ("Daily limit", money(DAILY_LIMIT)),
            ("Remaining today", money(self.atm.get_remaining_daily_limit()))])

        FlatButton(card, "BACK TO MENU", self.show_dashboard,
                   width=18).pack(pady=(25, 0))
# account details
    def show_details_screen(self):
        self.clear_screen()
        details = self.atm.get_account_details()
        card = self.make_card(self.content, padx=50, pady=25)
        card.pack(expand=True)
        tk.Label(card, text="ACCOUNT DETAILS", bg=PANEL, fg=WHITE,
                 font=HEADING_FONT).pack(pady=(0, 10))
        self.make_detail_rows(card, [
            ("Account holder", details["holder_name"]),
            ("Account number", details["account_number"]),
            ("Account type", details["account_type"]),
            ("Branch", details["branch"]),
            ("Currency", "PKR - Pakistani Rupee"),
            ("Available balance", money(details["balance"])),
            ("Daily withdrawal limit", money(details["daily_limit"])),
            ("Withdrawn today", money(details["withdrawn_today"])),
            ("Remaining today", money(details["remaining_today"])),
            ("Total transactions", str(details["total_transactions"]))])
        FlatButton(card, "BACK TO MENU", self.show_dashboard,
                   width=18, height=1).pack(pady=(15, 0))    
    # amount enter for withdrwal and deposite
    def show_amount_screen(self, mode):
        self.clear_screen()
        self.amount_mode = mode
        self.amount_entered = ""
        self.key_handler = lambda event: self.handle_keyboard(
            event, self.amount_add_digit, self.amount_backspace,
            self.amount_clear, self.amount_submit)

        left = self.make_card(self.content, padx=35, pady=25)
        left.pack(side="left", fill="both", expand=True, padx=(0, 20), pady=10)
        right = tk.Frame(self.content, bg=NAVY)
        right.pack(side="right", padx=(0, 10))

        if mode == "withdraw":
            title = "CASH WITHDRAWAL"
            hint = ("Available balance: " + money(self.atm.get_balance()) + "\n" +
                    "Daily limit left: " + money(self.atm.get_remaining_daily_limit()) + "\n" +
                    "Amounts must be multiples of PKR 100")
        else:
            title = "CASH DEPOSIT"
            hint = "Enter the amount you want to deposit"

        tk.Label(left, text=title, bg=PANEL, fg=WHITE, font=HEADING_FONT).pack(anchor="w")
        tk.Label(left, text=hint, bg=PANEL, fg=MUTED, font=BODY_FONT,
                 justify="left").pack(anchor="w", pady=(6, 14))

        self.amount_label = tk.Label(left, text="", bg=NAVY, fg=CYAN,
                                     font=(FONT, 28, "bold"), anchor="e",
                                     width=14, padx=15, pady=8)
        self.amount_label.pack(anchor="w")
        self.refresh_amount_display()

        self.amount_message = tk.Label(left, text="Enter amount, then press ENTER.",
                                       bg=PANEL, fg=CYAN, font=(FONT, 12, "bold"),
                                       wraplength=380, justify="left")
        self.amount_message.pack(anchor="w", pady=12)

        # Quick amount buttons
        quick_row = tk.Frame(left, bg=PANEL)
        quick_row.pack(anchor="w", pady=4)
        quick_amounts = [500, 1000, 5000, 10000]
        for value in quick_amounts:
            FlatButton(quick_row, format(value, ","),
                       lambda amount=value: self.set_quick_amount(amount),
                       bg=PANEL_LIGHT, hover=BLUE, font=(FONT, 11, "bold"),
                       width=7, height=1).pack(side="left", padx=(0, 8))

        FlatButton(left, "CANCEL", self.show_dashboard, bg=RED, hover=RED_HOVER,
                   width=10, height=1).pack(anchor="w", pady=(22, 0))

        Keypad(right, self.amount_add_digit, self.amount_clear,
               self.amount_submit).pack(pady=20)

    def refresh_amount_display(self):
        if self.amount_entered == "":
            self.amount_label.config(text=CURRENCY + " 0")
        else:
            self.amount_label.config(text=money(int(self.amount_entered)))

    def amount_add_digit(self, digit):
        # Limit to 7 digits and ignore leading zeros
        if len(self.amount_entered) < 7:
            if not (self.amount_entered == "" and digit == "0"):
                self.amount_entered = self.amount_entered + digit
                self.refresh_amount_display()

    def amount_backspace(self):
        self.amount_entered = self.amount_entered[:-1]
        self.refresh_amount_display()

    def amount_clear(self):
        self.amount_entered = ""
        self.refresh_amount_display()

    def set_quick_amount(self, value):
        self.amount_entered = str(value)
        self.refresh_amount_display()

    def amount_submit(self):
        """Ask the BACKEND to do the transaction, then show the result."""
        if self.amount_mode == "withdraw":
            result = self.atm.withdraw(self.amount_entered)
        else:
            result = self.atm.deposit(self.amount_entered)

        if result["success"]:
            self.show_receipt_screen(result)
        else:
            self.show_message(self.amount_message, result["message"], "error")
            self.amount_clear()
# recipt
    def show_receipt_screen(self, result):
        self.clear_screen()
        receipt = result["receipt"]

        tk.Label(self.content, text=result["message"].upper(), bg=NAVY, fg=GREEN,
                 font=HEADING_FONT).pack(anchor="w")
        if "notes" in result:
            note_text = "Please take your cash."
        else:
            note_text = "Your deposit has been added to your account."
        tk.Label(self.content, text=note_text, bg=NAVY, fg=MUTED,
                 font=BODY_FONT).pack(anchor="w", pady=(0, 10))

        middle = tk.Frame(self.content, bg=NAVY)
        middle.pack(expand=True)

        # paper receipt 
        paper = tk.Frame(middle, bg=PAPER, padx=30, pady=18)
        paper.pack(side="left", padx=15)
        line = "-" * 32
        lines = [
            "     Iqra Islamic BANK",
            "  TRANSACTION RECEIPT",
            line,
            "Txn ID  : " + receipt["id"],
            "Account : " + receipt["account"],
            "Type    : " + receipt["type"],
            "Date    : " + receipt["date"],
            "Time    : " + receipt["time"],
            line,
            "Amount  : " + money(receipt["amount"]),
            "Balance : " + money(receipt["balance_after"]),
            line,
            "  Thank you for banking",
            "     with Iqra Islamic BANK!",
        ]
        tk.Label(paper, text="\n".join(lines), bg=PAPER, fg=INK,
                 font=RECEIPT_FONT, justify="left").pack()

        # withdrawal notes
        if "notes" in result:
            self.build_dispense_card(middle, result["notes"], receipt["amount"])
        buttons = tk.Frame(self.content, bg=NAVY)
        buttons.pack(pady=(5, 0))
        FlatButton(buttons, "BACK TO MENU", self.show_dashboard,
                   width=16, height=1).pack(side="left", padx=8)
        FlatButton(buttons, "LOGOUT", self.logout, bg=AMBER, hover="#FBBF24",
                   fg=NAVY, width=16, height=1).pack(side="left", padx=8)
    def build_dispense_card(self, parent, notes, total):
        card = self.make_card(parent, padx=30, pady=18)
        card.pack(side="left", padx=15, anchor="n")
        tk.Label(card, text="CASH DISPENSED", bg=PANEL, fg=WHITE,
                 font=(FONT, 14, "bold")).pack(pady=(0, 10))
        for note_value in DENOMINATIONS:
            count = notes[note_value]
            if count > 0:
                row = tk.Frame(card, bg=PANEL)
                row.pack(fill="x", pady=4)
                tk.Label(row, text=CURRENCY + " " + format(note_value, ","),
                         bg=NOTE_COLORS[note_value], fg=WHITE, width=11,
                         font=(FONT, 12, "bold"), pady=4).pack(side="left")
                tk.Label(row, text="x  " + str(count), bg=PANEL, fg=TEXT,
                         font=(FONT, 14, "bold"), width=6).pack(side="left", padx=10)
        tk.Label(card, text="Total: " + money(total), bg=PANEL, fg=GREEN,
                 font=(FONT, 14, "bold")).pack(pady=(14, 0))
# for statement 
    def show_statement_screen(self):
        self.clear_screen()
        tk.Label(self.content, text="MINI STATEMENT", bg=NAVY, fg=WHITE,
                 font=HEADING_FONT).pack(anchor="w")
        tk.Label(self.content, text="Your last 5 transactions (newest first)",
                 bg=NAVY, fg=MUTED, font=BODY_FONT).pack(anchor="w", pady=(0, 10))

        columns = ("id", "type", "amount", "date", "time", "balance")
        headings = ("Transaction ID", "Type", "Amount", "Date", "Time", "Balance")
        widths = (120, 110, 130, 110, 100, 140)
        table = ttk.Treeview(self.content, columns=columns, show="headings", height=5)
        for index in range(len(columns)):
            table.heading(columns[index], text=headings[index])
            table.column(columns[index], width=widths[index], anchor="center")
        table.tag_configure("deposit", foreground="#4ADE80")
        table.tag_configure("withdrawal", foreground="#FCA5A5")
        table.pack(fill="x", pady=5)

        transactions = self.atm.get_mini_statement()
        if len(transactions) == 0:
            tk.Label(self.content, text="No transactions yet.", bg=NAVY, fg=MUTED,
                     font=BODY_FONT).pack(pady=15)
        for item in transactions:
            if item["type"] == "Deposit":
                tag = "deposit"
            else:
                tag = "withdrawal"
            table.insert("", "end", tags=(tag,), values=(
                item["id"], item["type"], money(item["amount"]),
                item["date"], item["time"], money(item["balance_after"])))

        FlatButton(self.content, "BACK TO MENU", self.show_dashboard,
                   width=18, height=1).pack(pady=20)
# change pin
    def show_change_pin_screen(self):
        self.clear_screen()
        self.pin_text = ""
        self.pin_values = []
        self.key_handler = lambda event: self.handle_keyboard(
            event, self.pin_add_digit, self.pin_backspace,
            self.pin_clear, self.pin_submit)

        left = self.make_card(self.content, padx=40, pady=30)
        left.pack(side="left", fill="both", expand=True, padx=(0, 20), pady=10)
        right = tk.Frame(self.content, bg=NAVY)
        right.pack(side="right", padx=(0, 10))

        tk.Label(left, text="CHANGE PIN", bg=PANEL, fg=WHITE,
                 font=HEADING_FONT).pack(anchor="w")
        self.pin_prompt = tk.Label(left, text="", bg=PANEL, fg=MUTED, font=BODY_FONT)
        self.pin_prompt.pack(anchor="w", pady=(6, 24))

        self.pin_dots = tk.Label(left, text="", bg=NAVY, fg=CYAN,
                                 font=(FONT, 34, "bold"), padx=30, pady=10)
        self.pin_dots.pack(anchor="w")

        self.pin_message = tk.Label(left, text="", bg=PANEL, fg=CYAN,
                                    font=(FONT, 12, "bold"), wraplength=400,
                                    justify="left")
        self.pin_message.pack(anchor="w", pady=20)

        FlatButton(left, "CANCEL", self.show_dashboard, bg=RED, hover=RED_HOVER,
                   width=10, height=1).pack(anchor="w", pady=(10, 0))
        Keypad(right, self.pin_add_digit, self.pin_clear,
               self.pin_submit).pack(pady=20)
        self.refresh_pin_screen()
    def refresh_pin_screen(self):
        prompts = ["Enter your CURRENT PIN",
                   "Enter your NEW 4-digit PIN",
                   "Re-enter the NEW PIN to confirm"]
        self.pin_prompt.config(text="Step " + str(len(self.pin_values) + 1) +
                               " of 3:  " + prompts[len(self.pin_values)])
        self.pin_dots.config(text=self.make_dots(self.pin_text))
    def pin_add_digit(self, digit):
        if len(self.pin_text) < PIN_LENGTH:
            self.pin_text = self.pin_text + digit
            self.refresh_pin_screen()
    def pin_backspace(self):
        self.pin_text = self.pin_text[:-1]
        self.refresh_pin_screen()
    def pin_clear(self):
        self.pin_text = ""
        self.refresh_pin_screen()
    def pin_submit(self):
        if len(self.pin_text) < PIN_LENGTH:
            self.show_message(self.pin_message, "PIN must have 4 digits.", "error")
            return
        # Store this step and move to the next one
        self.pin_values.append(self.pin_text)
        self.pin_text = ""
        if len(self.pin_values) < 3:
            self.pin_message.config(text="")
            self.refresh_pin_screen()
            return
        result = self.atm.change_pin(self.pin_values[0], self.pin_values[1],
                                     self.pin_values[2])
        if result["success"]:
            self.show_pin_changed_screen()
        else:
            self.pin_values = []
            self.refresh_pin_screen()
            self.show_message(self.pin_message, result["message"] + " Start again.",
                              "error")
    def show_pin_changed_screen(self):
        self.clear_screen()
        card = self.make_card(self.content, padx=60, pady=45)
        card.pack(expand=True)
        tk.Label(card, text="PIN CHANGED SUCCESSFULLY", bg=PANEL, fg=GREEN,
                 font=HEADING_FONT).pack()
        tk.Label(card, text="Please use your new PIN next time you log in.",
                 bg=PANEL, fg=TEXT, font=BODY_FONT).pack(pady=20)
        buttons = tk.Frame(card, bg=PANEL)
        buttons.pack()
        FlatButton(buttons, "BACK TO MENU", self.show_dashboard,
                   width=16, height=1).pack(side="left", padx=8)
        FlatButton(buttons, "LOGOUT", self.logout, bg=AMBER, hover="#FBBF24",
                   fg=NAVY, width=16, height=1).pack(side="left", padx=8)

    def logout(self):
        self.atm.logout()
        self.show_login_screen()

    def exit_atm(self):
        """Ask first, then close. Data is already saved after every transaction."""
        if messagebox.askyesno("Exit ATM", "Do you want to exit the ATM?"):
            self.destroy()
if __name__ == "__main__":
    app = ATMApp()
    app.mainloop()