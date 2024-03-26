from datetime import datetime, timedelta, date
import json
import copy
import random
import sys
import asyncio
import re
from rx.subject import Subject

DURACION_HORAS_DEFENSA = 1

DOCTOR_DOCTOR = 40
DOCTOR_LICENCIADO = 80
LINCIADO_LICENCIADO = 10

EXPERTO_EXPERTO = 60
EXPERTO_INTERESADO = 30
EXPERTO_NADA = 10

DEFENSA_INGLES_PROFE_INGLES = 90
DEFENSA_INGLES_PROFE_NO_INGLES = -20
DEFENSA_NO_INGLES_PROFE_INGLES = -20
DEFENSA_NO_INGLES_PROFE_NO_INGLES = 50


"""
Devuelve la jornada de un profesor cierto día, lo que equivaldría a transformar la jornada "escrita" a una jornada con objetos de tipo fecha

Input:
- teacher_json = {'nombre_tutor': 'Teodoro Hawk', 'email_tutor': 'teodoro.hawk@u-tad.com', 'tutor': {'titulacion': 'L', 'asignacion': ['malchy.olander@live.u-tad.com'], 'grado_principal': 'DIPI', 'grado_secundario': '', 'tribunales_maximos': 6, 'tribunales_asignados': 0, 'tribunales_restantes': 6, 'ingles': 'si', 'horario_ocupado': {'Tuesday': ['11:00-13:00'], 'Wednesday': ['17:00-19:00'], 'Thursday': ['11:00-13:00'], 'Friday': ['15:00-17:00', '17:00-19:00'], 'Monday': []}}, 'alumnos': [{'nombre': 'Malchy Olander', 'email': 'malchy.olander@live.u-tad.com', 'grado': 'DIPI', 'en_ingles': 'no'}]}

- dia_semana = "Tuesday"

Output:
*Lista de tuplas de objetos tipo datetime.datetime
[(datetime.datetime(1900, 1, 2, 11, 00), datetime.datetime(1900, 1, 2, 13, 00))]
"""
def get_working_hours(teacher_json, dia_semana):
    formato = "%Y-%m-%dT%H:%M"
    jornada = []

    # Extraer la jornada del profesor en tuplas
    for horas_clase in teacher_json["tutor"]["horario_ocupado"][dia_semana]:
        empieza_clase, termina_clase = horas_clase[0], horas_clase[1]

        jornada.append((datetime.strptime(empieza_clase, formato) , datetime.strptime(termina_clase, formato)))

    return jornada


"""
Devuelve la interseccion de entre dos horarios

Input:
*A y B son listas de tuplas de la siguiente forma:
A = [(datetime.datetime(1900, 1, 2, 11, 00), datetime.datetime(1900, 1, 2, 13, 00))]
B = [(datetime.datetime(1900, 1, 2, 12, 00), datetime.datetime(1900, 1, 2, 14, 00))]

Output:
A ∩ B -> [(datetime.datetime(1900, 1, 2, 12, 00), datetime.datetime(1900, 1, 2, 13, 00))]
"""
def intervalIntersection(A, B):
    ans = []
    i = j = 0

    while i < len(A) and j < len(B):
        lo = max(A[i][0], B[j][0])
        hi = min(A[i][1], B[j][1])

        if lo <= hi:
            ans.append((lo, hi))

        if A[i][1] < B[j][1]:
            i += 1
        else:
            j += 1

    return ans

"""
Quita intervalos que son de cero horas, por ejemplo un intervalo de 9:00 a 9:00 sería un intervalo de cero horas.

Input:
[(datetime.datetime(1900, 1, 2, 9, 00), datetime.datetime(1900, 1, 2, 9, 00)), (datetime.datetime(1900, 1, 2, 11, 00), datetime.datetime(1900, 1, 2, 13, 00))]

Output:
[(datetime.datetime(1900, 1, 2, 11, 00), datetime.datetime(1900, 1, 2, 13, 00))]
"""
def remove_zero_hour_interval_from_list(interval_list):
    return [filter_zero_hour_interval(i) for i in interval_list if filter_zero_hour_interval(i)]


"""
Filtra si un intervalo se considera de cero horas.
-------------------------------------------
Caso 1: 

Input:
(datetime.datetime(1900, 1, 2, 9, 00), datetime.datetime(1900, 1, 2, 9, 00))

Output:
<nada>

--------------------------------------------
Caso 2:

Input:
(datetime.datetime(1900, 1, 2, 9, 00), datetime.datetime(1900, 1, 2, 10, 00))

Output:
(datetime.datetime(1900, 1, 2, 9, 00), datetime.datetime(1900, 1, 2, 10, 00))
"""
def filter_zero_hour_interval(interval):
    start, end = interval
    if start != end:
        return start,end


