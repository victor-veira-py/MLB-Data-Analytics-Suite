import requests
import pandas as pd

# =============================================================================
# CONFIGURATION: ELITE PLAYER LIST / CONFIGURACIÓN: LISTA DE JUGADORES ÉLITE
# =============================================================================
# This script generates individual reports for each ID in the list.
# Este script genera reportes individuales por cada ID en la lista.
lista_jugadores_mlb = [
    "660670", "514888", "650333", "545361", "592518",
    "660271", "665742", "521692", "596019", "650402", "547180"
]


def generar_reporte_mlb_limpio(player_id):
    """
    Extracts data from MLB StatsAPI, calculates career totals, and
    generates an individual Excel file with professional executive formatting.

    Extrae datos de la MLB StatsAPI, calcula totales de carrera y
    genera un archivo Excel individual con formato ejecutivo profesional.
    """
    try:
        # 1. Player basic data retrieval / Obtención de datos básicos del jugador
        info = requests.get(f"https://statsapi.mlb.com/api/v1/people/{player_id}").json()
        nombre = info["people"][0].get("fullName", "Jugador")

        # Query year-by-year historical statistics / Consulta de estadísticas históricas año por año
        url = f"https://statsapi.mlb.com/api/v1/people/{player_id}/stats?stats=yearByYear&group=hitting&sportIds=1"
        data = requests.get(url).json()

        if "stats" not in data or not data["stats"][0]["splits"]: return

        splits = data["stats"][0]["splits"]
        lista_temporadas = []

        def fmt_mlb(valor):
            """Formats percentages to MLB standard (.XXX) / Formatea porcentajes al estándar MLB (.XXX)"""
            try:
                return f"{float(valor):.3f}".replace("0.", ".")
            except:
                return ".000"

        # 2. Season-by-season statistics processing / Procesamiento de estadísticas por temporada
        for s in splits:
            stat = s.get("stat", {})
            ab = int(stat.get("atBats", 0))
            if ab == 0: continue

            # Team name management (Handling team change splits) / Gestión de nombres de equipo
            equipo = s.get("team", {}).get("name", "---")
            if equipo == "---": equipo = "TOTAL"

            lista_temporadas.append({
                "TEMPORADA": int(s.get("season")),
                "EQUIPO": equipo,
                "J": int(stat.get("gamesPlayed", 0)), "AB": ab, "R": int(stat.get("runs", 0)),
                "H": int(stat.get("hits", 0)), "2B": int(stat.get("doubles", 0)),
                "3B": int(stat.get("triples", 0)), "HR": int(stat.get("homeRuns", 0)),
                "RBI": int(stat.get("rbi", 0)), "BB": int(stat.get("baseOnBalls", 0)),
                "HBP": int(stat.get("hitByPitch", 0)), "K": int(stat.get("strikeOuts", 0)),
                "SB": int(stat.get("stolenBases", 0)), "CS": int(stat.get("caughtStealing", 0)),
                # Stored as float for CAREER row calculations / Guardamos como float para el cálculo de CARRERA
                "AVG": float(stat.get("avg", 0)), "OBP": float(stat.get("obp", 0)),
                "SLG": float(stat.get("slg", 0)), "OPS": float(stat.get("ops", 0))
            })

        df = pd.DataFrame(lista_temporadas)

        # 3. CAREER Row Calculation (Sums and Averages) / Cálculo de Fila CARRERA (Sumatorias y Promedios)
        df_base = df[df["EQUIPO"] != "TOTAL"]

        fila_carrera = {
            "TEMPORADA": "", "EQUIPO": "CARRERA",
            "J": df_base["J"].sum(), "AB": df_base["AB"].sum(), "R": df_base["R"].sum(),
            "H": df_base["H"].sum(), "2B": df_base["2B"].sum(), "3B": df_base["3B"].sum(),
            "HR": df_base["HR"].sum(), "RBI": df_base["RBI"].sum(), "BB": df_base["BB"].sum(),
            "HBP": df_base["HBP"].sum(), "K": df_base["K"].sum(), "SB": df_base["SB"].sum(),
            "CS": df_base["CS"].sum(),
            "AVG": df_base["H"].sum() / df_base["AB"].sum() if df_base["AB"].sum() > 0 else 0,
            "OBP": df_base["OBP"].mean(), "SLG": df_base["SLG"].mean(), "OPS": df_base["OPS"].mean()
        }

        # Consolidate data and apply MLB formatting (.XXX) / Consolidar datos y aplicar formato MLB (.XXX)
        df = pd.concat([df, pd.DataFrame([fila_carrera])], ignore_index=True)
        for col in ["AVG", "OBP", "SLG", "OPS"]:
            df[col] = df[col].apply(fmt_mlb)

        # 4. Excel Configuration with Executive Styling / Configuración de Excel con Estilo Ejecutivo
        nombre_archivo = f"Reporte_Individual_{nombre.replace(' ', '_')}.xlsx"

        with pd.ExcelWriter(nombre_archivo, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Estadisticas', index=False)
            workbook = writer.book
            worksheet = writer.sheets['Estadisticas']

            # Cell Formats (Professional Blue and Gray for Totals) / Formatos de Celda (Azul y Gris)
            header_fmt = workbook.add_format(
                {'bold': True, 'align': 'center', 'bg_color': '#1F4E78', 'font_color': '#FFFFFF', 'border': 1})
            data_fmt = workbook.add_format({'align': 'center', 'border': 1, 'border_color': '#D9D9D9'})
            total_fmt = workbook.add_format({'bold': True, 'bg_color': '#F2F2F2', 'align': 'center', 'border': 1})

            worksheet.hide_gridlines(2)
            worksheet.ignore_errors({'number_stored_as_text': f'A2:T{len(df) + 1}'})

            # Dynamic column adjustment / Ajuste dinámico de columnas
            for i, col in enumerate(df.columns):
                ancho = max(df[col].astype(str).map(len).max(), len(str(col))) + 3
                worksheet.set_column(i, i, ancho, data_fmt)
                worksheet.write(0, i, col, header_fmt)

            # Apply distinctive style to final CAREER row / Estilo distintivo para la fila final de CARRERA
            idx_ultima = len(df)
            for i in range(len(df.columns)):
                worksheet.write(idx_ultima, i, df.iloc[-1, i], total_fmt)

        print(f"✅ [SYSTEM] INDIVIDUAL REPORT GENERATED: {nombre_archivo}")

    except Exception as e:
        print(f"❌ [ERROR] Processing ID {player_id}: {e}")


if __name__ == "__main__":
    # Batch execution of individual reports / Ejecución masiva de reportes individuales
    for id_j in lista_jugadores_mlb:
        generar_reporte_mlb_limpio(id_j)