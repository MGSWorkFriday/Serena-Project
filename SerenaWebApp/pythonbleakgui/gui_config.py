# gui_config.py
import flet as ft
import requests

SERVER_URL = "http://localhost:8000"  # Pas aan indien nodig

class FeedbackConfigDialog(ft.AlertDialog):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.title = ft.Text("Feedback & Audio Instellingen")
        self.modal = True
        
        # Data container
        self.rules_data = {}
        
        # UI Elementen
        self.tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[]
        )
        self.content = ft.Container(
            content=self.tabs, 
            width=600, 
            height=400,
            padding=10
        )
        
        self.actions = [
            ft.TextButton("Annuleren", on_click=self.close_dlg),
            ft.ElevatedButton("Opslaan", on_click=self.save_rules)
        ]
        
        # Laad data bij initialisatie
        self.load_rules()

    def load_rules(self):
        try:
            r = requests.get(f"{SERVER_URL}/feedback/rules", timeout=2)
            if r.status_code == 200:
                self.rules_data = r.json()
                self.build_form()
            else:
                self.content = ft.Text(f"Fout bij laden: {r.status_code}")
        except Exception as e:
            self.content = ft.Text(f"Verbindingsfout: {e}")

    def build_form(self):
        # We maken tabbladen voor elke categorie (Blue, Green, etc)
        # Mapping voor mooie namen
        labels = {
            "blue": "Start (Blauw)",
            "green": "Goed (Groen)",
            "orange": "Let op (Oranje)",
            "red_fast": "Te Snel (Rood)",
            "red_slow": "Te Traag (Rood)"
        }
        
        self.tabs.tabs.clear()
        
        for key, config in self.rules_data.items():
            friendly_name = labels.get(key, key)
            
            # Lijst met tekstvelden voor de berichten
            msg_controls = []
            if "messages" in config:
                for idx, msg in enumerate(config["messages"]):
                    txt_field = ft.TextField(
                        label=f"Bericht {idx+1}", 
                        value=msg.get("text", ""),
                        multiline=False,
                        data={"cat": key, "idx": idx} # Metadata om terug te vinden
                    )
                    msg_controls.append(txt_field)
            
            # Voeg een knop toe om regels toe te voegen (simpel gehouden: lege velden negeren we bij save)
            
            col = ft.Column(
                controls=[
                    ft.Text(f"Instellingen voor '{friendly_name}'", size=16, weight="bold"),
                    ft.Divider(),
                    *msg_controls,
                    ft.Text("Tip: Laat een veld leeg om bericht te verwijderen.", size=12, italic=True)
                ],
                scroll="auto"
            )
            
            self.tabs.tabs.append(ft.Tab(text=friendly_name, content=col))
        
        self.page.update()

    def save_rules(self, e):
        # We reconstrueren de JSON uit de inputs
        # Loop door alle Tabs -> Column -> Controls
        for tab in self.tabs.tabs:
            col = tab.content
            for ctrl in col.controls:
                if isinstance(ctrl, ft.TextField) and ctrl.data:
                    cat = ctrl.data["cat"]
                    idx = ctrl.data["idx"]
                    new_val = ctrl.value.strip()
                    
                    # Update in lokale data
                    if new_val:
                        self.rules_data[cat]["messages"][idx]["text"] = new_val
                    else:
                        # Als leeg gemaakt, zet placeholder (server kan schonen als nodig)
                        self.rules_data[cat]["messages"][idx]["text"] = "..."

        # Stuur naar server
        try:
            r = requests.post(f"{SERVER_URL}/feedback/rules", json=self.rules_data)
            if r.status_code == 200:
                self.page.show_snack_bar(ft.SnackBar(content=ft.Text("Regels opgeslagen!")))
                self.close_dlg(None)
            else:
                self.page.show_snack_bar(ft.SnackBar(content=ft.Text("Fout bij opslaan.")))
        except Exception as ex:
             self.page.show_snack_bar(ft.SnackBar(content=ft.Text(f"Error: {ex}")))

    def close_dlg(self, e):
        self.open = False
        self.page.update()

def open_config_dialog(page: ft.Page):
    dlg = FeedbackConfigDialog(page)
    page.dialog = dlg
    dlg.open = True
    page.update()