"""
Devuelve la union de un mismo horario

Input:
Donde un horario es una lista de tuplas de la siguiente forma:
intervals = [(datetime.datetime(1900, 1, 2, 9, 00), datetime.datetime(1900, 1, 2, 11, 00)), (datetime.datetime(1900, 1, 2, 11, 00), datetime.datetime(1900, 1, 2, 13, 00)), (datetime.datetime(1900, 1, 2, 13, 00), datetime.datetime(1900, 1, 2, 15, 00)), (datetime.datetime(1900, 1, 2, 17, 00), datetime.datetime(1900, 1, 2, 19, 00))]

Output:
∪ (intervalo_i) => [(datetime.datetime(1900, 1, 2, 9, 00), datetime.datetime(1900, 1, 2, 15, 00)), (datetime.datetime(1900, 1, 2, 17, 00), datetime.datetime(1900, 1, 2, 19, 00))]
"""
def interval_union(intervals):
    if not intervals:
        return []
    
    intervals.sort(key=lambda x: x[0])
    merged = [intervals[0]]
    
    for interval in intervals[1:]:
        if interval[0] <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], interval[1]))
        else:
            merged.append(interval)
    
    return merged

"""
Devolver los intervalos que son iguales entre sí:

Input:
intervals1 = [(datetime.datetime(1900, 1, 2, 9, 00), datetime.datetime(1900, 1, 2, 11, 00)), (datetime.datetime(1900, 1, 2, 11, 00), datetime.datetime(1900, 1, 2, 13, 00)), (datetime.datetime(1900, 1, 2, 13, 00), datetime.datetime(1900, 1, 2, 15, 00)), (datetime.datetime(1900, 1, 2, 17, 00), datetime.datetime(1900, 1, 2, 19, 00))]
intervals2 = [(datetime.datetime(1900, 1, 2, 9, 00), datetime.datetime(1900, 1, 2, 11, 00))]

Output:
[(datetime.datetime(1900, 1, 2, 9, 00), datetime.datetime(1900, 1, 2, 11, 00))]
"""
def equal_intervals(intervals1, intervals2):
    equal_intervals_list = []
    for interval in intervals1:
        if interval in intervals2: equal_intervals_list.append(interval)
    return equal_intervals_list


"""
Expande un intervalo contraído, es decir, un intervalo 9:00-13:00 -> 9:00-10:00, 10:00-11:00, 11:00-12:00, 12:00-13:00

Input:
intervals1 = [(datetime.datetime(1900, 1, 2, 9, 00), datetime.datetime(1900, 1, 2, 11, 00))]

Output:
[(datetime.datetime(1900, 1, 2, 9, 00), datetime.datetime(1900, 1, 2, 10, 00)), (datetime.datetime(1900, 1, 2, 10, 00), datetime.datetime(1900, 1, 2, 11, 00))]
"""
def expand_interval(intervals):
    new_intervals = []
    
    for start, end in intervals:
        current_time = start
        while current_time < end:
            new_end = min(current_time + timedelta(hours=1), end)
            new_intervals.append((current_time, new_end))
            current_time += timedelta(hours=1)

    return new_intervals

"""
Realiza la operación A - B, donde A y B son conjuntos. Esto es útil para extraer las horas libres de un profesor de tal manera que si tenemos:
() <- marca inicio y fin de intervalo de dos horas al comienzo y final de una clase del profesor
[] <- marca inicio y fin de clases de profesor
Pues la resta es útil para casos como: (--[-(-)-]--) -> Interesaría solamente las horas (-- y --)

Input:
A = [(datetime.datetime(1900, 1, 2, 9, 00), datetime.datetime(1900, 1, 2, 11, 00)), (datetime.datetime(1900, 1, 2, 11, 00), datetime.datetime(1900, 1, 2, 13, 00))]
B = [(datetime.datetime(1900, 1, 2, 10, 00), datetime.datetime(1900, 1, 2, 12, 00))]

Output:
A-B = [(datetime.datetime(1900, 1, 2, 9, 00), datetime.datetime(1900, 1, 2, 10, 00)), (datetime.datetime(1900, 1, 2, 12, 00), datetime.datetime(1900, 1, 2, 13, 00))]
"""
def interval_subtraction(A, B):
    union_A = interval_union(A)
    union_B = interval_union(B)
    
    A_expanded = expand_interval(union_A)
    B_expanded = expand_interval(union_B)
    
    interval_substracted = [i for i in A_expanded if i not in B_expanded]
    return interval_union(interval_substracted)


