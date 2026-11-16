import ctypes
import math
import os
import re
import tkinter as tk
from tkinter import messagebox, ttk


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DLL_PATH = os.path.join(CURRENT_DIR, "calculation.dll")


UNITS = {
    "seconds": "S",
    "minutes": "M",
    "hours": "H",
    "days": "D",
    "weeks": "W",
    "months": "O",
    "years": "Y",
}

SECONDS_PER_UNIT = {
    "S": 1,
    "M": 60,
    "H": 3600,
    "D": 86400,
    "W": 604800,
    "O": 2592000,
    "Y": 31536000,
}

SHORT_UNITS = {
    "S": "sec",
    "M": "min",
    "H": "hr",
    "D": "day",
    "W": "wk",
    "O": "mo",
    "Y": "yr",
}

ENTRY_WIDTH = 20
COMBO_WIDTH = 7

BG = "#141411"
CARD = "#242424"
FIELD = "#171718"
TEXT = "#DFDFDF"
MUTED = "#474A4E"
BORDER = "#1A1B1B"
ACCENT = "#FAED36"
ACCENT_HOVER = "#FAED36"
ACCENT_PRESSED = "#FAED36"


def load_library():
    library = ctypes.CDLL(DLL_PATH)

    library.convertTime.argtypes = [
        ctypes.c_double,
        ctypes.c_char,
        ctypes.c_char,
    ]
    library.convertTime.restype = ctypes.c_double

    library.compareTime.argtypes = [
        ctypes.c_double,
        ctypes.c_char,
        ctypes.c_double,
        ctypes.c_char,
    ]
    library.compareTime.restype = ctypes.c_int

    library.formatHumanReadable.argtypes = [
        ctypes.c_double,
        ctypes.c_char,
        ctypes.POINTER(ctypes.c_char),
        ctypes.c_int,
    ]
    library.formatHumanReadable.restype = None

    return library


try:
    lib = load_library()
except OSError as error:
    error_root = tk.Tk()
    error_root.withdraw()
    messagebox.showerror(
        "Error",
        "Could not load calculation.dll.\n\n"
        f"Make sure the DLL is located here:\n{DLL_PATH}\n\n"
        f"Details: {error}",
    )
    error_root.destroy()
    raise SystemExit


def unit_arg(code):
    return code.encode("ascii")


def read_number(entry):
    text = entry.get().strip().replace(",", ".")

    try:
        value = float(text)
    except ValueError:
        raise ValueError("Please enter a valid number.")

    if not math.isfinite(value):
        raise ValueError("The value must be a finite number.")

    if value < 0:
        raise ValueError("Negative values are not allowed.")

    return value


def format_number(value):
    if math.isclose(value, round(value), abs_tol=1e-10):
        return str(int(round(value)))

    return f"{value:.8f}".rstrip("0").rstrip(".")


def format_remainder_seconds(seconds):
    buffer = ctypes.create_string_buffer(128)

    lib.formatHumanReadable(
        ctypes.c_double(float(seconds)),
        unit_arg("S"),
        buffer,
        len(buffer),
    )

    text = buffer.value.decode("utf-8", errors="replace")
    parts = re.findall(r"(\d+)([SMHDWOY])", text)

    return " ".join(
        f"{amount} {SHORT_UNITS[code]}"
        for amount, code in parts
    )


def make_conversion_result(value, from_code, to_code):
    converted = lib.convertTime(
        ctypes.c_double(value),
        unit_arg(from_code),
        unit_arg(to_code),
    )

    if not math.isfinite(converted):
        raise ValueError("The result is too large to calculate.")

    if to_code == "S":
        return f"{format_number(converted)} sec"

    total_seconds = value * SECONDS_PER_UNIT[from_code]
    target_seconds = SECONDS_PER_UNIT[to_code]

    whole_units = math.floor(converted + 1e-12)
    remainder = total_seconds - whole_units * target_seconds

    if abs(remainder) < 1e-9:
        return f"{whole_units} {SHORT_UNITS[to_code]}"

    if remainder < 0:
        remainder = 0

    result_parts = []

    if whole_units > 0:
        result_parts.append(f"{whole_units} {SHORT_UNITS[to_code]}")

    if math.isclose(remainder, round(remainder), abs_tol=1e-9):
        remainder_text = format_remainder_seconds(round(remainder))
    else:
        remainder_text = f"{format_number(remainder)} sec"

    if remainder_text:
        result_parts.append(remainder_text)

    return " ".join(result_parts)


