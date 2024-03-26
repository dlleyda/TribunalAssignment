from playwright.async_api import async_playwright, expect

from bs4 import BeautifulSoup
import time
from unidecode import unidecode
from datetime import datetime, timedelta
import re
import pandas as pd
import numpy as np
import pickle
import asyncio
from relacionar_nombres import most_similar_name, standardize_name
from rx.subject import Subject
import json

TIMEOUT_MILISECONDS = 50000
HEADLESS = True
username = "horarios.utad"
password = "3Hjb6xd.2"
school = "U-TAD"

clases_libres_5 = ["MAIS", "FIIS"]

def ver_profesores_para_recoger_datos(excel_file):
    datos_tfg = pd.read_excel(excel_file, "Datos")
    profesores = datos_tfg.loc[datos_tfg['TFG contrato'] != 0 , "Nombre Apellidos"].to_list()
    
    return profesores


###################################### DAR FORMATO A HORARIO ########################################
def extract_timestamps(input_string):
    pattern = r'\d+-\d+-\d+T\d+%3A\d+'
    matches = re.findall(pattern, input_string)
    matches_formatted = [i.replace("%3A", ":") for i in matches]
    return matches_formatted

def format_time_range(start_time, end_time):
    return f"{start_time}-{end_time}"

def group_timestamps_by_weekday(timestamps):
    weekdays_dict = {}

    for start_datetime, end_datetime in timestamps:
        formato_hora = "%Y-%m-%dT%H:%M"
        weekday = start_datetime.strftime("%A")
        formatted_range = (start_datetime.strftime(formato_hora), end_datetime.strftime(formato_hora))

        if weekday not in weekdays_dict:
            weekdays_dict[weekday] = [formatted_range]
        else:
            weekdays_dict[weekday].append(formatted_range)
    
    # Días de la semana para que date_time lo identifique
    all_weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    for weekday in all_weekdays:
        weekdays_dict.setdefault(weekday, [])

    return weekdays_dict

async def crear_horario_medio_dia(fechas):
    # Convertir las cadenas de fecha en objetos datetime
    inicio = datetime.strptime(fechas[0], "%Y-%m-%d")
    fin = datetime.strptime(fechas[1], "%Y-%m-%d")
    
    # Lista para almacenar los días de entre semana
    weekdays_dict = {}

    # Recorrer cada día entre las fechas de inicio y fin
    current = inicio
    while current <= fin:
        
        await asyncio.sleep(0.01)
        
        # Verificar si el día actual es un día de entre semana (lunes=0, martes=1, ..., viernes=4)
        if current.weekday() >= 5:
            # Avanzar al siguiente día
            current += timedelta(days=1)
            continue
            
        formato_hora = "%Y-%m-%dT%H:%M"
        weekday = current.strftime("%A")
        jornada_inicio = current.replace(hour=9, minute=0)
        jornada_fin = current.replace(hour=14, minute=0)
        formatted_range = (jornada_inicio.strftime(formato_hora), jornada_fin.strftime(formato_hora))

        if weekday not in weekdays_dict:
            weekdays_dict[weekday] = [formatted_range]
        else:
            weekdays_dict[weekday].append(formatted_range)
        
        current += timedelta(days=1)
        
    return weekdays_dict


"""
input_dates_1 = ["2024-04-08", "2024-04-12"]
input_dates_2 = ["2024-04-09", "2024-04-22"]

output_1 = ['2024-04-08']
output_2 =['2024-04-08', '2024-04-15', '2024-04-22']
"""
def get_lunes_entre_fechas(start_date, end_date):
    
    # Find the Monday before or equal to the start date
    start_monday = start_date - timedelta(days=start_date.weekday())

    # Initialize list to store Mondays
    mondays = []

    # Include the Monday of the week of the start date if it's not already in the range
    if start_monday <= start_date:
        mondays.append(start_monday.strftime("%Y-%m-%d"))

    # Iterate over Mondays from start_monday to end_date
    current_date = start_monday + timedelta(days=7)
    while current_date <= end_date:
        mondays.append(current_date.strftime("%Y-%m-%d"))
        current_date += timedelta(days=7)

    return mondays


def extract_grado_curso(clase):
    info_list = []
#     1st Capturing Group (\D+) \D matches any character that's not a digit
#     2nd Capturing Group (\d+) \d matches a digit
    match = re.match(r'(\D+)(\d+)', clase)
    if match:
        grado = match.group(1)
        curso = match.group(2)
        return (grado,curso)
    return None


async def recoger_con_playwright_elementos_horarios(profesores, fechas, paran_clases, observable):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
#         await page.pause()
        # Enable Playwright inspector