"""
Genera horas libres entorno a las horas que tienen clase +- (horas_extra)

Input:
working_hours = [(datetime.datetime(1900, 1, 2, 9, 00), datetime.datetime(1900, 1, 2, 11, 00)), (datetime.datetime(1900, 1, 2, 11, 00), datetime.datetime(1900, 1, 2, 13, 00))]
extra_hours = 2

Output:
[(datetime.datetime(1900, 1, 2, 9, 00), datetime.datetime(1900, 1, 2, 9, 00)), (datetime.datetime(1900, 1, 2, 11, 00), datetime.datetime(1900, 1, 2, 13, 00)), (datetime.datetime(1900, 1, 2, 13, 00), datetime.datetime(1900, 1, 2, 15, 00))]
"""
def generate_free_hours(working_hours, extra_hours):
    free_hours = []
    
    for i in range(len(working_hours)):
        
        horario_comida = [(datetime(working_hours[i][0].year, working_hours[i][0].month, working_hours[i][0].day, 14, 0), 
                           datetime(working_hours[i][0].year, working_hours[i][0].month, working_hours[i][0].day, 15, 0))]
    
        primera_hora_posible = datetime(working_hours[i][0].year, working_hours[i][0].month, working_hours[i][0].day, 9, 0)
        ultima_hora_posible = datetime(working_hours[i][0].year, working_hours[i][0].month, working_hours[i][0].day, 19, 0)
        
        if(working_hours[i][0] - timedelta(hours=extra_hours) < primera_hora_posible):
            start_time1 = primera_hora_posible
        else:
            start_time1 = working_hours[i][0] - timedelta(hours=extra_hours)
            
        end_time1 = working_hours[i][0]
        
        start_time2 = working_hours[i][1]
        
        if(working_hours[i][1] + timedelta(hours=extra_hours) >= ultima_hora_posible):
            end_time2 = ultima_hora_posible
        else:
            end_time2 = working_hours[i][1] + timedelta(hours=extra_hours)
    
        interseccion_comida1 = intervalIntersection(horario_comida, [(start_time1,end_time1)])
        interseccion_comida1 = remove_zero_hour_interval_from_list(interseccion_comida1)
        
        interseccion_comida2 = intervalIntersection(horario_comida, [(start_time2,end_time2)])
        interseccion_comida2 = remove_zero_hour_interval_from_list(interseccion_comida2)
        
        if len(interseccion_comida1) > 0:
            continue
            
        free_hours.append((start_time1,end_time1))
        
        if len(interseccion_comida2) > 0:
            continue
        free_hours.append((start_time2,end_time2))
    
    return interval_subtraction(free_hours, working_hours)


"""
Input:
intervals = divide_interval(datetime(1900, 1, 1, 15, 0), datetime(1900, 1, 1, 17, 0))

Output:
(datetime(1900, 1, 1, 15, 0), datetime(1900, 1, 1, 16, 0))
(datetime(1900, 1, 1, 15, 30), datetime(1900, 1, 1, 16, 30))
(datetime(1900, 1, 1, 16, 0), datetime(1900, 1, 1, 17, 0))
"""
def divide_interval(start_datetime, end_datetime):
    # Initialize the list to store intervals
    intervals = []

    # Iterate through the interval with steps of 30 minutes and generate intervals
    current_time = start_datetime
    while current_time < end_datetime:
        next_time = current_time + timedelta(hours=DURACION_HORAS_DEFENSA)
        # Ensure the next_time does not exceed the end time
        if next_time > end_datetime:
            break
        intervals.append((current_time, next_time))
        current_time += timedelta(minutes=30)

    return intervals



"""
Código para una búsqueda rápida de los json de los profesores y alumnos
"""        
def get_student_json(student_email):
    indiceTutor, indiceAlumno = indices_teachers_students[student_email]
    
    return data[indiceTutor]["alumnos"][indiceAlumno]


def get_teacher_json(name_teacher):
    indiceTutor = indices_teachers_students[name_teacher]
    return data[indiceTutor]

fechas_asignacion = []
# jornada_completa = [datetime.strptime("2024-04-08T09:00", "%Y-%m-%dT%H:%M"), datetime.strptime("2024-04-08T14:00", "%Y-%m-%dT%H:%M")]
# fecha_para_externos = [datetime.strptime("2024-04-08T09:00", "%Y-%m-%dT%H:%M"), datetime.strptime("2024-04-08T14:00", "%Y-%m-%dT%H:%M")]

