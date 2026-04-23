import requests
import pandas as pd

# =============================================================================
# GLOBAL ID CONFIGURATION (MLB IDs) / CONFIGURACIÓN GLOBAL DE IDENTIFICADORES
# =============================================================================
# Curated list of official MLB IDs for elite players.
# Lista curada de IDs oficiales de MLB para jugadores élite.
lista_ids = [
    "592450", "660670", "605141", "571448", "518692",
    "608070", "608324", "660271", "514888", "663586",
    "650333", "592518"
]


def obtener_data_perfecta(player_id):
    """
    Extracts, processes, and formats historical hitting statistics
    from the official MLB API (StatsAPI).

    Extrae, procesa y formatea las estadísticas históricas de bateo
    desde la API oficial de MLB (StatsAPI).
    """
    try:
        # Basic player metadata retrieval / Recuperación de metadatos básicos
        info = requests.get(f"https://statsapi.mlb.com/api/v1/people/{player_id}").json()
        nombre_completo = info["people"][0].get("fullName", "Jugador")

        # Name standardization for Excel tabs / Estandarización de nombres para pestañas
        # Special case handling for special characters and length limits
        # Manejo de casos especiales para caracteres especiales y límites de longitud
        if "Acuña" in nombre_completo:
            nombre_pestaña = "Acuna Jr"
        else:
            nombre_pestaña = nombre_completo.split()[-1][:31]

        # Year-by-Year aggregated stats query / Consulta de estadísticas por temporada
        url = f"https://statsapi.mlb.com/api/v1/people/{player_id}/stats?stats=yearByYear&group=hitting&sportIds=1"
        data = requests.get(url).json()

        if "stats" not in data or not data["stats"][0]["splits"]:
            return None, None

        splits = data["stats"][0]["splits"]

        def fmt_mlb(valor):
            """Applies MLB standard format for percentages (.XXX) / Formato estándar MLB"""
            try:
                return f"{float(valor):.3f}".replace("0.", ".")
            except:
                return ".000"

        lista_temporadas = []
        for s in splits:
            stat = s.get("stat", {})
            ab = int(stat.get("atBats", 0))
            if ab == 0: continue

            # Annual Summary Management / Gestión de Resúmenes Anuales:
            # When a player moves between teams, the API returns a '---' or empty team split.
            # Cuando un jugador cambia de equipo, la API devuelve un split vacío o con '---'.
            nombre_equipo = s.get("team", {}).get("name", "---")
            if nombre_equipo == "---":
                nombre_equipo = "TOTAL"

            lista_temporadas.append({
                "AÑO": int(s.get("season")),
                "EQUIPO": nombre_equipo,
                "J": int(stat.get("gamesPlayed", 0)), "AB": ab, "R": int(stat.get("runs", 0)),
                "H": int(stat.get("hits", 0)), "2B": int(stat.get("doubles", 0)),
                "3B": int(stat.get("triples", 0)), "HR": int(stat.get("homeRuns", 0)),
                "RBI": int(stat.get("rbi", 0)), "BB": int(stat.get("baseOnBalls", 0)),
                "HBP": int(stat.get("hitByPitch", 0)), "K": int(stat.get("strikeOuts", 0)),
                "SB": int(stat.get("stolenBases", 0)), "CS": int(stat.get("caughtStealing", 0)),
                "AVG": float(stat.get("avg", 0)), "OBP": float(stat.get("obp", 0)),
                "SLG": float(stat.get("slg", 0)), "OPS": float(stat.get("ops", 0))
            })

        df = pd.DataFrame(lista_temporadas)

        # Aggregated Career Stats Calculation / Cálculo de Estadísticas de Carrera:
        # 'TOTAL' rows are filtered to avoid duplicate counts in the summation.
        # Se filtran las filas 'TOTAL' para evitar duplicidad en la sumatoria.
        df_solo_equipos = df[df["EQUIPO"] != "TOTAL"]

        fila_totales = {
            "AÑO": "",  # Empty cell for visual aesthetics / Celda vacía por estética
            "EQUIPO": "CARRERA",
            "J": df_solo_equipos["J"].sum(), "AB": df_solo_equipos["AB"].sum(),
            "R": df_solo_equipos["R"].sum(), "H": df_solo_equipos["H"].sum(),
            "2B": df_solo_equipos["2B"].sum(), "3B": df_solo_equipos["3B"].sum(),
            "HR": df_solo_equipos["HR"].sum(), "RBI": df_solo_equipos["RBI"].sum(),
            "BB": df_solo_equipos["BB"].sum(), "HBP": df_solo_equipos["HBP"].sum(),
            "K": df_solo_equipos["K"].sum(), "SB": df_solo_equipos["SB"].sum(),
            "CS": df_solo_equipos["CS"].sum(),
            "AVG": df_solo_equipos["H"].sum() / df_solo_equipos["AB"].sum() if df_solo_equipos["AB"].sum() > 0 else 0,
            "OBP": df_solo_equipos["OBP"].mean(), "SLG": df_solo_equipos["SLG"].mean(),
            "OPS": df_solo_equipos["OPS"].mean()
        }

        # Final consolidation and MLB string formatting / Consolidación y formato final
        df = pd.concat([df, pd.DataFrame([fila_totales])], ignore_index=True)
        for col in ["AVG", "OBP", "SLG", "OPS"]:
            df[col] = df[col].apply(fmt_mlb)

        return nombre_pestaña, df
    except Exception as e:
        print(f"❌ [ERROR] Could not process ID {player_id}: {e}")
        return None, None


# =============================================================================
# MAIN EXECUTION & EXCEL GENERATION / EJECUCIÓN Y GENERACIÓN DE EXCEL
# =============================================================================
if __name__ == "__main__":
    nombre_archivo = "MLB_Elite_Stats_Report.xlsx"

    with pd.ExcelWriter(nombre_archivo, engine='xlsxwriter') as writer:
        workbook = writer.book

        # Professional Style Definitions / Definición de estilos profesionales
        f_header = workbook.add_format({
            'bold': True, 'bg_color': '#1F4E78', 'font_color': 'white',
            'align': 'center', 'border': 1
        })
        f_data = workbook.add_format({
            'align': 'center', 'border': 1, 'border_color': '#D9D9D9'
        })
        f_total = workbook.add_format({
            'bold': True, 'bg_color': '#F2F2F2', 'align': 'center', 'border': 1
        })

        for pid in lista_ids:
            pestaña, df = obtener_data_perfecta(pid)
            if df is not None:
                # Export data to individual sheet / Exportación a hoja individual
                df.to_excel(writer, sheet_name=pestaña, index=False)
                worksheet = writer.sheets[pestaña]
                worksheet.hide_gridlines(2)

                # Ignore Excel warnings for numbers as text / Ignorar advertencias de Excel
                worksheet.ignore_errors({'number_stored_as_text': f'A2:T{len(df) + 1}'})

                # Dynamic column adjustment and styling / Ajuste de columnas y estilos
                for i, col in enumerate(df.columns):
                    ancho = max(df[col].astype(str).map(len).max(), len(col)) + 3
                    worksheet.set_column(i, i, ancho, f_data)
                    worksheet.write(0, i, col, f_header)

                # Distinctive style for CAREER row / Estilo para fila de CARRERA
                idx_ultima = len(df)
                for i in range(len(df.columns)):
                    worksheet.write(idx_ultima, i, df.iloc[-1, i], f_total)

    print(f"\n🚀 [SYSTEM] MLB Stats Report generated successfully: {nombre_archivo}")
    print("[INFO] All IDs in configuration list processed / Todos los IDs procesados.")