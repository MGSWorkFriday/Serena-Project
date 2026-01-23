# theme.py
from tkinter import ttk

def apply_dark_theme(root, listbox, text_box, alerts_text, figures, axes):
    """
    Past dark theme toe op de gegeven widgets en matplotlib figuren.
    figures: lijst met [ecg_fig, breath_fig]
    axes: lijst met [ax, ax2, breath_ax, ax2_breath]
    """
    # Kleurdefinitie
    BG_DARK = '#2e2e2e'
    FG_LIGHT = '#ffffff'
    INPUT_BG = '#3c3c3c'
    PLOT_BG = '#1e1e1e'
    ACCENT_BLUE = '#4a90e2' # Scan, Save, Accent
    ACCENT_GREEN = '#2ecc71' # Start
    ACCENT_RED = '#e74c3c' # Stop
    
    # 1. Root window
    root.tk_setPalette(background=BG_DARK, foreground=FG_LIGHT, activeBackground=INPUT_BG, activeForeground=FG_LIGHT)
    root.configure(bg=BG_DARK)
    
    style = ttk.Style(root)
    style.theme_use('clam') 
    
    # 2. Algemene stijlen
    style.configure("TFrame", background=BG_DARK)
    style.configure("TLabelframe", background=BG_DARK, foreground=FG_LIGHT, bordercolor=INPUT_BG)
    style.configure("TLabelframe.Label", background=BG_DARK, foreground=FG_LIGHT)
    style.configure("TLabel", background=BG_DARK, foreground=FG_LIGHT)
    style.configure("TCheckbutton", background=BG_DARK, foreground=FG_LIGHT, indicatorcolor=INPUT_BG)
    style.configure("TEntry", fieldbackground=INPUT_BG, foreground=FG_LIGHT, bordercolor=INPUT_BG)

    # 3. Knoppen
    style.configure("TButton", background=INPUT_BG, foreground=FG_LIGHT, borderwidth=1, focuscolor=ACCENT_BLUE)
    style.map("TButton", background=[('active', INPUT_BG)]) 
    
    style.configure("Blue.TButton", background=ACCENT_BLUE, foreground=FG_LIGHT)
    style.map("Blue.TButton", background=[('active', '#5DADE2')], foreground=[('active', FG_LIGHT)])

    style.configure("Green.TButton", background=ACCENT_GREEN, foreground=FG_LIGHT)
    style.map("Green.TButton", background=[('active', '#27AE60')], foreground=[('active', FG_LIGHT)])
    
    style.configure("Red.TButton", background=ACCENT_RED, foreground=FG_LIGHT)
    style.map("Red.TButton", background=[('active', '#C0392B')], foreground=[('active', FG_LIGHT)])

    # 4. Widgets handmatig
    listbox.configure(bg=INPUT_BG, fg=FG_LIGHT, selectbackground=ACCENT_BLUE, selectforeground=FG_LIGHT, borderwidth=0)
    text_box.configure(bg=INPUT_BG, fg=FG_LIGHT, borderwidth=0, insertbackground=FG_LIGHT)
    
    alerts_text.configure(bg=INPUT_BG, fg=FG_LIGHT, borderwidth=0, insertbackground=FG_LIGHT)
    alerts_text.tag_configure("info", foreground="#5DADE2") 
    alerts_text.tag_configure("warn", foreground="#F39C12")
    alerts_text.tag_configure("error", foreground="#E74C3C")

    # 5. Treeview
    style.configure("Treeview", background=INPUT_BG, foreground=FG_LIGHT, fieldbackground=INPUT_BG, rowheight=25, bordercolor=BG_DARK)
    style.map("Treeview", background=[('selected', ACCENT_BLUE)], foreground=[('selected', FG_LIGHT)])
    style.configure("Treeview.Heading", background=BG_DARK, foreground=FG_LIGHT)
    
    # 6. Matplotlib Grafieken
    for fig in figures:
        fig.patch.set_facecolor(PLOT_BG)
        
    for ax in axes:
        ax.set_facecolor(PLOT_BG)
        ax.tick_params(axis='x', colors=FG_LIGHT)
        ax.tick_params(axis='y', colors=FG_LIGHT)
        ax.spines['left'].set_color(FG_LIGHT)
        ax.spines['bottom'].set_color(FG_LIGHT)
        if ax.get_title():
            ax.set_title(ax.get_title(), color=FG_LIGHT)