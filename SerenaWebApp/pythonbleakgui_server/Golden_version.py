import os

# --- Configuratie ---
INPUT_BESTAND = "analyse_report_20251203_113742.txt"
OUTPUT_BESTAND = "gefilterd_rapport.txt"
AFWIJKING_PERCENTAGE = 2.0  # Maximaal 5% afwijking

def parse_report(input_file, output_file):
    print(f"Start analyse van {input_file}...")
    
    # Opslag voor statistieken
    succesvolle_regels = []
    unieke_input_bestanden = set()
    versie_scores = {}  # Dictionary: {versie_naam: {set van input_bestanden}}

    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Fout: Kan bestand '{input_file}' niet vinden.")
        return

    # Header overslaan en verwerken
    header_found = False
    
    for line in lines:
        # Sla scheidingslijnen en headers over of lege regels
        if "---" in line or "BESTAND" in line or not line.strip():
            continue
        
        # Splits de regel op de pipe '|'
        parts = [p.strip() for p in line.split('|')]
        
        # We verwachten minstens 5 kolommen (Bestand, Versie, Target, Gem, Laatste 20)
        # Soms staat er een Delta kolom achter, maar die hebben we niet strikt nodig voor de berekening
        if len(parts) < 5:
            continue

        try:
            bestandsnaam = parts[0]
            versie = parts[1]
            target_str = parts[2]
            laatste_20_str = parts[4] # Dit is de 5e kolom (index 4)

            # Sla regels over waar data leeg is
            if not target_str or not laatste_20_str:
                continue

            target = float(target_str)
            calculated = float(laatste_20_str)

            # Bereken afwijking
            if target == 0:
                afwijking = 0 if calculated == 0 else 100
            else:
                diff = abs(calculated - target)
                afwijking = (diff / target) * 100

            # --- Logica: Input Bestand Groepering ---
            # We moeten weten bij welke "groep" dit bestand hoort.
            # We nemen de naam tot aan de timestamp (tweede underscore part of de datum)
            # Voorbeeld: ingest_20251101-1_0_1_0_20251203_08085 -> ID is ingest_20251101-1_0_1_0
            # Een simpele manier is splitten op '_20251203' (de datum van vandaag in je voorbeeld)
            # Of generieker: splitten op de laatste paar underscores.
            
            # Hier gebruiken we de target + eerste deel naam als unieke sleutel voor de "Test Set"
            # Omdat de bestandsnamen timestamps bevatten, strippen we de laatste timestamp.
            # We gaan ervan uit dat de "basisnaam" eindigt vóór de datum van de analyse (20251203).
            base_file_id = bestandsnaam.rsplit('_', 2)[0] 
            
            unieke_input_bestanden.add(base_file_id)

            # --- Logica: Filter < 5% ---
            if afwijking < AFWIJKING_PERCENTAGE:
                # Format: Bestand | Versie | Target | Calc | Afwijking %
                result_line = f"{bestandsnaam} | {versie} | Target: {target} | Calc: {calculated} | Dev: {afwijking:.2f}%"
                succesvolle_regels.append(result_line)

                # Update de score voor deze versie
                if versie not in versie_scores:
                    versie_scores[versie] = set()
                versie_scores[versie].add(base_file_id)

        except ValueError:
            # Skip regels die niet naar float geconverteerd kunnen worden
            continue

    # --- Analyseer de winnaars ---
    totaal_input_bestanden = len(unieke_input_bestanden)
    perfecte_versies = []

    for versie, passed_files in versie_scores.items():
        if len(passed_files) == totaal_input_bestanden:
            perfecte_versies.append(versie)

    # --- Schrijven naar output ---
    with open(output_file, 'w', encoding='utf-8') as out:
        out.write(f"ANALYSE RAPPORT - Filter: < {AFWIJKING_PERCENTAGE}% afwijking\n")
        out.write("=======================================================\n\n")
        
        out.write(f"Aantal unieke input scenario's gevonden: {totaal_input_bestanden}\n")
        out.write(f"Input groepen: {', '.join(unieke_input_bestanden)}\n\n")

        out.write("--- DE WINNAARS (Versies die slagen voor ALLE input scenario's) ---\n")
        if perfecte_versies:
            for v in sorted(perfecte_versies):
                out.write(f"[WINNER] {v}\n")
        else:
            out.write("Geen enkele versie scoorde < 5% op alle bestanden.\n")
        
        out.write("\n--- DETAIL REGELS (Alle geslaagde pogingen) ---\n")
        out.write(f"{'Bestand':<50} | {'Versie':<15} | {'Target':<10} | {'Calc':<10} | {'Dev %':<10}\n")
        out.write("-" * 110 + "\n")
        
        for line in succesvolle_regels:
            # We splitsen de opgemaakte string weer even voor nette uitlijning in text file
            # Dit is puur cosmetisch
            parts = line.split('|')
            out.write(f"{parts[0].strip():<50} | {parts[1].strip():<15} | {parts[2].strip():<10} | {parts[3].strip():<10} | {parts[4].strip():<10}\n")

    print(f"Klaar! Resultaat opgeslagen in '{output_file}'.")
    print(f"Gevonden 'Perfecte Versies': {len(perfecte_versies)}")

if __name__ == "__main__":
    # Controleer of het bestand bestaat, maak eventueel een dummy bestand aan als test
    if not os.path.exists(INPUT_BESTAND):
        print(f"Let op: bestand '{INPUT_BESTAND}' niet gevonden in huidige map.")
    else:
        parse_report(INPUT_BESTAND, OUTPUT_BESTAND)