def convert_time():
    try:
        value = read_number(input_value)
        from_code = UNITS[from_unit.get()]
        to_code = UNITS[to_unit.get()]

        result = make_conversion_result(value, from_code, to_code)

        output_value.configure(state="normal")
        output_value.delete(0, tk.END)
        output_value.insert(0, result)
        output_value.configure(state="readonly")

    except (ValueError, KeyError) as error:
        messagebox.showerror("Error", str(error))


def compare_time():
    try:
        value1 = read_number(compare_input_1)
        value2 = read_number(compare_input_2)

        unit1 = UNITS[compare_unit_1.get()]
        unit2 = UNITS[compare_unit_2.get()]

        result = lib.compareTime(
            ctypes.c_double(value1),
            unit_arg(unit1),
            ctypes.c_double(value2),
            unit_arg(unit2),
        )

        if result == -99:
            raise ValueError("Could not compare the entered values.")

        compare_button.configure(text={1: ">", 0: "=", -1: "<"}[result])

    except (ValueError, KeyError) as error:
        messagebox.showerror("Error", str(error))


tooltip_window = None


def show_tooltip(event):
    global tooltip_window

    if tooltip_window is not None:
        return

    x = event.widget.winfo_rootx()
    y = event.widget.winfo_rooty() - 50

    tooltip_window = tk.Toplevel(root)
    tooltip_window.wm_overrideredirect(True)
    tooltip_window.wm_geometry(f"+{x}+{y}")

    tk.Label(
        tooltip_window,
        text="1 month = 30 days\n1 year = 365 days",
        bg=CARD,
        fg=TEXT,
        font=(FONT_FAMILY, 9),
        padx=10,
        pady=7,
        relief="solid",
        borderwidth=1,
    ).pack()


def hide_tooltip(_event=None):
    global tooltip_window

    if tooltip_window is not None:
        tooltip_window.destroy()
        tooltip_window = None


root = tk.Tk()
root.title("Time Converter")
root.resizable(False, False)
root.configure(bg=BG)

FONT_FAMILY = "Aptos"
root.option_add("*Font", (FONT_FAMILY, 10))

style = ttk.Style(root)
if "clam" in style.theme_names():
    style.theme_use("clam")

style.configure(
    "TEntry",
    fieldbackground=FIELD,
    foreground=TEXT,
    insertcolor=TEXT,
    padding=(7, 5),
    borderwidth=1,
    bordercolor=BORDER,
    lightcolor=BORDER,
    darkcolor=BORDER,
    relief="flat",
)

style.map(
    "TEntry",
    fieldbackground=[
        ("readonly", FIELD),
        ("focus", FIELD),
    ],
    foreground=[("readonly", TEXT)],
    bordercolor=[("focus", BORDER)],
    lightcolor=[("focus", BORDER)],
    darkcolor=[("focus", BORDER)],
)


style.configure(
    "TCombobox",
    fieldbackground=FIELD,
    background=FIELD,
    foreground=TEXT,
    arrowcolor=MUTED,
    padding=(7, 5),
    borderwidth=1,
    bordercolor=BORDER,
    lightcolor=BORDER,
    darkcolor=BORDER,
    relief="flat",
)

style.map(
    "TCombobox",
    fieldbackground=[
        ("readonly", FIELD),
        ("focus", FIELD),
    ],
    foreground=[("readonly", TEXT)],
    selectbackground=[("readonly", FIELD)],
    selectforeground=[("readonly", TEXT)],
    bordercolor=[("focus", BORDER)],
    lightcolor=[("focus", BORDER)],
    darkcolor=[("focus", BORDER)],
)


style.configure(
    "Accent.TButton",
    background=ACCENT,
    foreground="#06201D",
    font=(FONT_FAMILY, 12, "bold"),
    padding=(4, 3),
    borderwidth=0,
    relief="flat",
)

