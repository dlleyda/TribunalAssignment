import pandas as pd
import numpy as np
import pickle
import json
import asyncio
from rx.subject import Subject
from datetime import datetime
import warnings

warnings.simplefilter(action='ignore', category=UserWarning)

def clean_columns(df_columns):
    df_columns = df_columns.str.lower()  # Convert to lowercase
    df_columns = df_columns.str.strip()  # Remove initial and ending spaces
    df_columns = df_columns.str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8')  # Remove accents
    
    return df_columns

datos_tfg = None

def lectura_datos_excel(fichero):
    global datos_tfg
    
#     fichero = "../Ficheros excel tribunales/23-24 GESTOR_ficticio.xlsm"
    warnings.simplefilter(action='ignore', category=UserWarning)
    
    datos_tfg = pd.read_excel("../Ficheros excel tribunales/23-24 GESTOR.xlsm", "Datos")
    datos_tfg = datos_tfg[datos_tfg["TFG contrato"] != 0]
    datos_tfg.columns = clean_columns(datos_tfg.columns)
    
    datos_tfg_fict = pd.read_excel(fichero, "Datos")
    datos_tfg_fict = datos_tfg_fict[datos_tfg_fict["TFG contrato"] != 0]
    datos_tfg_fict.columns = clean_columns(datos_tfg_fict.columns)

    listado_alumnos_tfg = pd.read_excel(fichero, "ListadoAlumnosTFG")
    listado_alumnos_tfg.columns = clean_columns(listado_alumnos_tfg.columns)
    
    asignacion_tfg = pd.read_excel(fichero, "Asignación TFG")
    asignacion_tfg.columns = clean_columns(asignacion_tfg.columns)
    
    
    return datos_tfg_fict, listado_alumnos_tfg, asignacion_tfg


def lectura_horarios(fichero):
    fichero = 'horarios_profesores.pkl'
    with open(fichero, 'rb') as file:
        horarios_profesores = pickle.load(file)
    return horarios_profesores


# Function to get points for a given name
def get_schedule(profesor, horarios_profesores):
    for horario in horarios_profesores:
        if horario["Profesor"] == profesor:
            horario_copia = horario.copy()
            horario_copia.pop("Profesor", None)
            
            return horario_copia
    # Return None if the name is not found
    return {"Monday":[], "Tuesday":[], "Wednesday":[], "Thursday":[], "Friday":[]}


def asignar_alumnos_a_tutor(datos_tfg_fict, listado_alumnos_tfg):
    # Calcular la proporción de alumnos por profesor
    datos_tfg_fict['proporcion'] = datos_tfg_fict['tfg contrato'] / datos_tfg_fict['tfg contrato'].sum()

    # Crear una columna para asignar al tutor en la hoja de alumnos
#     listado_alumnos_tfg['tutor'] = np.nan

    # Asignar aleatoriamente a cada alumno a un tutor teniendo en cuenta la proporción
    for index, alumno in listado_alumnos_tfg.iterrows():
        tutor_asignado = np.random.choice(datos_tfg_fict['nombre apellidos'], p=datos_tfg_fict['proporcion'].values)
        listado_alumnos_tfg.at[index, 'tutor'] = tutor_asignado

    return listado_alumnos_tfg

# # Ahora quiero crear el json de la manera que tenía antes:
# async def recoger_datos(datos_tfg_fict, listado_alumnos_tfg, asignacion_tfg, horarios_profesores, observable):
async def recoger_datos(datos_tfg_fict, listado_alumnos_tfg, asignacion_tfg, observable):

    lista_json = []
    # horarios = [get_schedule(i, horarios_profesores) for i in datos_tfg["nombre apellidos"].to_list()]
    max_iters = len(datos_tfg_fict)
    iteracion = 0
    for index, row in datos_tfg_fict.iterrows():
        
        await asyncio.sleep(0.01)
        
        json_tutor_tutorando = {}

        json_tutor_tutorando["nombre_tutor"] = row["nombre apellidos"]
        json_tutor_tutorando["email_tutor"] = row["email"]

        diccionario_tutor = {}

        diccionario_tutor["titulacion"] = "L" if pd.isna(row["titulacion"]) else row["titulacion"]
        diccionario_tutor["asignacion"] = listado_alumnos_tfg.loc[listado_alumnos_tfg['tutor'] == row["nombre apellidos"], "email utad (alumno) (alumno)"].to_list()
        diccionario_tutor["grado_principal"] = "" if pd.isna(row["grado principal"]) else row["grado principal"]
        diccionario_tutor["grado_secundario"] = "" if pd.isna(row["grado secundario"]) else row["grado secundario"]
        diccionario_tutor["tribunales_maximos"] = 0 if pd.isna(row["tribunales maximo"]) else int(row["tribunales maximo"])
        diccionario_tutor["tribunales_asignados"] = 0 if pd.isna(row["tribunales asignados"]) else int(row["tribunales asignados"])
        diccionario_tutor["tribunales_restantes"] = 0 if pd.isna(row["tribunales restantes"]) else int(row["tribunales restantes"])
        diccionario_tutor["ingles"] = "" if pd.isna(row["ingles"]) else row["ingles"]
        # diccionario_tutor["horario_ocupado"] = horarios[iteracion]
        diccionario_tutor["horario_ocupado"] = ""
        iteracion += 1

        json_tutor_tutorando["tutor"] = diccionario_tutor

        json_tutor_tutorando["alumnos"] = []
        for email_alumno in diccionario_tutor["asignacion"]:
            json_alumno = {}
            df_alumno = listado_alumnos_tfg.loc[listado_alumnos_tfg['email utad (alumno) (alumno)'] == email_alumno]

            json_alumno["nombre"] = df_alumno["alumno"].to_list()[0]
            json_alumno["email"] = email_alumno
            json_alumno["grado"] = df_alumno["titulacion2"].to_list()[0]

            grados_ingles = ["ANIG", "DIPG", "INSG"]
            ingles = "si" if df_alumno["titulacion2"].to_list()[0] in grados_ingles else "no"
            json_alumno["en_ingles"] = ingles
            
            # df_alumno = asignacion_tfg.loc[asignacion_tfg['email alumno'] == email_alumno]
            # json_alumno["nombre"] = df_alumno["nombre alumno"].to_list()[0]
            # json_alumno["email"] = email_alumno
            # json_alumno["grado"] = df_alumno["titulacion"].to_list()[0]
            # json_alumno["en_ingles"] = df_alumno["ingles"].to_list()[0]

            json_tutor_tutorando["alumnos"].append(json_alumno)

        lista_json.append(json_tutor_tutorando)
        
        observable.on_next(("recoger_datos_excel", iteracion, max_iters))
       
    return lista_json


# async def leer_escribir_datos(fichero_excel, fichero_horarios, observable):
async def leer_escribir_datos(fichero_excel, observable):
    # horarios = None
    
    # if isinstance(fichero_horarios, str):
    #     horarios = lectura_horarios(fichero_horarios)
    # else:
    #     horarios = fichero_horarios
    
    datos_tfg_fict, listado_alumnos_tfg, asignacion_tfg = lectura_datos_excel(fichero_excel)
    
    listado_alumnos_tfg = asignar_alumnos_a_tutor(datos_tfg_fict, listado_alumnos_tfg)

    lista_json = await recoger_datos(datos_tfg_fict, listado_alumnos_tfg, asignacion_tfg, observable)
    
    # escribir_datos_leidos(lista_json)
    
    return lista_json
    
# asyncio.run(leer_escribir_datos("../Ficheros excel tribunales/23-24 GESTOR_ficticio.xlsm", "horarios_profesores.pkl", Subject()))