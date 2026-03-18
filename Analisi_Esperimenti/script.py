import os
import json
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import statsmodels.api as sm
from statsmodels.formula.api import ols

# --- 1. CONFIGURAZIONE ---
BASE_PATH = "/Users/antoniopepe/Desktop/Tesi/Esperimenti"

OUTPUT_DIR = "Analisi_Esperimenti_Payload"
OUTPUT_EXCEL_NAME = "Analisi_Avanzata_Payload_ProStyle.xlsx"

FOLDERS_CONFIG = {
    "results_json":  {"Delay": 0,  "Cooldown": "No (Base)"},
    "results_json2": {"Delay": 0,  "Cooldown": "Si (10s)"},
    "results_json3": {"Delay": 20, "Cooldown": "No (Base)"},
    "results_json4": {"Delay": 20, "Cooldown": "Si (10s)"}
}

IMPLEMENTATIONS = ["quiche_version", "openSSL_version", "ngtcp2_version"]
PAYLOADS = ["file_128b", "file_1k", "file_8k", "file_64k", "file_512k", "file_4m"]
METRICS = ["energy", "time"]

IMPL_LABELS = {
    "quiche_version": "Quiche", 
    "openSSL_version": "OpenSSL", 
    "ngtcp2_version": "ngtcp2"
}

# --- MAPPATURA ESATTA DEI COLORI (Colori MATLAB standard) ---
COLOR_MAPPING = {
    "Quiche": "#0072BD",   # Blu
    "OpenSSL": "#D95319",  # Arancione
    "ngtcp2": "#EDB120"    # Giallo Senape
}

def set_original_style():
    """Ripristina lo stile grafico originale (font, griglia, box)"""
    plt.rcParams['font.family'] = 'serif'
    plt.rcParams['font.serif'] = ['Times New Roman', 'DejaVu Serif', 'serif']
    plt.rcParams['font.size'] = 12
    plt.rcParams['axes.linewidth'] = 1.0
    plt.rcParams['grid.alpha'] = 0.5
    plt.rcParams['grid.linestyle'] = ':'
    sns.set_style("ticks") 

def load_data():
    all_data = []
    print(f"--- Caricamento dati da: {BASE_PATH} ---")
    
    for folder, config in FOLDERS_CONFIG.items():
        folder_path = os.path.join(BASE_PATH, folder)
        if not os.path.exists(folder_path): continue

        for impl in IMPLEMENTATIONS:
            for payload in PAYLOADS:
                for metric in METRICS:
                    filename = f"{metric}_{impl}_{payload}.json"
                    filepath = os.path.join(folder_path, filename)
                    
                    if os.path.exists(filepath):
                        try:
                            with open(filepath, 'r') as f:
                                content = json.load(f)
                            if isinstance(content, list):
                                flat_data = []
                                for item in content:
                                    if isinstance(item, list): flat_data.extend(item)
                                    else: flat_data.append(item)
                                content = flat_data
                            
                            for val in content:
                                if isinstance(val, (int, float)) and val > 0: # Assicurarsi che i valori siano > 0 per il log
                                    all_data.append({
                                        "Scenario": f"Delay {config['Delay']}ms - Cooldown {config['Cooldown']}",
                                        "Delay": config["Delay"],
                                        "Cooldown": config["Cooldown"],
                                        "Metrica": "Energia" if metric == "energy" else "Tempo",
                                        "Valore": val,
                                        "Implementazione": IMPL_LABELS.get(impl, impl),
                                        "Payload": payload.replace("file_", "")
                                    })
                        except Exception: 
                            pass
                            
    return pd.DataFrame(all_data)