def generate_all_free_hours():
    global fechas_asignacion
    
    json_all_free_hours = {
        "Monday": [],
        "Tuesday": [],
        "Wednesday": [],
        "Thursday": [],
        "Friday": []
    }
    json_all_partial_hours = {
        "Monday": [],
        "Tuesday": [],
        "Wednesday": [],
        "Thursday": [],
        "Friday": []
    }
    
    fecha_actual = datetime.strptime(fechas_asignacion[0], "%Y-%m-%d")
    fin = datetime.strptime(fechas_asignacion[1], "%Y-%m-%d")
    
    while fecha_actual < fin:
        if fecha_actual.weekday() < 5:
            dia_semana = fecha_actual.strftime("%A")
            # 9:00 - 14:00
            inicio_am = fecha_actual.replace(hour=9, minute=0)
            fin_am = fecha_actual.replace(hour=14, minute=0)
            horas_divididas_am = divide_interval(inicio_am, fin_am)
            json_all_free_hours[dia_semana].extend(horas_divididas_am)
            json_all_partial_hours[dia_semana].extend(horas_divididas_am)

            # 15:00 - 19:00
            inicio_pm = fecha_actual.replace(hour=15, minute=0)
            fin_pm = fecha_actual.replace(hour=19, minute=0)
            horas_divididas_pm = divide_interval(inicio_pm, fin_pm)
            json_all_free_hours[dia_semana].extend(horas_divididas_pm)

        # Move to the next day
        fecha_actual += timedelta(days=1)
        
    return json_all_free_hours, json_all_partial_hours

"""
Generar horas libres para cada profesor +-2h
"""
def generate_possible_free_hours_per_teacher(data):
    dias_semana = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    
    json_vacio = {}
    for weekday in dias_semana:
        json_vacio.setdefault(weekday, [])
    
    json_dia_completo, json_dia_parcial = generate_all_free_hours()
    
    for tutor_data in data:
        json_horas_libres = {}
        
        # profesor = get_teacher_json(tutor_data["nombre_tutor"])
        profesor = tutor_data
            
        for weekday in dias_semana:
            jornada = get_working_hours(profesor, weekday)
            tiempos_libres = generate_free_hours(jornada, 2) 
            tiempos_libres_extendido = []
            for intervalo_libre_start, intervalo_libre_end in tiempos_libres:
                intervalo_dividido = divide_interval(intervalo_libre_start, intervalo_libre_end)
                
                tiempos_libres_extendido.extend(intervalo_dividido)

            indice = data.index(profesor)
            json_horas_libres[weekday] = tiempos_libres_extendido
            
        if profesor["tutor"]["horario_ocupado"] == json_vacio:
            if convocatoria == "julio":
                json_horas_libres = copy.deepcopy(json_dia_parcial)
            else:
                json_horas_libres = copy.deepcopy(json_dia_completo)
        
        data[indice]["horas_libres"] = json_horas_libres
    
    return data


"""
Recoger los estudiantes y profesores
"""
def get_students_and_teachers(data):
    students = []
    english_students = []
    teachers = []
    english_teachers = []


    # Iterate through the data
    for tutor_data in data:
        # Extract students
        english_students.extend(student["email"] for student in tutor_data["alumnos"] if student["en_ingles"]=="si")
        students.extend(student["email"] for student in tutor_data["alumnos"])

        # Extract teachers
        english_teachers.extend([tutor_data["nombre_tutor"]] if tutor_data["tutor"]["ingles"] == "si" else [])
        teachers.append(tutor_data["nombre_tutor"])

    # Remove duplicates by converting lists to sets and back to lists
    students = list(students)
    teachers = list(teachers)
    english_students = list(english_students)
    english_teachers = list(english_teachers)
    
    return students, english_students, teachers, english_teachers


"""
Generar posibles tribunales
"""
def generate_possible_tribunales(teachers):
    dias = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    tribunales = []
    
    for profesor_i in range(len(teachers)):
        
        profesor1_json = get_teacher_json(teachers[profesor_i])
        if profesor1_json["tutor"]["tribunales_restantes"] == 0:
            continue
        
        for profesor_j in range(profesor_i+1, len(teachers)):
            peso = 0
            profesor2_json = get_teacher_json(teachers[profesor_j])
            
            if profesor2_json["tutor"]["tribunales_restantes"] == 0:
                continue
            
            if "D" in profesor1_json["tutor"]["titulacion"] and "D" in profesor2_json["tutor"]["titulacion"]:
                peso = DOCTOR_DOCTOR
            elif "D" in profesor1_json["tutor"]["titulacion"] or "D" in profesor2_json["tutor"]["titulacion"]:
                peso = DOCTOR_LICENCIADO
            else:
                peso = LINCIADO_LICENCIADO
                
            for dia in dias:
                horas_libres1 = profesor1_json["horas_libres"][dia]
                horas_libres2 = profesor2_json["horas_libres"][dia]

                interseccion = equal_intervals(horas_libres1, horas_libres2)
                
                if len(interseccion) == 0:
                    continue
                else:
                    for inicio, fin in interseccion:
                        # El tribunal debe ser como mínimo de la duracion dada
                        if inicio + timedelta(hours=DURACION_HORAS_DEFENSA) > fin:
                            break
                        
                        tribunales.append(
                            {
                            "profesor1": profesor1_json['nombre_tutor'], 
                            "profesor2": profesor2_json['nombre_tutor'],
                            "dia": dia,
                            "intervalo": (inicio, fin),
                            "peso": peso,
                            "asignado": False
                            })
        
    return tribunales

