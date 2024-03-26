from asignar_tribunales_ING_ESP_asyncio_multiples_semanas import *
from prueba_calendario import *
# from lectura_horarios_de_profesores import *
from lectura_horarios_de_profesores_playwright_semanas import *
from lectura_excel import *
from exportar_asignaciones import *

# from asignar_tribunales_threading import *
# Librería Tkinter
import tkinter as tk
from tkinter import ttk
from tkinter import Tk
from tkinter import messagebox, Label, Entry
from tkinter import filedialog
from tkcalendar import Calendar
import os

#Librería asyncio
import asyncio

#Librería RXpy
from rx.core import Observable
from rx.subject import Subject



##### La idea de esta clase es de: https://bugs.python.org/file50712/tkasyncio.py
class AsyncTk(Tk):
    "Basic Tk with an asyncio-compatible event loop"
    def __init__(self):
        super().__init__()
        self.running = True
        self.runners = [self.tk_loop()]

    async def tk_loop(self):
        "asyncio 'compatible' tk event loop?"
        # Is there a better way to trigger loop exit than using a state vrbl?
        while self.running:
            self.update()
            await asyncio.sleep(0.01) # obviously, sleep time could be parameterized

    def stop(self):
        print("HOLA ESTO ES STOP")
#         super().quit()
        self.destroy()
        self.running = False

    async def run(self):
        await asyncio.gather(*self.runners)


class AsignTribunalsGUI(AsyncTk):
    def __init__(self):
        
        super().__init__()
        
        # Iniciamos la cola y los workers
        self.queue = asyncio.Queue()
        self.runners.append(self.worker("1"))
        self.runners.append(self.worker("2"))
        self.runners.append(self.worker("3"))
        
        # No funciona -> Aún dándole a la x sigue corriendo el programa🤷‍♂️
        self.protocol("WM_DELETE_WINDOW", self.stop)
        
        self.title("GUI")
        
        tabControl = ttk.Notebook()
        tab1 = ttk.Frame(tabControl)
        tab2 = ttk.Frame(tabControl)
        tabControl.add(tab1, text='Carga de datos')
        tabControl.add(tab2, text='Asignaciones')
        
        tabControl.pack(expand = 1, fill ="both") 
        
        # Title label
        self.title_label = tk.Label(tab1, text="Cargar excel con datos", font=("Helvetica", 12, "bold"))
        self.title_label.grid(row=0, columnspan=3, padx=5, pady=10)

        # Cargar excel
        self.upload_button = tk.Button(tab1, text="Cargar excel", command=self.upload_excel)
        self.upload_button.grid(row=1, column=0, padx=5, pady=5)
        
        self.upload_label = tk.Label(tab1, text="Archivo cargado:")
        self.upload_label.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        self.uploaded_file_label = tk.Label(tab1, text="")
        self.uploaded_file_label.grid(row=1, column=2, padx=5, pady=5)

        # Line
        self.line = tk.Canvas(tab1, width=600, height=20)
        self.line.create_line(0, 20, 600, 20, fill="black")
        self.line.grid(row=2, columnspan=3, padx=5, pady=5)
        
        # Title label
        title_label = tk.Label(tab1, text="Parón de clases y convocatoria", font=("Helvetica", 12, "bold"))
        title_label.grid(row=3, columnspan = 3, padx=5, pady=5)

        # Checkbox
        self.checkbox_var = tk.BooleanVar()
        self.checkbox = tk.Checkbutton(tab1, text="Se pararán las clases", variable=self.checkbox_var, command=self.on_checkbox_click)
        self.checkbox.grid(row=4, column = 0, padx=5, pady=5)
        
        # Add a combobox
        self.convocatoria_combobox = ttk.Combobox(tab1, values=["diciembre", "abril", "julio"], state="readonly")
        self.convocatoria_combobox.grid(row=4, column = 1, pady=10)
        self.convocatoria_combobox.set("abril")  # Set default selection
        
        # Line
        self.line = tk.Canvas(tab1, width=600, height=20)
        self.line.create_line(0, 20, 600, 20, fill="black")
        self.line.grid(row=5, columnspan=3, padx=5, pady=5)
        
        # Title label
        self.title_label2 = tk.Label(tab1, text="Selecciona el intervalo de defensas", font=("Helvetica", 12, "bold"))
        self.title_label2.grid(row=6, columnspan=3, padx=5, pady=10)
        
        # Fecha inicio de tribunales
        self.title_label2 = tk.Label(tab1, text="Selecciona la fecha de inicio", font=("Helvetica", 12, "bold"))
        self.title_label2.grid(row=7, column = 0, padx=0, pady=10)
        # Fecha inicio de tribunales
        self.title_label2 = tk.Label(tab1, text="Selecciona la fecha de fin", font=("Helvetica", 12, "bold"))
        self.title_label2.grid(row=7, column = 1, padx=5, pady=10)
        
       # Recoger horarios
        self.cal_ini = Calendar(tab1, font="Arial 8", selectmode="day", date_pattern="y-mm-dd", date_entry_width=50, date_entry_height=50)
        self.cal_ini.grid(row=8, column=0, padx=3, pady=3)
        # Recoger horarios
        self.cal_fin = Calendar(tab1, font="Arial 8", selectmode="day", date_pattern="y-mm-dd", date_entry_width=50, date_entry_height=50)
        self.cal_fin.grid(row=8, column=1, padx=3, pady=3)

        self.get_horarios_button = tk.Button(tab1, text="Recoger horarios", command=self.get_horarios)
        if not self.uploaded_file_label.cget("text"):
            self.get_horarios_button.config(state="disabled")
        self.get_horarios_button.grid(row=8, column=2, padx=5, pady=5)

        # Line
        self.line = tk.Canvas(tab1, width=600, height=20)
        self.line.create_line(0, 20, 600, 20, fill="black")
        self.line.grid(row=9, columnspan=3, padx=5, pady=5)
        
        # Title label
        self.title_label4 = tk.Label(tab1, text="Asignar con los datos recogidos", font=("Helvetica", 12, "bold"))
        self.title_label4.grid(row=10, columnspan=3, padx=5, pady=10)

        # Button to assign tribunales
        self.assign_button = tk.Button(tab1, text="Asignar tribunales", command=self.asignar_tribunales)
