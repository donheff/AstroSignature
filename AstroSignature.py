#
# ***********************************************
#
# AstroSignature.py — Custom Text Signature Tool for Siril
# Author: Randy Holder
# Contact: randy.holder7@gmail.com
# Version: 1.3.0
#
# Copyright (C) 2026 Randy Holder
# SPDX-License-Identifier: GPL-3.0-or-later
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
#
# ***********************************************
#
# Description:
# Adds a two-line italic text signature to the currently loaded Siril image.
# Line 1: Your name + target name (editable each time)
# Line 2: Session details (editable each time)
# Features: 9-position grid selector, font dropdown, independent font size
# sliders for each line, opacity control, and vertical flip correction.
#
# VERTICAL FLIP CORRECTION CHECKBOX:
# Check ON  — for images that have been plate-solved in Siril (Siril flips
#             the image during plate solving). Also applies to smart scopes
#             such as Dwarf 3, Seestar, Vespera whose raw data is natively
#             vertically flipped. This is the correct setting for most users.
# Check OFF — for images whose pixel data is correctly oriented and has NOT
#             been flipped by Siril. If unsure, try ON first.
#
# IMPORTANT: The signature is permanently written into the image pixel data.
# Always save the signed image as a NEW file after applying to preserve
# your unsigned master image.
#
# Tested with Siril 1.4.2 on Windows. Requires sirilpy >= 0.6.37.
# Should work on any telescope/camera combination supported by Siril.
#
# Version History:
# 1.0.0 - Initial release — two-line text signature, flip correction
# 1.1.0 - Added 9-position grid selector (dropdown)
# 1.2.0 - Added font selection dropdown from available Windows fonts
# 1.3.0 - Added independent font size sliders for Line 1 and Line 2
#          QA verified across all 9 positions and both flip states
# 1.3.1 - Cross-platform font support — Windows, macOS, Linux
#
# ***********************************************

VERSION = "1.3.1"

import sys
import os

# ── Siril interface ───────────────────────────────────────────────────────────
try:
    import sirilpy as s
    if not s.check_module_version('>=0.6.37'):
        print("Error: requires sirilpy module >= 0.6.37 (Siril >= 1.4.0)")
        sys.exit(1)
    from sirilpy import SirilError
    s.ensure_installed("numpy", "Pillow")
except ImportError as e:
    print(f"ERROR: Could not import sirilpy: {e}")
    sys.exit(1)

import numpy as np
from PIL import Image, ImageDraw, ImageFont