"""
Agrupar datos por peso
"""
def group_by_weight(data):
    grouped_by_weight = {}

    for entry in data:
        weight = entry['peso']

        # Append the current dictionary to the list associated with the key
        if weight not in grouped_by_weight.keys():
            grouped_by_weight[weight] = []
            
        grouped_by_weight[weight].append(entry)
            
    return grouped_by_weight

"""
Agrupar datos por profesores
"""
def group_by_teacher(data, teachers):
    grouped_by_teacher_weight = {}
    
    for weight in data.keys():
        grouped_by_teacher_weight[weight] = {}
        for teacher in teachers:
            grouped_by_teacher_weight[weight][teacher] = []
    
    for weight, entries in data.items():
        for entry in entries:
            teacher1 = entry['profesor1']
            teacher2 = entry['profesor2']

            # Append the current dictionary to the list associated with the key
            if entry not in grouped_by_teacher_weight[weight][teacher1]:
                grouped_by_teacher_weight[weight][teacher1].append(entry)
            if entry not in grouped_by_teacher_weight[weight][teacher2]:
                grouped_by_teacher_weight[weight][teacher2].append(entry)
            
        
    return grouped_by_teacher_weight

"""
Calcula el número de tribunales por profesor (para que todos los profesores tengan mismo porcentaje de carga o alrededor)
"""
def calcular_tribunales_por_profesor(estudiantes, teachers):
    suma_tribunales_maximos = [get_teacher_json(i)["tutor"]["tribunales_restantes"] for i in teachers]
    suma_tribunales_maximos = sum(suma_tribunales_maximos)
    return len(estudiantes)/suma_tribunales_maximos



"""
Comprobar si un tribunal interseca con otros tribunales ya asignados (para que no se pisen)
"""
def tribunalsIntersect(tribunal, tribunales_asignados):
    for tribunal_asignado in tribunales_asignados:
        horario_asignado = tribunal_asignado["intervalo"]
        horario_para_asignar = tribunal["intervalo"]
        
        interseccion = intervalIntersection([horario_para_asignar], [horario_asignado])
        interseccion = remove_zero_hour_interval_from_list(interseccion)
        
        if len(interseccion) > 0:
            return True
        
    return False
    

"""
Ir asignando tribunales
"""
num_estudiantes_asignados = 0
num_estudiantes_total = 0
async def asignar_tribunales(students, tribunales, constraints, observable):
    global num_estudiantes_asignados
    
    at_least_one_expert, at_least_one_interested, at_least_expert_interested = constraints
    
    copia_tribunales = copy.deepcopy(tribunales)
    estudiantes_asignados = []
    tribunales_asignados_por_profesor = {}
    nuevos_tribunales_asignados = {}
    
    for teacher in copia_tribunales.keys():
        nuevos_tribunales_asignados[teacher] = []
        tribunales_asignados_por_profesor[teacher] = [tribunal for tribunal in copia_tribunales[teacher] if tribunal["asignado"]]
    
    for student in students:
        estudiante_json = get_student_json(student)
        siguiente_student = False
            
        for profesor, posibles_tribunales in copia_tribunales.items():
            if siguiente_student:
                break
            
            profesor_json = get_teacher_json(profesor)
            profesor2_json = None
            # tutor constraint
            if student in profesor_json["tutor"]["asignacion"]:
                continue

            for tribunal in posibles_tribunales:
                
                await asyncio.sleep(0.001)
                
                # Ver si el tribunal ya está asignado
                if tribunal["asignado"]:
                    continue
                    
                if profesor == tribunal["profesor1"]: 
                    profesor2_json = get_teacher_json(tribunal["profesor2"])
                else:
                    profesor2_json = get_teacher_json(tribunal["profesor1"])

                # tutor constraint        
                if student in profesor2_json["tutor"]["asignacion"]:
                    continue

                 # Comprobar si el profesor ya ha cumplido con su máximo de tribunales asignados
                num_tribunales_asignados = sum(1 for tribunal in copia_tribunales[profesor_json["nombre_tutor"]] if tribunal['asignado'])

                if num_tribunales_asignados == profesor_json["tutor"]["tribunales_restantes"]:
                    continue
#                 if num_tribunales_asignados == ((num_tribunales_profesor * profesor_json["tutor"]["tribunales_restantes"]) // 1) + 1:
#                     continue


                 # Comprobar si el profesor ya ha cumplido con su máximo de tribunales asignados
                num_tribunales_asignados2 = sum(1 for tribunal2 in copia_tribunales[profesor2_json["nombre_tutor"]] if tribunal2['asignado'])

                if num_tribunales_asignados2 == profesor2_json["tutor"]["tribunales_restantes"]:
                    continue