#         await page.set_devtools_agent(True)

    
        fechas_datetime = [datetime.strptime(fecha_i, "%Y-%m-%d") for fecha_i in fechas]
        lunes = get_lunes_entre_fechas(*fechas_datetime)
            
        try:
            # Navegar a la página de login
            await page.goto(f"https://mese.webuntis.com/WebUntis/?school={school}")

            # Rellenar con usuario y contraseña
            await page.get_by_text("Nombre del usuario").click()
            await page.get_by_text("Nombre del usuario").fill(username)
            await page.get_by_text("Clave de acceso (password)").click()
            await page.get_by_text("Clave de acceso (password)").fill(password)
            await page.get_by_role("button", name="Clave/Login").click()
            
            await asyncio.sleep(1)
            
            await page.get_by_role("link", name="Horarios", exact=True).click()
            await page.get_by_role("link", name="Sumario de profesores").click()

            option_elements = page.frame_locator("iframe[title=\"WebUntis\"]").locator('//*[@id="selectElementForm.idelementIds"]')
            contenidos = await option_elements.inner_html()
            
            pattern = r'<option value="(\d+)">(.*?)<\/option>'

            # Encontrar todos las coincidencias
            matches = re.findall(pattern, contenidos)
            
            lista_profesores_dict = {}
            for value, name in matches:
                full_name = standardize_name(name)
                lista_profesores_dict[full_name] = value

            observable.on_next(("get_horarios", -1, 1, "Se han recogido los ids de los profesores"))

            # Relacionar profesores de Excel con Webunits y sus IDs
            profesores_y_ids = []
            for profesor in profesores:
                nombre_profesor = standardize_name(profesor)
                if nombre_profesor not in lista_profesores_dict.keys():
                    name_max_similarity, max_similarity = most_similar_name(nombre_profesor, lista_profesores_dict.keys())
                    
                    id_max_similar_name = lista_profesores_dict[name_max_similarity]
                    profesores_y_ids.append((profesor, id_max_similar_name))
                else:
                    profesores_y_ids.append((profesor, lista_profesores_dict[nombre_profesor]))
                    
            print(profesores_y_ids)
    
            # Extract schedule for each professor
            listas_de_a_profesores = []
            iterador = 0
            for nombre_profesor, id_profesor in profesores_y_ids:
                lista_de_a_copia = []
                for lunes_i in lunes:
                    await page.goto(f"https://mese.webuntis.com/timetable-teachers/{id_profesor}/{lunes_i}")
                    await expect(page.frame_locator("iframe").locator(".entryLayer")).to_be_visible(timeout=TIMEOUT_MILISECONDS)

                    lista_de_a = await page.frame_locator("iframe").locator(".entryLayer").locator('a').all()
                    
                    for a in lista_de_a:
                        
                        # En el caso de que el curso sea el último año del grado se supone que es un hueco libre, ya que no habría clases
                        clase = await a.locator("span").first.inner_html()
                        
                        tupla = extract_grado_curso(clase)
                        
                        try:
                            a_href = await a.get_attribute('href')
                            horario = extract_timestamps(a_href)
                            horario_datetime = [datetime.strptime(horario_i, "%Y-%m-%dT%H:%M") for horario_i in horario]
                            if horario_datetime[0] < fechas_datetime[0]:
                                continue
                            if horario_datetime[0] > fechas_datetime[1]:
                                break
                                
                            if tupla and paran_clases:
                                grado, curso = tupla
                                if (grado in clases_libres_5 and curso == '5') or (curso == '4' and grado not in clases_libres_5):
                                    print(f"El profesor {nombre_profesor} tiene el horario: {horario_datetime} que se pararían sus clases de {grado}{curso}")
                                    lista_de_a_copia.append([horario_datetime[0], horario_datetime[0]])
                                else:
                                    lista_de_a_copia.append(horario_datetime)   
                            else:
                                lista_de_a_copia.append(horario_datetime)
                            
                        except:
                            print(f"**** ERROR **** recogiendo los atributos href de {nombre_profesor}")
                                
                listas_de_a_profesores.append((nombre_profesor, lista_de_a_copia))
                iterador += 1
                
                print(f'Se ha descargado el horario de {nombre_profesor} ({iterador}/{len(profesores_y_ids)})')
                observable.on_next(("get_horarios", iterador, len(profesores_y_ids), nombre_profesor))
                

            return listas_de_a_profesores

        finally:
            await browser.close()


def agrupar_horarios(listas_de_a_profesores):
    horarios_profesores = []
    
    for nombre_profesor, horario_profe in listas_de_a_profesores:
        result_dict = group_timestamps_by_weekday(horario_profe)
        result_dict["Profesor"] = nombre_profesor

        horarios_profesores.append(result_dict)
        
    return horarios_profesores
    
def json_encoder(obj):
    if isinstance(obj, datetime):
        fecha = obj.strftime("%Y-%m-%d %H:%M")
        return fecha
        
    raise TypeError("Type not serializable")


def escribir_datos_leidos(fichero):
    nombre_fich = "datos_simulados.json"

    with open(nombre_fich, 'w', encoding='utf-8') as json_file:
         json.dump(fichero, json_file, indent=2, ensure_ascii=False, default=json_encoder)    

async def recoger_y_almacenar_horarios(excel_file, datos, fechas, paran_clases, observable):
    excel_file = "../Ficheros excel tribunales/23-24 GESTOR.xlsm"
    
    profesores = ver_profesores_para_recoger_datos(excel_file)
    
    listas_de_a_profesores = await recoger_con_playwright_elementos_horarios(profesores, fechas, paran_clases, observable)

    horarios = agrupar_horarios(listas_de_a_profesores)
    
    for indice, horario in enumerate(horarios):
        horario.pop('Profesor', None)
        datos[indice]["tutor"]["horario_ocupado"] = horario
        
    escribir_datos_leidos(datos)
    
    return datos
        
# recoger_y_almacenar_horarios("")
# asyncio.run(recoger_y_almacenar_horarios("", ["2024-04-08","2024-04-16"], True, Subject()))