# ── GUI dialog ────────────────────────────────────────────────────────────────
def get_user_input():
    try:
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.title("AstroSignature Tool v1.3.1")
        root.resizable(False, False)
        root.configure(bg="#2b2b2b")

        root.update_idletasks()
        w, h = 620, 680
        x = (root.winfo_screenwidth() // 2) - (w // 2)
        y = (root.winfo_screenheight() // 2) - (h // 2)
        root.geometry(f"{w}x{h}+{x}+{y}")

        tk.Label(root, text="AstroSignature Tool  v1.3.1",
                bg="#1a1a2e", fg="#c9a84c",
                font=("Arial", 13, "bold"), pady=10).pack(fill="x")

        tk.Label(root, text="Line 1 — Your name (fixed) + Target (edit each time):",
                bg="#2b2b2b", fg="#ffffff",
                font=("Arial", 9)).pack(anchor="w", padx=20, pady=(12, 0))
        name_var = tk.StringVar(value="Randy Holder  |  M63 - Sunflower Galaxy")
        name_entry = tk.Entry(root, textvariable=name_var, width=58,
                bg="#3c3f41", fg="#ffffff",
                font=("Arial", 10),
                relief="flat", bd=4)
        name_entry.pack(padx=20, pady=(2, 0))

        tk.Label(root, text="Line 2 — Session details (edit each time):",
                bg="#2b2b2b", fg="#ffffff",
                font=("Arial", 9)).pack(anchor="w", padx=20, pady=(10, 0))
        session_var = tk.StringVar(
            value="Dwarf 3  |  30s Exp  |  Gain 80  |  278 subs  |  Astro Filter"
        )
        session_entry = tk.Entry(root, textvariable=session_var, width=58,
                                 bg="#3c3f41", fg="#ffffff",
                                 font=("Arial", 10), relief="flat", bd=4)
        session_entry.pack(padx=20, pady=(2, 0))
        session_entry.focus()
        session_entry.select_range(0, "end")

        tk.Label(root, text="Opacity (%):",
                bg="#2b2b2b", fg="#ffffff",
                font=("Arial", 9)).pack(anchor="w", padx=20, pady=(10, 0))
        opacity_var = tk.IntVar(value=40)
        oframe = tk.Frame(root, bg="#2b2b2b")
        oframe.pack(fill="x", padx=20)
        tk.Scale(oframe, from_=10, to=80, orient="horizontal",
                variable=opacity_var, bg="#2b2b2b", fg="#ffffff",
                highlightthickness=0, troughcolor="#3c3f41",
                activebackground="#c9a84c", length=400).pack(side="left")
        tk.Label(oframe, textvariable=opacity_var,
                bg="#2b2b2b", fg="#c9a84c",
                font=("Arial", 10, "bold"), width=3).pack(side="left", padx=4)

        # Flip checkbox
        flipped_var = tk.BooleanVar(value=True)
        tk.Checkbutton(root,
                      text="Apply vertical flip correction\n"
                           "(ON for plate-solved images and smart scopes — Dwarf 3, Seestar, Vespera etc.)",
                      variable=flipped_var,
                      bg="#2b2b2b", fg="#ffffff", selectcolor="#3c3f41",
                      activebackground="#2b2b2b", activeforeground="#c9a84c",
                      font=("Arial", 9), justify="left").pack(anchor="w", padx=20, pady=(8, 0))

        # Position selector — dropdown
        tk.Label(root, text="Signature Position:",
                bg="#2b2b2b", fg="#ffffff",
                font=("Arial", 9)).pack(anchor="w", padx=20, pady=(12, 4))

        pos_var = tk.StringVar(value="Bottom Right")
        positions = [
            "Top Left", "Top Center", "Top Right",
            "Middle Left", "Center", "Middle Right",
            "Bottom Left", "Bottom Center", "Bottom Right"
        ]
        pos_dropdown = tk.OptionMenu(root, pos_var, *positions)
        pos_dropdown.config(bg="#3c3f41", fg="#ffffff", font=("Arial", 10),
                           activebackground="#4a6fa5", activeforeground="#ffffff",
                           highlightthickness=0, relief="flat", width=20)
        pos_dropdown["menu"].config(bg="#3c3f41", fg="#ffffff",
                                   activebackground="#4a6fa5", activeforeground="#ffffff",
                                   font=("Arial", 10))
        pos_dropdown.pack(anchor="w", padx=20, pady=(0, 4))

        # Font selector dropdown
        tk.Label(root, text="Font:",
                bg="#2b2b2b", fg="#ffffff",
                font=("Arial", 9)).pack(anchor="w", padx=20, pady=(10, 4))

        available_fonts = get_available_fonts()
        font_names = [f[0] for f in available_fonts]
        font_paths = {f[0]: f[1] for f in available_fonts}

        # Default to Georgia Italic if available, otherwise first available
        default_font = font_names[0]
        for name in font_names:
            if "Georgia" in name and "Bold" not in name:
                default_font = name
                break

        font_var = tk.StringVar(value=default_font)
        font_dropdown = tk.OptionMenu(root, font_var, *font_names)
        font_dropdown.config(bg="#3c3f41", fg="#ffffff", font=("Arial", 10),
                            activebackground="#4a6fa5", activeforeground="#ffffff",
                            highlightthickness=0, relief="flat", width=25)
        font_dropdown["menu"].config(bg="#3c3f41", fg="#ffffff",
                                    activebackground="#4a6fa5", activeforeground="#ffffff",
                                    font=("Arial", 10))
        font_dropdown.pack(anchor="w", padx=20, pady=(0, 4))

        # Font size controls — Line 1 and Line 2 independent
        tk.Label(root, text="Font Size — Line 1 (Name / Target):",
                bg="#2b2b2b", fg="#ffffff",
                font=("Arial", 9)).pack(anchor="w", padx=20, pady=(10, 0))
        size1_var = tk.IntVar(value=28)
        sf1 = tk.Frame(root, bg="#2b2b2b")
        sf1.pack(fill="x", padx=20)
        tk.Scale(sf1, from_=12, to=120, orient="horizontal",
                variable=size1_var, bg="#2b2b2b", fg="#ffffff",
                highlightthickness=0, troughcolor="#3c3f41",
                activebackground="#c9a84c", length=440).pack(side="left")
        tk.Label(sf1, textvariable=size1_var,
                bg="#2b2b2b", fg="#c9a84c",
                font=("Arial", 10, "bold"), width=3).pack(side="left", padx=4)

        tk.Label(root, text="Font Size — Line 2 (Session Details):",
                bg="#2b2b2b", fg="#ffffff",
                font=("Arial", 9)).pack(anchor="w", padx=20, pady=(8, 0))
        size2_var = tk.IntVar(value=22)
        sf2 = tk.Frame(root, bg="#2b2b2b")
        sf2.pack(fill="x", padx=20)
        tk.Scale(sf2, from_=12, to=120, orient="horizontal",
                variable=size2_var, bg="#2b2b2b", fg="#ffffff",
                highlightthickness=0, troughcolor="#3c3f41",
                activebackground="#c9a84c", length=440).pack(side="left")
        tk.Label(sf2, textvariable=size2_var,
                bg="#2b2b2b", fg="#c9a84c",
                font=("Arial", 10, "bold"), width=3).pack(side="left", padx=4)

        result = {"ok": False}

        # Save warning
        warn_frame = tk.Frame(root, bg="#3a1a00", bd=1, relief="solid")
        warn_frame.pack(fill="x", padx=20, pady=(12, 0))
        tk.Label(warn_frame,
                text="⚠  The signature is permanently baked into the image pixels.\n"
                     "After applying, save as a NEW file — do not overwrite your master.",
                bg="#3a1a00", fg="#ffcc66",
                font=("Arial", 9, "bold"), pady=6, justify="center").pack()

        def on_apply():
            if not session_var.get().strip():
                messagebox.showwarning("Missing", "Please enter session details.")
                return
            result.update({
                "ok": True,
                "name": name_var.get().strip(),
                "session": session_var.get().strip(),
                "opacity": opacity_var.get(),
                "flipped": flipped_var.get(),
                "position": pos_var.get(),
                "font_path": font_paths[font_var.get()],
                "size1": size1_var.get(),
                "size2": size2_var.get()
            })
            root.destroy()

        def on_cancel():
            root.destroy()

        bframe = tk.Frame(root, bg="#2b2b2b")
        bframe.pack(pady=14)
        tk.Button(bframe, text="  Apply Signature  ", command=on_apply,
                 bg="#4a6fa5", fg="white", font=("Arial", 10, "bold"),
                 relief="flat", padx=12, pady=6,
                 cursor="hand2").pack(side="left", padx=8)
        tk.Button(bframe, text="  Cancel  ", command=on_cancel,
                 bg="#555555", fg="white", font=("Arial", 10),
                 relief="flat", padx=12, pady=6,
                 cursor="hand2").pack(side="left", padx=8)

        root.mainloop()
        return result if result["ok"] else None

    except Exception as e:
        print(f"ERROR opening dialog: {e}")
        return None


def get_font_dirs():
    """Return a list of font directories for the current OS."""
    import platform
    system = platform.system()
    if system == "Windows":
        return ["C:/Windows/Fonts/"]
    elif system == "Darwin":  # macOS
        return [
            "/Library/Fonts/",
            "/System/Library/Fonts/",
            os.path.expanduser("~/Library/Fonts/"),
        ]
    else:  # Linux
        return [
            "/usr/share/fonts/",
            "/usr/local/share/fonts/",
            os.path.expanduser("~/.fonts/"),
            os.path.expanduser("~/.local/share/fonts/"),
        ]


def get_available_fonts():
    """Scan system font directories and return available (display_name, file_path) tuples."""
    import platform
    system = platform.system()

    # Curated font candidates per OS
    if system == "Windows":
        candidates = [
            ("Georgia Italic",              "georgiai.ttf"),
            ("Georgia Bold Italic",         "georgiaz.ttf"),
            ("Times New Roman Italic",      "timesi.ttf"),
            ("Times New Roman Bold Italic", "timesbi.ttf"),
            ("Palatino Italic",             "palatinoi.ttf"),
            ("Garamond Italic",             "garamondi.ttf"),
            ("Calibri Italic",              "calibrii.ttf"),
            ("Calibri Bold Italic",         "calibriz.ttf"),
            ("Cambria Italic",              "cambriai.ttf"),
            ("Cambria Bold Italic",         "cambriaz.ttf"),
            ("Arial Italic",                "ariali.ttf"),
            ("Arial Bold Italic",           "arialbi.ttf"),
            ("Verdana Italic",              "verdanai.ttf"),
            ("Verdana Bold Italic",         "verdanaz.ttf"),
            ("Trebuchet Italic",            "trebucit.ttf"),
            ("Book Antiqua Italic",         "bkanti.ttf"),
            ("Century Gothic Italic",       "gothici.ttf"),
            ("Comic Sans MS Italic",        "comicsi.ttf"),
            ("Segoe UI Italic",             "segoeuii.ttf"),
            ("Consolas Italic",             "consolasbi.ttf"),
        ]
    elif system == "Darwin":  # macOS
        candidates = [
            ("Georgia Italic",              "Georgia Italic.ttf"),
            ("Georgia Bold Italic",         "Georgia Bold Italic.ttf"),
            ("Times New Roman Italic",      "Times New Roman Italic.ttf"),
            ("Times New Roman Bold Italic", "Times New Roman Bold Italic.ttf"),
            ("Palatino Italic",             "Palatino.ttc"),
            ("Baskerville Italic",          "Baskerville.ttc"),
            ("Didot Italic",                "Didot.ttc"),
            ("Garamond Italic",             "EBGaramond-Italic.ttf"),
            ("Helvetica Italic",            "Helvetica.ttc"),
            ("Arial Italic",                "Arial Italic.ttf"),
            ("Arial Bold Italic",           "Arial Bold Italic.ttf"),
            ("Verdana Italic",              "Verdana Italic.ttf"),
            ("Verdana Bold Italic",         "Verdana Bold Italic.ttf"),
            ("Trebuchet Italic",            "Trebuchet MS Italic.ttf"),
            ("Futura Italic",               "Futura.ttc"),
            ("Optima Italic",               "Optima.ttc"),
            ("Comic Sans MS Italic",        "Comic Sans MS Italic.ttf"),
        ]
    else:  # Linux
        candidates = [
            ("DejaVu Serif Italic",         "DejaVuSerif-Italic.ttf"),
            ("DejaVu Serif Bold Italic",    "DejaVuSerif-BoldItalic.ttf"),
            ("DejaVu Sans Italic",          "DejaVuSans-Oblique.ttf"),
            ("DejaVu Sans Bold Italic",     "DejaVuSans-BoldOblique.ttf"),
            ("Liberation Serif Italic",     "LiberationSerif-Italic.ttf"),
            ("Liberation Serif Bold Italic","LiberationSerif-BoldItalic.ttf"),
            ("Liberation Sans Italic",      "LiberationSans-Italic.ttf"),
            ("Liberation Sans Bold Italic", "LiberationSans-BoldItalic.ttf"),
            ("FreeSerif Italic",            "FreeSerif.ttf"),
            ("FreeSans Italic",             "FreeSans.ttf"),
            ("Ubuntu Italic",               "Ubuntu-RI.ttf"),
            ("Ubuntu Bold Italic",          "Ubuntu-BI.ttf"),
            ("Noto Serif Italic",           "NotoSerif-Italic.ttf"),
            ("Noto Sans Italic",            "NotoSans-Italic.ttf"),
        ]

    font_dirs = get_font_dirs()
    available = []

    for name, filename in candidates:
        for font_dir in font_dirs:
            # Search recursively for Linux which has subdirectories
            if system == "Linux":
                for root_dir, dirs, files in os.walk(font_dir):
                    if filename in files:
                        available.append((name, os.path.join(root_dir, filename)))
                        break
            else:
                path = os.path.join(font_dir, filename)
                if os.path.exists(path):
                    available.append((name, path))
                    break

    # Fallback — use Pillow's default if nothing found
    if not available:
        available.append(("Default Font", "default"))
        print("WARNING: No system fonts found — using Pillow default font.")

    return available


def find_font(size, font_path=None):
    """Load a font by path, with cross-platform fallback chain."""
    # Try the requested font first
    if font_path and font_path != "default" and os.path.exists(font_path):
        try:
            return ImageFont.truetype(font_path, size)
        except Exception:
            pass

    # Cross-platform fallback chain
    import platform
    system = platform.system()

    if system == "Windows":
        fallbacks = [
            "C:/Windows/Fonts/georgiai.ttf",
            "C:/Windows/Fonts/timesi.ttf",
            "C:/Windows/Fonts/calibrii.ttf",
            "C:/Windows/Fonts/ariali.ttf",
            "C:/Windows/Fonts/verdanai.ttf",
            "C:/Windows/Fonts/arial.ttf",
        ]
    elif system == "Darwin":
        fallbacks = [
            "/Library/Fonts/Arial Italic.ttf",
            "/Library/Fonts/Verdana Italic.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "/Library/Fonts/Arial.ttf",
        ]
    else:  # Linux
        fallbacks = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSerif.ttf",
        ]

    for path in fallbacks:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue

    # Final fallback — Pillow default (no path needed)
    print(f"WARNING: No fonts found — using Pillow default (no size control).")
    return ImageFont.load_default()


def apply_signature(siril, line1, line2, opacity_pct, flipped=True, position="Bottom Right", font_path=None, size1=28, size2=22):
    print(f"Applying signature — opacity {opacity_pct}% — position: {position} — font: {os.path.basename(font_path) if font_path else 'default'} — sizes: {size1}/{size2}")

    try:
        with siril.image_lock():
            fit = siril.get_image(True)
            if fit is None:
                print("ERROR: No image loaded in Siril.")
                return False
            img_array = np.array(fit.data, dtype=np.float32)
            print(f"Image shape from Siril: {img_array.shape}")

            # Normalise to [0, 1]
            if img_array.max() > 1.0:
                img_array = img_array / 65535.0

            # Ensure HWC RGB — Siril returns CHW (3, H, W)
            if img_array.ndim == 3 and img_array.shape[0] == 3:
                img_hwc = np.transpose(img_array, (1, 2, 0))
            elif img_array.ndim == 2:
                img_hwc = np.stack([img_array] * 3, axis=-1)
            else:
                img_hwc = img_array

            height, width = img_hwc.shape[:2]
            img_uint8 = (np.clip(img_hwc, 0, 1) * 255).astype(np.uint8)
            pil_img = Image.fromarray(img_uint8, mode="RGB").convert("RGBA")

            # Font loading — use selected font and user-specified sizes
            font1 = find_font(size1, font_path)
            font2 = find_font(size2, font_path)

            # Measure text
            dummy_draw = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
            bb1 = dummy_draw.textbbox((0, 0), line1, font=font1)
            bb2 = dummy_draw.textbbox((0, 0), line2, font=font2)
            tw1, th1 = bb1[2] - bb1[0], bb1[3] - bb1[1]
            tw2, th2 = bb2[2] - bb2[0], bb2[3] - bb2[1]
            gap = max(6, int(height * 0.005))

            # Use user's flip selection from dialog
            print(f"Flip correction: {flipped}")

            # Calculate position from dropdown selector (case-insensitive)
            # When flipped=True: Siril has vertically flipped the data, so
            #   "bottom" on screen = "top" in data array — we invert vertical axis
            # When flipped=False: data and display match — use position directly
            pos = position.lower()
            mx = int(width  * 0.025)
            my = int(height * 0.025)
            block_h = th1 + gap + th2

            # Horizontal alignment
            if "left" in pos:
                if flipped:
                    x1 = mx
                    x2 = mx
                else:
                    x1 = width - mx - tw1
                    x2 = width - mx - tw2
            elif "right" in pos:
                if flipped:
                    x1 = width - mx - tw1
                    x2 = width - mx - tw2
                else:
                    x1 = mx
                    x2 = mx
            else:  # center
                x1 = (width - tw1) // 2
                x2 = (width - tw2) // 2

            # Vertical alignment
            # For both flipped and non-flipped: calculate position as if normal
            # When flipped=True, the overlay flip below will mirror the position
            # so "bottom" coordinates end up displaying at bottom of screen correctly
            if "top" in pos:
                y1 = my
                y2 = y1 + th1 + gap
            elif "bottom" in pos:
                y1 = height - my - block_h
                y2 = y1 + th1 + gap
            else:  # middle / center
                y1 = (height - block_h) // 2
                y2 = y1 + th1 + gap

            # Draw text on a separate overlay
            overlay = Image.new("RGBA", pil_img.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)
            alpha = int(255 * opacity_pct / 100.0)
            shadow_alpha = max(20, int(alpha * 0.35))

            draw.text((x1 + 1, y1 + 1), line1, font=font1, fill=(0, 0, 0, shadow_alpha))
            draw.text((x2 + 1, y2 + 1), line2, font=font2, fill=(0, 0, 0, shadow_alpha))
            draw.text((x1, y1), line1, font=font1, fill=(255, 255, 255, alpha))
            draw.text((x2, y2), line2, font=font2, fill=(255, 255, 255, alpha))

            # For plate-solve flipped images, flip overlay vertically to correct text orientation
            # For non-flipped images, flip overlay horizontally to correct text orientation
            if flipped:
                print("Image is plate-solve flipped — correcting text orientation.")
                overlay = overlay.transpose(Image.FLIP_TOP_BOTTOM)
            else:
                overlay = overlay.transpose(Image.FLIP_LEFT_RIGHT)

            # Composite text overlay onto original unmodified image
            composited = Image.alpha_composite(pil_img, overlay).convert("RGB")
            result_hwc = np.array(composited, dtype=np.float32) / 255.0
            result_chw = np.transpose(result_hwc, (2, 0, 1))  # back to CHW

            # Write back to Siril using correct API
            fit.data[:] = result_chw
            siril.set_image_pixeldata(fit.data)

            print("Signature applied successfully.")
            print(f"  Line 1 : {line1}")
            print(f"  Line 2 : {line2}")
            return True

    except Exception as e:
        print(f"ERROR applying signature: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("=" * 55)
    print("  AstroSignature Tool v1.3.1 — Randy Holder")
    print("  Two-line text signature for Siril 1.4+")
    print("=" * 55)

    params = get_user_input()
    if params is None:
        print("Cancelled.")
        return

    siril = s.SirilInterface()
    try:
        siril.connect()
        print("Connected to Siril.")
        success = apply_signature(siril, params["name"],
                                  params["session"], params["opacity"],
                                  params["flipped"], params["position"],
                                  params["font_path"], params["size1"],
                                  params["size2"])
        if success:
            print("")
            print("Done! Save as a new file to preserve your unsigned master.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        siril.disconnect()


if __name__ == "__main__":
    main()
