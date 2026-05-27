"""
OLED Piksel Dönüştürücü & Düzenleyici
Sıfırdan yeniden yazılmış, temiz mimari ve modern UX ile.
Gereksinimler: pip install pillow numpy customtkinter
"""

import tkinter as tk
from tkinter import filedialog, messagebox, colorchooser
import customtkinter as ctk
from PIL import Image, ImageTk, ImageEnhance, ImageFilter
import numpy as np
import copy

# ─── Tema ────────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ─── Renkler ─────────────────────────────────────────────────────────────────
BG_DARK    = "#0d0d0d"
BG_PANEL   = "#161616"
BG_CARD    = "#1e1e1e"
BG_CANVAS  = "#111111"
ACCENT     = "#00ff88"
ACCENT2    = "#0088ff"
TEXT_PRI   = "#f0f0f0"
TEXT_SEC   = "#888888"
BORDER     = "#2a2a2a"
WHITE_PIX  = "#f5f5f5"
BLACK_PIX  = "#0a0a0a"

# ─── Sabitler ────────────────────────────────────────────────────────────────
MAX_PIX_DIM      = 256   # Piksel matrisinin maksimum boyutu
EDITOR_SIZE      = 512   # Düzenleyici canvas boyutu (px)
PREVIEW_SIZE     = 200   # Gerçek boyut önizleme (px)
HISTORY_LIMIT    = 30    # Geri alma geçmişi derinliği

FILTER_MAP = {
    "Nearest (Piksel)": Image.Resampling.NEAREST,
    "Bilinear":         Image.Resampling.BILINEAR,
    "Bicubic":          Image.Resampling.BICUBIC,
    "Lanczos (Keskin)": Image.Resampling.LANCZOS,
}

DITHER_MAP = {
    "Floyd-Steinberg":  Image.Dither.FLOYDSTEINBERG,
    "Yok (Eşik)":       None,
    "Ordered":          Image.Dither.ORDERED,
}