style.map(
    "Accent.TButton",
    background=[
        ("active", ACCENT_HOVER),
        ("pressed", ACCENT_PRESSED),
    ],
    foreground=[
        ("active", "#06201D"),
        ("pressed", "#06201D"),
    ],
)

main = tk.Frame(root, bg=BG)
main.pack(fill="both", expand=True, padx=16, pady=(12, 20))


def make_card(parent):
    return tk.Frame(
        parent,
        bg=CARD,
        highlightthickness=0,
        highlightbackground=BORDER,
        bd=0,
    )


def make_heading(parent, text):
    return tk.Label(
        parent,
        text=text,
        bg=CARD,
        fg=TEXT,
        font=(FONT_FAMILY, 11, "bold"),
    )


convert_card = make_card(main)
convert_card.pack(fill="x", pady=(0, 10))

make_heading(convert_card, "Time Conversion").pack(pady=(10, 8))

convert_row = tk.Frame(convert_card, bg=CARD)
convert_row.pack(padx=12, pady=(0, 11))

convert_left = tk.Frame(convert_row, bg=CARD)
convert_left.pack(side="left")

input_value = ttk.Entry(convert_left, width=ENTRY_WIDTH)
input_value.pack(side="left")

from_unit = ttk.Combobox(
    convert_left,
    values=list(UNITS.keys()),
    state="readonly",
    width=COMBO_WIDTH,
)
from_unit.set("seconds")
from_unit.pack(side="left")

convert_button = ttk.Button(
    convert_row,
    text="=",
    width=3,
    style="Accent.TButton",
    command=convert_time,
)
convert_button.pack(side="left", padx=12)

convert_right = tk.Frame(convert_row, bg=CARD)
convert_right.pack(side="left")

output_value = ttk.Entry(
    convert_right,
    width=ENTRY_WIDTH,
    state="readonly",
)
output_value.pack(side="left")

to_unit = ttk.Combobox(
    convert_right,
    values=list(UNITS.keys()),
    state="readonly",
    width=COMBO_WIDTH,
)
to_unit.set("minutes")
to_unit.pack(side="left")

compare_card = make_card(main)
compare_card.pack(fill="x")

make_heading(compare_card, "Compare Time Values").pack(pady=(10, 8))

compare_row = tk.Frame(compare_card, bg=CARD)
compare_row.pack(padx=12, pady=(0, 11))

compare_left = tk.Frame(compare_row, bg=CARD)
compare_left.pack(side="left")

compare_input_1 = ttk.Entry(compare_left, width=ENTRY_WIDTH)
compare_input_1.pack(side="left")

compare_unit_1 = ttk.Combobox(
    compare_left,
    values=list(UNITS.keys()),
    state="readonly",
    width=COMBO_WIDTH,
)
compare_unit_1.set("minutes")
compare_unit_1.pack(side="left")

compare_button = ttk.Button(
    compare_row,
    text="?",
    width=3,
    style="Accent.TButton",
    command=compare_time,
)
compare_button.pack(side="left", padx=12)

compare_right = tk.Frame(compare_row, bg=CARD)
compare_right.pack(side="left")

compare_input_2 = ttk.Entry(compare_right, width=ENTRY_WIDTH)
compare_input_2.pack(side="left")

compare_unit_2 = ttk.Combobox(
    compare_right,
    values=list(UNITS.keys()),
    state="readonly",
    width=COMBO_WIDTH,
)
compare_unit_2.set("hours")
compare_unit_2.pack(side="left")

question_mark = tk.Label(
    root,
    text="?",
    bg=CARD,
    fg=ACCENT,
    font=(FONT_FAMILY, 10, "bold"),
    width=2,
    height=1,
    cursor="question_arrow",
)
question_mark.place(relx=0, rely=1, anchor="sw", x=8, y=-5)
question_mark.bind("<Enter>", show_tooltip)
question_mark.bind("<Leave>", hide_tooltip)

root.update_idletasks()
root.geometry(f"{root.winfo_reqwidth()}x250")

root.mainloop()
