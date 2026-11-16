import ctypes
import math
import os
import re
import tkinter as tk
from tkinter import messagebox, ttk


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DLL_PATH = os.path.join(CURRENT_DIR, "calc.dll")


UNITS = {
    "Seconds": "S",
    "Minutes": "M",
    "Hours": "H",
    "Days": "D",
    "Weeks": "W",
    "Months": "O",
    "Years": "Y",
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

ENTRY_WIDTH = 14
COMBO_WIDTH = 10


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
        "Could not load calc.dll.\n\n"
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
        raise ValueError("Enter a valid number.")

    if not math.isfinite(value):
        raise ValueError("The value must be a finite number.")

    if value < 0:
        raise ValueError("Enter a non-negative number.")

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

        sign_label.configure(text={1: ">", 0: "=", -1: "<"}[result])

    except (ValueError, KeyError) as error:
        messagebox.showerror("Error", str(error))


tooltip_window = None


def show_tooltip(event):
    global tooltip_window

    if tooltip_window is not None:
        return

    x = event.widget.winfo_rootx()
    y = event.widget.winfo_rooty() - 55

    tooltip_window = tk.Toplevel(root)
    tooltip_window.wm_overrideredirect(True)
    tooltip_window.wm_geometry(f"+{x}+{y}")

    ttk.Label(
        tooltip_window,
        text="For calculations, a month is 30 days,\nand a year is 365 days.",
        padding=8,
        relief="solid",
    ).pack()


def hide_tooltip(_event=None):
    global tooltip_window

    if tooltip_window is not None:
        tooltip_window.destroy()
        tooltip_window = None


root = tk.Tk()
root.title("Time Converter")
root.resizable(False, False)

FONT_FAMILY = "Segoe UI"
root.option_add("*Font", (FONT_FAMILY, 10))

style = ttk.Style(root)
if "clam" in style.theme_names():
    style.theme_use("clam")

style.configure("TEntry", padding=3)
style.configure("TCombobox", padding=2)
style.configure("TButton", padding=(8, 4))

main = ttk.Frame(root, padding=16)
main.pack(fill="both", expand=True)


ttk.Label(
    main,
    text="Time Conversion",
    font=(FONT_FAMILY, 11, "bold"),
).grid(row=0, column=0, columnspan=3, pady=(0, 14))


convert_left = ttk.Frame(main)
convert_left.grid(row=1, column=0)

input_value = ttk.Entry(convert_left, width=ENTRY_WIDTH)
input_value.pack(side="left")

from_unit = ttk.Combobox(
    convert_left,
    values=list(UNITS.keys()),
    state="readonly",
    width=COMBO_WIDTH,
)
from_unit.set("Seconds")
from_unit.pack(side="left")


convert_button = ttk.Button(
    main,
    text="=",
    width=4,
    command=convert_time,
)
convert_button.grid(row=1, column=1, padx=16)


convert_right = ttk.Frame(main)
convert_right.grid(row=1, column=2)

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
to_unit.set("Minutes")
to_unit.pack(side="left")


ttk.Separator(main).grid(
    row=2,
    column=0,
    columnspan=3,
    sticky="ew",
    pady=18,
)


ttk.Label(
    main,
    text="Compare Time Intervals",
    font=(FONT_FAMILY, 11, "bold"),
).grid(row=3, column=0, columnspan=3, pady=(0, 12))


compare_left = ttk.Frame(main)
compare_left.grid(row=4, column=0)

compare_input_1 = ttk.Entry(compare_left, width=ENTRY_WIDTH)
compare_input_1.pack(side="left")

compare_unit_1 = ttk.Combobox(
    compare_left,
    values=list(UNITS.keys()),
    state="readonly",
    width=COMBO_WIDTH,
)
compare_unit_1.set("Minutes")
compare_unit_1.pack(side="left")


sign_label = ttk.Label(
    main,
    text="",
    width=4,
    anchor="center",
    font=(FONT_FAMILY, 14, "bold"),
)
sign_label.grid(row=4, column=1, padx=16)


compare_right = ttk.Frame(main)
compare_right.grid(row=4, column=2)

compare_input_2 = ttk.Entry(compare_right, width=ENTRY_WIDTH)
compare_input_2.pack(side="left")

compare_unit_2 = ttk.Combobox(
    compare_right,
    values=list(UNITS.keys()),
    state="readonly",
    width=COMBO_WIDTH,
)
compare_unit_2.set("Hours")
compare_unit_2.pack(side="left")


ttk.Button(
    main,
    text="Compare",
    command=compare_time,
).grid(row=5, column=0, columnspan=3, pady=14)


question_mark = ttk.Label(
    root,
    text="?",
    cursor="question_arrow",
    font=(FONT_FAMILY, 12, "bold"),
)
question_mark.place(relx=0, rely=1, anchor="sw", x=8, y=-6)
question_mark.bind("<Enter>", show_tooltip)
question_mark.bind("<Leave>", hide_tooltip)


root.mainloop()