# ═════════════════════════════════════════════════════════════════════════════
class PixelEditor(ctk.CTk):
    """OLED için optimize edilmiş piksel dönüştürücü ve düzenleyici."""

    def __init__(self):
        super().__init__()
        self.title("OLED Pixel Studio")
        self.geometry("1500x860")
        self.minsize(1200, 700)
        self.configure(fg_color=BG_DARK)

        # ── Durum değişkenleri ──────────────────────────────────────────────
        self.original_img: Image.Image | None = None
        self.processed_img: Image.Image | None = None
        self.pixel_matrix: list[list[tuple]] = []   # (r,g,b) matris
        self.history: list[list[list[tuple]]] = []  # Geri alma yığıtı
        self.redo_stack: list[list[list[tuple]]] = []

        # Kırpma
        self._crop_active   = False
        self._crop_start    = None
        self._crop_rect_id  = None
        self._displayed_img_on_canvas: Image.Image | None = None  # canvas'taki ölçekli resim

        # Çizim araçları
        self._tool          = tk.StringVar(value="pencil")
        self._draw_color    = (0, 0, 0)      # Siyah
        self._erase_color   = (255, 255, 255) # Beyaz
        self._rect_start    = None
        self._tmp_shape     = None
        self._selection     = None           # (x0,y0,x1,y1) piksel koordinatları
        self._last_drag_pos = None

        # Ayar değişkenleri
        self.v_brightness  = tk.DoubleVar(value=1.0)
        self.v_contrast    = tk.DoubleVar(value=1.0)
        self.v_sharpness   = tk.DoubleVar(value=1.0)
        self.v_saturation  = tk.DoubleVar(value=1.0)
        self.v_threshold   = tk.IntVar(value=128)
        self.v_width       = tk.IntVar(value=128)
        self.v_height      = tk.IntVar(value=64)
        self.v_proportional = tk.BooleanVar(value=True)
        self.v_dither      = tk.StringVar(value="Floyd-Steinberg")
        self.v_filter      = tk.StringVar(value="Nearest (Piksel)")
        self.v_invert      = tk.BooleanVar(value=False)
        self.v_grid        = tk.BooleanVar(value=True)
        self.v_zoom        = tk.DoubleVar(value=1.0)  # Zoom çarpanı

        self._build_ui()
        self._reset_matrix(128, 64)

    # ═══════════════════════════════════════════════════════════════════════
    # UI İNŞASI
    # ═══════════════════════════════════════════════════════════════════════

    def _build_ui(self):
        self.columnconfigure(0, weight=0)  # Sol panel sabit
        self.columnconfigure(1, weight=1)  # Orta: önizleme
        self.columnconfigure(2, weight=2)  # Sağ: düzenleyici
        self.rowconfigure(0, weight=1)

        self._build_left_panel()
        self._build_middle_panel()
        self._build_right_panel()

        # Klavye kısayolları
        self.bind("<Control-z>", lambda e: self._undo())
        self.bind("<Control-y>", lambda e: self._redo())
        self.bind("<Control-s>", lambda e: self._save_output())
        self.bind("<Control-o>", lambda e: self._load_image())

    # ── Sol Panel ─────────────────────────────────────────────────────────

    def _build_left_panel(self):
        panel = ctk.CTkScrollableFrame(
            self, width=270, fg_color=BG_PANEL,
            corner_radius=0, border_width=0
        )
        panel.grid(row=0, column=0, sticky="nsew", padx=(8,0), pady=8)
        panel.columnconfigure(0, weight=1)

        # ── Başlık ──
        hdr = ctk.CTkFrame(panel, fg_color="transparent")
        hdr.pack(fill="x", pady=(8,16))
        ctk.CTkLabel(hdr, text="OLED", font=("Courier New", 22, "bold"),
                     text_color=ACCENT).pack(side="left")
        ctk.CTkLabel(hdr, text=" PIXEL STUDIO", font=("Courier New", 14),
                     text_color=TEXT_SEC).pack(side="left", padx=(2,0))

        # ── Dosya işlemleri ──
        self._section(panel, "DOSYA")
        ctk.CTkButton(panel, text="📂  Resim Yükle", command=self._load_image,
                      fg_color=ACCENT2, hover_color="#0066cc",
                      font=("Consolas", 12, "bold")).pack(fill="x", pady=(0,4))
        ctk.CTkButton(panel, text="✂️  Kırpma Modu", command=self._activate_crop,
                      fg_color=BG_CARD, hover_color=BORDER).pack(fill="x", pady=2)
        ctk.CTkButton(panel, text="🔄  Sıfırla", command=self._full_reset,
                      fg_color=BG_CARD, hover_color="#330000").pack(fill="x", pady=2)

        # ── Çıkış Boyutu ──
        self._section(panel, "ÇIKIŞ BOYUTU")
        row_dim = ctk.CTkFrame(panel, fg_color="transparent")
        row_dim.pack(fill="x", pady=4)

        ctk.CTkLabel(row_dim, text="G:", font=("Consolas",11), text_color=TEXT_SEC,
                     width=16).pack(side="left")
        self._entry_w = ctk.CTkEntry(row_dim, textvariable=self.v_width, width=70,
                                      font=("Consolas",12))
        self._entry_w.pack(side="left", padx=4)
        ctk.CTkLabel(row_dim, text="Y:", font=("Consolas",11), text_color=TEXT_SEC,
                     width=16).pack(side="left")
        self._entry_h = ctk.CTkEntry(row_dim, textvariable=self.v_height, width=70,
                                      font=("Consolas",12))
        self._entry_h.pack(side="left", padx=4)

        ctk.CTkCheckBox(panel, text="Oransal", variable=self.v_proportional,
                        font=("Consolas",11), text_color=TEXT_SEC).pack(anchor="w", pady=2)

        # Önceden ayarlanmış boyutlar
        presets_frame = ctk.CTkFrame(panel, fg_color="transparent")
        presets_frame.pack(fill="x", pady=4)
        ctk.CTkLabel(presets_frame, text="Hazır:", font=("Consolas",10),
                     text_color=TEXT_SEC).pack(side="left")
        for lbl, w, h in [("128×64", 128, 64), ("128×32", 128, 32), ("64×48", 64, 48), ("32×32", 32, 32)]:
            ctk.CTkButton(presets_frame, text=lbl, width=58, height=24,
                          font=("Consolas", 9),
                          command=lambda ww=w, hh=h: self._apply_preset(ww, hh),
                          fg_color=BG_CARD, hover_color=BORDER).pack(side="left", padx=2)

        ctk.CTkButton(panel, text="▶  Uygula", command=self._process_image,
                      fg_color=ACCENT, hover_color="#00cc66",
                      text_color="#000000",
                      font=("Consolas", 12, "bold")).pack(fill="x", pady=(8,4))

        # ── Görüntü Ayarları ──
        self._section(panel, "GÖRÜNTÜ AYARLARI")

        sliders = [
            ("Parlaklık",  self.v_brightness, 0.1, 3.0, 0.05),
            ("Kontrast",   self.v_contrast,   0.1, 3.0, 0.05),
            ("Keskinlik",  self.v_sharpness,  0.0, 3.0, 0.05),
            ("Doygunluk",  self.v_saturation, 0.0, 3.0, 0.05),
            ("Eşik (B/W)", self.v_threshold,  0,   255, 1),
        ]
        for name, var, lo, hi, res in sliders:
            self._labeled_slider(panel, name, var, lo, hi, res)

        # ── Dönüşüm Seçenekleri ──
        self._section(panel, "DÖNÜŞÜM")

        ctk.CTkLabel(panel, text="Dithering:", font=("Consolas",11),
                     text_color=TEXT_SEC).pack(anchor="w")
        ctk.CTkOptionMenu(panel, variable=self.v_dither,
                          values=list(DITHER_MAP.keys()),
                          font=("Consolas",11)).pack(fill="x", pady=2)

        ctk.CTkLabel(panel, text="Yeniden Boyutlandırma Filtresi:", font=("Consolas",11),
                     text_color=TEXT_SEC).pack(anchor="w", pady=(6,0))
        ctk.CTkOptionMenu(panel, variable=self.v_filter,
                          values=list(FILTER_MAP.keys()),
                          font=("Consolas",11)).pack(fill="x", pady=2)

        ctk.CTkCheckBox(panel, text="Renkleri Ters Çevir (OLED: Beyaz=OFF)",
                        variable=self.v_invert, font=("Consolas",11),
                        text_color=TEXT_SEC).pack(anchor="w", pady=4)

        # ── Kaydet ──
        self._section(panel, "ÇIKTI")
        ctk.CTkButton(panel, text="💾  PNG Olarak İndir",
                      command=self._save_output,
                      fg_color=ACCENT2, hover_color="#0066cc",
                      font=("Consolas", 12, "bold")).pack(fill="x", pady=2)
        ctk.CTkButton(panel, text="📋  C Array Kopyala",
                      command=self._copy_c_array,
                      fg_color=BG_CARD, hover_color=BORDER,
                      font=("Consolas", 11)).pack(fill="x", pady=2)

    # ── Orta Panel ────────────────────────────────────────────────────────

    def _build_middle_panel(self):
        panel = ctk.CTkFrame(self, fg_color=BG_PANEL, corner_radius=8)
        panel.grid(row=0, column=1, sticky="nsew", padx=8, pady=8)
        panel.rowconfigure(1, weight=1)
        panel.rowconfigure(3, weight=1)
        panel.columnconfigure(0, weight=1)

        # Kaynak Resim
        ctk.CTkLabel(panel, text="KAYNAK RESİM", font=("Consolas",11,"bold"),
                     text_color=ACCENT).grid(row=0, column=0, padx=10, pady=(10,4), sticky="w")
        self.canvas_source = tk.Canvas(panel, bg=BG_CANVAS, highlightthickness=1,
                                        highlightbackground=BORDER, cursor="crosshair")
        self.canvas_source.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0,8))
        self.canvas_source.bind("<Configure>", self._on_source_resize)

        # Gerçek Boyut Önizleme
        ctk.CTkLabel(panel, text="GERÇEK BOYUT ÇIKTI", font=("Consolas",11,"bold"),
                     text_color=ACCENT).grid(row=2, column=0, padx=10, pady=(8,4), sticky="w")

        preview_wrap = ctk.CTkFrame(panel, fg_color=BG_CARD, corner_radius=6)
        preview_wrap.grid(row=3, column=0, sticky="nsew", padx=8, pady=(0,8))
        preview_wrap.rowconfigure(0, weight=1)
        preview_wrap.columnconfigure(0, weight=1)

        self.canvas_preview = tk.Canvas(preview_wrap, bg=BG_CANVAS, highlightthickness=0)
        self.canvas_preview.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)

        # Bilgi etiketi
        self.lbl_info = ctk.CTkLabel(panel, text="—", font=("Consolas",10),
                                      text_color=TEXT_SEC)
        self.lbl_info.grid(row=4, column=0, padx=10, pady=(0,8), sticky="w")

    # ── Sağ Panel ─────────────────────────────────────────────────────────

    def _build_right_panel(self):
        panel = ctk.CTkFrame(self, fg_color=BG_PANEL, corner_radius=8)
        panel.grid(row=0, column=2, sticky="nsew", padx=(0,8), pady=8)
        panel.rowconfigure(1, weight=1)
        panel.columnconfigure(0, weight=1)
        panel.columnconfigure(1, weight=0)

        # Başlık + araçlar satırı
        top_bar = ctk.CTkFrame(panel, fg_color="transparent")
        top_bar.grid(row=0, column=0, columnspan=2, sticky="ew", padx=8, pady=(10,4))

        self.lbl_editor = ctk.CTkLabel(top_bar, text="PİKSEL DÜZENLEYİCİ",
                                        font=("Consolas",12,"bold"), text_color=ACCENT)
        self.lbl_editor.pack(side="left")

        self.lbl_dim = ctk.CTkLabel(top_bar, text="0×0 | 1×",
                                     font=("Consolas",10), text_color=TEXT_SEC)
        self.lbl_dim.pack(side="left", padx=10)

        # Geri/İleri
        btn_undo = ctk.CTkButton(top_bar, text="↩", width=36, height=28,
                                  command=self._undo, fg_color=BG_CARD,
                                  hover_color=BORDER, font=("Consolas",14))
        btn_undo.pack(side="right", padx=2)
        btn_redo = ctk.CTkButton(top_bar, text="↪", width=36, height=28,
                                  command=self._redo, fg_color=BG_CARD,
                                  hover_color=BORDER, font=("Consolas",14))
        btn_redo.pack(side="right", padx=2)

        ctk.CTkCheckBox(top_bar, text="Izgara", variable=self.v_grid,
                         command=self._redraw_editor, font=("Consolas",11),
                         text_color=TEXT_SEC).pack(side="right", padx=8)

        # Zoom kontrolleri
        zoom_frame = ctk.CTkFrame(top_bar, fg_color="transparent")
        zoom_frame.pack(side="right", padx=4)
        ctk.CTkButton(zoom_frame, text="−", width=28, height=28,
                       command=lambda: self._zoom(-1), fg_color=BG_CARD,
                       font=("Consolas",14)).pack(side="left")
        self.lbl_zoom = ctk.CTkLabel(zoom_frame, text="1×", font=("Consolas",11),
                                      text_color=TEXT_SEC, width=36)
        self.lbl_zoom.pack(side="left")
        ctk.CTkButton(zoom_frame, text="+", width=28, height=28,
                       command=lambda: self._zoom(+1), fg_color=BG_CARD,
                       font=("Consolas",14)).pack(side="left")

        # Düzenleyici Canvas
        canvas_frame = ctk.CTkFrame(panel, fg_color=BG_CANVAS, corner_radius=4)
        canvas_frame.grid(row=1, column=0, sticky="nsew", padx=(8,4), pady=(0,8))
        canvas_frame.rowconfigure(0, weight=1)
        canvas_frame.columnconfigure(0, weight=1)

        self.canvas_editor = tk.Canvas(canvas_frame, bg=BG_CANVAS,
                                        highlightthickness=0, cursor="pencil")
        self.canvas_editor.grid(row=0, column=0, sticky="nsew")

        # Kaydırma çubukları
        sb_y = tk.Scrollbar(canvas_frame, orient="vertical",
                             command=self.canvas_editor.yview)
        sb_y.grid(row=0, column=1, sticky="ns")
        sb_x = tk.Scrollbar(canvas_frame, orient="horizontal",
                             command=self.canvas_editor.xview)
        sb_x.grid(row=1, column=0, sticky="ew")
        self.canvas_editor.configure(xscrollcommand=sb_x.set, yscrollcommand=sb_y.set)

        self.canvas_editor.bind("<ButtonPress-1>",   self._ed_press)
        self.canvas_editor.bind("<B1-Motion>",       self._ed_drag)
        self.canvas_editor.bind("<ButtonRelease-1>", self._ed_release)
        self.canvas_editor.bind("<Motion>",          self._ed_hover)

        # Araç Paneli (sağ taraf)
        self._build_tool_panel(panel)

    def _build_tool_panel(self, parent):
        tools_frame = ctk.CTkScrollableFrame(parent, width=120, fg_color=BG_CARD,
                                              corner_radius=6)
        tools_frame.grid(row=1, column=1, sticky="nsew", padx=(0,8), pady=(0,8))
        tools_frame.columnconfigure(0, weight=1)

        ctk.CTkLabel(tools_frame, text="ARAÇLAR", font=("Consolas",10,"bold"),
                     text_color=ACCENT).pack(pady=(8,4))

        tools = [
            ("✏️ Kalem",       "pencil"),
            ("🧹 Silgi",       "eraser"),
            ("🪣 Doldur",      "fill"),
            ("⬛ Kare Doldur", "rect_fill"),
            ("⬜ Kare Çerçeve","rect_outline"),
            ("➖ Çizgi",       "line"),
            ("🔲 Alan Seç",    "select"),
        ]
        for lbl, val in tools:
            ctk.CTkRadioButton(tools_frame, text=lbl, variable=self._tool,
                               value=val, font=("Consolas",11),
                               command=self._on_tool_change).pack(
                anchor="w", padx=4, pady=2)

        ctk.CTkLabel(tools_frame, text="RENK", font=("Consolas",10,"bold"),
                     text_color=ACCENT).pack(pady=(12,4))

        self.btn_draw_color = ctk.CTkButton(
            tools_frame, text="■ Çiz", width=100,
            fg_color=self._rgb_hex(self._draw_color),
            hover_color="#333",
            command=self._pick_draw_color,
            font=("Consolas",11))
        self.btn_draw_color.pack(pady=2)

        self.btn_erase_color = ctk.CTkButton(
            tools_frame, text="□ Sil", width=100,
            fg_color=self._rgb_hex(self._erase_color),
            hover_color="#aaa",
            text_color="#000",
            command=self._pick_erase_color,
            font=("Consolas",11))
        self.btn_erase_color.pack(pady=2)

        # Hızlı renk swap
        ctk.CTkButton(tools_frame, text="⇄ Değiştir", width=100,
                       command=self._swap_colors,
                       fg_color=BG_PANEL, hover_color=BORDER,
                       font=("Consolas",10)).pack(pady=2)

        # Seçim işlemleri
        ctk.CTkLabel(tools_frame, text="SEÇİM", font=("Consolas",10,"bold"),
                     text_color=ACCENT).pack(pady=(12,4))
        ctk.CTkButton(tools_frame, text="Tümünü Doldur", width=100,
                       command=self._fill_all,
                       fg_color=BG_PANEL, font=("Consolas",10)).pack(pady=2)
        ctk.CTkButton(tools_frame, text="Seçimi Doldur", width=100,
                       command=self._fill_selection,
                       fg_color=BG_PANEL, font=("Consolas",10)).pack(pady=2)
        ctk.CTkButton(tools_frame, text="Seçimi Sil", width=100,
                       command=self._clear_selection,
                       fg_color=BG_PANEL, font=("Consolas",10)).pack(pady=2)
        ctk.CTkButton(tools_frame, text="Seçimi Temizle", width=100,
                       command=self._deselect,
                       fg_color=BG_PANEL, font=("Consolas",10)).pack(pady=2)

        # Dönüşümler
        ctk.CTkLabel(tools_frame, text="DÖNÜŞÜM", font=("Consolas",10,"bold"),
                     text_color=ACCENT).pack(pady=(12,4))
        for lbl, fn in [
            ("↔ Yatay Çevir",  self._flip_h),
            ("↕ Dikey Çevir",  self._flip_v),
            ("↻ 90° Döndür",  self._rotate_90),
            ("⬛ Tersine Çevir", self._invert_canvas),
        ]:
            ctk.CTkButton(tools_frame, text=lbl, width=100,
                           command=fn, fg_color=BG_PANEL,
                           font=("Consolas",10)).pack(pady=2)

        # Koordinat göstergesi
        self.lbl_cursor = ctk.CTkLabel(tools_frame, text="x:— y:—",
                                        font=("Consolas",10), text_color=TEXT_SEC)
        self.lbl_cursor.pack(pady=(16,4))

    # ═══════════════════════════════════════════════════════════════════════
    # UI YARDIMCI METODLARI
    # ═══════════════════════════════════════════════════════════════════════

    def _section(self, parent, text):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(fill="x", pady=(10,2))
        ctk.CTkLabel(f, text=text, font=("Consolas",10,"bold"),
                     text_color=ACCENT).pack(side="left")
        ctk.CTkFrame(f, height=1, fg_color=BORDER).pack(
            side="left", fill="x", expand=True, padx=(6,0), pady=0)

    def _labeled_slider(self, parent, name, var, lo, hi, res):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=1)
        ctk.CTkLabel(row, text=name, font=("Consolas",10),
                     text_color=TEXT_SEC, width=90, anchor="w").pack(side="left")
        val_lbl = ctk.CTkLabel(row, text=f"{var.get():.2f}" if isinstance(var.get(), float) else str(var.get()),
                                font=("Consolas",10), text_color=TEXT_PRI, width=40)
        val_lbl.pack(side="right")
        sl = ctk.CTkSlider(parent, variable=var, from_=lo, to=hi, number_of_steps=int((hi-lo)/res))
        sl.pack(fill="x", pady=(0,4))

        def _update_label(*_):
            v = var.get()
            val_lbl.configure(text=f"{v:.2f}" if isinstance(v, float) else str(v))
        var.trace_add("write", _update_label)
        sl.bind("<ButtonRelease-1>", lambda e: self._process_image() if self.original_img else None)

    # ═══════════════════════════════════════════════════════════════════════
    # DOSYA İŞLEMLERİ
    # ═══════════════════════════════════════════════════════════════════════

    def _load_image(self):
        path = filedialog.askopenfilename(
            filetypes=[("Resim", "*.png *.jpg *.jpeg *.bmp *.gif *.webp *.tiff")])
        if not path:
            return
        try:
            img = Image.open(path).convert("RGB")
            self.original_img = img
            # Orijinal boyutları öneriyi doldur ama MAX'ı aşma
            w = min(img.width, MAX_PIX_DIM)
            h = min(img.height, MAX_PIX_DIM)
            # En-boy oranını koru
            if img.width / img.height > 1:
                h = max(1, int(w * img.height / img.width))
            else:
                w = max(1, int(h * img.width / img.height))
            self.v_width.set(w)
            self.v_height.set(h)
            self._process_image()
        except Exception as e:
            messagebox.showerror("Hata", f"Resim yüklenemedi:\n{e}")

    def _save_output(self):
        if not self.pixel_matrix:
            messagebox.showwarning("Uyarı", "Kaydedilecek çıktı yok.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("BMP", "*.bmp")])
        if not path:
            return
        try:
            img = self._matrix_to_image()
            img.save(path)
            messagebox.showinfo("Kaydedildi", f"Kaydedildi: {path}")
        except Exception as e:
            messagebox.showerror("Hata", str(e))

    def _copy_c_array(self):
        """Piksel matrisini Arduino/ESP32 uyumlu C dizisi olarak panoya kopyalar."""
        if not self.pixel_matrix:
            messagebox.showwarning("Uyarı", "Önce bir resim dönüştürün.")
            return
        h = len(self.pixel_matrix)
        w = len(self.pixel_matrix[0])

        # Piksel matrisini bitmap'e dönüştür (1 bit / piksel, satır başına byte hizalı)
        lines = [f"// {w}x{h} OLED bitmap",
                 f"static const uint8_t PROGMEM img_bitmap[] = {{"]
        for row in self.pixel_matrix:
            byte_vals = []
            byte = 0
            bit_pos = 7
            for r, g, b in row:
                pixel = 0 if (r + g + b) < 384 else 1  # Siyah=0, Beyaz=1
                byte |= (pixel << bit_pos)
                bit_pos -= 1
                if bit_pos < 0:
                    byte_vals.append(f"0x{byte:02X}")
                    byte = 0
                    bit_pos = 7
            if bit_pos < 7:  # Kalan bitler
                byte_vals.append(f"0x{byte:02X}")
            lines.append("  " + ", ".join(byte_vals) + ",")
        lines.append("};")

        result = "\n".join(lines)
        self.clipboard_clear()
        self.clipboard_append(result)
        messagebox.showinfo("Kopyalandı", f"C dizisi panoya kopyalandı!\n{w}×{h} = {w*h} piksel")

    # ═══════════════════════════════════════════════════════════════════════
    # GÖRÜNTÜ İŞLEME
    # ═══════════════════════════════════════════════════════════════════════

    def _process_image(self, *_):
        if not self.original_img:
            return

        w = max(1, min(self.v_width.get(),  MAX_PIX_DIM))
        h = max(1, min(self.v_height.get(), MAX_PIX_DIM))

        filt = FILTER_MAP.get(self.v_filter.get(), Image.Resampling.NEAREST)

        # Gelişmeleri uygula
        img = self.original_img.copy()
        img = ImageEnhance.Brightness(img).enhance(self.v_brightness.get())
        img = ImageEnhance.Contrast(img).enhance(self.v_contrast.get())
        img = ImageEnhance.Sharpness(img).enhance(self.v_sharpness.get())
        img = ImageEnhance.Color(img).enhance(self.v_saturation.get())

        # Yeniden boyutlandır
        img = img.resize((w, h), filt)
        self.processed_img = img.copy()

        # Siyah-beyaza dönüştür
        gray = img.convert("L")

        dither_key = self.v_dither.get()
        dither_mode = DITHER_MAP.get(dither_key)
        thresh = self.v_threshold.get()

        if dither_mode is not None:
            bw = gray.convert("1", dither=dither_mode)
        else:
            # Manuel eşik
            bw = gray.point(lambda p: 255 if p >= thresh else 0).convert("1")

        if self.v_invert.get():
            bw = bw.point(lambda p: 255 - p)

        # Matrise yükle
        arr = np.array(bw)
        self.pixel_matrix = [
            [(0,0,0) if arr[y,x] == 0 else (255,255,255)
             for x in range(w)]
            for y in range(h)
        ]
        self.history.clear()
        self.redo_stack.clear()
        self._selection = None

        self._update_source_canvas()
        self._redraw_editor()
        self._redraw_preview()
        self._update_info()

    def _update_source_canvas(self):
        """Kaynak resim önizlemesini güncelle."""
        cw = self.canvas_source.winfo_width()
        ch = self.canvas_source.winfo_height()
        if cw < 2 or ch < 2:
            self.after(150, self._update_source_canvas)
            return
        self.canvas_source.delete("all")
        if not self.processed_img:
            return
        img = self.processed_img.copy()
        img.thumbnail((cw, ch), Image.LANCZOS)
        self._source_tk = ImageTk.PhotoImage(img)
        self._displayed_img_on_canvas = img
        x = (cw - img.width) // 2
        y = (ch - img.height) // 2
        self.canvas_source.create_image(x, y, anchor="nw", image=self._source_tk)

    def _on_source_resize(self, e):
        if self.processed_img:
            self.after(100, self._update_source_canvas)

    # ═══════════════════════════════════════════════════════════════════════
    # PİKSEL TUVAL
    # ═══════════════════════════════════════════════════════════════════════

    def _get_cell_size(self):
        """Piksel başına tuvaldeki piksel boyutu."""
        if not self.pixel_matrix or not self.pixel_matrix[0]:
            return 4
        w = len(self.pixel_matrix[0])
        h = len(self.pixel_matrix)
        cw = max(self.canvas_editor.winfo_width(), EDITOR_SIZE)
        ch = max(self.canvas_editor.winfo_height(), EDITOR_SIZE)
        base = min(cw / w, ch / h)
        zoom = [0.5, 1, 2, 3, 4, 6, 8, 12, 16]
        idx = int(self.v_zoom.get())
        idx = max(0, min(idx, len(zoom)-1))
        return max(1, base * zoom[idx])

    def _zoom(self, delta):
        z = int(self.v_zoom.get()) + delta
        z = max(0, min(z, 8))
        self.v_zoom.set(z)
        levels = [0.5, 1, 2, 3, 4, 6, 8, 12, 16]
        self.lbl_zoom.configure(text=f"{levels[z]}×")
        self._redraw_editor()

    def _redraw_editor(self, *_):
        self.canvas_editor.delete("all")
        if not self.pixel_matrix or not self.pixel_matrix[0]:
            return

        h = len(self.pixel_matrix)
        w = len(self.pixel_matrix[0])
        cs = self._get_cell_size()

        total_w = int(w * cs)
        total_h = int(h * cs)
        self.canvas_editor.configure(scrollregion=(0, 0, total_w, total_h))

        draw_grid = self.v_grid.get() and cs >= 4

        for row in range(h):
            for col in range(w):
                r, g, b = self.pixel_matrix[row][col]
                color = "#000000" if (r+g+b) < 384 else "#ffffff"
                x0 = col * cs
                y0 = row * cs
                x1 = x0 + cs
                y1 = y0 + cs
                outline = "#1a1a1a" if draw_grid else color
                self.canvas_editor.create_rectangle(
                    x0, y0, x1, y1,
                    fill=color, outline=outline,
                    width=1 if draw_grid else 0,
                    tags=f"p{col}_{row}")

        # Seçim kutusunu çiz
        if self._selection:
            self._draw_selection_rect()

        # Boyut etiketini güncelle
        self.lbl_dim.configure(text=f"{w}×{h} | {cs:.1f}×")

    def _draw_selection_rect(self):
        if not self._selection:
            return
        x0, y0, x1, y1 = self._selection
        cs = self._get_cell_size()
        self.canvas_editor.delete("sel_rect")
        self.canvas_editor.create_rectangle(
            x0*cs, y0*cs, (x1+1)*cs, (y1+1)*cs,
            outline=ACCENT, width=2, dash=(4,3), tags="sel_rect")

    def _redraw_preview(self):
        self.canvas_preview.delete("all")
        if not self.pixel_matrix or not self.pixel_matrix[0]:
            return
        img = self._matrix_to_image()
        # Canvas boyutuna sığdır
        pw = self.canvas_preview.winfo_width() or PREVIEW_SIZE
        ph = self.canvas_preview.winfo_height() or PREVIEW_SIZE
        # Gerçek boyut göster ama çok küçükse büyüt
        dw, dh = img.width, img.height
        scale = min(pw/dw, ph/dh, 1.0)  # Max: 1× (büyütme yok)
        if dw * dh <= 64*128:  # Küçük resimler için 2× büyüt
            scale = min(pw/dw, ph/dh, 2.0)
        dw2 = max(1, int(dw * scale))
        dh2 = max(1, int(dh * scale))
        disp = img.resize((dw2, dh2), Image.NEAREST)
        self._preview_tk = ImageTk.PhotoImage(disp)
        x = (pw - dw2) // 2
        y = (ph - dh2) // 2
        self.canvas_preview.create_image(x, y, anchor="nw", image=self._preview_tk)

    def _update_info(self):
        if not self.pixel_matrix or not self.pixel_matrix[0]:
            self.lbl_info.configure(text="—")
            return
        w = len(self.pixel_matrix[0])
        h = len(self.pixel_matrix)
        black = sum(1 for row in self.pixel_matrix for p in row if p == (0,0,0))
        white = w * h - black
        self.lbl_info.configure(
            text=f"{w}×{h}px  |  ⬛{black}  ⬜{white}  |  Ctrl+Z: geri al  Ctrl+S: kaydet")

    # ═══════════════════════════════════════════════════════════════════════
    # TUVAL ARAÇ OLAYLARI
    # ═══════════════════════════════════════════════════════════════════════

    def _canvas_to_pixel(self, event) -> tuple[int, int] | tuple[None, None]:
        """Canvas koordinatını piksel matris indeksine çevirir."""
        if not self.pixel_matrix or not self.pixel_matrix[0]:
            return None, None
        cs = self._get_cell_size()
        # Scrolled canvas için gerçek koordinatlar
        x = self.canvas_editor.canvasx(event.x)
        y = self.canvas_editor.canvasy(event.y)
        col = int(x / cs)
        row = int(y / cs)
        W = len(self.pixel_matrix[0])
        H = len(self.pixel_matrix)
        if 0 <= col < W and 0 <= row < H:
            return col, row
        return None, None

    def _push_history(self):
        self.history.append(copy.deepcopy(self.pixel_matrix))
        if len(self.history) > HISTORY_LIMIT:
            self.history.pop(0)
        self.redo_stack.clear()

    def _ed_press(self, event):
        col, row = self._canvas_to_pixel(event)
        if col is None:
            return
        tool = self._tool.get()
        self._rect_start = (col, row)
        self._push_history()

        if tool == "pencil":
            self._set_pixel(col, row, self._draw_color)
        elif tool == "eraser":
            self._set_pixel(col, row, self._erase_color)
        elif tool == "fill":
            target = self.pixel_matrix[row][col]
            self._flood_fill(col, row, target, self._draw_color)
            self._redraw_editor()
            self._redraw_preview()
        elif tool in ("rect_fill", "rect_outline", "line", "select"):
            pass  # Sürükleme ile tamamlanır

    def _ed_drag(self, event):
        col, row = self._canvas_to_pixel(event)
        if col is None:
            return
        tool = self._tool.get()

        if tool == "pencil":
            if self._last_drag_pos:
                self._draw_line_bresenham(*self._last_drag_pos, col, row, self._draw_color)
            else:
                self._set_pixel(col, row, self._draw_color)
        elif tool == "eraser":
            if self._last_drag_pos:
                self._draw_line_bresenham(*self._last_drag_pos, col, row, self._erase_color)
            else:
                self._set_pixel(col, row, self._erase_color)
        elif tool in ("rect_fill", "rect_outline", "line", "select") and self._rect_start:
            # Geçici önizleme
            self.canvas_editor.delete("tmp_shape")
            x0, y0 = self._rect_start
            cs = self._get_cell_size()
            if tool == "line":
                self.canvas_editor.create_line(
                    x0*cs+cs/2, y0*cs+cs/2, col*cs+cs/2, row*cs+cs/2,
                    fill=self._rgb_hex(self._draw_color), width=max(1, cs/4), tags="tmp_shape")
            elif tool == "select":
                self.canvas_editor.create_rectangle(
                    min(x0,col)*cs, min(y0,row)*cs,
                    (max(x0,col)+1)*cs, (max(y0,row)+1)*cs,
                    outline=ACCENT, width=2, dash=(4,3), tags="tmp_shape")
            else:
                self.canvas_editor.create_rectangle(
                    min(x0,col)*cs, min(y0,row)*cs,
                    (max(x0,col)+1)*cs, (max(y0,row)+1)*cs,
                    fill=self._rgb_hex(self._draw_color) if tool=="rect_fill" else "",
                    outline=self._rgb_hex(self._draw_color), width=2, tags="tmp_shape")

        self._last_drag_pos = (col, row)

    def _ed_release(self, event):
        col, row = self._canvas_to_pixel(event)
        self._last_drag_pos = None
        tool = self._tool.get()
        if col is None or not self._rect_start:
            return

        x0, y0 = self._rect_start

        if tool == "rect_fill":
            self._draw_rect_on_matrix(x0, y0, col, row, self._draw_color, fill=True)
            self._redraw_editor()
            self._redraw_preview()
        elif tool == "rect_outline":
            self._draw_rect_on_matrix(x0, y0, col, row, self._draw_color, fill=False)
            self._redraw_editor()
            self._redraw_preview()
        elif tool == "line":
            self._draw_line_bresenham(x0, y0, col, row, self._draw_color)
            self._redraw_editor()
            self._redraw_preview()
        elif tool == "select":
            self._selection = (min(x0,col), min(y0,row), max(x0,col), max(y0,row))
            self.canvas_editor.delete("tmp_shape")
            self._redraw_editor()

        self._update_info()
        self._rect_start = None

    def _ed_hover(self, event):
        col, row = self._canvas_to_pixel(event)
        if col is None:
            self.lbl_cursor.configure(text="x:— y:—")
        else:
            r, g, b = self.pixel_matrix[row][col]
            color_txt = "⬛" if (r+g+b) < 384 else "⬜"
            self.lbl_cursor.configure(text=f"x:{col} y:{row} {color_txt}")

    def _on_tool_change(self):
        cursors = {
            "pencil": "pencil", "eraser": "circle",
            "fill": "spraycan", "select": "crosshair",
            "rect_fill": "crosshair", "rect_outline": "crosshair",
            "line": "crosshair",
        }
        self.canvas_editor.configure(cursor=cursors.get(self._tool.get(), "crosshair"))

    # ═══════════════════════════════════════════════════════════════════════
    # ÇIZIM ALGORİTMALARI
    # ═══════════════════════════════════════════════════════════════════════

    def _set_pixel(self, col, row, color):
        if 0 <= row < len(self.pixel_matrix) and 0 <= col < len(self.pixel_matrix[0]):
            self.pixel_matrix[row][col] = color
            cs = self._get_cell_size()
            draw_grid = self.v_grid.get() and cs >= 4
            hex_c = self._rgb_hex(color)
            outline = "#1a1a1a" if draw_grid else hex_c
            self.canvas_editor.itemconfigure(f"p{col}_{row}",
                                              fill=hex_c, outline=outline)
            # Önizlemeyi de güncelle
            self._redraw_preview()

    def _draw_line_bresenham(self, x0, y0, x1, y1, color):
        """Bresenham çizgi algoritması."""
        dx = abs(x1 - x0); dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            self._set_pixel(x0, y0, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy; x0 += sx
            if e2 < dx:
                err += dx; y0 += sy

    def _flood_fill(self, sx, sy, target, replacement):
        if target == replacement:
            return
        W = len(self.pixel_matrix[0])
        H = len(self.pixel_matrix)
        stack = [(sx, sy)]
        visited = set()
        while stack:
            x, y = stack.pop()
            if (x, y) in visited or not (0 <= x < W and 0 <= y < H):
                continue
            if self.pixel_matrix[y][x] != target:
                continue
            visited.add((x, y))
            self.pixel_matrix[y][x] = replacement
            stack += [(x+1,y),(x-1,y),(x,y+1),(x,y-1)]

    def _draw_rect_on_matrix(self, x0, y0, x1, y1, color, fill=True):
        xl, xr = min(x0,x1), max(x0,x1)
        yt, yb = min(y0,y1), max(y0,y1)
        W = len(self.pixel_matrix[0])
        H = len(self.pixel_matrix)
        for y in range(max(0,yt), min(H, yb+1)):
            for x in range(max(0,xl), min(W, xr+1)):
                if fill or x==xl or x==xr or y==yt or y==yb:
                    self.pixel_matrix[y][x] = color

    # ═══════════════════════════════════════════════════════════════════════
    # SEÇİM & DÖNÜŞÜMLER
    # ═══════════════════════════════════════════════════════════════════════

    def _fill_all(self):
        self._push_history()
        for y in range(len(self.pixel_matrix)):
            for x in range(len(self.pixel_matrix[0])):
                self.pixel_matrix[y][x] = self._draw_color
        self._redraw_editor(); self._redraw_preview(); self._update_info()

    def _fill_selection(self):
        if not self._selection:
            messagebox.showwarning("Uyarı", "Önce Alan Seç aracıyla seçim yapın.")
            return
        self._push_history()
        x0, y0, x1, y1 = self._selection
        self._draw_rect_on_matrix(x0, y0, x1, y1, self._draw_color, fill=True)
        self._redraw_editor(); self._redraw_preview(); self._update_info()

    def _clear_selection(self):
        if not self._selection:
            messagebox.showwarning("Uyarı", "Önce Alan Seç aracıyla seçim yapın.")
            return
        self._push_history()
        x0, y0, x1, y1 = self._selection
        self._draw_rect_on_matrix(x0, y0, x1, y1, self._erase_color, fill=True)
        self._redraw_editor(); self._redraw_preview(); self._update_info()

    def _deselect(self):
        self._selection = None
        self.canvas_editor.delete("sel_rect")

    def _flip_h(self):
        self._push_history()
        self.pixel_matrix = [row[::-1] for row in self.pixel_matrix]
        self._redraw_editor(); self._redraw_preview()

    def _flip_v(self):
        self._push_history()
        self.pixel_matrix = self.pixel_matrix[::-1]
        self._redraw_editor(); self._redraw_preview()

    def _rotate_90(self):
        self._push_history()
        h = len(self.pixel_matrix)
        w = len(self.pixel_matrix[0])
        # 90° saat yönünde
        new_mat = [[(0,0,0)]*h for _ in range(w)]
        for y in range(h):
            for x in range(w):
                new_mat[x][h-1-y] = self.pixel_matrix[y][x]
        self.pixel_matrix = new_mat
        self._redraw_editor(); self._redraw_preview(); self._update_info()

    def _invert_canvas(self):
        self._push_history()
        for y in range(len(self.pixel_matrix)):
            for x in range(len(self.pixel_matrix[0])):
                r, g, b = self.pixel_matrix[y][x]
                self.pixel_matrix[y][x] = (255-r, 255-g, 255-b)
        self._redraw_editor(); self._redraw_preview()

    # ═══════════════════════════════════════════════════════════════════════
    # GERİ ALMA / İLERİ ALMA
    # ═══════════════════════════════════════════════════════════════════════

    def _undo(self):
        if not self.history:
            return
        self.redo_stack.append(copy.deepcopy(self.pixel_matrix))
        self.pixel_matrix = self.history.pop()
        self._redraw_editor(); self._redraw_preview(); self._update_info()

    def _redo(self):
        if not self.redo_stack:
            return
        self.history.append(copy.deepcopy(self.pixel_matrix))
        self.pixel_matrix = self.redo_stack.pop()
        self._redraw_editor(); self._redraw_preview(); self._update_info()

    # ═══════════════════════════════════════════════════════════════════════
    # KIRPMA
    # ═══════════════════════════════════════════════════════════════════════

    def _activate_crop(self):
        if not self.original_img:
            messagebox.showwarning("Uyarı", "Önce bir resim yükleyin.")
            return
        self._crop_active = True
        self._crop_start = None
        self.canvas_source.configure(cursor="crosshair")
        self.canvas_source.bind("<ButtonPress-1>",   self._crop_press)
        self.canvas_source.bind("<B1-Motion>",       self._crop_drag)
        self.canvas_source.bind("<ButtonRelease-1>", self._crop_release)

    def _crop_press(self, event):
        self._crop_start = (event.x, event.y)
        if self._crop_rect_id:
            self.canvas_source.delete(self._crop_rect_id)

    def _crop_drag(self, event):
        if not self._crop_start:
            return
        if self._crop_rect_id:
            self.canvas_source.delete(self._crop_rect_id)
        x0, y0 = self._crop_start
        self._crop_rect_id = self.canvas_source.create_rectangle(
            x0, y0, event.x, event.y,
            outline="#ff4444", width=2, dash=(5,3))

    def _crop_release(self, event):
        if not self._crop_start or not self._displayed_img_on_canvas:
            return
        x0, y0 = self._crop_start
        x1, y1 = event.x, event.y

        # Canvas üzerindeki resmin pozisyonunu bul
        items = self.canvas_source.find_all()
        if not items:
            return
        ix, iy = self.canvas_source.coords(items[0])[:2]
        disp_w = self._displayed_img_on_canvas.width
        disp_h = self._displayed_img_on_canvas.height

        # Ölçek faktörü (görüntülenen → orijinal)
        ox, oy = self.original_img.size
        sx = ox / disp_w
        sy = oy / disp_h

        # Canvas → orijinal koordinatlar
        lf = max(0, int((min(x0,x1) - ix) * sx))
        tp = max(0, int((min(y0,y1) - iy) * sy))
        rt = min(ox, int((max(x0,x1) - ix) * sx))
        bt = min(oy, int((max(y0,y1) - iy) * sy))

        if rt - lf < 5 or bt - tp < 5:
            messagebox.showwarning("Uyarı", "Kırpma alanı çok küçük.")
        else:
            self.original_img = self.original_img.crop((lf, tp, rt, bt))
            self.v_width.set(min(rt-lf, MAX_PIX_DIM))
            self.v_height.set(min(bt-tp, MAX_PIX_DIM))
            self._process_image()

        self._crop_end()

    def _crop_end(self):
        self._crop_active = False
        self._crop_start = None
        if self._crop_rect_id:
            self.canvas_source.delete(self._crop_rect_id)
            self._crop_rect_id = None
        self.canvas_source.configure(cursor="crosshair")
        self.canvas_source.unbind("<ButtonPress-1>")
        self.canvas_source.unbind("<B1-Motion>")
        self.canvas_source.unbind("<ButtonRelease-1>")

    # ═══════════════════════════════════════════════════════════════════════
    # RENK SEÇİMİ
    # ═══════════════════════════════════════════════════════════════════════

    def _pick_draw_color(self):
        result = colorchooser.askcolor(color=self._rgb_hex(self._draw_color),
                                        title="Çizim Rengi")
        if result[0]:
            self._draw_color = tuple(int(c) for c in result[0])
            self.btn_draw_color.configure(fg_color=self._rgb_hex(self._draw_color))

    def _pick_erase_color(self):
        result = colorchooser.askcolor(color=self._rgb_hex(self._erase_color),
                                        title="Silgi Rengi")
        if result[0]:
            self._erase_color = tuple(int(c) for c in result[0])
            self.btn_erase_color.configure(fg_color=self._rgb_hex(self._erase_color))

    def _swap_colors(self):
        self._draw_color, self._erase_color = self._erase_color, self._draw_color
        self.btn_draw_color.configure(fg_color=self._rgb_hex(self._draw_color))
        self.btn_erase_color.configure(fg_color=self._rgb_hex(self._erase_color))

    # ═══════════════════════════════════════════════════════════════════════
    # YARDIMCI METODLAR
    # ═══════════════════════════════════════════════════════════════════════

    def _reset_matrix(self, w, h):
        self.pixel_matrix = [[(255,255,255)]*w for _ in range(h)]
        self.history.clear()
        self.redo_stack.clear()
        self._selection = None
        self._redraw_editor()
        self._redraw_preview()
        self._update_info()

    def _apply_preset(self, w, h):
        self.v_width.set(w)
        self.v_height.set(h)
        if self.original_img:
            self._process_image()
        else:
            self._reset_matrix(w, h)

    def _full_reset(self):
        if not messagebox.askyesno("Sıfırla", "Her şey sıfırlanacak. Emin misiniz?"):
            return
        self.original_img = None
        self.processed_img = None
        self.v_brightness.set(1.0); self.v_contrast.set(1.0)
        self.v_sharpness.set(1.0);  self.v_saturation.set(1.0)
        self.v_threshold.set(128)
        self.v_dither.set("Floyd-Steinberg")
        self.v_filter.set("Nearest (Piksel)")
        self.v_invert.set(False)
        self.canvas_source.delete("all")
        self._reset_matrix(128, 64)
        self.lbl_info.configure(text="—")

    def _matrix_to_image(self) -> Image.Image:
        if not self.pixel_matrix or not self.pixel_matrix[0]:
            return Image.new("RGB", (1, 1), (255,255,255))
        h = len(self.pixel_matrix)
        w = len(self.pixel_matrix[0])
        arr = np.zeros((h, w, 3), dtype=np.uint8)
        for y in range(h):
            for x in range(w):
                arr[y, x] = self.pixel_matrix[y][x]
        return Image.fromarray(arr, "RGB")

    @staticmethod
    def _rgb_hex(rgb) -> str:
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"


# ─── Giriş Noktası ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = PixelEditor()
    app.mainloop()