def main():
    if not os.path.exists(OUTPUT_DIR):
        try: os.makedirs(OUTPUT_DIR)
        except Exception: return

    df = load_data()
    if df.empty:
        print("❌ Nessun dato trovato nei percorsi specificati.")
        return

    set_original_style()
    anova_results_list = []
    
    clean_payloads = [p.replace("file_", "") for p in PAYLOADS]

    print(f"\n--- Generazione Grafici con Scala Logaritmica ---")

    scenari = df["Scenario"].unique()
    metriche = df["Metrica"].unique()

    for metrica in metriche:
        for scenario in scenari:
            subset = df[(df["Metrica"] == metrica) & (df["Scenario"] == scenario)].copy()
            if subset.empty: continue
            
            safe_scenario_name = scenario.replace(" ", "_").replace("-", "").replace("(", "").replace(")", "")
            print(f" -> Elaborazione {metrica} - {scenario}...")

            fig, ax = plt.subplots(figsize=(8, 5))
            
            # 1. PUNTI SPARSI
            sns.stripplot(
                data=subset, 
                x="Payload", 
                y="Valore", 
                hue="Implementazione", 
                order=clean_payloads,
                palette=COLOR_MAPPING,
                dodge=True,        
                jitter=True,       
                alpha=0.5,         
                size=4,            
                linewidth=0.3,     
                edgecolor="white", 
                ax=ax,
                zorder=1           
            )

            # 2. LINEA CENTRALE (Linee sottili)
            sns.pointplot(
                data=subset, 
                x="Payload", 
                y="Valore", 
                hue="Implementazione", 
                order=clean_payloads,
                palette=COLOR_MAPPING,
                dodge=True,
                markers="o",       
                linewidth=1.2,     
                markersize=6,      
                err_kws={'linewidth': 1.0},
                ax=ax,
                zorder=2           
            )

            handles, labels = ax.get_legend_handles_labels()
            # Manteniamo solo le prime N etichette
            n_impl = len(subset['Implementazione'].unique())
            ax.legend(handles[:n_impl], labels[:n_impl], title="Implementazione", bbox_to_anchor=(1.05, 1), loc='upper left')

            # --- APPLICAZIONE SCALA LOGARITMICA ---
            ax.set_yscale('log')
            
            y_label = "Energia (Joule) - Scala Log" if metrica == "Energia" else "Tempo (Secondi) - Scala Log"
            ax.set_ylabel(y_label)
            ax.set_xlabel("Dimensione Payload")
            ax.set_title(f"Analisi {metrica} - {scenario}", y=1.05, fontsize=14, weight='bold')
            
            # Griglia ottimizzata per scala logaritmica (mostra anche le righe secondarie minori)
            ax.grid(True, which='major', linestyle='-', alpha=0.6)
            ax.grid(True, which='minor', linestyle=':', alpha=0.4)
            
            for spine in ax.spines.values():
                spine.set_edgecolor('black')
                spine.set_linewidth(1)
                spine.set_visible(True)

            plt.xticks(rotation=45)
            plt.tight_layout()

            # Salvataggio
            save_path = os.path.join(OUTPUT_DIR, f"Fig_Log_{metrica}_{safe_scenario_name}.pdf")
            fig.savefig(save_path, format='pdf', bbox_inches='tight')
            plt.close()

            # --- STATISTICA ---
            try:
                model = ols('Valore ~ C(Payload) * C(Implementazione)', data=subset).fit()
                anova = sm.stats.anova_lm(model, typ=2)
                res_row = {
                    "Metrica": metrica, "Scenario": scenario,
                    "P-Val Payload": anova.loc['C(Payload)', 'PR(>F)'],
                    "P-Val Impl": anova.loc['C(Implementazione)', 'PR(>F)'],
                    "P-Val Interazione": anova.loc['C(Payload):C(Implementazione)', 'PR(>F)']
                }
                anova_results_list.append(res_row)
            except Exception: pass

    # --- EXCEL ---
    excel_path = os.path.join(OUTPUT_DIR, OUTPUT_EXCEL_NAME)
    print(f"\n--- Creazione Excel: {excel_path} ---")
    
    try:
        with pd.ExcelWriter(excel_path, engine='xlsxwriter') as writer:
            workbook = writer.book
            fmt_header = workbook.add_format({'bold': True, 'bg_color': '#34495E', 'font_color': 'white', 'border': 1, 'align': 'center'})
            fmt_sig_good = workbook.add_format({'bg_color': '#E8F8F5', 'font_color': '#117864', 'border': 1}) 
            fmt_sig_bad = workbook.add_format({'bg_color': '#FDEDEC', 'font_color': '#922B21', 'border': 1})  

            df_energy = df[df["Metrica"] == "Energia"]
            if not df_energy.empty:
                pivot_energy = df_energy.groupby(['Scenario', 'Implementazione', 'Payload'])['Valore'].mean().unstack('Payload')
                pivot_energy = pivot_energy[[p for p in clean_payloads if p in pivot_energy.columns]]
                pivot_energy.to_excel(writer, sheet_name='Medie Energia')
                writer.sheets['Medie Energia'].set_column(0, 1, 25)

            df_time = df[df["Metrica"] == "Tempo"]
            if not df_time.empty:
                pivot_time = df_time.groupby(['Scenario', 'Implementazione', 'Payload'])['Valore'].mean().unstack('Payload')
                pivot_time = pivot_time[[p for p in clean_payloads if p in pivot_time.columns]]
                pivot_time.to_excel(writer, sheet_name='Medie Tempo')
                writer.sheets['Medie Tempo'].set_column(0, 1, 25)

            if len(anova_results_list) > 0:
                df_res = pd.DataFrame(anova_results_list)
                df_res.replace([np.inf, -np.inf], np.nan, inplace=True)
                df_res.fillna("N/A", inplace=True)
                df_res.to_excel(writer, sheet_name='Statistica ANCOVA', index=False)
                
                if 'Statistica ANCOVA' in writer.sheets:
                    ws2 = writer.sheets['Statistica ANCOVA']
                    for col_num, value in enumerate(df_res.columns.values):
                        ws2.write(0, col_num, value, fmt_header)
                        ws2.set_column(col_num, col_num, 20)

                    ws2.conditional_format(1, 2, len(df_res), len(df_res.columns)-1, {
                        'type': 'cell', 'criteria': '<', 'value': 0.05, 'format': fmt_sig_good
                    })
                    ws2.conditional_format(1, 2, len(df_res), len(df_res.columns)-1, {
                        'type': 'cell', 'criteria': '>=', 'value': 0.05, 'format': fmt_sig_bad
                    })

    except Exception as e:
        print(f"❌ Errore Excel finale: {e}")

if __name__ == "__main__":
    main()