#                 if num_tribunales_asignados2 == ((num_tribunales_profesor * profesor2_json["tutor"]["tribunales_restantes"]) // 1) + 1:
#                     continue

                grado_alumno = estudiante_json["grado"]
                grado_principal1 = profesor_json["tutor"]["grado_principal"]
                grado_secundario1 = profesor_json["tutor"]["grado_secundario"]
                grado_principal2 = profesor2_json["tutor"]["grado_principal"]
                grado_secundario2 = profesor2_json["tutor"]["grado_secundario"]
                
                # At least one is expert
                if at_least_expert_interested:
                    # At least they are either expert-expert or expert-intereseted
                    if grado_alumno == grado_principal1 and grado_alumno == grado_principal2:
                        pass
                    elif (grado_alumno == grado_principal1 and grado_alumno == grado_secundario2) or \
                         (grado_alumno == grado_secundario1 and grado_alumno == grado_principal2):
                        pass
                    else:
                        continue  
                elif at_least_one_expert:
                    if grado_alumno != grado_principal1 and grado_alumno != grado_principal2:
                        continue
                elif at_least_one_interested:
                    if grado_alumno != grado_secundario1 and grado_alumno != grado_secundario1:
                        continue

                # Ver si el tribunal que es está evaluando tiene compatibilidad con el resto de los tribunales de los profesores
                if tribunalsIntersect(tribunal, tribunales_asignados_por_profesor[tribunal["profesor1"]]) or tribunalsIntersect(tribunal, tribunales_asignados_por_profesor[tribunal["profesor2"]]):
                    continue
                    
                print(f"Se ha encontrado un tribunal para {student}")

                indice_tribunal1 = copia_tribunales[tribunal["profesor1"]].index(tribunal)
                indice_tribunal2 = copia_tribunales[tribunal["profesor2"]].index(tribunal)

                copia_tribunales[tribunal["profesor1"]][indice_tribunal1]["asignado"] = True
                copia_tribunales[tribunal["profesor2"]][indice_tribunal2]["asignado"] = True
                
                nuevos_tribunales_asignados[tribunal["profesor1"]].append({ "Tribunal": tribunal, "Estudiante": student })
                nuevos_tribunales_asignados[tribunal["profesor2"]].append({ "Tribunal": tribunal, "Estudiante": student })

                tribunales_asignados_por_profesor[tribunal["profesor1"]].append(tribunal)
                tribunales_asignados_por_profesor[tribunal["profesor2"]].append(tribunal)
                
                estudiantes_asignados.append(student)
                num_estudiantes_asignados += 1
                observable.on_next(("asignar_tribunales", num_estudiantes_asignados, num_estudiantes_total, student))
                
                siguiente_student = True
                break
                
    
            
    return nuevos_tribunales_asignados, copia_tribunales, estudiantes_asignados


"""
Asegura que los tribunales se van asignando todo el rato hasta que no se encuentren más posibles tribunales tras varios intentos
"""
async def asegura_asignacion_tribunales(tribunales_group_profesor, students, num_tribunales_profesor, observable):
    
    tribunales_asignados_por_profesor = {}
    num_asignados = 0
    num_estudiantes_asignados = 0
    
    for weight in tribunales_group_profesor.keys():
        tribunales_asignados_por_profesor[weight] = {}
        for teacher in tribunales_group_profesor[weight].keys():
            tribunales_asignados_por_profesor[weight][teacher] = []
    
    
    for weight in tribunales_group_profesor.keys():
        for teacher in tribunales_group_profesor[weight].keys():
            for tribunal in tribunales_group_profesor[weight][teacher]:
                if tribunal["asignado"]:

                    teacher1 = tribunal["profesor1"]
                    teacher2 = tribunal["profesor2"]

                    num_asignados += 1
                    dict_tribunal = {}
                    if "estudiante" in tribunal.keys():
                        dict_tribunal["Estudiante"] = tribunal['estudiante']
                        dict_tribunal["Tribunal"] = tribunal
                        del dict_tribunal["Tribunal"]['estudiante']

                        tribunales_asignados_por_profesor[weight][teacher1].append(dict_tribunal)
                        tribunales_asignados_por_profesor[weight][teacher2].append(dict_tribunal)

                        num_estudiantes_asignados += 1
            
