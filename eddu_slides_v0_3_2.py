#!/usr/bin/env python3
"""
Programa para digitalizar diapositivas
"""
import io
import os
import shutil
import configparser
import logging
import sys
import threading
import subprocess
from pathlib import Path # pylint: disable=W0611
try:
    import tkinter as tk
    from tkinter import filedialog, messagebox
except ImportError:
    print("tkinter no está instalado. Instalando...")
    subprocess.check_call(['sudo', 'apt', 'install', '-y', 'python3-tk'])
    os.execv(sys.executable, ['python3'] + sys.argv)
    import tkinter as tk
    from tkinter import filedialog, messagebox
try:
    import gphoto2 as gp
except ImportError:
    print("gphoto2 no está instalado. Instalando...")
    subprocess.check_call(['sudo', 'apt', 'install', '-y', 'python3-gphoto2'])
    os.execv(sys.executable, ['python3'] + sys.argv)  # Reinicia el script
    import gphoto2 as gp
try:
    import numpy as np
except ImportError:
    print("numpy no está instalado. Instalando...")
    subprocess.check_call(['sudo', 'apt', 'install', '-y', 'python3-numpy'])
    os.execv(sys.executable, ['python3'] + sys.argv)  # Reinicia el script
    import numpy as np
from PIL import Image as Imge

try:
    from kivy.app import App
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.anchorlayout import AnchorLayout
    from kivy.uix.image import Image
    from kivy.clock import Clock
    from kivy.graphics.texture import Texture # pylint: disable=E0611
    from kivy.uix.button import Button
    from kivy.uix.gridlayout import GridLayout
    from kivy.uix.label import Label
    from kivy.properties import StringProperty # pylint: disable=E0611
    from kivy.uix.popup import Popup
    from kivy.uix.scrollview import ScrollView
    from kivy.uix.textinput import TextInput
    from kivy.core.window import Window
    from kivy.uix.filechooser import FileChooserListView #FileChooserIconView
except ModuleNotFoundError:
    print("Kivy no está instalado. Instalando...")
    subprocess.check_call(["sudo", "apt", "install", "-y", "python3-kivy"])
    os.execv(sys.executable, ['python3'] + sys.argv)
    from kivy.app import App
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.anchorlayout import AnchorLayout
    from kivy.uix.image import Image
    from kivy.clock import Clock
    from kivy.graphics.texture import Texture # pylint: disable=E0611
    from kivy.uix.button import Button
    from kivy.uix.gridlayout import GridLayout
    from kivy.uix.label import Label
    from kivy.properties import StringProperty # pylint: disable=E0611
    from kivy.uix.popup import Popup
    from kivy.uix.scrollview import ScrollView
    from kivy.uix.textinput import TextInput
    from kivy.core.window import Window
    from kivy.uix.filechooser import FileChooserListView #FileChooserIconView

logging.getLogger("PIL").setLevel(logging.CRITICAL)

config = configparser.ConfigParser()
# TODO : mejorar esto, que se fije el archivo en el mismo directorio del .py
#config.read('/home/cintel/Descargas/lapaslides.ini')

# TODO: Preguntar por nombre del archivo
#nombre_archivo = config ['DEFAULT']['nombre_archivo']
PREFIJO_ARCHIVO = "UY-UDELAR-AGU-"

# Constantes para mensajes
MENSAJE_PIDO_ROLLO = ("Es necesario saber el número de rollo con el que va a trabajar \n"
    "y la cantidad de dígitos.")

@staticmethod
def ingresar_nombre_archivo():
    """Ingresar el nombre que le sigue a UY-UDELAR-AGU"""
    # Crear la ventana principal
    root = tk.Tk()
    root.title("Ingreso del nombre de archivo")

    # Obtener las dimensiones de la pantalla
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    # Obtener las dimensiones de la ventana
    window_width = 400  # Ancho de la ventana
    window_height = 200  # Alto de la ventana

    # Calcular las coordenadas de la posición central
    position_top = int(screen_height / 2 - window_height / 2)
    position_right = int(screen_width / 2 - window_width / 2)

    # Establecer la geometría de la ventana (concentrada)
    root.geometry(f'{window_width}x{window_height}+{position_right}+{position_top}')

    # Eviar que el usuario cierre la ventana sin ingresar datos
    def on_closing():
        if messagebox.askyesno("Salir", "¿Seguro que quieres salir?"):
            root.destroy()
            sys.exit()

    root.protocol("WM_DELETE_WINDOW", on_closing)

    # Etiqueta para mostrar el mensaje
    label = tk.Label(
        root,
        text="Ingresa el nombre del archivo:\n" + PREFIJO_ARCHIVO,
        font=("Arial", 12)
    )
    label.pack(pady=10)

    # Campo de texto centrado
    nombre_archivo_var = tk.StringVar()

    # Crear un Entry centrado
    entry = tk.Entry(
        root,
        textvariable=nombre_archivo_var,
        font=("Arial", 12),
        justify="center"
    )
    entry.pack(pady=10)
    entry.focus()

    # Función de acción para el botón
    def on_ok():
        if nombre_archivo_var.get().strip():
            root.destroy()  # Cerrar la ventana
        else:
            messagebox.showerror(
                "Error",
                "No ha ingresado el nombre del archivo.\nPor favor, ingrese nuevamente."
            )

    # Botón OK
    ok_button = tk.Button(root, text="OK", command=on_ok)
    ok_button.pack(pady=10)

    entry.bind("<Return>", lambda event: ok_button.invoke())
    entry.bind("<KP_Enter>", lambda event: ok_button.invoke())

    # Iniciar la ventana
    root.mainloop()

    return PREFIJO_ARCHIVO + nombre_archivo_var.get().upper().strip() + '-'

NOMBRE_ARCHIVO = ingresar_nombre_archivo()
print(NOMBRE_ARCHIVO)

# directorio = config ['DEFAULT']['directorio']
def seleccionar_directorio():
    """
    Selecciona donde se van a guardar las fotos
    """
    root = tk.Tk()
    root.withdraw()
    while True:
        carpeta_seleccionada = filedialog.askdirectory(
                                    title="Selecionar Carpeta",
                                    initialdir=os.path.expanduser("~/Documentos/Slides/Fotos/")
                                )
        if carpeta_seleccionada:
            return carpeta_seleccionada

        respuesta = messagebox.askretrycancel(
            "Error",
            "No se ha seleccionado ninguna carpeta. ¿Quieres intentarlo de nuevo?"
        )
        if not respuesta:  # Si el usuario presiona 'Cancelar'
            sys.exit() # cierra completamente el programa

directorio = seleccionar_directorio()
print(directorio)

