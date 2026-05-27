import tkinter as tk
from tkinter import ttk, messagebox, Toplevel, filedialog
import math, re, json
from PIL import Image, ImageTk

# ═══════════════════════════════════════════════════
#  TEMA
# ═══════════════════════════════════════════════════
C = {
    "bg":          "#12121a",
    "bg2":         "#1a1a24",
    "bg3":         "#22222e",
    "bg4":         "#2a2a38",
    "border":      "#333344",
    "border2":     "#44445a",
    "accent":      "#5b9cf6",
    "accent2":     "#3a6fd8",
    "accent3":     "#1e3d7a",
    "text":        "#e2e2ee",
    "text2":       "#8888aa",
    "text3":       "#555570",
    "success":     "#4ec994",
    "warning":     "#f0a03f",
    "danger":      "#e05555",
    "px_black":    "#0a0a10",
    "px_white":    "#f4f4fc",
    "grid_line":   "#2a2a38",
    "sel_color":   "#e05555",
    "preview_col": "#5b9cf6",
    "canvas_bg":   "#0e0e18",
    "scrollbar":   "#333344",
    "scrollthumb": "#555570",
}

TOOL_NAMES = {
    "pencil":            "✏  Kalem",
    "eraser":            "◻  Silgi",
    "fill":              "▓  Doldur",
    "line":              "╱  Çizgi",
    "rect_outline":      "□  Çerçeve",
    "rect_fill":         "■  Dolu Çerçeve",
    "ellipse_outline":   "○  Elips",
    "cut_selection":     "⊡  Seç/Kes",
    "paste":             "⎘  Yapıştır",
}

# ═══════════════════════════════════════════════════
#  YARDIMCI: Kaydırılabilir Çerçeve
# ═══════════════════════════════════════════════════
class ScrollFrame(tk.Frame):
    """İçeriğini kaydırılabilir yapan çerçeve."""
    def __init__(self, parent, **kw):
        super().__init__(parent, bg=C["bg2"])
        vscroll = tk.Scrollbar(self, orient="vertical", width=8,
                               bg=C["bg3"], troughcolor=C["bg2"],
                               activebackground=C["border2"],
                               highlightthickness=0, bd=0)
        vscroll.pack(side="right", fill="y")
        self.canvas_scroll = tk.Canvas(self, bg=C["bg2"],
                                       highlightthickness=0,
                                       yscrollcommand=vscroll.set)
        self.canvas_scroll.pack(side="left", fill="both", expand=True)
        vscroll.config(command=self.canvas_scroll.yview)
        self.inner = tk.Frame(self.canvas_scroll, bg=C["bg2"])
        self._win_id = self.canvas_scroll.create_window(
            (0, 0), window=self.inner, anchor="nw")
        self.inner.bind("<Configure>", self._on_inner_configure)
        self.canvas_scroll.bind("<Configure>", self._on_canvas_configure)
        self.canvas_scroll.bind("<MouseWheel>", self._on_mw)
        self.canvas_scroll.bind("<Button-4>",   self._on_mw)
        self.canvas_scroll.bind("<Button-5>",   self._on_mw)
        self.inner.bind("<MouseWheel>", self._on_mw)
        self.inner.bind("<Button-4>",   self._on_mw)
        self.inner.bind("<Button-5>",   self._on_mw)

    def _on_inner_configure(self, e):
        self.canvas_scroll.configure(
            scrollregion=self.canvas_scroll.bbox("all"))

    def _on_canvas_configure(self, e):
        self.canvas_scroll.itemconfig(self._win_id, width=e.width)

    def _on_mw(self, e):
        if e.num == 4 or (hasattr(e, "delta") and e.delta > 0):
            self.canvas_scroll.yview_scroll(-1, "units")
        else:
            self.canvas_scroll.yview_scroll(1, "units")

    def bind_children_scroll(self, widget=None):
        """Tüm alt widget'lara kaydırma bağla."""
        w = widget or self.inner
        w.bind("<MouseWheel>", self._on_mw)
        w.bind("<Button-4>",   self._on_mw)
        w.bind("<Button-5>",   self._on_mw)
        for child in w.winfo_children():
            self.bind_children_scroll(child)


# ═══════════════════════════════════════════════════
#  YARDIMCI: Koyu Tema ttk stilleri
# ═══════════════════════════════════════════════════
def apply_dark_style(root):
    style = ttk.Style(root)
    style.theme_use("default")
    bg = C["bg"]; bg2 = C["bg2"]; bg3 = C["bg3"]; bg4 = C["bg4"]
    bd = C["border"]; bd2 = C["border2"]
    tx = C["text"]; tx2 = C["text2"]; ac = C["accent"]

    style.configure(".", background=bg, foreground=tx,
                    font=("Segoe UI", 9), borderwidth=0)
    style.configure("TFrame",     background=bg)
    style.configure("TLabel",     background=bg,  foreground=tx)
    style.configure("TLabelframe",
        background=bg2, foreground=tx,
        relief="flat", bordercolor=bd,
        lightcolor=bd, darkcolor=bd)
    style.configure("TLabelframe.Label",
        background=bg2, foreground=ac,
        font=("Segoe UI", 8, "bold"))

    style.configure("TButton",
        background=bg4, foreground=tx,
        relief="flat", borderwidth=1,
        padding=(6, 3),
        font=("Segoe UI", 9))
    style.map("TButton",
        background=[("active", ac), ("pressed", C["accent2"])],
        foreground=[("active", "#ffffff")])

    style.configure("Accent.TButton",
        background=ac, foreground="#fff",
        relief="flat", borderwidth=0,
        padding=(8, 4),
        font=("Segoe UI", 9, "bold"))
    style.map("Accent.TButton",
        background=[("active", C["accent2"]), ("pressed", C["accent2"])])

    style.configure("Danger.TButton",
        background=C["danger"], foreground="#fff",
        relief="flat", borderwidth=0, padding=(6, 3))
    style.map("Danger.TButton",
        background=[("active", "#b83333"), ("pressed", "#a02828")])

    style.configure("Tool.TRadiobutton",
        background=bg2, foreground=tx2,
        focusthickness=0, font=("Segoe UI", 9))
    style.map("Tool.TRadiobutton",
        background=[("selected", bg4), ("active", bg3)],
        foreground=[("selected", ac), ("active", tx)])

    style.configure("TCheckbutton",
        background=bg2, foreground=tx2, focusthickness=0)
    style.map("TCheckbutton",
        background=[("active", bg2)],
        foreground=[("selected", tx), ("active", tx)])

    style.configure("TEntry",
        fieldbackground=bg4, foreground=tx,
        insertcolor=tx, bordercolor=bd,
        lightcolor=bd, darkcolor=bd,
        relief="flat", padding=(4, 3))
    style.map("TEntry", bordercolor=[("focus", ac)])

    style.configure("TCombobox",
        fieldbackground=bg4, foreground=tx,
        background=bg4, arrowcolor=tx2,
        bordercolor=bd, relief="flat", padding=(4, 3))
    style.map("TCombobox",
        fieldbackground=[("readonly", bg4)],
        foreground=[("readonly", tx)],
        bordercolor=[("focus", ac)])
    root.option_add("*TCombobox*Listbox.background", bg4)
    root.option_add("*TCombobox*Listbox.foreground", tx)
    root.option_add("*TCombobox*Listbox.selectBackground", ac)

    style.configure("TScrollbar",
        background=bg3, troughcolor=bg2,
        arrowcolor=tx2, bordercolor=bg, relief="flat")
    style.map("TScrollbar", background=[("active", bd2)])

    style.configure("Separator.TFrame", background=bd)
    style.configure("TNotebook",
        background=bg2, bordercolor=bd, tabmargins=[0,0,0,0])
    style.configure("TNotebook.Tab",
        background=bg3, foreground=tx2,
        padding=[8, 4], font=("Segoe UI", 8))
    style.map("TNotebook.Tab",
        background=[("selected", bg4), ("active", bg4)],
        foreground=[("selected", ac), ("active", tx)])