#         print(f"El numero de tribunales asignados de {teacher} es: {len(tribunales_asignados_por_profesor[teacher])}")
#     print(f"Los tribunales asignados son: {tribunales_asignados_por_profesor}")
    
    copia_tribunales = copy.deepcopy(tribunales_group_profesor)

    copia_students = set(copy.deepcopy(students))

    estudiantes_asignados = []

    iteracion = 0

    at_least_expert_interested = True
    at_least_one_expert = True
    at_least_one_interested = True

    constraints = [at_least_one_expert, at_least_one_interested, at_least_expert_interested]

    num_iters_sin_asignaciones = 0
    num_tribunales_asignados = 0

    # Podría hacer algo así como: while not siguiente_student (buscar tribunal posible, relajando constraints o algo así)
    for weight in tribunales_group_profesor.keys():
        print(weight)
        num_iters_sin_asignaciones = 0
        
        while num_tribunales_asignados < len(students):

            # "Desordenar" los tribunales de orden para evitar que si hay un profesor que provoca que no haya soluciones evitarle
            l = list(copia_tribunales[weight].items())
            random.shuffle(l)
            d_shuffled = dict(l)
            copia_tribunales[weight] = copy.deepcopy(d_shuffled)

            print(f"**************************\nIteracion {iteracion}")
            tribunales_asignados_por_profesor_iter, tribunales_actualizados, estudiantes_asignados_nuevos = await asignar_tribunales(copia_students, copia_tribunales[weight], constraints, observable)

            for profesor, tribunal_asignado_iter in tribunales_asignados_por_profesor_iter.items():
                tribunales_asignados_por_profesor[weight][profesor].extend(tribunal_asignado_iter)

            estudiantes_asignados.extend(estudiantes_asignados_nuevos)
            copia_students = set(copia_students) - set(estudiantes_asignados_nuevos)

            copia_tribunales[weight] = copy.deepcopy(tribunales_actualizados)

            if(len(estudiantes_asignados_nuevos) == 0):
                num_iters_sin_asignaciones+= 1

            if(num_iters_sin_asignaciones == 2):
                print("Ahora da igual que la pareja sea experto-interesado como minimo")
                at_least_expert_interested = False

            if(num_iters_sin_asignaciones == 4):
                print("Ahora da igual que no haya un experto")
                at_least_one_expert = False

            if(num_iters_sin_asignaciones == 6):
                print("Ahora da igual que no estén interesados")
                at_least_one_interested = False

            if(num_iters_sin_asignaciones == 10):
                print("No se encuentran más posibles tribunales")
                break


            constraints = [at_least_one_expert, at_least_one_interested, at_least_expert_interested]

            num_tribunales_asignados = len(estudiantes_asignados)
            print(f"El numero de tribunales asignados es: {num_tribunales_asignados}\n")
            iteracion += 1
    
    return tribunales_asignados_por_profesor, estudiantes_asignados


"""
Leer datos de profesores que están en un fichero json
"""
def leer_datos_profesores(fichero):
    with open(fichero, 'r', encoding = "UTF-8") as j:
         data = json.loads(j.read())
    return data

    
"""
Realizar todos los pasos para asignar tribunales
"""
async def realiza_pasos_y_asigna(data, observable):
    global num_estudiantes_total
    nuevo_data = generate_possible_free_hours_per_teacher(data)
    
    students, english_students, teachers, english_teachers = get_students_and_teachers(nuevo_data)
    num_estudiantes_total = len(students)
    
    tribunales_ingles = generate_possible_tribunales(english_teachers)
    tribunales_ingles.sort(key=lambda x: x["peso"], reverse=True)
    
    tribunales_group_peso_ingles = group_by_weight(tribunales_ingles)
    tribunales_group_profesor_ingles = group_by_teacher(tribunales_group_peso_ingles, english_teachers)
    
    
    tribunales = generate_possible_tribunales(teachers)
    tribunales.sort(key=lambda x: x["peso"], reverse=True)
    
    tribunales_group_peso = group_by_weight(tribunales)
    tribunales_group_profesor = group_by_teacher(tribunales_group_peso, teachers)