#Builder.load_string("""
#""")

#Raiz donde se guardaràn las fotos
#nombre_archivo = 'test-'
#Nombre que se despliega del script
TITULO = NOMBRE_ARCHIVO
#directorio = '/home/lapa/cacho/test/'

# TODO: Pensar una forma de designarlas
CAMARA_2='c0424154da82472289e0caaf837f612b'
CAMARA_1='00000000000000000000000008841539'

class CustomFileChooserListView(FileChooserListView):
    '''
    Clase para deshabilitar scroll en el FileChooserListView y permitir seleccionar solo carpetas.
    '''
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Habilitar solo la navegación por teclado
        self.do_scroll_y = False  # Deshabilitar el desplazamiento vertical
        self.do_scroll_x = False  # Deshabilitar el desplazamiento horizontal

        # Establecemos la selección inicial al primer elemento
        if self.files:
            self.selected = self.files[0]  # Seleccionar el primer archivo
        else:
            self.selected = None


    def is_selected(self, filename):
        '''
        Permitir seleccionar solo carpetas (no archivos).
        '''
        return os.path.isdir(filename) and not filename.startswith('.')

class CamApp(App):
    '''
    CamAppp
    '''
    directorio_app = directorio
    print(f"Directorio app {directorio_app}")

    ruta_script = os.path.abspath(__file__)
    directorio_base = os.path.dirname(ruta_script)
    directorio_temporal = os.path.join(directorio_base, "temp")

    if not os.path.exists(directorio_temporal):
        os.makedirs(directorio_temporal)

    camaras_conectadas = False  # Flag para saber si las cámaras están conectadas
    reconnect_attempts = 0 # Contador de intentos
    max_retries = 10 # Número máximo de intentos

    layout = any

    def __init__(self, **kwargs):
        '''Método de inicialización de la clase'''
        super().__init__(**kwargs)

        self.color_botones = (1, 0, 0, 0.5)  # Color original (rojo traslúcido)
        self.numero_de_rollo =  StringProperty(' ')
        self.camara_previ = '0'
        self.lview = False
        self.img1 = Image(source='fb.png', size=(1024,768))
        self.title = TITULO

        self.estado_actual = self.directorio_app
        self.numero_de_rollo_anterior = ''
        self.operacion_en_curso = False
        self.imagen_espejada = False
        self.timer = ''
        self.path_label = ''
        self.popup = ''
        self.error_label = ''
        self.textinput = ''
        self.camera_01 = ''
        self.camera = ''
        self.camara = ''
        self.camera_der = ''
        self.camera_izq = ''
        self.cartel_rollo = ''
        self.muestro_nro_rollo = ''
        self.btn0 = ''
        self.btn1 = ''
        self.btn2 = ''
        self.btn_rollo = ''
        self.btn_directorio = ''
        self.btn_ndiapo = ''
        self.btn_diapo = ''
        self.btn_apertura = ''
        self.btn_caratula = ''
        self.textinput_digitos = ''
        self.btn_abrir_carpeta = ''

    def build(self):
        '''Crea la applicacion'''
        # Window.bind(on_key_down=self.key_action)

        # Vincular el evento de cierre de la ventana a la función btn_exit_callback
        #Window.bind(on_request_close=self.btn_exit_callback)

        # Tamaño de la pantalla
        Window.maximize()
        Window.top = 0  # Posiciona la ventana en la parte superior
        Window.left = 0  # Posiciona la ventana en la parte izquierda
        #Window.clearcolor = (0.1, 0.1, 0.1, 0.2)

        layout = BoxLayout(orientation='vertical')

        self.estado_actual = Button(
            text=f"Directorio: {self.directorio_app}",
            size_hint=(None, 0.04),
            pos_hint={'center_x':0.5},
            background_color=(0.1, 0.1, 0.1, 0.2)
        )
        layout.add_widget(self.estado_actual)

        layout.add_widget(self.img1, 0)
        self.asignar_camaras()

        #Interfaz kivi
        bottom_layout = BoxLayout(
            orientation='horizontal',
            size_hint=(1,None),
            height=100,
            pos_hint={'center_x': 0.5, 'bottom':1}
        )
        # Crear un AnchorLayout para centrar el GridLayout (box2) horizontalmente
        anchor_layout = AnchorLayout(anchor_x='center', anchor_y='bottom', size_hint=(1, 1))

        box2 = GridLayout(
            cols = 11,
            col_default_width=20,
            row_default_height=80,
            size_hint=(None, None)
        )
        # pylint: disable=no-member
        box2.bind(minimum_size=box2.setter('size'))

        self.muestro_nro_rollo  = Label(
            text=MENSAJE_PIDO_ROLLO,
            halign="center",
            valign='middle'
        )

        ## Digitalizar
        self.btn_diapo = Button(
            text = "Diapo\n(z)",
            size_hint = (None,0.1),
            background_color = self.color_botones,
            halign="center",
            valign="middle"
        )
        self.btn_caratula = Button(
            text = "Anverso\n(x)",
            size_hint = (None,0.1),
            background_color = self.color_botones,
            halign="center",
            valign="middle"
        )
        self.btn_apertura = Button(
            text = "Reverso\n(c)",
            size_hint = (None,0.1),
            background_color = self.color_botones,
            halign="center",
            valign="middle"
        )

        self.btn_ndiapo = Button(
            text = "Editar N° ítem\n(v)",
            size_hint = (None,0.1),
            background_color = self.color_botones,
            halign="center",
            valign="middle"
        )
        self.btn_directorio = Button(
            text = "Cambiar Dir\n(,)",
            size_hint=(None, 0.1),
            background_color = self.color_botones,
            halign="center",
            valign="middle"
        )

        ## extras
        self.btn0 = Button(
            text = "Prev Marco\n(b)",
            size_hint = (None,0.1),
            background_color = self.color_botones,
            halign="center",
            valign="middle"
        )
        self.btn1 = Button(
            text = "Prev Diapo\n(n)",
            size_hint = (None,0.1),
            background_color = self.color_botones,
            halign="center",
            valign="middle"
        )

        self.btn2 = Button(
            text = "Salir\n(m)",
            size_hint = (None,0.1),
            background_color = self.color_botones,
            halign="center",
            valign="middle"
        )
        self.btn_rollo = Button(
            text = " ",
            size_hint = (None,0.1),
            background_color = self.color_botones,
            halign="center",
            valign="middle"
        )
        self.btn_abrir_carpeta = Button(
            text="Abrir Carpeta\n(-)",
            size_hint = (None,0.1),
            background_color = self.color_botones,
            halign="center",
            valign="middle"
        )
        self.btn_rotar_diapo = Button(
            text="Rotar Diapo\n(r)",
            size_hint = (None,0.1),
            background_color = self.color_botones,
            halign="center",
            valign="middle"
        )

        self.btn_caratula.bind(on_press=lambda *args: self.btn0_callback(self,'anverso'))
        self.btn_apertura.bind(on_press=lambda *args: self.btn0_callback(self,'reverso'))
        self.btn_diapo.bind(on_press=lambda *args: self.btn0_callback_camera_01(self,'diapo'))

        self.btn0.bind(on_press=lambda *args: self.arranca_callback(self,'0'))
        self.btn1.bind(on_press=lambda *args: self.arranca_callback(self,'1'))
        self.btn_ndiapo.bind(on_press=lambda *args: self.pido_rollo())
        self.btn2.bind(on_press=self.btn_exit_callback)
        self.btn_rollo.bind(on_press=self.aumentar_1_nro_rollo)
        self.btn_rotar_diapo.bind(on_press=self.rotar_diapo)

        self.btn_directorio.bind(on_press=self.cambiar_directorio)

        box2.add_widget(self.btn_diapo)
        box2.add_widget(self.btn_caratula)
        box2.add_widget(self.btn_apertura)

        box2.add_widget(self.btn_ndiapo)
        box2.add_widget(self.btn0)
        box2.add_widget(self.btn1)
        box2.add_widget(self.btn2)
        box2.add_widget(self.btn_directorio)
        box2.add_widget(self.btn_rollo)
        box2.add_widget(self.btn_abrir_carpeta)
        box2.add_widget(self.btn_rotar_diapo)

        anchor_layout.add_widget(box2)
        bottom_layout.add_widget(anchor_layout)
        layout.add_widget(bottom_layout)
        # layout.add_widget(box2,0)
        self.cartel_rollo = GridLayout()
        self.timer = any

        return layout

    def asignar_camaras(self):
        """Asignar las cámaras disponibles basadas en los seriales."""
        asignacion_ok = True
        print("Comenzando asignación de cámaras")
        
        try:
            # Liberar cualquier cámara previamente asignada
            for attr in ['camera', 'camera_01', 'camara']:
                if hasattr(self, attr) and getattr(self, attr):
                    getattr(self, attr).exit()
                    setattr(self, attr, None)

            # Obtener lista de cámaras (método compatible)
            context = gp.Context()
            camera_list = []
            
            try:
                # Método moderno (nuevas versiones de gphoto2)
                for name, addr in gp.Camera.autodetect(context):
                    camera_list.append((name, addr))
            except AttributeError:
                # Método alternativo para versiones antiguas
                port_info_list = gp.PortInfoList()
                port_info_list.load()
                abilities_list = gp.CameraAbilitiesList()
                abilities_list.load(context)
                for name, addr in abilities_list.detect(port_info_list, context):
                    camera_list.append((name, addr))

            if not camera_list:
                print("No se detectaron cámaras conectadas")
                return False

            camera_list.sort(key=lambda x: x[0])  # Ordenar por nombre

            port_info_list = gp.PortInfoList()
            port_info_list.load()

            for name, addr in camera_list:
                print(f"Detectada cámara: {name} en {addr}")
                
                try:
                    camara = gp.Camera()
                    idx = port_info_list.lookup_path(addr)
                    camara.set_port_info(port_info_list[idx])
                    
                    print("Inicializando cámara...")
                    camara.init(context)
                    config_camara = camara.get_config(context)
                    
                    # Obtener número de serie
                    serialnumber_config = config_camara.get_child_by_name('serialnumber')
                    if serialnumber_config:
                        raw_value = serialnumber_config.get_value()
                        print(f"Serial detectado: {raw_value}")

                        # Asignar cámaras según el serial
                        if raw_value == CAMARA_1:
                            self.camera = camara
                            print(f"Asignada cámara 1 (serial: {raw_value})")
                        elif raw_value == CAMARA_2:
                            self.camera_01 = camara
                            print(f"Asignada cámara 2 (serial: {raw_value})")
                        else:
                            print(f"Serial no reconocido: {raw_value}")
                            camara.exit(context)
                            asignacion_ok = False
                    else:
                        print("No se pudo obtener el número de serie")
                        camara.exit(context)
                        asignacion_ok = False
                        
                except gp.GPhoto2Error as e:
                    print(f"Error al inicializar cámara {name}: {e}")
                    if 'camara' in locals():
                        camara.exit(context)
                    asignacion_ok = False

            return asignacion_ok
        except Exception as e:
            print(f"Error inesperado: {str(e)}")
            return False

    def key_action(self, *args):
        '''Teclas'''
        print (f"got a key event: {args[3]}")

        if args[3] == 'm': # Salir
            self.btn_exit_callback()
        elif args[3] == 'z': # Diapo
            self.btn0_callback_camera_01(self,'diapo')
        elif args[3] == 'x': # Anverso
            self.btn0_callback(self,'anverso')
        elif args[3] == 'c': # Reverso
            self.btn0_callback(self,'reverso')
        elif args[3] == 'v': # Item Numero
            self.pido_rollo()
        elif args[3]=='b': # Prev Marco
            self.arranca_callback(self,'0')
        elif args[3]=='n': # Prev Diapo
            self.arranca_callback(self,'1')
        elif args[3]==',': # Cambiar Dir
            self.cambiar_directorio()
        elif args[3]=='-':
            self.abrir_carpeta()
        elif args[3]=='+':
            self.aumentar_1_nro_rollo()
        elif args[3]=='r':
            self.rotar_diapo()
        return True

    def on_start(self):
        # Tamaño de la pantalla
        #Window.size = (1280, 720)
        Window.clearcolor = (0.1, 0.1, 0.1, 0.2)
        Window.bind(on_request_close=self.btn_exit_callback)

        Clock.schedule_once(lambda dt: self.pido_rollo(), 0.1)
        # self.pido_rollo()
        print ('arrancó')

    def pido_rollo(self):
        '''Ventana emergente para pedir el número de rollo'''
        Window.unbind(on_key_down=self.key_action)

        path = self.directorio_app

        ultimo_rollo = ""
        print('Data:', self.numero_de_rollo, path)

        # Crear el layout del popup
        self.cartel_rollo = GridLayout(cols = 1, rows = 7)

        # Etiqueta para el mensaje
        cartel = Label(
            text=MENSAJE_PIDO_ROLLO,
            valign='middle'
        )

        # Etiqueta para el mensaje de error
        self.error_label = Label(text='', color=(1, 0, 0, 1)) # Rojo para el mensaje de error

        #Botón para continuar
        archivo_nuevo = Button(text = "Continuar")

        # Agregar widgets al layout
        self.cartel_rollo.add_widget(cartel)

        # Etiqueta "Cantidad de dígitos"
        label_digitos = Label(
            text="Cantidad de dígitos",
            size_hint_y=None,
            height=30,
            valign='middle'
        )

        # Input para asignar entre 1 y 4
        self.textinput_digitos = TextInput(
            text='4',
            input_filter='int',
            multiline=False,
            hint_text="Cantidad de dígitos"
        )

        # Etiqueta "Número de rollo"
        label_num_rollo = Label(
            text="Número de Rollo",
            size_hint_y=None,
            height=30,
            valign='middle'
        )

         # Campo de entrada para el número de rollo
        self.textinput = TextInput(
            text=(ultimo_rollo),
            unfocus_on_touch=False,
            multiline = False,
            input_filter='int',
            hint_text="Número de Rollo",
        )

        # Agrega la etiqueta y el spinner al layout
        self.cartel_rollo.add_widget(label_digitos)
        self.cartel_rollo.add_widget(self.textinput_digitos)
        self.cartel_rollo.add_widget(label_num_rollo)
        self.cartel_rollo.add_widget(self.textinput)
        self.cartel_rollo.add_widget(self.error_label)

        # Agregar el botón "Continuar"
        self.cartel_rollo.add_widget(archivo_nuevo)

        self.popup = Popup(
            title='Ingrese Número de Rollo y Cantidad de Dígitos',
            content=self.cartel_rollo,
            size_hint=(None, None),
            size=(450, 400),
            auto_dismiss=False
        )
        self.popup.open()

        # Función para poner el foco en el campo de texto
        # pylint: disable=unused-argument
        def focus_input(*args):
            self.textinput.focus = True
        Clock.schedule_once(focus_input, 0.1)

        # Vincular el botón "Continuar" a la función de asignación del número de rollo
        # pylint: disable=no-member
        archivo_nuevo.bind(on_press=self.asignar_numero_rollo)

        # Vincular Enter (on_text_validate) al mismo método del botón
        # pylint: disable=no-member
        self.textinput.bind(
            on_text_validate=lambda instance: archivo_nuevo.trigger_action(duration=0.1)
        )

        # Crea el directorio temporal
        self.crear_directorio_temporal()
        #return

    def asignar_numero_rollo(self, *args): # pylint: disable=unused-argument
        '''Asigna el numero de rollo'''
        try:
            Window.bind(on_key_down=self.key_action)
            # Obtener el texto ingresado y quitar espacios extra
            self.numero_de_rollo = self.textinput.text.strip()

            # Verificar que el campo no esté vacío
            if self.numero_de_rollo:
                # Intentar convertir a entero para asegurar que es un número
                num_rollo = int(self.numero_de_rollo)

                cantidad_digitos_text = self.textinput_digitos.text.strip()
                if cantidad_digitos_text:
                    cantidad_digitos = int(cantidad_digitos_text)
                else:
                    self.error_label.text = "Por favor, ingrese la cantidad de dígitos."
                    return

                # Formatear con ceros a la izquierda
                self.numero_de_rollo = f"{num_rollo:0{cantidad_digitos}d}"

                # Formatear el número con ceros a la izquierda
                #if num_rollo < 10:
                #    num_rollo = '000' + str(num_rollo)
                #elif num_rollo < 100:
                #    num_rollo = '00' + str(num_rollo)
                #elif num_rollo < 1000:
                #    num_rollo = '0' + str(num_rollo)
                #else:
                #    num_rollo = str(num_rollo)

                # Asignar el número de rollo formateado
                #self.numero_de_rollo = num_rollo

                # Actualizar la interfaz con el número de rollo
                self.muestro_nro_rollo.text = self.numero_de_rollo
                #self.muestro_nro_rollo.text = self.numero_de_rollo
                print('Num Rollo',self.numero_de_rollo)
                self.btn_rollo.text = "Ítem: " + self.numero_de_rollo + "\n(+)"

                Window.bind(on_key_down=self.key_action)

                # Cerrar el popup
                self.popup.dismiss()

                # Llamar al callback para continuar con el flujo
                self.arranca_callback(self,'1')
            else:
                # Si el campo está vacío, mostrar mensaje de error
                self.error_label.text = "Por favor, ingrese un número válido."
                self.textinput.text = '' # Limpiar el campo texto
        except ValueError:
            # Si el valor no se puede conovertir a número, mostrar mensaje de error
            self.error_label.text = "Debe ingresar un número válido." # Mensaje de error
            self.textinput.text = '' # Limpiar el campo texto

    def crear_directorio (self):
        '''Crea directorio si es necesario'''
        path = self.directorio_app+self.numero_de_rollo

        try:
            os.mkdir(path)
        except OSError:
            print (f"Falló la creación del directorio {path}. Ya existe?")
        else:
            print (f"Se creó el directorio: {path} ")

    def crear_directorio_temporal(self):
        '''Crea carpeta temp'''
        path = self.directorio_temporal

        try:
            os.mkdir(path)
        except OSError:
            print (f"Falló la creación del directorio temporal {path}. Ya existe?")
        else:
            print (f"Se creó el directorio temporal: {path} ")

    def eliminar_directorio_temporal(self):
        '''Elimina carpeta temp'''
        # path = f"{self.directorio_app}/temp/"
        path = self.directorio_temporal
        print(f"Eliminando directorio temporal: {path}")
        try:
            shutil.rmtree(path)
        except shutil.Error:
            print (f"Falló la creación del directorio temporal {path} . Ya existe?")
        else:
            print (f"Se eliminó el directorio temporal: {path} ")

    def arranca_callback(self, *args):
        '''Callback'''
        if self.lview:
            self.timer = Clock.unschedule(self.update, 2)

        #if args[1] == '0':
            # self.estado_actual.text = 'Prev Marco'
        #else:
            # self.estado_actual.text = 'Prev Diapo'

        self.camara_previ = args[1]
        self.lview = True
        print ('Self.camara_previ', self.camara_previ)
        self.timer = Clock.schedule_interval(self.update, 1.0/24.0)
        self.loading_cursor(False)

    def btn0_callback(self, *args):
        '''Camara Marco - Anverso/Reverso'''
        self.capture_and_save_image(self.camera, args, 'camera')

    def btn0_callback_camera_01(self, *args):
        '''Camara Diapo'''
        self.capture_and_save_image(self.camera_01, args, 'camera_01')

    def capture_and_save_image(self, camera, args, camera_type):
        '''Lógica común para capturar y guardar imagen de cualquier cámara'''
        if hasattr(self, 'operacion_en_curso') and self.operacion_en_curso:
            print("Otra operación está en curso. Espera a que termine.")
            return
        self.operacion_en_curso = True

        try:
            # Cancelamos cualquier temporizador previo antes de realizar cualquier acción
            if hasattr(self, 'timer') and self.timer:
                Clock.unschedule(self.timer)
                print("Temporizador cancelado")

            self.loading_cursor()
            print(f'Camera {camera_type} Canon')

            ## Desactivo el reloj
            print(f"Timer {self.timer}")
            self.timer = Clock.unschedule(self.update)

            Clock.schedule_once(self._despues_de_esperar, 2)

            ## Me traigo dónde dejará la captura
            file_path = camera.capture(gp.GP_CAPTURE_IMAGE) # pylint: disable=no-member
            print(f'Camera {camera_type} file path: {file_path.folder}/{file_path.name}')

            # Nombre y destino de la imagen
            nombre = NOMBRE_ARCHIVO + str(self.numero_de_rollo) + '-' + str(args[1]) + '.jpg'
            target = os.path.join(self.directorio_app, nombre)
            print('Copying image to', target)

            # Verificación extra antes de comprobar existencia del archivo
            if not os.path.isdir(self.directorio_app):
                print(f"ERROR: El directorio '{self.directorio_app}' no existe.")
                self.operacion_en_curso = False
                return

            # Guardar imagen temporal
            camera_file = camera.file_get(
                file_path.folder,
                file_path.name,
                gp.GP_FILE_TYPE_NORMAL # pylint: disable=no-member
            )
            target_temp = os.path.join(self.directorio_temporal, args[1] + '-' + file_path.name)
            print("Guardando imagen temporal")

            try:
                camera_file.save(target_temp)
            except Exception as e: # pylint: disable=broad-exception-caught
                self.operacion_en_curso = False
                print(f"Error al guardar la imagen temporal Camera {camera_type}: {e}")
                self.loading_cursor(False)

            # Verificación de si el popup ya está abierto
            if hasattr(self, 'popup') and self.popup.parent:
                self.operacion_en_curso = False
                return  # Si el popup ya está abierto, no permitir abrir otro

            def save_image():
                self.loading_cursor()
                print("Copying image to ", target)
                camera_file = camera.file_get(
                    file_path.folder,
                    file_path.name,
                    gp.GP_FILE_TYPE_NORMAL # pylint: disable=E1101
                )
                try:
                    camera_file.save(target)

                    # *** NUEVO: Si es Diapo (camera_01) y espejado está activado, procesamos la imagen guardada ***
                    if camera_type == 'camera_01' and self.imagen_espejada:
                        # Cargar la imagen recién guardada
                        img_pil = Imge.open(target)
                        img_array = np.asarray(img_pil)
                        
                        # Aplicar flip horizontal
                        img_array_flipped = np.fliplr(img_array)
                        
                        # Convertir de vuelta a PIL Image
                        img_pil_flipped = Imge.fromarray(img_array_flipped.astype('uint8'))
                        
                        # Sobreescribir el archivo guardado con la versión espejada
                        img_pil_flipped.save(target)
                        print(f"Imagen espejada y guardada en {target}")
                    else:
                        print(f"Imagen guardada en {target}")

                except Exception as e: # pylint: disable=broad-exception-caught
                    self.operacion_en_curso = False
                    print(f"Error al guardar la imagen Camera {camera_type}: {e}")
                    self.loading_cursor(False)

                try:
                    camera.file_delete(file_path.folder, file_path.name)
                except gp.GPhoto2Error as e:
                    self.operacion_en_curso = False
                    print(f"Error deleting file: {e}")

                typ, data = camera.wait_for_event(200)

                attempts = 10
                while typ != gp.GP_EVENT_TIMEOUT and attempts > 0: # pylint: disable=no-member
                    print("Event")
                    if typ == gp.GP_EVENT_FILE_ADDED: # pylint: disable=no-member
                        print(f'Camera: {camera_type} - file path: {data.folder}/{data.name}')
                        if camera_type == "camera_01":
                            raw_nombre = (
                                NOMBRE_ARCHIVO +
                                str(self.numero_de_rollo) +
                                '-' +
                                str(args[1]) +
                                '.cr3'
                            )
                        else:
                            raw_nombre = (
                                NOMBRE_ARCHIVO +
                                str(self.numero_de_rollo) +
                                '-' +
                                str(args[1])+'.nef'
                            )
                        raw_target = os.path.join(self.directorio_app, raw_nombre)
                        print('Copying image to', raw_target)
                        camera_file = camera.file_get(
                            data.folder,
                            data.name,
                            gp.GP_FILE_TYPE_NORMAL # pylint: disable=no-member
                        )
                        camera_file.save(raw_target)

                        if camera_type == 'camera_01':
                            self.arranca_callback(self, '0')
                        elif camera_type == 'camera':
                            self.mostrar_pregunta(self.manejar_respuesta)

                    typ, data = camera.wait_for_event(1)
                    attempts -= 1

            # Check if file already exists, then open a popup for confirmation
            if os.path.isfile(target):
                self._show_confirmation_popup(target, target_temp, save_image)
            else:
                self._show_confirmation_popup(target, target_temp, save_image)

        except gp.GPhoto2Error as e:
            print(f"Error de GPhoto2: {e}")
            self.operacion_en_curso = False
        except FileNotFoundError as e:
            print(f"Archivo no encontrado: {e}")
            self.operacion_en_curso = False
        except PermissionError as e:
            print(f"Permiso denegado: {e}")
            self.operacion_en_curso = False
        except OSError as e:
            print(f"Error del sistema operativo: {e}")
            self.operacion_en_curso = False
        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"Error inesperado: {e}")
            self.operacion_en_curso = False

    def _show_confirmation_popup(self, target, target_temp, save_image):
        self.loading_cursor(False)

        # *** NUEVO: Cargar la imagen temporal y procesarla si es necesario ***
        try:
            # Cargar la imagen desde el archivo temporal
            img_pil = Imge.open(target_temp)
            img_array = np.asarray(img_pil)
            
            # Si es Diapo (camera_01) y espejado está activado, hacer flip
            print(f"Camara Previ: {self.camara_previ}, Imagen Espejada: {self.imagen_espejada}")
            if self.camara_previ == '1' and self.imagen_espejada:
                img_array = np.fliplr(img_array)  # Flip horizontal
                
            # Convertir el array numpy de vuelta a imagen PIL
            img_pil_processed = Imge.fromarray(img_array.astype('uint8'))
            
            # Guardar la imagen procesada temporalmente para mostrar en preview
            preview_temp = os.path.join(self.directorio_temporal, 'preview_temp.jpg')
            img_pil_processed.save(preview_temp)
            
        except Exception as e:
            print(f"Error procesando imagen para preview: {e}")
            preview_temp = target_temp  # Si hay error, usar la original
        
        # *** FIN DE LO NUEVO ***

        def on_confirm(instance=None): # pylint: disable=unused-argument
            self.loading_cursor()
            self.popup.dismiss()
            self.timer = Clock.schedule_interval(self.update, 1.0 / 24.0)
            os.remove(target_temp)
            # Limpiar el archivo de preview temporal si existe
            if os.path.exists(preview_temp):
                try:
                    os.remove(preview_temp)
                except:
                    pass
            save_image()
            # threading.Thread(target=save_image).start()
            self.loading_cursor(False)
            self.operacion_en_curso = False

        def on_cancel(instance=None): # pylint: disable=unused-argument
            self.loading_cursor(False)
            self.popup.dismiss()
            self.timer = Clock.schedule_interval(self.update, 1.0 / 24.0)
            os.remove(target_temp)
            # Limpiar el archivo de preview temporal si existe
            if os.path.exists(preview_temp):
                try:
                    os.remove(preview_temp)
                except:
                    pass
            print("Operación cancelada por el usuario.")
            self.operacion_en_curso = False
            Clock.schedule_once(self._despues_de_esperar, 1)

        box = BoxLayout(orientation='vertical', spacing=10, padding=10)
        img_preview = Image(
            source=preview_temp,
            size_hint=(None, None),
            size=(800, 600),
            pos_hint={'center_x': 0.5}
        )
        img_preview.reload()

        btn_yes = Button(text="Sí", size_hint_y=None, height=40)
        btn_no = Button(text="No", size_hint_y=None, height=40)

        btn_yes.bind(on_release=on_confirm) # pylint: disable=E1101
        btn_no.bind(on_release=on_cancel) # pylint: disable=E1101

        print(f"Target: {target}")
        print(f"Exite? {os.path.isfile(target)}")
        if os.path.isfile(target):
            label_popup = (f"El archivo '{os.path.basename(target)}' " +
                            "ya existe. ¿Desea sobreescribirlo?")
        else:
            label_popup = "¿Desea guardar la imágen?"

        box.add_widget(Label(
            text=label_popup
        ))
        box.add_widget(img_preview)
        box.add_widget(btn_yes)
        box.add_widget(btn_no)

        self.popup = Popup(
            title="Confirmación",
            content=box,
            size_hint=(None, None),
            size=(1024, 768),
            auto_dismiss=False
        )
        self.popup.open()

    def btn_exit_callback(self, *args): # pylint: disable=unused-argument
        '''Salir del programa'''
        self.eliminar_directorio_temporal()
        self.camera.exit()
        self.camera.init()
        self.camera_01.exit()
        self.camera_01.init()
        App.get_running_app().stop()

    def _despues_de_esperar(self, dt): # pylint: disable=unused-argument
        # Código a ejecutar después de la espera de 2 segundos
        print("Esperando 2 segundos para que la cámara termine la operación anterior...")
        self.loading_cursor(False)

    def capture_preview_from_camara(self, camera, camera_id):
        '''Captura la vista previa de la cámara indicada'''
        if not hasattr(camera, "capture_preview"):
            error_message = (f"Error: La cámara {camera_id} no está disponible o es inválida.\n"+
                             "Debe de reiniciar o encender las cámaras")
            print(error_message)
            self.show_error_dialog(error_message)
            return None
        try:
            # print(f"Capturando vista previa de la cámara {camera_id}...")
            return camera.capture_preview()
        except gp.GPhoto2Error as e:
            print(f"Error al capturar la vista previa de {camera_id}: {e}")

        return None

    def show_error_dialog(self, message):
        """Muestra un popup de error con un botón para cerrar la aplicación."""
        if hasattr(self, 'popup') and self.popup.parent:
            # Si el popup ya está abierto, no lo volvemos a mostrar
            print("El popup ya está abierto, no se abrirá nuevamente")
            self.popup.dismiss()

        def close_app(instance): # pylint: disable=unused-argument
            sys.exit()  # Cierra la aplicación cuando el usuario presiona "Cerrar"

        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Etiqueta para mostrar el mensaje de error
        message_label = Label(text=message, size_hint=(1, 0.7))

        # Botón "Cerrar"
        close_button = Button(text="Cerrar", size_hint=(1, 0.3))
        close_button.bind(on_press=close_app) # pylint: disable=E1101

        # Agregar elementos al layout
        layout.add_widget(message_label)
        layout.add_widget(close_button)

        popup = Popup(
            title="Error",
            content=layout,
            size_hint=(None, None),
            size=(500, 200),
            auto_dismiss=False  # Evita que el usuario cierre el popup sin el botón
        )

        popup.open()

    def update(self, *args): # pylint: disable=unused-argument
        '''Update'''
        capture = None
        # Intentamos capturar la vista previa de las cámaras
        if self.camara_previ == '0':
            capture = self.capture_preview_from_camara(self.camera, 'camera')
        elif self.camara_previ == '1':
            capture = self.capture_preview_from_camara(self.camera_01, 'camera_01')

        if capture:
            # Procesamiento de la imagen
            filedata = capture.get_data_and_size()
            image = Imge.open(io.BytesIO(filedata))
            image_array = np.asarray(image)

            # Convertir la imagen a formato OpenCV y rotar la imagen
            # imcv = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
            rotated_image = np.rot90(np.swapaxes(image_array, 0, 1))

            # *** NUEVO: Aplicar flip horizontal si se está viendo la Diapo y está activado ***
            if self.camara_previ == '1' and self.imagen_espejada:
                rotated_image = np.fliplr(rotated_image)

            # Crear una textura con la imagen para Kivy
            video_texture = Texture.create(
                size=(rotated_image.shape[1], rotated_image.shape[0]),
                colorfmt='bgr'
            )
            video_texture.blit_buffer(
                rotated_image.tobytes(),
                colorfmt='rgb',
                bufferfmt='ubyte'
            )

            # Asignar la textura a la iagen de Kivy
            self.img1.texture = video_texture
        else:
            print("No se pudo capturar la vista previa.")

    def mostrar_pregunta(self, callback):
        ''' Muestra un popup con una pregunta de Sí o No '''
        # Esperamos 2 segundo antes de continuarr para dar tiempo a la cámara a terminar
        print("Esperando 2 segundo para que la cáamara termina la operación anterior...")
        Clock.schedule_once(self._despues_de_esperar, 2)

        if hasattr(self, 'popup') and self.popup.parent:
            # Si el popup ya está abierto, no lo volvemos a mostrar
            print("El popup ya está abierto, no se abrirá nuevamente")
            self.popup.dismiss()

        box = BoxLayout(orientation='vertical', padding=10, spacing=10)
        label = Label(text="¿Desea finalizar?", size_hint_y=None, height=50)

        botones = BoxLayout(orientation='horizontal', spacing=10)
        btn_si = Button(text="Sí")
        btn_no = Button(text="No")

        botones.add_widget(btn_si)
        botones.add_widget(btn_no)

        box.add_widget(label)
        box.add_widget(botones)

        # Vincular botones a las funciones correspondientes
        # pylint: disable=no-member
        btn_si.bind(on_press=lambda instance: self._cerrar_popup(callback, True))
        # pylint: disable=no-member
        btn_no.bind(on_press=lambda instance: self._cerrar_popup(callback, False))

        self.popup = Popup(
            title="Finalizar proceso",
            content=box,
            size_hint=(None, None),
            size=(400, 200),
            auto_dismiss=False
        )
        self.popup.open()

        self.loading_cursor(False)

    def _cerrar_popup(self, callback, respuesta):
        ''' Cierra el popup y llama a la función de callback con la respuesta '''
        Clock.schedule_once(lambda dt: self.popup.dismiss(), 0.1)
        # Ensure the callback is invoked only after the popup is dismissed
        Clock.schedule_once(lambda dt: callback(respuesta), 0.2)

    def aumentar_1_nro_rollo(self, *args): # pylint: disable=W0613
        '''Función para aumentar en 1 el nro de rollo'''
        self.textinput.text = str(int(self.numero_de_rollo) + 1)
        print(f'Nuevo numero de rollo: {self.textinput.text}')
        self.asignar_numero_rollo()

    def abrir_carpeta(self, *args): # pylint: disable=W0613
        '''Función para abrir la carpeta desitno'''
        try:
            subprocess.run(["xdg-open", self.directorio_app], check=False)
        except subprocess.CalledProcessError as e:
            print(f"Occurió un error al intentar abrir la carpeta: {e}")

    def manejar_respuesta(self, respuesta):
        '''Respuesta'''
        self.loading_cursor(True)
        if respuesta:
            print("El usuario eligió Sí")
            # Tengo que agarrar las 3 fotos y armar una sola
            if not self.combinar_imagenes():
                self.loading_cursor(False)
                return # Si falta alguna imagen, no continuar

            self.cambio_de_diapo()

            self.numero_de_rollo_anterior = self.numero_de_rollo
            self.textinput.text = str(int(self.numero_de_rollo) + 1)
            print('# nuevo',self.numero_de_rollo)
            self.asignar_numero_rollo()

            self.arranca_callback(self, '1')  # Llama a Prev Diapo
            Clock.schedule_once(lambda dt: self.arranca_callback(self, '1'), 0.1)
            self.loading_cursor(False)
        else:
            print("El usuario eligió No")
            self.arranca_callback(self,'0') # Llama a Prev Marco
            Clock.schedule_once(lambda dt: self.arranca_callback(self,'0'), 0.1)
            self.loading_cursor(False)

    def loading_cursor(self, wait = True):
        '''Cargando'''
        if wait:
            Window.set_system_cursor("wait")
        else:
            Window.set_system_cursor("arrow")

    def cambio_de_diapo(self):
        '''Popup fin de diapo'''
        def show_popup(*args): # pylint: disable=unused-argument
            cartel_cambio = GridLayout(
                cols = 1,
                rows = 2,
                col_default_width=20,
                row_default_height=20,
                height=400
            )
            cartel = Label(
                text="AVISO: Tiene que ingresar una nueva diapositiva",
                font_size=24,
                color=(1, 1, 1, 1),
                bold=True,
                halign='center',
                valign='middle',
                size_hint_y=None,
                height=100
            )

            cambio_diapo = Button(
                text="Continuar",
                font_size=20,
                background_color=(0.2,0.6,1,1),
                color=(1,1,1,1),
                size_hint_y=None,
                height=60,
                padding=(10, 10)
            )

            # self.cartel_cambio.add_widget(imagen_combinada)
            cartel_cambio.add_widget(cartel)
            cartel_cambio.add_widget(cambio_diapo)

            self.popup = Popup(
                title='Nueva diapositiva',
                title_size=24,
                title_align='center',
                content=cartel_cambio,
                size_hint=(None, None),
                size=(600, 250),
                auto_dismiss=False
            )

            self.popup.open()
            cambio_diapo.bind(on_press=self.close_popup) # pylint: disable=no-member
        Clock.schedule_once(show_popup)

    def close_popup(self, *args): # pylint: disable=unused-argument
        '''Cierre popup'''
        self.popup.dismiss()

    def cambiar_directorio(self, *args): # pylint: disable=unused-argument
        '''Solucionar la selección'''
        chooser = CustomFileChooserListView(dirselect=True)

        # Establecer el directorio inicial
        if self.directorio_app == '':
            chooser.path = '/home/eddu/Documentos/Slides/Fotos/'  # Ruta inicial
        else:
            chooser.path = self.directorio_app

        # Crear un botón adicional dentro del Popup
        btn_aceptar = Button(text="Aceptar", size_hint=(None, None), width=200)
        # pylint: disable=no-member
        btn_aceptar.bind(on_press=lambda *args: self.select_directory(chooser.selection))

        # Crear un label para mostrar la ruta
        self.path_label = Label(text='Ruta: ', size_hint_y=None, height=30)

        # Función para actualizar la ruta cuando el usuario seleccione un archivo o carpeta
        def update_label(instance, value):
            if value:
                selected_path = value[0]
                if os.path.isfile(selected_path):
                    # Si es un archivo, obtener su carpeta
                    selected_path = os.path.dirname(selected_path)
                self.path_label.text = f"Ruta: {selected_path}"
            else:
                self.path_label.text = f'Ruta: {instance.path}'


        # Vincular la propiedad 'selection' del FileChooserIconView con la función update_label
        chooser.bind(selection=update_label)

        # Usar un ScrollView para permitir el desplazamiento solo cuando sea necesario
        scroll = ScrollView(do_scroll_x=False, do_scroll_y=True)
        scroll.add_widget(chooser)

        # Layout para la parte inferior (botón y ruta)
        box2 = BoxLayout(orientation='horizontal', size_hint_y=None, height=50)
        box2.add_widget(self.path_label)
        box2.add_widget(btn_aceptar)

        # Layout del Popup (contendrá tanto el selector como el botón adicional)
        popup_layout = BoxLayout(orientation='vertical')
        popup_layout.add_widget(scroll) # El selector de directorios está dentro de un ScrollView
        popup_layout.add_widget(box2) # El BoxLayout estará en la parte inferior

        # Crear el popup
        self.popup = Popup(title="Seleccionar Carpeta", content=popup_layout, size_hint=(0.8, 0.8))
        self.popup.open()

    def select_directory(self, selection):
        '''Selecciona directorio'''
        if not selection:
            print("No se seleccionó ninguna carpeta.")
            return  # Evita continuar si no hay selección

        selected_path = selection[0]
        if os.path.isfile(selected_path):
            selected_path = os.path.dirname(selected_path)

        if selected_path != self.directorio_app:
            self.directorio_app = selected_path
            self.estado_actual.text = f"Directorio: {selected_path}"
            print(f"Carpeta seleccionada: {self.directorio_app}")
        else:
            print("La carpeta seleccionada es la misma.")

        # Cerrar popup de manera segura
        if hasattr(self, 'popup') and self.popup and self.popup.parent:
            self.popup.dismiss()

    def rotar_diapo(self, *args):
        '''
        Alterna entre mostrar/espejar la imagen de la Diapo.
        Si imagen_espejada es False, muestra la imagen normal.
        Si imagen_espejada es True, muestra y guarda la imagen espejada.
        '''
        # Alternar la variable booleana
        self.imagen_espejada = not self.imagen_espejada
        
        # Actualizar el texto del botón para mostrar el estado actual
        if self.imagen_espejada:
            # Si está espejada, mostrar en verde o indicar que está activo
            self.btn_rotar_diapo.text = "Rotar Diapo\n(r)\n✓ ON"
            self.btn_rotar_diapo.background_color = (0.2, 0.8, 0.2, 0.8)  # Verde
        else:
            # Si no está espejada, mostrar el estado normal
            self.btn_rotar_diapo.text = "Rotar Diapo\n(r)"
            self.btn_rotar_diapo.background_color = self.color_botones  # Color original (rojo)        
        print(f"Espejado: {self.imagen_espejada}")

        # *** NUEVO: Refrescar el preview de Diapo para ver el cambio inmediatamente ***
        self.arranca_callback(self, '1')

    def combinar_imagenes(self):
        '''Nombre de las imagenes'''
        nombre_diapo = os.path.join(
            self.directorio_app,
            NOMBRE_ARCHIVO+str(self.numero_de_rollo)+'-diapo.jpg'
        )
        nombre_anverso = os.path.join(
            self.directorio_app,
            NOMBRE_ARCHIVO+str(self.numero_de_rollo)+'-anverso.jpg'
        )
        nombre_reverso = os.path.join(
            self.directorio_app,
            NOMBRE_ARCHIVO+str(self.numero_de_rollo)+'-reverso.jpg'
        )

        # Verificar la existencia de las imágenes
        imagenes_faltantes = []
        if not os.path.exists(nombre_diapo):
            imagenes_faltantes.append("Diapo")
        if not os.path.exists(nombre_anverso):
            imagenes_faltantes.append("Anverso Marco")
        if not os.path.exists(nombre_reverso):
            imagenes_faltantes.append("Reverso Marco")

        if imagenes_faltantes:
            print(f"Faltan las siguientes imágenes: {', '.join(imagenes_faltantes)}")
            mensaje = f"Faltan las siguientes imágenes: \n{', '.join(imagenes_faltantes)}"
            self.mostrar_popup_error(mensaje)
            self.loading_cursor(False)
            return False # Detener la función

        try:
            # Abrir las imágenes
            imagen_diapo = Imge.open(
                os.path.join(
                    self.directorio_app,
                    NOMBRE_ARCHIVO+str(self.numero_de_rollo)+'-diapo.jpg'
                )
            )
            imagen_anverso = Imge.open(
                os.path.join(
                    self.directorio_app,
                    NOMBRE_ARCHIVO+str(self.numero_de_rollo)+'-anverso.jpg'
                )
            )
            imagen_reverso = Imge.open(
                os.path.join(
                    self.directorio_app,
                    NOMBRE_ARCHIVO+str(self.numero_de_rollo)+'-reverso.jpg'
                )
            )

            # Calcular dimensiones de la imagen final
            ancho_final = 1500
            alto_final = 1500

            # Redimensionar las imagenes
            #Diapo: 1500X1000 (2/3 de la altura)
            imagen_diapo = imagen_diapo.resize((1500,1000), Imge.Resampling.LANCZOS)
            #Anverso y Reversoo: 750x500 (1/3 de la altura, dividio en dos)
            imagen_anverso = imagen_anverso.resize((750,500), Imge.Resampling.LANCZOS)
            imagen_reverso = imagen_reverso.resize((750,500), Imge.Resampling.LANCZOS)

            # Crear una imagen en blanco para la combinación
            imagen_combinada = Imge.new('RGB', (ancho_final, alto_final), color='white')

            # Pegar la imagen diapo arriba
            imagen_combinada.paste(imagen_diapo, (0, 0))

            # Pegar la imagen anverso abajo a la izquierda
            imagen_combinada.paste(imagen_anverso, (0, 1000))

            # Pegar la imagen reverso abajo a la derecha
            imagen_combinada.paste(imagen_reverso, (750, 1000))

            # Guardar la imagen combinada
            imagen_combinada.save(
                os.path.join(
                    self.directorio_app,
                    NOMBRE_ARCHIVO+str(self.numero_de_rollo)+'.jpg'
                )
            )
            print(f"Combinada guardada en {NOMBRE_ARCHIVO+str(self.numero_de_rollo)+'.jpg'}")
            return True # Retornar True si la combinación fue exitosa
        except Exception as e: # pylint: disable=broad-exception-caught
            # Manejar errorer al procesar las imagenes
            self.mostrar_popup_error(f"Error al combinar las imágenes: {str(e)}")
            return False

    def mostrar_popup_error(self, mensaje):
        '''Crear un popup para mostar el mensaje de error'''
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        label = Label(text=mensaje, font_size=20, halign='center', valign='middle')
        boton = Button(text="Cerrar", size_hint=(None, None), size=(100, 50))
        layout.add_widget(label)
        layout.add_widget(boton)

        self.popup = Popup(
            title="Error",
            content=layout,
            size_hint=(None, None),
            size=(400, 200),
            auto_dismiss=False
        )
        boton.bind(on_press=self.popup.dismiss) # pylint: disable=no-member
        self.popup.open()
        self.loading_cursor(False)

if __name__ == "__main__":
    CamApp().run()
