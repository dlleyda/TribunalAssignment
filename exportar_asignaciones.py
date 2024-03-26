
import pandas as pd
import re

def get_presidente_secretario(profesor1, profesor2):
    peso_titulaciones = {"L":0, "D":1, "DS":2, "DA":3, "DAS":4}
    dict_presi_secre = {"Presidente": None, "Secretario": None}
    # Expresión regular para encontrar palabras entre paréntesis
    expresion_regular = r'\((.*?)\)'

    # Encontrar todas las coincidencias en el texto
    titulacion1 = re.findall(expresion_regular, profesor1)[0]
    titulacion2 = re.findall(expresion_regular, profesor2)[0]
    
    if peso_titulaciones[titulacion1] > peso_titulaciones[titulacion2]:
        return {"Presidente": profesor1, "Secretario": profesor2}
    elif peso_titulaciones[titulacion1] < peso_titulaciones[titulacion2]:
        return {"Presidente": profesor2, "Secretario": profesor1}
    else:
        return {"Presidente": profesor1, "Secretario": profesor2}

async def generate_excel(data, start_date, end_date):
    date_range = pd.date_range(start=start_date, end=end_date)
    # Create an Excel writer object
    writer = pd.ExcelWriter('asignaciones.xlsx', engine='xlsxwriter')
    
    # Iterate through each day in the date range
    dfs_dias = []
    
    for date in date_range:
        # Filter data for the current day
        df = pd.DataFrame(columns=['Presidente', 'Secretario', 'Estudiante', 'Horario'])
        df_anteriores = []
        for weight in data.keys():
            for profesor, tribunales in data[weight].items():
                for tribunal in tribunales:
                    
                    hora_comienzo_tribunal = tribunal["Tribunal"]["intervalo"][0]
                    hora_fin_tribunal = tribunal["Tribunal"]["intervalo"][1]
                    
                    hora_comienzo_str = hora_comienzo_tribunal.isoformat(timespec="minutes")
                    hora_fin_str = hora_fin_tribunal.isoformat(timespec="minutes")

                    str_hora_tribunal = hora_comienzo_str.split("T")[1] + " - " + hora_fin_str.split("T")[1]
                    dia_tribunal = hora_comienzo_str.split("T")[0]

                    if dia_tribunal != str(date.date()):
                        continue

                    puestos = get_presidente_secretario(tribunal['Tribunal']['profesor1'], tribunal['Tribunal']['profesor2'])
                    presidente = puestos["Presidente"]
                    secretario = puestos["Secretario"]
                        
                    dict_para_df = {
                        'Presidente': presidente,
                        'Secretario': secretario,
                        'Estudiante': tribunal['Estudiante'],
                        'Horario': str_hora_tribunal
                    }

                    if dict_para_df not in df_anteriores:
                        df_anteriores.append(dict_para_df)
                        df_aux = pd.DataFrame([dict_para_df])
                        df = pd.concat([df, df_aux], ignore_index=True)
    #                 print(df)
        
        # Write the DataFrame to a new sheet in the Excel file
        df.to_excel(writer, sheet_name=date.strftime('%Y-%m-%d'), index=False)
    
    # Save the Excel file
    writer.close()

async def exportar_asignaciones_excel(asignaciones, intervalo_fechas):
    start_date, end_date = intervalo_fechas

    await generate_excel(asignaciones, start_date, end_date)