#     print(len(tribunales))
    num_tribunales_profesor_ingles = calcular_tribunales_por_profesor(english_students, english_teachers)
    num_tribunales_profesor = calcular_tribunales_por_profesor(students, teachers)
    
    tribunales_asignados_por_profesor_ingles, estudiantes_asignados_ingles = await asegura_asignacion_tribunales(tribunales_group_profesor_ingles, english_students, num_tribunales_profesor_ingles, observable)
    
    
    for weight in tribunales_asignados_por_profesor_ingles.keys():
        for english_teacher, english_tribunales_asignados in tribunales_asignados_por_profesor_ingles[weight].items():
            overall_tribunales_por_asignar_profesor = copy.deepcopy(tribunales_group_profesor[weight][english_teacher])

            for english_tribunal_asignado in english_tribunales_asignados:

                copia_tribunal = copy.deepcopy(english_tribunal_asignado["Tribunal"])
                copia_tribunal["asignado"] = False

                if copia_tribunal in overall_tribunales_por_asignar_profesor:
                    ## Marcar los tribunales que se han asignado en inglés como asignados en los tribunales "generales", añadimos también la key: estudiante para no perder esa información
                    teacher1 = copia_tribunal["profesor1"]
                    teacher2 = copia_tribunal["profesor2"]

                    indice1 = tribunales_group_profesor[weight][teacher1].index(copia_tribunal)
                    indice2 = tribunales_group_profesor[weight][teacher2].index(copia_tribunal)

                    tribunales_group_profesor[weight][teacher1][indice1]["asignado"] = True
                    tribunales_group_profesor[weight][teacher1][indice1]["estudiante"] = english_tribunal_asignado["Estudiante"]
                    tribunales_group_profesor[weight][teacher2][indice2]["asignado"] = True
                    tribunales_group_profesor[weight][teacher2][indice2]["estudiante"] = english_tribunal_asignado["Estudiante"]
                
    students = list(set(students)-set(estudiantes_asignados_ingles))
    
    tribunales_asignados_por_profesor, estudiantes_asignados = await asegura_asignacion_tribunales(tribunales_group_profesor, students, num_tribunales_profesor, observable)
    
    
    
    ########################################## IMPRIMIR DATOS DE ASIGNACION ##########################################
    
    for weight in tribunales_asignados_por_profesor.keys():
        for profesor, tribunales_asignados in tribunales_asignados_por_profesor[weight].items():
            profesor_json = get_teacher_json(profesor)

            print(f"El profesor {profesor} ({profesor_json['tutor']['titulacion']}) tiene {len(tribunales_asignados)}/{profesor_json['tutor']['tribunales_restantes']} tribunales asignados")
            if len(tribunales_asignados) == 0:
                continue

    #         print(tribunales_asignados)
            if len(tribunales_asignados) > profesor_json['tutor']['tribunales_restantes']:
                print("########################")
                print(tribunales_asignados)
                print("########################")

            for tribunal_asignado in tribunales_asignados:
                await asyncio.sleep(0.01)

                if "(" in tribunal_asignado["Tribunal"]["profesor1"] and "(" in tribunal_asignado["Tribunal"]["profesor2"]:
                    continue

                profesor1 = copy.deepcopy(tribunal_asignado["Tribunal"]["profesor1"])
                profesor2 = copy.deepcopy(tribunal_asignado["Tribunal"]["profesor2"])

                pattern = r"\(\w+\)"
                profesor1 = re.sub(pattern, '', profesor1)
                profesor2 = re.sub(pattern, '', profesor2)

                if profesor in tribunal_asignado["Tribunal"]["profesor1"]: 
                    profesor2_json = get_teacher_json(profesor2)
                else:
                    profesor2_json = get_teacher_json(profesor1)

                profesor2_json = get_teacher_json(profesor2)

                titulacion_profesor1 = profesor_json["tutor"]["titulacion"]
                titulacion_profesor2 = profesor2_json["tutor"]["titulacion"]


                tribunal_asignado["Tribunal"]["profesor1"] += " (" + titulacion_profesor1 + ")"
                tribunal_asignado["Tribunal"]["profesor2"] += " (" + titulacion_profesor2 + ")"
    
    return tribunales_asignados_por_profesor
    
    
    
def json_encoder(obj):
    if isinstance(obj, datetime):
        fecha = obj.isoformat(timespec="minutes") # Devuelve: 1900-01-01T20:00
        return fecha
        
    raise TypeError("Type not serializable")
    
    
    
indices_teachers_students = {}
convocatoria = None
data = None

async def main_asignar(datos, fechas, convocatoria_input, observable):
    global fechas_asignacion
    global indices_teachers_students
    global data
    global convocatoria
    
    if isinstance(datos,str):
        data = leer_datos_profesores(datos)
    else:
        data = datos
    
    # print(data)
    # data = datos
    fechas_asignacion = fechas
    convocatoria = convocatoria_input
    
    # Iterate through the data
    # Save indices of appearance:
    for index, tutor_data in enumerate(data):
        indices_teachers_students[tutor_data["nombre_tutor"]] = index
        for index2, alumnos_asignados in enumerate(tutor_data["tutor"]["asignacion"]):
            indices_teachers_students[alumnos_asignados] = [index, index2]

    tribunales_asignados_por_profesor = await realiza_pasos_y_asigna(data, observable)
    
    file_path = 'asignaciones.json'

    # Open the file in write mode and use json.dump to write the data
    with open(file_path, 'w') as json_file:
        json.dump(tribunales_asignados_por_profesor, json_file, indent=2, default=json_encoder)
    
    return tribunales_asignados_por_profesor
        
# asyncio.run(main_asignar("datos_simulados.json", ["2024-04-08","2024-04-16"], "julio", Subject()))