# ═══════════════════════════════════════════════════
#  ANA UYGULAMA
# ═══════════════════════════════════════════════════
class PixelEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Pixel Bitmap Editörü v2")
        self.root.geometry("1480x920")
        self.root.configure(bg=C["bg"])
        self.root.minsize(1100, 700)
        apply_dark_style(root)

        # ── Durum değişkenleri ──────────────────
        self.base_w = 16
        self.base_h = 16
        self.base_grid = [[0]*self.base_w for _ in range(self.base_h)]
        self.display_grid = [[0]*self.base_w for _ in range(self.base_h)]
        self.disp_w = self.base_w
        self.disp_h = self.base_h

        # Görünüm
        self.zoom = 1.0
        self.base_canvas_size = 512
        self.cell_w = self.base_canvas_size / self.base_w
        self.cell_h = self.base_canvas_size / self.base_h
        self.show_grid_var = tk.BooleanVar(value=True)
        self.show_coords_var = tk.BooleanVar(value=True)

        # Araç
        self.tool_var = tk.StringVar(value="pencil")
        self.draw_color = 1   # 1=siyah, 0=beyaz
        self.tool_state = {}
        self.last_drag_cell = None

        # Tarihçe
        self.history = []
        self.hist_idx = -1

        # Pano
        self.clipboard = None
        self.clip_w = 0
        self.clip_h = 0

        # Depo
        self.stored = []

        # Hex panel kilidi
        self._hex_lock = False

        # Bitmap seçenekleri
        self.reading_order_var = tk.StringVar(value="Sayfa Bazlı (Yatay) - Sütun MSB İlk")
        self.flip_h_var = tk.BooleanVar(value=False)
        self.flip_v_var = tk.BooleanVar(value=False)
        self.invert_var = tk.BooleanVar(value=False)
        self.rotation_var = tk.StringVar(value="Yok")
        self.oled_bg_var = tk.StringVar(value="Siyah")
        self.hex_fmt_var = tk.StringVar(value="C Array")

        self.reading_modes = {
            "Yatay (Satır) - MSB":           {"major_axis":"horizontal",       "bit_order":"msb_first","page_oriented":False},
            "Yatay (Satır) - LSB":           {"major_axis":"horizontal",       "bit_order":"lsb_first","page_oriented":False},
            "Dikey (Sütun) - MSB":           {"major_axis":"vertical",         "bit_order":"msb_first","page_oriented":False},
            "Dikey (Sütun) - LSB":           {"major_axis":"vertical",         "bit_order":"lsb_first","page_oriented":False},
            "Sayfa Bazlı (Yatay) - Sütun MSB İlk": {"major_axis":"horizontal_pages","bit_order":"msb_first","page_oriented":True},
            "Sayfa Bazlı (Yatay) - Sütun LSB İlk": {"major_axis":"horizontal_pages","bit_order":"lsb_first","page_oriented":True},
            "Sayfa Bazlı (Dikey) - Satır MSB İlk":  {"major_axis":"vertical_pages",  "bit_order":"msb_first","page_oriented":True},
            "Sayfa Bazlı (Dikey) - Satır LSB İlk":  {"major_axis":"vertical_pages",  "bit_order":"lsb_first","page_oriented":True},
        }
        self.data_formats = {
            "C Array":               {"parse": self._parse_c,    "gen": self._gen_c_array},
            "Arduino (PROGMEM)":     {"parse": self._parse_c,    "gen": self._gen_arduino},
            "Plain Hex":             {"parse": self._parse_plain,"gen": self._gen_plain},
            "Python List (int)":     {"parse": self._parse_pyint,"gen": self._gen_pyint},
            "Python List (hex str)": {"parse": self._parse_pyhex,"gen": self._gen_pyhex},
        }
        self.rotation_map = {
            "Yok":"0", "90° Saat Yönü":"90_cw",
            "180°":"180", "90° Saat Yönü Tersi":"90_ccw"
        }

        self._build_ui()
        self._record_history()
        self._redraw_canvas()
        self._bind_shortcuts()

    # ══════════════════════════════════════════
    #  UI İNŞASI
    # ══════════════════════════════════════════
    def _build_ui(self):
        # ── Menü çubuğu ─────────────────────
        self._build_menubar()

        # ── Ana düzen: sol | orta | sağ ──────
        main = tk.Frame(self.root, bg=C["bg"])
        main.pack(fill="both", expand=True, padx=6, pady=(0,6))

        # Sol panel (kaydırılabilir)
        left_outer = tk.Frame(main, bg=C["bg"], width=230)
        left_outer.pack(side="left", fill="y", padx=(0,6))
        left_outer.pack_propagate(False)
        self.left_sf = ScrollFrame(left_outer)
        self.left_sf.pack(fill="both", expand=True)
        self._build_left(self.left_sf.inner)

        # Orta (canvas + kontrol altı)
        center = tk.Frame(main, bg=C["bg"])
        center.pack(side="left", fill="both", expand=True)
        self._build_center(center)

        # Sağ panel (kaydırılabilir)
        right_outer = tk.Frame(main, bg=C["bg"], width=340)
        right_outer.pack(side="right", fill="y", padx=(6,0))
        right_outer.pack_propagate(False)
        self.right_sf = ScrollFrame(right_outer)
        self.right_sf.pack(fill="both", expand=True)
        self._build_right(self.right_sf.inner)

        # Bağlama kaydırma
        self.root.after(200, lambda: (
            self.left_sf.bind_children_scroll(),
            self.right_sf.bind_children_scroll()
        ))

    def _build_menubar(self):
        kw = dict(bg=C["bg2"], fg=C["text"],
                  activebackground=C["accent"], activeforeground="#fff",
                  borderwidth=0, relief="flat")
        mb = tk.Menu(self.root, **kw)
        self.root.config(menu=mb)

        def add_menu(label, items):
            m = tk.Menu(mb, tearoff=0, **kw)
            mb.add_cascade(label=label, menu=m)
            for it in items:
                if it is None:
                    m.add_separator()
                elif isinstance(it, tuple) and len(it)==2:
                    m.add_command(label=it[0], command=it[1])
            return m

        add_menu("Dosya", [
            ("PNG Yükle",         self.load_png),
            ("Hex'ten Yükle",     self._open_hex_load_dialog),
            ("PNG Olarak Kaydet", self.save_png),
            None,
            ("Sıfırla",           self._full_reset_prompt),
        ])
        add_menu("Düzenle", [
            ("Geri Al   Ctrl+Z",  self.undo),
            ("Yinele    Ctrl+Y",  self.redo),
            None,
            ("Tümünü Seç  Ctrl+A",self._select_all),
            ("Kes         Ctrl+X",self._cut_all),
            ("Kopyala     Ctrl+C",self._copy_selection),
            ("Yapıştır    Ctrl+V",self._activate_paste),
            ("Temizle     Del",   self._delete_all),
        ])
        add_menu("Görünüm", [
            ("Grid Göster/Gizle  G", lambda: self.show_grid_var.set(not self.show_grid_var.get()) or self._redraw_canvas()),
        ])
        add_menu("Dönüşüm", [
            ("Yatay Çevir",       lambda: self.flip_h_var.set(not self.flip_h_var.get()) or self._transform_redraw()),
            ("Dikey Çevir",       lambda: self.flip_v_var.set(not self.flip_v_var.get()) or self._transform_redraw()),
            ("Renkleri Ters Çevir", lambda: self.invert_var.set(not self.invert_var.get()) or self._transform_redraw()),
            None,
            ("90° Döndür (SY)",   lambda: self._quick_rotate("90_cw")),
            ("180° Döndür",       lambda: self._quick_rotate("180")),
            ("90° Döndür (SYT)",  lambda: self._quick_rotate("90_ccw")),
        ])

    # ── Sol panel ─────────────────────────────
    def _build_left(self, parent):
        parent.configure(bg=C["bg2"])

        # Araçlar
        tf = self._lf(parent, "ARAÇLAR")
        tools = [
            ("✏  Kalem      [P]",      "pencil"),
            ("◻  Silgi      [E]",      "eraser"),
            ("▓  Doldur     [F]",      "fill"),
            ("╱  Çizgi      [L]",      "line"),
            ("□  Çerçeve    [R]",      "rect_outline"),
            ("■  Dolu Kare  [Shift+R]","rect_fill"),
            ("○  Elips      [O]",      "ellipse_outline"),
            ("⊡  Seç/Kes    [S]",      "cut_selection"),
            ("⎘  Yapıştır   [V]",      "paste"),
        ]
        for text, val in tools:
            rb = ttk.Radiobutton(tf, text=text, variable=self.tool_var,
                                 value=val, style="Tool.TRadiobutton",
                                 command=lambda v=val: self._set_tool(v))
            rb.pack(anchor="w", fill="x", padx=4, pady=1)

        # Renk
        cf = self._lf(parent, "RENK  [X]")
        cr = tk.Frame(cf, bg=C["bg2"])
        cr.pack(fill="x")
        self.color_swatch = tk.Canvas(cr, width=40, height=40,
            bg=C["px_black"], highlightthickness=2,
            highlightbackground=C["accent"])
        self.color_swatch.pack(side="left", padx=(0,10))
        self.color_swatch.bind("<Button-1>", lambda e: self.toggle_color())
        ci = tk.Frame(cr, bg=C["bg2"])
        ci.pack(side="left")
        self.color_label = tk.Label(ci, text="● Siyah",
            bg=C["bg2"], fg=C["text"],
            font=("Segoe UI", 10, "bold"))
        self.color_label.pack(anchor="w")
        tk.Label(ci, text="X tuşu ile değiştir",
            bg=C["bg2"], fg=C["text2"],
            font=("Segoe UI", 8)).pack(anchor="w")

        # Fırça büyüklüğü
        bf = self._lf(parent, "FIRÇA")
        br = tk.Frame(bf, bg=C["bg2"])
        br.pack(fill="x")
        tk.Label(br, text="Boyut:", bg=C["bg2"], fg=C["text2"],
                 font=("Segoe UI", 8)).pack(side="left")
        self.brush_size_var = tk.IntVar(value=1)
        self.brush_label = tk.Label(br, text="1px", bg=C["bg2"],
            fg=C["accent"], font=("Segoe UI", 9, "bold"), width=4)
        self.brush_label.pack(side="right")
        brush_slider = tk.Scale(bf, from_=1, to=20,
            orient="horizontal", variable=self.brush_size_var,
            bg=C["bg2"], fg=C["text2"], troughcolor=C["bg4"],
            activebackground=C["accent"], highlightthickness=0,
            bd=0, showvalue=False,
            command=lambda v: self.brush_label.config(text=f"{v}px"))
        brush_slider.pack(fill="x", padx=4)

        # Boyutlar
        sf = self._lf(parent, "TUVAL BOYUTU")
        dr = tk.Frame(sf, bg=C["bg2"])
        dr.pack(fill="x", pady=(0,4))
        for lbl, var_name in [("G:", "width_var"), ("Y:", "height_var")]:
            tk.Label(dr, text=lbl, bg=C["bg2"], fg=C["text2"],
                     font=("Segoe UI", 9), width=2).pack(side="left")
            setattr(self, var_name, tk.StringVar(
                value=str(self.base_w if "w" in var_name else self.base_h)))
            e = ttk.Entry(dr, textvariable=getattr(self, var_name), width=5)
            e.pack(side="left", padx=(0,8))
        ttk.Button(sf, text="Boyutu Uygula",
            style="Accent.TButton",
            command=self.apply_size).pack(fill="x")

        # Görünüm / Zoom
        vf = self._lf(parent, "GÖRÜNÜM & ZOOM")
        ttk.Checkbutton(vf, text="Grid Göster  [G]",
            variable=self.show_grid_var,
            command=self._redraw_canvas).pack(anchor="w")
        ttk.Checkbutton(vf, text="Koordinat Göster",
            variable=self.show_coords_var).pack(anchor="w", pady=(2,4))
        zr = tk.Frame(vf, bg=C["bg2"])
        zr.pack(fill="x")
        tk.Label(zr, text="Zoom:", bg=C["bg2"], fg=C["text2"],
                 font=("Segoe UI", 8)).pack(side="left")
        for lbl, fn in [("−", lambda: self._zoom_step(-1)),
                        ("+", lambda: self._zoom_step(1)),
                        ("1:1", self._zoom_reset)]:
            tk.Button(zr, text=lbl, bg=C["bg4"], fg=C["text"],
                activebackground=C["accent"], activeforeground="#fff",
                relief="flat", bd=0, padx=6, pady=2,
                font=("Segoe UI", 9),
                command=fn).pack(side="left", padx=2)
        self.zoom_label = tk.Label(zr, text="1.0×",
            bg=C["bg2"], fg=C["accent"],
            font=("Segoe UI", 9, "bold"), width=5)
        self.zoom_label.pack(side="left")

        # Tarihçe
        hf = self._lf(parent, "GEÇMİŞ")
        hr = tk.Frame(hf, bg=C["bg2"])
        hr.pack(fill="x")
        self.undo_btn = ttk.Button(hr, text="↩ Geri  Ctrl+Z",
            command=self.undo)
        self.undo_btn.pack(side="left", expand=True, fill="x", padx=(0,3))
        self.redo_btn = ttk.Button(hr, text="↪ Yinele  Ctrl+Y",
            command=self.redo)
        self.redo_btn.pack(side="left", expand=True, fill="x")
        self._update_hist_buttons()

        # Hızlı işlemler
        af = self._lf(parent, "İŞLEMLER")
        for txt, cmd in [
            ("🗑  Tuvali Temizle",   self._clear_canvas_prompt),
            ("⟳  Tam Sıfırla",      self._full_reset_prompt),
            ("📂  PNG Yükle",        self.load_png),
            ("💾  PNG Kaydet",       self.save_png),
            ("📝  Hex'ten Yükle",    self._open_hex_load_dialog),
        ]:
            tk.Button(af, text=txt, bg=C["bg4"], fg=C["text"],
                activebackground=C["accent"], activeforeground="#fff",
                relief="flat", bd=0, padx=8, pady=4,
                font=("Segoe UI", 9), anchor="w",
                command=cmd).pack(fill="x", pady=1)

        # Kısayollar
        kf = self._lf(parent, "KISAYOLLAR")
        shorts = [
            ("P/E/F/L/R/O", "Araç seç"),
            ("S/V",         "Seç/Yapıştır"),
            ("X",           "Renk değiştir"),
            ("G",           "Grid aç/kapat"),
            ("Ctrl+Z/Y",    "Geri/Yinele"),
            ("Ctrl+A",      "Tümünü seç"),
            ("Ctrl+C/X/V",  "Kopyala/Kes/Yapıştır"),
            ("Del",         "Tümünü sil"),
            ("Esc",         "Araç sıfırla"),
            ("Scroll",      "Yakınlaştır"),
            ("Sağ Tık",     "Sil (beyaz çiz)"),
        ]
        for key, desc in shorts:
            row = tk.Frame(kf, bg=C["bg2"])
            row.pack(fill="x", pady=0)
            tk.Label(row, text=key, bg=C["bg2"], fg=C["accent"],
                     font=("Consolas", 8), width=14, anchor="w").pack(side="left")
            tk.Label(row, text=desc, bg=C["bg2"], fg=C["text2"],
                     font=("Segoe UI", 8)).pack(side="left")

    # ── Orta alan (canvas) ────────────────────
    def _build_center(self, parent):
        # Üst durum çubuğu
        sb = tk.Frame(parent, bg=C["bg"], height=28)
        sb.pack(fill="x", pady=(0,4))
        sb.pack_propagate(False)

        self.tool_indicator = tk.Label(sb,
            text="✏ Kalem", bg=C["bg"], fg=C["accent"],
            font=("Segoe UI", 9, "bold"))
        self.tool_indicator.pack(side="left", padx=4)

        sep = tk.Frame(sb, bg=C["border"], width=1)
        sep.pack(side="left", fill="y", padx=6, pady=4)

        self.size_indicator = tk.Label(sb,
            text="16×16", bg=C["bg"], fg=C["text2"],
            font=("Segoe UI", 8))
        self.size_indicator.pack(side="left")

        self.status_label = tk.Label(sb, text="",
            bg=C["bg"], fg=C["success"],
            font=("Segoe UI", 9))
        self.status_label.pack(side="right", padx=8)

        self.coord_label = tk.Label(sb, text="",
            bg=C["bg"], fg=C["text2"],
            font=("Consolas", 8))
        self.coord_label.pack(side="right", padx=8)

        # Canvas wrapper (kaydırılabilir)
        canvas_wrapper = tk.Frame(parent, bg=C["border"], bd=1, relief="flat")
        canvas_wrapper.pack(expand=True, fill="both")

        self.canvas_outer = tk.Frame(canvas_wrapper, bg=C["canvas_bg"])
        self.canvas_outer.pack(fill="both", expand=True)

        # H ve V scrollbar
        self.v_scroll = tk.Scrollbar(self.canvas_outer, orient="vertical",
            bg=C["bg3"], troughcolor=C["bg2"],
            activebackground=C["border2"],
            highlightthickness=0, bd=0)
        self.v_scroll.pack(side="right", fill="y")

        self.h_scroll = tk.Scrollbar(self.canvas_outer, orient="horizontal",
            bg=C["bg3"], troughcolor=C["bg2"],
            activebackground=C["border2"],
            highlightthickness=0, bd=0)
        self.h_scroll.pack(side="bottom", fill="x")

        self.canvas = tk.Canvas(self.canvas_outer,
            bg=C["canvas_bg"],
            highlightthickness=0,
            cursor="crosshair",
            xscrollcommand=self.h_scroll.set,
            yscrollcommand=self.v_scroll.set)
        self.canvas.pack(fill="both", expand=True)
        self.v_scroll.config(command=self.canvas.yview)
        self.h_scroll.config(command=self.canvas.xview)

        self.canvas.bind("<Button-1>",         self._on_click)
        self.canvas.bind("<B1-Motion>",        self._on_drag)
        self.canvas.bind("<ButtonRelease-1>",  self._on_release)
        self.canvas.bind("<Motion>",           self._on_motion)
        self.canvas.bind("<Leave>",            lambda e: self.coord_label.config(text=""))
        self.canvas.bind("<Button-3>",         self._on_right_click)
        self.canvas.bind("<B3-Motion>",        self._on_right_drag)
        self.canvas.bind("<MouseWheel>",       self._on_scroll_zoom)
        self.canvas.bind("<Button-4>",         self._on_scroll_zoom)
        self.canvas.bind("<Button-5>",         self._on_scroll_zoom)

        # Alt kontrol çubuğu
        self._build_bottom_bar(parent)

    def _build_bottom_bar(self, parent):
        """Canvas altındaki kontrol çubuğu."""
        bar = tk.Frame(parent, bg=C["bg2"], bd=0)
        bar.pack(fill="x", pady=(4, 0))

        # Zoom
        zf = tk.LabelFrame(bar, text=" ZOOM ", bg=C["bg2"], fg=C["accent"],
            font=("Segoe UI", 8, "bold"), bd=1, relief="flat",
            highlightthickness=1, highlightbackground=C["border"])
        zf.pack(side="left", padx=(4, 8), pady=3)
        zr = tk.Frame(zf, bg=C["bg2"])
        zr.pack(padx=4, pady=2)
        for txt, fn in [("−", lambda: self._zoom_step(-1)),
                        ("+", lambda: self._zoom_step(1)),
                        ("1:1", self._zoom_reset)]:
            tk.Button(zr, text=txt, bg=C["bg4"], fg=C["text"],
                activebackground=C["accent"], activeforeground="#fff",
                relief="flat", bd=0, padx=8, pady=3,
                font=("Segoe UI", 10, "bold"),
                command=fn).pack(side="left", padx=2)
        self.zoom_bar_label = tk.Label(zr, text="1.0×",
            bg=C["bg2"], fg=C["accent"],
            font=("Segoe UI", 9, "bold"), width=5)
        self.zoom_bar_label.pack(side="left", padx=4)

        # Kaydır zoom slider
        sf2 = tk.Frame(bar, bg=C["bg2"])
        sf2.pack(side="left", padx=4, pady=3)
        tk.Label(sf2, text="Zoom:", bg=C["bg2"], fg=C["text2"],
                 font=("Segoe UI", 8)).pack(side="left")
        self.zoom_slider = tk.Scale(sf2, from_=25, to=1600,
            orient="horizontal", bg=C["bg2"], fg=C["text2"],
            troughcolor=C["bg4"], activebackground=C["accent"],
            highlightthickness=0, bd=0, showvalue=False,
            length=140,
            command=self._on_zoom_slider)
        self.zoom_slider.set(100)
        self.zoom_slider.pack(side="left")

        # Tuval sıfırla
        tk.Button(bar, text="⊞ Tuval Sıfırla",
            bg=C["bg4"], fg=C["text"],
            activebackground=C["accent"], activeforeground="#fff",
            relief="flat", bd=0, padx=10, pady=4,
            font=("Segoe UI", 9),
            command=self._canvas_view_reset).pack(side="left", padx=8)

        # Koordinat / boyut bilgisi
        self.bottom_info = tk.Label(bar, text="16×16  |  1.0×",
            bg=C["bg2"], fg=C["text2"],
            font=("Consolas", 8))
        self.bottom_info.pack(side="right", padx=10)

    # ── Sağ panel ─────────────────────────────
    def _build_right(self, parent):
        parent.configure(bg=C["bg2"])

        # Bitmap seçenekleri
        bf = self._lf(parent, "BİTMAP SEÇENEKLERİ")
        tk.Label(bf, text="Okuma Yönü:", bg=C["bg2"], fg=C["text2"],
                 font=("Segoe UI", 8)).pack(anchor="w")
        rm_cb = ttk.Combobox(bf, textvariable=self.reading_order_var,
            values=list(self.reading_modes.keys()),
            state="readonly", width=34)
        rm_cb.pack(anchor="w", pady=(2,6), fill="x")
        rm_cb.bind("<<ComboboxSelected>>", lambda e: self._transform_redraw())

        tr1 = tk.Frame(bf, bg=C["bg2"])
        tr1.pack(fill="x", pady=2)
        ttk.Checkbutton(tr1, text="↔ Yatay Aynala",
            variable=self.flip_h_var,
            command=self._transform_redraw).pack(side="left")
        ttk.Checkbutton(tr1, text="↕ Dikey Aynala",
            variable=self.flip_v_var,
            command=self._transform_redraw).pack(side="left", padx=8)

        tr2 = tk.Frame(bf, bg=C["bg2"])
        tr2.pack(fill="x", pady=2)
        ttk.Checkbutton(tr2, text="⊘ Renkleri Ters Çevir",
            variable=self.invert_var,
            command=self._transform_redraw).pack(side="left")

        rr = tk.Frame(bf, bg=C["bg2"])
        rr.pack(fill="x", pady=(4,2))
        tk.Label(rr, text="Döndürme:", bg=C["bg2"], fg=C["text2"],
                 font=("Segoe UI", 8), width=10).pack(side="left")
        rot_cb = ttk.Combobox(rr, textvariable=self.rotation_var,
            values=list(self.rotation_map.keys()),
            state="readonly", width=18)
        rot_cb.pack(side="left")
        rot_cb.bind("<<ComboboxSelected>>", lambda e: self._transform_redraw())

        tk.Label(bf, text="OLED Arka Plan:", bg=C["bg2"], fg=C["text2"],
                 font=("Segoe UI", 8)).pack(anchor="w", pady=(4,0))
        bg_r = tk.Frame(bf, bg=C["bg2"])
        bg_r.pack(fill="x")
        for val in ("Siyah", "Beyaz"):
            ttk.Radiobutton(bg_r, text=val, variable=self.oled_bg_var,
                value=val).pack(side="left", padx=(0,12))

        # Canlı Hex Editörü
        hf = self._lf(parent, "CANLI HEX EDITÖRÜ")
        fr = tk.Frame(hf, bg=C["bg2"])
        fr.pack(fill="x", pady=(0,4))
        tk.Label(fr, text="Format:", bg=C["bg2"], fg=C["text2"],
                 font=("Segoe UI", 8), width=7).pack(side="left")
        fmt_cb = ttk.Combobox(fr, textvariable=self.hex_fmt_var,
            values=list(self.data_formats.keys()),
            state="readonly", width=22)
        fmt_cb.pack(side="left")
        fmt_cb.bind("<<ComboboxSelected>>", lambda e: self._refresh_hex())

        br2 = tk.Frame(hf, bg=C["bg2"])
        br2.pack(fill="x", pady=(0,4))
        for txt, cmd, style in [
            ("↻ Yenile",    self._refresh_hex,        "TButton"),
            ("📋 Kopyala",  self._copy_hex,           "Accent.TButton"),
            ("⬆ Uygula",   self._apply_hex_from_edit, "TButton"),
        ]:
            ttk.Button(br2, text=txt, command=cmd, style=style).pack(
                side="left", padx=(0,4))
        self.hex_status = tk.Label(br2, text="",
            bg=C["bg2"], fg=C["success"], font=("Segoe UI", 8))
        self.hex_status.pack(side="left")

        # Hex metin alanı + kaydırma
        ta_frame = tk.Frame(hf, bg=C["bg2"])
        ta_frame.pack(fill="both", expand=True)
        ta_frame.rowconfigure(0, weight=1)
        ta_frame.columnconfigure(0, weight=1)

        self.hex_text = tk.Text(ta_frame, wrap="none",
            bg=C["bg4"], fg="#7ec8e3",
            insertbackground=C["text"],
            selectbackground=C["accent2"],
            font=("Consolas", 8),
            relief="flat", bd=0,
            padx=6, pady=4, height=12)
        sy = ttk.Scrollbar(ta_frame, orient="vertical",
            command=self.hex_text.yview)
        sx = ttk.Scrollbar(ta_frame, orient="horizontal",
            command=self.hex_text.xview)
        self.hex_text["yscrollcommand"] = sy.set
        self.hex_text["xscrollcommand"] = sx.set
        self.hex_text.grid(row=0, column=0, sticky="nsew")
        sy.grid(row=0, column=1, sticky="ns")
        sx.grid(row=1, column=0, sticky="ew")

        self.byte_label = tk.Label(hf, text="0 byte",
            bg=C["bg2"], fg=C["text2"], font=("Segoe UI", 8))
        self.byte_label.pack(anchor="e", pady=(2,0))

        # Hex Depolama
        stf = self._lf(parent, "HEX DEPOLAMA")
        sr = tk.Frame(stf, bg=C["bg2"])
        sr.pack(fill="x")
        ttk.Button(sr, text="+ Depola & Temizle",
            style="Accent.TButton",
            command=self._store_hex).pack(side="left", padx=(0,4))
        ttk.Button(sr, text="📋 Depolananları Gör",
            command=self._show_stored).pack(side="left")
        self.stored_label = tk.Label(stf, text="0 kayıt",
            bg=C["bg2"], fg=C["text2"], font=("Segoe UI", 8))
        self.stored_label.pack(anchor="e")

        # Önizleme
        pf = self._lf(parent, "ÖNİZLEME (64×64)")
        self.preview_canvas = tk.Canvas(pf,
            width=128, height=128,
            bg=C["bg4"], highlightthickness=1,
            highlightbackground=C["border"])
        self.preview_canvas.pack(pady=4)

    # ── Yardımcı: LabelFrame ─────────────────
    def _lf(self, parent, title):
        f = tk.LabelFrame(parent, text=f" {title} ",
            bg=C["bg2"], fg=C["accent"],
            font=("Segoe UI", 8, "bold"),
            bd=1, relief="flat",
            highlightthickness=1,
            highlightbackground=C["border"])
        f.pack(fill="x", padx=4, pady=(0,5))
        # İç dolgu
        tk.Frame(f, bg=C["bg2"], height=2).pack()
        return f

    # ══════════════════════════════════════════
    #  KISAYOLLAR
    # ══════════════════════════════════════════
    def _bind_shortcuts(self):
        r = self.root
        r.bind("<Control-z>", lambda e: self.undo())
        r.bind("<Control-Z>", lambda e: self.undo())
        r.bind("<Control-y>", lambda e: self.redo())
        r.bind("<Control-Y>", lambda e: self.redo())
        r.bind("<Control-Shift-z>", lambda e: self.redo())
        r.bind("<Control-Shift-Z>", lambda e: self.redo())
        r.bind("<Control-a>", lambda e: self._select_all())
        r.bind("<Control-c>", lambda e: self._copy_selection())
        r.bind("<Control-x>", lambda e: self._cut_all())
        r.bind("<Control-v>", lambda e: self._activate_paste())
        r.bind("<Delete>",    lambda e: self._delete_all())
        r.bind("<Escape>",    lambda e: self._reset_tool_state())

        r.bind("p", lambda e: self._set_tool("pencil"))
        r.bind("P", lambda e: self._set_tool("pencil"))
        r.bind("e", lambda e: self._set_tool("eraser"))
        r.bind("E", lambda e: self._set_tool("eraser"))
        r.bind("f", lambda e: self._set_tool("fill"))
        r.bind("F", lambda e: self._set_tool("fill"))
        r.bind("l", lambda e: self._set_tool("line"))
        r.bind("L", lambda e: self._set_tool("line"))
        r.bind("r", lambda e: self._set_tool("rect_outline"))
        r.bind("R", lambda e: self._set_tool("rect_outline"))
        r.bind("<Shift-r>", lambda e: self._set_tool("rect_fill"))
        r.bind("<Shift-R>", lambda e: self._set_tool("rect_fill"))
        r.bind("o", lambda e: self._set_tool("ellipse_outline"))
        r.bind("O", lambda e: self._set_tool("ellipse_outline"))
        r.bind("s", lambda e: self._set_tool("cut_selection"))
        r.bind("S", lambda e: self._set_tool("cut_selection"))
        r.bind("v", lambda e: self._set_tool("paste"))
        r.bind("V", lambda e: self._set_tool("paste"))
        r.bind("x", lambda e: self.toggle_color())
        r.bind("X", lambda e: self.toggle_color())
        r.bind("g", lambda e: self._toggle_grid())
        r.bind("G", lambda e: self._toggle_grid())

    # ══════════════════════════════════════════
    #  ARAÇ YÖNETİMİ
    # ══════════════════════════════════════════
    def _set_tool(self, name):
        self.tool_var.set(name)
        self._reset_tool_state()
        names = TOOL_NAMES
        self.tool_indicator.config(text=names.get(name, name))

    def _reset_tool_state(self):
        self.tool_state = {}
        self.canvas.delete("preview")
        self.canvas.delete("sel_outline")

    def _toggle_grid(self):
        self.show_grid_var.set(not self.show_grid_var.get())
        self._redraw_canvas()

    # ══════════════════════════════════════════
    #  ZOOM
    # ══════════════════════════════════════════
    def _update_zoom_ui(self):
        txt = f"{self.zoom:.1f}×"
        self.zoom_label.config(text=txt)
        self.zoom_bar_label.config(text=txt)
        self.bottom_info.config(
            text=f"{self.base_w}×{self.base_h}  |  {self.zoom:.1f}×")
        self.zoom_slider.set(int(self.zoom * 100))

    def _on_zoom_slider(self, val):
        self.zoom = int(val) / 100.0
        self._recalc_cell_sizes()
        self._redraw_canvas()
        txt = f"{self.zoom:.1f}×"
        self.zoom_label.config(text=txt)
        self.zoom_bar_label.config(text=txt)
        self.bottom_info.config(
            text=f"{self.base_w}×{self.base_h}  |  {self.zoom:.1f}×")

    def _zoom_step(self, direction):
        if direction > 0:
            self.zoom = min(16.0, self.zoom * 1.25)
        else:
            self.zoom = max(0.25, self.zoom / 1.25)
        self._recalc_cell_sizes()
        self._redraw_canvas()
        self._update_zoom_ui()

    def _zoom_reset(self):
        self.zoom = 1.0
        self._recalc_cell_sizes()
        self._redraw_canvas()
        self._update_zoom_ui()
        self.canvas.xview_moveto(0)
        self.canvas.yview_moveto(0)

    def _canvas_view_reset(self):
        """Görünümü ve zoom'u sıfırla."""
        self._zoom_reset()
        self._show_status("Görünüm sıfırlandı ✓")

    def _recalc_cell_sizes(self):
        self.cell_w = (self.base_canvas_size * self.zoom) / self.disp_w
        self.cell_h = (self.base_canvas_size * self.zoom) / self.disp_h
        total_w = int(self.disp_w * self.cell_w)
        total_h = int(self.disp_h * self.cell_h)
        self.canvas.config(scrollregion=(0, 0, total_w, total_h))

    def _on_scroll_zoom(self, event):
        if event.num == 4 or (hasattr(event, "delta") and event.delta > 0):
            self.zoom = min(16.0, self.zoom * 1.12)
        else:
            self.zoom = max(0.25, self.zoom / 1.12)
        self._recalc_cell_sizes()
        self._redraw_canvas()
        self._update_zoom_ui()

    # ══════════════════════════════════════════
    #  CANVAS ÇİZİMİ
    # ══════════════════════════════════════════
    def _redraw_canvas(self):
        self.canvas.delete("pixel")
        self.canvas.delete("grid_line")
        show_grid = self.show_grid_var.get()
        cw = self.cell_w; ch = self.cell_h
        grid = self.display_grid
        h = self.disp_h; w = self.disp_w
        px_b = C["px_black"]; px_w = C["px_white"]
        gl = C["grid_line"]

        for r in range(h):
            y0 = r * ch; y1 = y0 + ch
            for c in range(w):
                x0 = c * cw; x1 = x0 + cw
                fill = px_b if grid[r][c] == 1 else px_w
                outline = gl if show_grid else fill
                self.canvas.create_rectangle(
                    x0, y0, x1, y1,
                    fill=fill, outline=outline,
                    tags="pixel")

        total_w = int(w * cw); total_h = int(h * ch)
        self.canvas.config(scrollregion=(0, 0, total_w, total_h))
        self._update_preview()

    def _update_single_pixel(self, r, c):
        if not (0 <= r < self.disp_h and 0 <= c < self.disp_w):
            return
        self.canvas.delete(f"px_{r}_{c}")
        x0 = c * self.cell_w; y0 = r * self.cell_h
        x1 = x0 + self.cell_w; y1 = y0 + self.cell_h
        fill = C["px_black"] if self.display_grid[r][c] == 1 else C["px_white"]
        outline = C["grid_line"] if self.show_grid_var.get() else fill
        self.canvas.create_rectangle(x0, y0, x1, y1,
            fill=fill, outline=outline,
            tags=("pixel", f"px_{r}_{c}"))

    def _update_preview(self):
        pw = 128; ph = 128
        self.preview_canvas.delete("all")
        if self.disp_w == 0 or self.disp_h == 0:
            return
        cx = pw / self.disp_w; cy = ph / self.disp_h
        for r in range(self.disp_h):
            for c in range(self.disp_w):
                x0 = c*cx; y0 = r*cy
                fill = C["px_black"] if self.display_grid[r][c]==1 else C["px_white"]
                self.preview_canvas.create_rectangle(
                    x0, y0, x0+cx+1, y0+cy+1,
                    fill=fill, outline=fill)

    # ══════════════════════════════════════════
    #  CANVAS OLAY YÖNETİMİ
    # ══════════════════════════════════════════
    def _canvas_to_cell(self, event):
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)
        total_w = self.disp_w * self.cell_w
        total_h = self.disp_h * self.cell_h
        if not (0 <= cx < total_w and 0 <= cy < total_h):
            return None, None
        col = max(0, min(int(cx / self.cell_w), self.disp_w - 1))
        row = max(0, min(int(cy / self.cell_h), self.disp_h - 1))
        return row, col

    def _draw_at(self, r, c, color=None):
        """Fırça boyutunu dikkate alarak boyar."""
        if color is None:
            color = self.draw_color
        size = self.brush_size_var.get()
        half = size // 2
        changed = False
        for dr in range(-half, half + (1 if size % 2 == 1 else 0)):
            for dc in range(-half, half + (1 if size % 2 == 1 else 0)):
                nr = r + dr; nc = c + dc
                if 0 <= nr < self.base_h and 0 <= nc < self.base_w:
                    if self.base_grid[nr][nc] != color:
                        self.base_grid[nr][nc] = color
                        changed = True
        return changed

    def _on_click(self, event):
        r, c = self._canvas_to_cell(event)
        if r is None: return
        tool = self.tool_var.get()

        if tool in ("line", "rect_outline", "rect_fill",
                    "ellipse_outline", "cut_selection"):
            self.tool_state["start"] = (r, c)
            self.canvas.delete("preview")
            self.canvas.delete("sel_outline")

        elif tool == "paste":
            self._paste_at(r, c)
            self._record_history()
            self._transform_redraw()

        elif tool == "fill":
            tc = self.base_grid[r][c]
            fc = self.draw_color
            if tc != fc:
                self._flood_fill(r, c, tc, fc)
                self._record_history()
                self._transform_redraw()

        elif tool == "eraser":
            if self._draw_at(r, c, 0):
                self._transform_redraw()
            self.last_drag_cell = (r, c)

        else:  # pencil
            if self._draw_at(r, c):
                self._transform_redraw()
            self.last_drag_cell = (r, c)

    def _on_drag(self, event):
        r, c = self._canvas_to_cell(event)
        tool = self.tool_var.get()
        if tool in ("line", "rect_outline", "rect_fill",
                    "ellipse_outline", "cut_selection"):
            if "start" in self.tool_state and r is not None:
                self._draw_preview(r, c)
        elif tool in ("pencil", "eraser"):
            if r is None: return
            last = self.last_drag_cell
            color = 0 if tool == "eraser" else self.draw_color
            if last and last != (r, c):
                # Ara hücreleri de doldur (Bresenham)
                for pr, pc in self._bresenham_cells(last[0], last[1], r, c):
                    self._draw_at(pr, pc, color)
                self._transform_redraw()
            elif not last:
                if self._draw_at(r, c, color):
                    self._transform_redraw()
            self.last_drag_cell = (r, c)
        if r is not None and self.show_coords_var.get():
            self.coord_label.config(text=f"({c}, {r})")

    def _on_release(self, event):
        r, c = self._canvas_to_cell(event)
        tool = self.tool_var.get()
        self.last_drag_cell = None

        if tool in ("line", "rect_outline", "rect_fill",
                    "ellipse_outline", "cut_selection") and "start" in self.tool_state:
            if r is None: r, c = self.tool_state["start"]
            r0, c0 = self.tool_state.pop("start")
            self.canvas.delete("preview")
            self.canvas.delete("sel_outline")

            if tool == "line":
                self._draw_line(r0, c0, r, c)
            elif tool == "rect_outline":
                self._draw_rect_outline(r0, c0, r, c)
            elif tool == "rect_fill":
                self._draw_rect_fill(r0, c0, r, c)
            elif tool == "ellipse_outline":
                self._draw_ellipse(r0, c0, r, c)
            elif tool == "cut_selection":
                self._cut_region(r0, c0, r, c)

            self._record_history()
            self._transform_redraw()

        elif tool in ("pencil", "eraser"):
            self._record_history()

    def _on_motion(self, event):
        r, c = self._canvas_to_cell(event)
        if r is not None and self.show_coords_var.get():
            self.coord_label.config(text=f"({c}, {r})")
        tool = self.tool_var.get()
        if tool in ("line", "rect_outline", "rect_fill",
                    "ellipse_outline", "cut_selection") and "start" in self.tool_state and r is not None:
            self._draw_preview(r, c)

    def _on_right_click(self, event):
        r, c = self._canvas_to_cell(event)
        if r is None: return
        if self._draw_at(r, c, 0):
            self._transform_redraw()
        self.last_drag_cell = (r, c)

    def _on_right_drag(self, event):
        r, c = self._canvas_to_cell(event)
        if r is None: return
        last = self.last_drag_cell
        if last and last != (r, c):
            for pr, pc in self._bresenham_cells(last[0], last[1], r, c):
                self._draw_at(pr, pc, 0)
            self._transform_redraw()
        elif not last:
            if self._draw_at(r, c, 0):
                self._transform_redraw()
        self.last_drag_cell = (r, c)

    def _draw_preview(self, r, c):
        self.canvas.delete("preview")
        self.canvas.delete("sel_outline")
        if "start" not in self.tool_state: return
        r0, c0 = self.tool_state["start"]
        tool = self.tool_var.get()
        cw = self.cell_w; ch = self.cell_h

        if tool == "line":
            x0=(c0+.5)*cw; y0=(r0+.5)*ch
            x1=(c+.5)*cw;  y1=(r+.5)*ch
            self.canvas.create_line(x0,y0,x1,y1,
                fill=C["preview_col"], width=2, tags="preview")
        else:
            min_c=min(c0,c); max_c=max(c0,c)
            min_r=min(r0,r); max_r=max(r0,r)
            x0=min_c*cw; y0=min_r*ch
            x1=(max_c+1)*cw; y1=(max_r+1)*ch
            color = C["sel_color"] if tool=="cut_selection" else C["preview_col"]
            tag = "sel_outline" if tool=="cut_selection" else "preview"
            self.canvas.create_rectangle(x0,y0,x1,y1,
                outline=color, width=2, tags=tag)

    # ══════════════════════════════════════════
    #  ÇİZİM PRİMİTİFLERİ
    # ══════════════════════════════════════════
    def _bresenham_cells(self, r0, c0, r1, c1):
        """Bresenham ile iki hücre arasındaki tüm hücreleri döndür."""
        cells = []
        dr=abs(r1-r0); dc=abs(c1-c0)
        sr=1 if r0<r1 else -1; sc=1 if c0<c1 else -1
        err=dr-dc
        while True:
            cells.append((r0, c0))
            if r0==r1 and c0==c1: break
            e2=2*err
            if e2>-dc: err-=dc; r0+=sr
            if e2< dr: err+=dr; c0+=sc
        return cells

    def _draw_line(self, r0, c0, r1, c1):
        col = self.draw_color
        for pr, pc in self._bresenham_cells(r0, c0, r1, c1):
            self._draw_at(pr, pc, col)

    def _draw_rect_outline(self, r0, c0, r1, c1):
        col = self.draw_color
        min_r=min(r0,r1); max_r=max(r0,r1)
        min_c=min(c0,c1); max_c=max(c0,c1)
        for r in range(min_r, max_r+1):
            for c in range(min_c, max_c+1):
                if 0<=r<self.base_h and 0<=c<self.base_w:
                    if r in (min_r, max_r) or c in (min_c, max_c):
                        self.base_grid[r][c] = col

    def _draw_rect_fill(self, r0, c0, r1, c1):
        col = self.draw_color
        min_r=min(r0,r1); max_r=max(r0,r1)
        min_c=min(c0,c1); max_c=max(c0,c1)
        for r in range(min_r, max_r+1):
            for c in range(min_c, max_c+1):
                if 0<=r<self.base_h and 0<=c<self.base_w:
                    self.base_grid[r][c] = col

    def _draw_ellipse(self, r0, c0, r1, c1):
        """Orta nokta elips algoritması."""
        col = self.draw_color
        min_r=min(r0,r1); max_r=max(r0,r1)
        min_c=min(c0,c1); max_c=max(c0,c1)
        cx=(min_c+max_c)/2; cy=(min_r+max_r)/2
        a=max((max_c-min_c)/2, 0.5); b=max((max_r-min_r)/2, 0.5)
        # Tüm piksel hücrelerini test et
        for r in range(min_r, max_r+1):
            for c in range(min_c, max_c+1):
                val = ((c-cx)/a)**2 + ((r-cy)/b)**2
                if 0.6 <= val <= 1.4:
                    if 0<=r<self.base_h and 0<=c<self.base_w:
                        self.base_grid[r][c] = col

    def _flood_fill(self, r, c, target, fill_c):
        if target == fill_c: return
        stack = [(r, c)]
        visited = set()
        while stack:
            cr, cc = stack.pop()
            if (cr, cc) in visited: continue
            if not (0<=cr<self.base_h and 0<=cc<self.base_w): continue
            if self.base_grid[cr][cc] != target: continue
            visited.add((cr, cc))
            self.base_grid[cr][cc] = fill_c
            stack += [(cr+1,cc),(cr-1,cc),(cr,cc+1),(cr,cc-1)]

    def _cut_region(self, r0, c0, r1, c1):
        min_r=min(r0,r1); max_r=max(r0,r1)
        min_c=min(c0,c1); max_c=max(c0,c1)
        self.clipboard = []
        for r in range(min_r, max_r+1):
            row = []
            for c in range(min_c, max_c+1):
                if 0<=r<self.base_h and 0<=c<self.base_w:
                    row.append(self.base_grid[r][c])
                    self.base_grid[r][c] = 0
                else:
                    row.append(0)
            self.clipboard.append(row)
        self.clip_h = len(self.clipboard)
        self.clip_w = len(self.clipboard[0]) if self.clipboard else 0
        self._show_status(f"Kesildi: {self.clip_w}×{self.clip_h} ✓")

    def _paste_at(self, r_t, c_t):
        if not self.clipboard:
            self._show_status("Panoda içerik yok!")
            return
        for dr in range(self.clip_h):
            for dc in range(self.clip_w):
                tr=r_t+dr; tc=c_t+dc
                if 0<=tr<self.base_h and 0<=tc<self.base_w:
                    self.base_grid[tr][tc] = self.clipboard[dr][dc]
        self._show_status("Yapıştırıldı ✓")

    # ══════════════════════════════════════════
    #  KLİPBOART
    # ══════════════════════════════════════════
    def _select_all(self):
        self._set_tool("cut_selection")
        self.tool_state["start"] = (0, 0)

    def _copy_selection(self):
        self.clipboard = [row[:] for row in self.base_grid]
        self.clip_h = self.base_h
        self.clip_w = self.base_w
        self._show_status("Kopyalandı ✓")

    def _cut_all(self):
        self._copy_selection()
        self.base_grid = [[0]*self.base_w for _ in range(self.base_h)]
        self._record_history()
        self._transform_redraw()
        self._show_status("Kesildi ✓")

    def _activate_paste(self):
        if self.clipboard:
            self._set_tool("paste")
            self._show_status("Yapıştır: Tuvale tıkla ▸")

    def _delete_all(self):
        self.base_grid = [[0]*self.base_w for _ in range(self.base_h)]
        self._record_history()
        self._transform_redraw()

    # ══════════════════════════════════════════
    #  DÖNÜŞÜM
    # ══════════════════════════════════════════
    def _transform_grid(self, data, w, h):
        rot = self.rotation_map.get(self.rotation_var.get(), "0")
        if rot == "90_cw":
            nd = [[0]*h for _ in range(w)]
            for r in range(h):
                for c in range(w): nd[c][h-1-r] = data[r][c]
            data = nd; w, h = h, w
        elif rot == "180":
            nd = [[0]*w for _ in range(h)]
            for r in range(h):
                for c in range(w): nd[h-1-r][w-1-c] = data[r][c]
            data = nd
        elif rot == "90_ccw":
            nd = [[0]*h for _ in range(w)]
            for r in range(h):
                for c in range(w): nd[w-1-c][r] = data[r][c]
            data = nd; w, h = h, w
        if self.flip_h_var.get():
            for row in data: row.reverse()
        if self.flip_v_var.get():
            data.reverse()
        return data, w, h

    def _transform_redraw(self):
        data = [row[:] for row in self.base_grid]
        w = self.base_w; h = self.base_h
        data, w, h = self._transform_grid(data, w, h)
        inv = self.invert_var.get()
        final = [[0]*w for _ in range(h)]
        for r in range(h):
            for c in range(w):
                final[r][c] = (1-data[r][c]) if inv else data[r][c]
        self.disp_w = w; self.disp_h = h
        self.display_grid = final
        self.cell_w = (self.base_canvas_size * self.zoom) / w
        self.cell_h = (self.base_canvas_size * self.zoom) / h
        total_w = int(w * self.cell_w); total_h = int(h * self.cell_h)
        self.canvas.config(scrollregion=(0, 0, total_w, total_h))
        self._redraw_canvas()
        self._refresh_hex()
        self.size_indicator.config(text=f"{self.base_w}×{self.base_h}")
        self.bottom_info.config(
            text=f"{self.base_w}×{self.base_h}  |  {self.zoom:.1f}×")

    def _quick_rotate(self, rot):
        self.rotation_var.set(
            {v: k for k,v in self.rotation_map.items()}.get(rot, "Yok"))
        self._transform_redraw()

    # ══════════════════════════════════════════
    #  GEÇMİŞ
    # ══════════════════════════════════════════
    def _record_history(self):
        if self.hist_idx < len(self.history)-1:
            self.history = self.history[:self.hist_idx+1]
        self.history.append([row[:] for row in self.base_grid])
        self.hist_idx = len(self.history)-1
        if len(self.history) > 200:
            self.history = self.history[-200:]
            self.hist_idx = len(self.history)-1
        self._update_hist_buttons()

    def undo(self):
        if self.hist_idx > 0:
            self.hist_idx -= 1
            self.base_grid = [row[:] for row in self.history[self.hist_idx]]
            self._transform_redraw()
            self._update_hist_buttons()

    def redo(self):
        if self.hist_idx < len(self.history)-1:
            self.hist_idx += 1
            self.base_grid = [row[:] for row in self.history[self.hist_idx]]
            self._transform_redraw()
            self._update_hist_buttons()

    def _update_hist_buttons(self):
        self.undo_btn.config(
            state="normal" if self.hist_idx > 0 else "disabled")
        self.redo_btn.config(
            state="normal" if self.hist_idx < len(self.history)-1 else "disabled")

    # ══════════════════════════════════════════
    #  RENK
    # ══════════════════════════════════════════
    def toggle_color(self):
        self.draw_color = 1 - self.draw_color
        if self.draw_color == 1:
            self.color_swatch.config(bg=C["px_black"])
            self.color_label.config(text="● Siyah")
        else:
            self.color_swatch.config(bg=C["px_white"])
            self.color_label.config(text="○ Beyaz")

    # ══════════════════════════════════════════
    #  BOYUT
    # ══════════════════════════════════════════
    def apply_size(self):
        try:
            w = int(self.width_var.get())
            h = int(self.height_var.get())
        except ValueError:
            messagebox.showerror("Hata", "Sayısal değer giriniz."); return
        if not (1 <= w <= 256 and 1 <= h <= 256):
            messagebox.showerror("Hata", "1–256 arasında olmalıdır."); return
        self.base_w = w; self.base_h = h
        self.base_grid = [[0]*w for _ in range(h)]
        self.disp_w = w; self.disp_h = h
        self.zoom = 1.0
        self.cell_w = self.base_canvas_size / w
        self.cell_h = self.base_canvas_size / h
        self._update_zoom_ui()
        self._record_history()
        self._transform_redraw()
        self._show_status(f"Boyut uygulandı: {w}×{h} ✓")

    # ══════════════════════════════════════════
    #  TEMİZLE / SIFIRLA
    # ══════════════════════════════════════════
    def _clear_canvas_prompt(self):
        if messagebox.askyesno("Temizle", "Tuval temizlensin mi?"):
            self.base_grid = [[0]*self.base_w for _ in range(self.base_h)]
            self._record_history()
            self._transform_redraw()
            self._show_status("Temizlendi ✓")

    def _full_reset_prompt(self):
        if messagebox.askyesno("Sıfırla", "Tüm ayarlar ve çizim sıfırlansın mı?"):
            self._full_reset()

    def _full_reset(self):
        self.base_w = 16; self.base_h = 16
        self.disp_w = 16; self.disp_h = 16
        self.base_grid = [[0]*16 for _ in range(16)]
        self.width_var.set("16"); self.height_var.set("16")
        self.reading_order_var.set("Sayfa Bazlı (Yatay) - Sütun MSB İlk")
        self.flip_h_var.set(False); self.flip_v_var.set(False)
        self.invert_var.set(False); self.rotation_var.set("Yok")
        self.oled_bg_var.set("Siyah"); self.hex_fmt_var.set("C Array")
        self.draw_color = 1
        self.color_swatch.config(bg=C["px_black"])
        self.color_label.config(text="● Siyah")
        self.zoom = 1.0; self.brush_size_var.set(1)
        self.cell_w = self.base_canvas_size / 16
        self.cell_h = self.base_canvas_size / 16
        self.history = []; self.hist_idx = -1
        self.clipboard = None; self.clip_w = 0; self.clip_h = 0
        self._update_zoom_ui()
        self._record_history()
        self._transform_redraw()
        self._reset_tool_state()
        self._show_status("Sıfırlandı ✓")

    # ══════════════════════════════════════════
    #  PNG YÜKLE / KAYDET
    # ══════════════════════════════════════════
    def load_png(self):
        path = filedialog.askopenfilename(
            title="PNG Seç",
            filetypes=[("PNG", "*.png"), ("Tüm dosyalar", "*.*")])
        if not path: return
        try:
            img = Image.open(path).convert("1")
            w, h = img.size
            if not (1 <= w <= 256 and 1 <= h <= 256):
                messagebox.showerror("Hata", "Maks. 256×256 piksel"); return
            self.base_w = w; self.base_h = h
            self.width_var.set(str(w)); self.height_var.set(str(h))
            grid = [[0]*w for _ in range(h)]
            px = img.load()
            for r in range(h):
                for c in range(w):
                    grid[r][c] = 1 if px[c, r] == 0 else 0
            self.base_grid = grid; self.disp_w = w; self.disp_h = h
            self.zoom = 1.0
            self.cell_w = self.base_canvas_size / w
            self.cell_h = self.base_canvas_size / h
            self._update_zoom_ui()
            self._record_history()
            self._transform_redraw()
            self._show_status(f"PNG yüklendi: {w}×{h} ✓")
        except Exception as ex:
            messagebox.showerror("Hata", str(ex))

    def save_png(self):
        path = filedialog.asksaveasfilename(
            title="PNG Kaydet",
            defaultextension=".png",
            filetypes=[("PNG", "*.png")])
        if not path: return
        try:
            img = Image.new("1", (self.disp_w, self.disp_h))
            px = img.load()
            for r in range(self.disp_h):
                for c in range(self.disp_w):
                    px[c, r] = 0 if self.display_grid[r][c] == 1 else 255
            img.save(path)
            self._show_status("PNG kaydedildi ✓")
        except Exception as ex:
            messagebox.showerror("Hata", str(ex))

    # ══════════════════════════════════════════
    #  BYTE DÖNÜŞÜM
    # ══════════════════════════════════════════
    def _get_output_bytes(self):
        data = [row[:] for row in self.base_grid]
        w = self.base_w; h = self.base_h
        data, w, h = self._transform_grid(data, w, h)
        inv = self.invert_var.get()
        oled_w = self.oled_bg_var.get() == "Beyaz"
        final = [[0]*w for _ in range(h)]
        for r in range(h):
            for c in range(w):
                pv = data[r][c]
                if inv: pv = 1-pv
                if oled_w: pv = 1-pv
                final[r][c] = pv
        mode_key = self.reading_order_var.get()
        mode = self.reading_modes.get(mode_key)
        if not mode: return None, w, h
        return self._grid_to_bytes(final, w, h, mode), w, h

    def _grid_to_bytes(self, grid, w, h, mode):
        out = []; ma = mode["major_axis"]; bo = mode["bit_order"]
        po = mode["page_oriented"]
        if not po:
            if ma == "horizontal":
                bpr = math.ceil(w/8)
                for r in range(h):
                    for bi in range(bpr):
                        b = 0
                        for bit in range(8):
                            pc = bi*8+bit
                            if pc < w:
                                pv = grid[r][pc]
                                b |= pv << (7-bit) if bo=="msb_first" else pv << bit
                        out.append(b)
            else:
                bpc = math.ceil(h/8)
                for c in range(w):
                    for bi in range(bpc):
                        b = 0
                        for bit in range(8):
                            pr = bi*8+bit
                            if pr < h:
                                pv = grid[pr][c]
                                b |= pv << (7-bit) if bo=="msb_first" else pv << bit
                        out.append(b)
        else:
            if ma == "horizontal_pages":
                pages_h = math.ceil(h/8)
                for ph in range(pages_h):
                    for c in range(w):
                        b = 0
                        for bit in range(8):
                            pr = ph*8+bit
                            if pr < h:
                                pv = grid[pr][c]
                                b |= pv << bit if bo=="msb_first" else pv << (7-bit)
                        out.append(b)
            elif ma == "vertical_pages":
                pages_w = math.ceil(w/8)
                for pw in range(pages_w):
                    for r in range(h):
                        b = 0
                        for bit in range(8):
                            pc = pw*8+bit
                            if pc < w:
                                pv = grid[r][pc]
                                b |= pv << (7-bit) if bo=="msb_first" else pv << bit
                        out.append(b)
        return out

    def _bytes_to_grid(self, bvals, w, h, mode):
        grid = [[0]*w for _ in range(h)]
        bi = 0; ma = mode["major_axis"]; bo = mode["bit_order"]
        po = mode["page_oriented"]
        if not po:
            if ma == "horizontal":
                bpr = math.ceil(w/8)
                for r in range(h):
                    for cbi in range(bpr):
                        if bi >= len(bvals): break
                        b = bvals[bi]; bi += 1
                        for bp in range(8):
                            pc = cbi*8+bp
                            if pc < w:
                                grid[r][pc] = (1 if ((b>>(7-bp))&1) else 0) if bo=="msb_first" else (1 if ((b>>bp)&1) else 0)
            else:
                bpc = math.ceil(h/8)
                for c in range(w):
                    for rbi in range(bpc):
                        if bi >= len(bvals): break
                        b = bvals[bi]; bi += 1
                        for bp in range(8):
                            pr = rbi*8+bp
                            if pr < h:
                                grid[pr][c] = (1 if ((b>>(7-bp))&1) else 0) if bo=="msb_first" else (1 if ((b>>bp)&1) else 0)
        else:
            if ma == "horizontal_pages":
                pages_h = math.ceil(h/8)
                for ph in range(pages_h):
                    for c in range(w):
                        if bi >= len(bvals): break
                        b = bvals[bi]; bi += 1
                        for bp in range(8):
                            pr = ph*8+bp
                            if pr < h:
                                grid[pr][c] = (1 if ((b>>bp)&1) else 0) if bo=="msb_first" else (1 if ((b>>(7-bp))&1) else 0)
            elif ma == "vertical_pages":
                pages_w = math.ceil(w/8)
                for pw in range(pages_w):
                    for r in range(h):
                        if bi >= len(bvals): break
                        b = bvals[bi]; bi += 1
                        for bp in range(8):
                            pc = pw*8+bp
                            if pc < w:
                                grid[r][pc] = (1 if ((b>>(7-bp))&1) else 0) if bo=="msb_first" else (1 if ((b>>bp)&1) else 0)
        return grid

    # ══════════════════════════════════════════
    #  FORMAT ÜRETICILER & AYRIŞTIRICILARI
    # ══════════════════════════════════════════
    def _gen_c_array(self, bvals, w, h):
        s = f"// {w}x{h} px | {len(bvals)} bytes\n"
        s += f"const unsigned char bitmap[{len(bvals)}] = {{\n  "
        lc = 0
        for i, b in enumerate(bvals):
            s += f"0x{b:02X}"
            if i < len(bvals)-1: s += ","
            lc += 1
            if lc >= 16 and i < len(bvals)-1: s += "\n  "; lc = 0
            elif i < len(bvals)-1: s += " "
        s += "\n};"
        return s

    def _gen_arduino(self, bvals, w, h):
        s = f"// {w}x{h} px | {len(bvals)} bytes\n"
        s += f"const unsigned char PROGMEM bitmap[{len(bvals)}] = {{\n  "
        lc = 0
        for i, b in enumerate(bvals):
            s += f"0x{b:02X}"
            if i < len(bvals)-1: s += ","
            lc += 1
            if lc >= 16 and i < len(bvals)-1: s += "\n  "; lc = 0
            elif i < len(bvals)-1: s += " "
        s += "\n};"
        return s

    def _gen_plain(self, bvals, w, h):
        return "".join(f"{b:02X}" for b in bvals)

    def _gen_pyint(self, bvals, w, h):
        s = f"# {w}x{h} px | {len(bvals)} bytes\nbytes_data = [\n  "
        for i, b in enumerate(bvals):
            s += str(b)
            if i < len(bvals)-1: s += ","
            if (i+1) % 16 == 0 and i < len(bvals)-1: s += "\n  "
            elif i < len(bvals)-1: s += " "
        s += "\n]"
        return s

    def _gen_pyhex(self, bvals, w, h):
        s = f"# {w}x{h} px | {len(bvals)} bytes\nbytes_data = [\n  "
        for i, b in enumerate(bvals):
            s += f'"0x{b:02X}"'
            if i < len(bvals)-1: s += ","
            if (i+1) % 16 == 0 and i < len(bvals)-1: s += "\n  "
            elif i < len(bvals)-1: s += " "
        s += "\n]"
        return s

    def _parse_c(self, s):
        m = re.findall(r"0x([0-9a-fA-F]{2})", s, re.IGNORECASE)
        if not m: raise ValueError("C dizisi formatında geçerli hex bulunamadı.")
        return [int(x, 16) for x in m]

    def _parse_plain(self, s):
        c = re.sub(r"[^0-9a-fA-F]", "", s)
        if len(c) % 2 != 0: raise ValueError("Çift sayıda karakter gerekli.")
        return [int(c[i:i+2], 16) for i in range(0, len(c), 2)]

    def _parse_pyint(self, s):
        m = re.findall(r"\b(\d+)\b", s)
        if not m: raise ValueError("Tamsayı bulunamadı.")
        vals = [int(x) for x in m]
        for v in vals:
            if not 0 <= v <= 255: raise ValueError(f"0-255 dışı: {v}")
        return vals

    def _parse_pyhex(self, s):
        m = re.findall(r'"?0x([0-9a-fA-F]{2})"?', s, re.IGNORECASE)
        if not m: raise ValueError("Hex string listesi bulunamadı.")
        return [int(x, 16) for x in m]

    # ══════════════════════════════════════════
    #  HEX PANEL
    # ══════════════════════════════════════════
    def _refresh_hex(self):
        if self._hex_lock: return
        bvals, w, h = self._get_output_bytes()
        if bvals is None: return
        fmt_key = self.hex_fmt_var.get()
        fmt = self.data_formats.get(fmt_key, {})
        gen = fmt.get("gen")
        if not gen: return
        code = gen(bvals, w, h)
        self._hex_lock = True
        self.hex_text.config(state="normal")
        self.hex_text.delete("1.0", "end")
        self.hex_text.insert("1.0", code)
        self._hex_lock = False
        self.byte_label.config(text=f"{len(bvals)} byte  |  {w}×{h} px")

    def _copy_hex(self):
        code = self.hex_text.get("1.0", "end").strip()
        if not code:
            self._refresh_hex()
            code = self.hex_text.get("1.0", "end").strip()
        self.root.clipboard_clear()
        self.root.clipboard_append(code)
        self.root.update()
        self.hex_status.config(text="Kopyalandı ✓")
        self.root.after(2000, lambda: self.hex_status.config(text=""))

    def _apply_hex_from_edit(self):
        code = self.hex_text.get("1.0", "end").strip()
        if not code: return
        fmt_key = self.hex_fmt_var.get()
        fmt = self.data_formats.get(fmt_key, {})
        parse = fmt.get("parse")
        if not parse:
            messagebox.showerror("Hata", "Bu format için ayrıştırıcı yok."); return
        try:
            bvals = parse(code)
        except Exception as e:
            messagebox.showerror("Ayrıştırma Hatası", str(e)); return
        if not bvals:
            messagebox.showerror("Hata", "Byte değeri bulunamadı."); return
        w = self.base_w; h = self.base_h
        mode = self.reading_modes.get(self.reading_order_var.get())
        if not mode: return
        grid = self._bytes_to_grid(bvals, w, h, mode)
        self.base_grid = grid
        self._record_history()
        self._transform_redraw()
        self._show_status("Hex uygulandı ✓")

    # ══════════════════════════════════════════
    #  DEPOLAMA
    # ══════════════════════════════════════════
    def _store_hex(self):
        bvals, w, h = self._get_output_bytes()
        if bvals is None: return
        fmt_key = self.hex_fmt_var.get()
        fmt = self.data_formats.get(fmt_key, {})
        gen = fmt.get("gen")
        if not gen: return
        code = gen(bvals, w, h)
        self.stored.append({"dims": f"{w}×{h}", "bytes": len(bvals), "code": code})
        self.stored_label.config(text=f"{len(self.stored)} kayıt")
        self._show_status(f"Depolandı ({len(self.stored)}) ✓")
        # Temizle
        self.base_grid = [[0]*self.base_w for _ in range(self.base_h)]
        self._record_history()
        self._transform_redraw()

    def _show_stored(self):
        if not self.stored:
            messagebox.showinfo("Depolama", "Henüz kayıt yok."); return
        win = Toplevel(self.root)
        win.title("Depolanan Hex Kodları")
        win.geometry("800x600")
        win.configure(bg=C["bg"])
        win.grab_set()
        apply_dark_style(win)

        tk.Label(win, text=f"{len(self.stored)} kayıt",
            bg=C["bg"], fg=C["accent"],
            font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=12, pady=(8,0))

        nb = ttk.Notebook(win)
        nb.pack(fill="both", expand=True, padx=8, pady=8)

        # Tümü sekmesi
        af = ttk.Frame(nb); nb.add(af, text="Tümü")
        af.rowconfigure(0, weight=1); af.columnconfigure(0, weight=1)
        ta = tk.Text(af, wrap="none", bg=C["bg4"], fg="#7ec8e3",
            font=("Consolas", 9), relief="flat",
            insertbackground=C["text"])
        sy = ttk.Scrollbar(af, orient="vertical", command=ta.yview)
        sx = ttk.Scrollbar(af, orient="horizontal", command=ta.xview)
        ta["yscrollcommand"] = sy.set; ta["xscrollcommand"] = sx.set
        ta.grid(row=0, column=0, sticky="nsew")
        sy.grid(row=0, column=1, sticky="ns")
        sx.grid(row=1, column=0, sticky="ew")
        for i, item in enumerate(self.stored):
            ta.insert(tk.END, f"// ─── Kayıt {i+1}: {item['dims']} | {item['bytes']} bytes ───\n")
            ta.insert(tk.END, item["code"] + "\n\n")
        ta.config(state="disabled")

        # Bireysel sekmeler
        for i, item in enumerate(self.stored):
            f = ttk.Frame(nb); nb.add(f, text=f"#{i+1} {item['dims']}")
            f.rowconfigure(0, weight=1); f.columnconfigure(0, weight=1)
            t = tk.Text(f, wrap="none", bg=C["bg4"], fg="#7ec8e3",
                font=("Consolas", 9), relief="flat",
                insertbackground=C["text"])
            sy2 = ttk.Scrollbar(f, orient="vertical", command=t.yview)
            sx2 = ttk.Scrollbar(f, orient="horizontal", command=t.xview)
            t["yscrollcommand"] = sy2.set; t["xscrollcommand"] = sx2.set
            t.grid(row=0, column=0, sticky="nsew")
            sy2.grid(row=0, column=1, sticky="ns")
            sx2.grid(row=1, column=0, sticky="ew")
            t.insert("1.0", item["code"])
            bf2 = ttk.Frame(f); bf2.grid(row=2, column=0, columnspan=2,
                sticky="ew", pady=4, padx=4)
            def _copy(code=item["code"]):
                self.root.clipboard_clear()
                self.root.clipboard_append(code)
                self.root.update()
                self._show_status("Kopyalandı ✓")
            ttk.Button(bf2, text="📋 Kopyala",
                style="Accent.TButton", command=_copy).pack(side="left", padx=4)

        # Alt çubuk
        bf3 = tk.Frame(win, bg=C["bg"]); bf3.pack(fill="x", padx=8, pady=(0,8))
        def copy_all():
            all_c = "\n\n".join(
                f"// ─── Kayıt {i+1}: {it['dims']} | {it['bytes']} bytes ───\n{it['code']}"
                for i, it in enumerate(self.stored))
            self.root.clipboard_clear()
            self.root.clipboard_append(all_c)
            self.root.update()
            self._show_status("Tümü kopyalandı ✓")
        ttk.Button(bf3, text="📋 Tümünü Kopyala",
            style="Accent.TButton", command=copy_all).pack(side="left", padx=(0,4))
        def clear_all():
            if messagebox.askyesno("Temizle", "Tüm depolananlar silinsin mi?", parent=win):
                self.stored = []
                self.stored_label.config(text="0 kayıt")
                win.destroy()
        ttk.Button(bf3, text="🗑 Tümünü Sil",
            style="Danger.TButton", command=clear_all).pack(side="left", padx=(0,4))
        ttk.Button(bf3, text="Kapat",
            command=win.destroy).pack(side="right", padx=4)

    # ══════════════════════════════════════════
    #  HEX YÜKLEME DİYALOĞU
    # ══════════════════════════════════════════
    def _open_hex_load_dialog(self):
        win = Toplevel(self.root)
        win.title("Hex'ten Yükle")
        win.geometry("560x400")
        win.configure(bg=C["bg"]); win.grab_set()
        apply_dark_style(win)

        tk.Label(win, text="Hex Kodu:", bg=C["bg"], fg=C["text2"],
                 font=("Segoe UI", 9)).pack(anchor="w", padx=12, pady=(10,2))
        ta = tk.Text(win, height=9, bg=C["bg4"], fg="#7ec8e3",
            font=("Consolas", 9), relief="flat",
            insertbackground=C["text"], padx=6, pady=4)
        ta.pack(fill="x", padx=12)

        row = tk.Frame(win, bg=C["bg"]); row.pack(fill="x", padx=12, pady=6)
        tk.Label(row, text="G:", bg=C["bg"], fg=C["text2"],
                 font=("Segoe UI", 9)).pack(side="left")
        wv = tk.StringVar(value=str(self.base_w))
        ttk.Entry(row, textvariable=wv, width=5).pack(side="left", padx=(2,10))
        tk.Label(row, text="Y:", bg=C["bg"], fg=C["text2"],
                 font=("Segoe UI", 9)).pack(side="left")
        hv = tk.StringVar(value=str(self.base_h))
        ttk.Entry(row, textvariable=hv, width=5).pack(side="left", padx=2)

        fmt_var = tk.StringVar(value=self.hex_fmt_var.get())
        tk.Label(win, text="Format:", bg=C["bg"], fg=C["text2"],
                 font=("Segoe UI", 9)).pack(anchor="w", padx=12)
        ttk.Combobox(win, textvariable=fmt_var,
            values=list(self.data_formats.keys()),
            state="readonly", width=28).pack(anchor="w", padx=12, pady=(0,8))

        err = tk.Label(win, text="", bg=C["bg"], fg=C["danger"],
            font=("Segoe UI", 9)); err.pack(anchor="w", padx=12)

        def _load():
            code = ta.get("1.0", "end").strip()
            try: lw = int(wv.get()); lh = int(hv.get())
            except: err.config(text="Genişlik/yükseklik sayısal olmalı"); return
            fmt = self.data_formats.get(fmt_var.get(), {})
            parse = fmt.get("parse")
            if not parse: err.config(text="Format hatası"); return
            try: bvals = parse(code)
            except Exception as e: err.config(text=str(e)); return
            mode = self.reading_modes.get(self.reading_order_var.get())
            if not mode: return
            grid = self._bytes_to_grid(bvals, lw, lh, mode)
            self.base_grid = grid
            self.base_w = lw; self.base_h = lh
            self.disp_w = lw; self.disp_h = lh
            self.width_var.set(str(lw)); self.height_var.set(str(lh))
            self.zoom = 1.0
            self.cell_w = self.base_canvas_size / lw
            self.cell_h = self.base_canvas_size / lh
            self._update_zoom_ui()
            self._record_history()
            self._transform_redraw()
            self._show_status(f"Hex yüklendi: {lw}×{lh} ✓")
            win.destroy()

        bf = tk.Frame(win, bg=C["bg"]); bf.pack(fill="x", padx=12, pady=4)
        ttk.Button(bf, text="Yükle",
            style="Accent.TButton", command=_load).pack(side="left", padx=(0,6))
        ttk.Button(bf, text="İptal",
            command=win.destroy).pack(side="left")

    # ══════════════════════════════════════════
    #  STATUS
    # ══════════════════════════════════════════
    def _show_status(self, msg, delay=2500):
        self.status_label.config(text=msg)
        self.root.after(delay, lambda: self.status_label.config(text=""))


# ═══════════════════════════════════════════════════
#  GİRİŞ NOKTASI
# ═══════════════════════════════════════════════════
if __name__ == "__main__":
    root = tk.Tk()
    app = PixelEditor(root)
    root.mainloop()