#         if "datos.txt" not in os.listdir() and not self.reused_file_label.cget("text"):
        self.assign_button.config(state="normal")
        self.assign_button.grid(row=11, columnspan=3, padx=5, pady=5)
        
        # Observable and observer
        self.observable = Subject()
        self.observable.subscribe(self.observer)
        
        # Data from executions
        self.horarios_con_datos = None
        self.lista_datos = None
        self.datos_excel = None
        self.intervalo_tribunales = None
        self.asignaciones = None
        
        
        
    async def worker(self,name):
        while self.running:
            # Recogemos una url y su titulo para cada imagen detectada
            tarea, fichero = await self.queue.get()

            if tarea == "asignar_tribunales":
                await self.asignar(fichero)
            elif tarea == "get_horarios":
                await self.recoger_horarios(fichero)
            elif tarea == "recoger_datos_excel":
                await self.recoger_datos(fichero)
            elif tarea == "exportar_tribunales":
                await self.exportar_tribunales_excel(fichero)
                
            # Notificamos a la cola que la tarea se ha completado
            self.queue.task_done()
        if not self.running:
            print(f"Ha parado el worker{name}")

            
            
    def upload_excel(self):
        file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xls*"), ("All files", "*.*")])
        if file_path:
            self.uploaded_file_label.config(text=file_path)
            self.get_all_data()
            
    def on_checkbox_click(self):
        if self.checkbox_var.get() == 1:
            print("Clases se pararán")
        else:
            print("Clases no se pararán")
    
    ############################### REALIZAR TAREAS ASÍNCRONAS ###############################
    
    # Recogemos todos los horarios de los profesores de forma asíncrona
    async def recoger_horarios(self, fichero):
        # Toplevel object which will 
        # be treated as a new window
        self.newWindow = tk.Toplevel(self)
        self.progressbar = ttk.Progressbar(self.newWindow, orient=tk.HORIZONTAL, length=300, mode='determinate')
        self.progressbar.grid(row=2, column=0, padx=(8, 8), pady=(16, 0), columnspan=3)
        
        self.text_area = tk.Text(self.newWindow, height=10, width=40)
        self.text_area.grid(row=0, pady=10)
        
        # Create a vertical scrollbar
        self.scrollbar = tk.Scrollbar(self.newWindow, command=self.text_area.yview)
        self.scrollbar.grid(row=0, column=1, sticky='ns')
        # Attach the scrollbar to the text area
        self.text_area.config(yscrollcommand=self.scrollbar.set)

        
        fecha_inicial = self.cal_ini.get_date()
        fecha_final = self.cal_fin.get_date()
        paran_las_clases = self.checkbox_var.get()
        convocatoria = self.convocatoria_combobox.get()
        
        self.intervalo_tribunales = [fecha_inicial,fecha_final]
        # print(self.convocatoria_combobox.get())

        self.horarios_con_datos = await recoger_y_almacenar_horarios(fichero, self.datos_excel, self.intervalo_tribunales, paran_las_clases, self.observable)
        self.assign_button.config(state="normal")
        # self.get_other_data_button.config(state="normal")
        
    async def recoger_datos(self, fichero_excel):
        # Toplevel object which will 
        # be treated as a new window
        self.newWindow = tk.Toplevel(self)
        self.progressbar = ttk.Progressbar(self.newWindow, orient=tk.HORIZONTAL, length=300, mode='determinate')
        self.progressbar.grid(row=2, column=0, padx=(8, 8), pady=(16, 0), columnspan=3)
        
        self.datos_excel = await leer_escribir_datos(fichero_excel, self.observable)
            
        # self.assign_button.config(state="normal")
        self.get_horarios_button.config(state="normal")
    
    # Hacemos la asignacion de forma asíncrona
    async def asignar(self, fichero):
        # Toplevel object which will 
        # be treated as a new window
        self.newWindow = tk.Toplevel(self)
        self.progressbar = ttk.Progressbar(self.newWindow, orient=tk.HORIZONTAL, length=300, mode='determinate')
        self.progressbar.grid(row=2, column=0, padx=(8, 8), pady=(16, 0), columnspan=3)
        
        self.text_area = tk.Text(self.newWindow, height=10, width=40)
        self.text_area.grid(row=0, pady=10)
        
        # Create a vertical scrollbar
        self.scrollbar = tk.Scrollbar(self.newWindow, command=self.text_area.yview)
        self.scrollbar.grid(row=0, column=1, sticky='ns')
        # Attach the scrollbar to the text area
        self.text_area.config(yscrollcommand=self.scrollbar.set)
        
        self.button_exportar = tk.Button(self.newWindow, text="Exportar asignación de tribunales", command=self.exportar_tribunales)
        self.button_exportar.config(state="disabled")
        self.button_exportar.grid(row=3, columnspan=3, padx=5, pady=5)

        convocatoria = self.convocatoria_combobox.get()

        self.asignaciones = await main_asignar(fichero, self.intervalo_tribunales, convocatoria, self.observable)
        
    async def exportar_tribunales_excel(self, fichero):
        
        fecha_inicial = self.cal_ini.get_date()
        fecha_final = self.cal_fin.get_date()
        self.intervalo_tribunales = [fecha_inicial,fecha_final]
        
        await exportar_asignaciones_excel(fichero, self.intervalo_tribunales)
        self.newWindow.destroy()
    ##########################################################################################
        
    
    
    ############################### AÑADIR A LA COLA TAREAS ASÍNCRONAS #################################  
    
    def get_horarios(self):
        self.queue.put_nowait(("get_horarios",self.uploaded_file_label.cget("text")))
        
    def get_all_data(self):
        self.queue.put_nowait(("recoger_datos_excel",self.uploaded_file_label.cget("text")))
    
    def asignar_tribunales(self):
        self.queue.put_nowait(("asignar_tribunales", self.horarios_con_datos))
        
    def exportar_tribunales(self):
        self.queue.put_nowait(("exportar_tribunales", self.asignaciones))
    
    ####################################################################################################    
        
    
    # En el caso de que la descarga se realice con exito, se actualiza la GUI
    def observer(self, data):
        tarea, *datos = data
        
        if tarea == "asignar_tribunales":
            num_estudiantes_asignados, num_estudiantes_total, student = datos
            if num_estudiantes_asignados == -1:
                self.progressbar['maximum'] = 1
                self.progressbar['value'] = 0
            
                self.text_area.insert("end", string + "\n")
            else:
                
                self.progressbar['maximum'] = num_estudiantes_total
                # Actualizamos la barra de progreso
                self.progressbar['value'] = num_estudiantes_asignados

                texto = f"Se ha asignado un tribunal para {student}"

                self.text_area.insert("end", texto + "\n")
            
            if num_estudiantes_asignados == num_estudiantes_total:
                self.button_exportar.config(state="normal")
            
        elif tarea == "get_horarios":
            iteracion, max_iters, string = datos
            
            if iteracion == -1:
                self.progressbar['maximum'] = 1
                self.progressbar['value'] = 0
            
                self.text_area.insert("end", string + "\n")
            else:
                
                self.progressbar['maximum'] = max_iters
                # Actualizamos la barra de progreso
                self.progressbar['value'] = iteracion

                texto = f"Se ha descargado el horario de {string}"

                self.text_area.insert("end", texto + "\n")
            
            if iteracion == max_iters:
                self.newWindow.destroy()

        
        elif tarea == "recoger_datos_excel":
            iteracion, max_iters = datos
            self.progressbar['maximum'] = max_iters
            # Actualizamos la barra de progreso
            self.progressbar['value'] = iteracion
            if iteracion == max_iters:
                self.newWindow.destroy()
            descargado con éxito {int(self.progressbar['value'])} imagenes")

async def main():
    asing_tribunal_gui = AsignTribunalsGUI()
    await asing_tribunal_gui.run()

# if __name__ == '__main__':
asyncio.run(main())
