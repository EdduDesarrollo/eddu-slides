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
import time
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
try:
    from PIL import Image as Imge
except ImportError:
    print("Pillow (PIL) no está instalado. Instalando...")
    subprocess.check_call(['sudo', 'apt', 'install', '-y', 'python3-pil'])
    os.execv(sys.executable, ['python3'] + sys.argv)
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
MENSAJE_PIDO_QTY_CAMARAS = "Cuantas cámaras va a utilizar?"


def desmontar_camara_gphoto2():
    '''Desmonta cámaras montadas por gphoto2/FUSE/GVFS.'''
    gvfs_base = f"/run/user/{os.getuid()}/gvfs"
    encontrado = False
    if os.path.exists(gvfs_base):
        for entry in os.listdir(gvfs_base):
            if "gphoto2:" in entry:
                mount_path = os.path.join(gvfs_base, entry)
                print(f"Desmontando cámara gphoto2 en: {mount_path}")
                try:
                    subprocess.run(['gio', 'mount', '-u', mount_path], check=True)
                    encontrado = True
                except Exception as e:  # pylint: disable=broad-exception-caught
                    print(f"Error al desmontar {mount_path}: {e}")
    if not encontrado:
        print("No se encontró cámara gphoto2 montada.")

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

desmontar_camara_gphoto2()

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
        self.color_boton_foco = (0.2, 0.75, 0.3, 0.95)
        self.numero_de_rollo =  StringProperty(' ')
        self.cantidad_digitos = 4
        self.camara_previ = '0'
        self.cantidad_camaras = 2
        self.lview = False
        self.img1 = Image(source='fb.png', size=(1024,768))
        self.title = TITULO

        self.estado_actual = self.directorio_app
        self.label_item = ''
        self.numero_de_rollo_anterior = ''
        self.operacion_en_curso = False
        self.imagen_espejada = False
        self.timer = ''
        self.path_label = ''
        self.popup = ''
        self.popup_qty_camaras = ''
        self.error_label = ''
        self.textinput = ''
        self.camera_01 = ''
        self.camera = ''
        self.camara = ''
        self.camera_der = ''
        self.camera_izq = ''
        self.cartel_rollo = ''
        self.muestro_nro_rollo = ''
        self.box2 = ''
        self.btn0 = ''
        self.btn1 = ''
        self.btn2 = ''
        self.btn_rollo = ''
        self.btn_directorio = ''
        self.btn_ndiapo = ''
        self.btn_diapo = ''
        self.btn_apertura = ''
        self.btn_caratula = ''
        self.btn_rotar_diapo = ''
        self.textinput_digitos = ''
        self.btn_abrir_carpeta = ''
        self._yn_focus = 0
        self._yn_buttons = ()
        self._yn_callbacks = ()
        self._yn_normal_colors = ()
        self._popup_keyboard_mode = None
        self._eligiendo_directorio = False


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
            size_hint=(1, 0.04),
            pos_hint={'center_x':0.5},
            background_color=(0.1, 0.1, 0.1, 0.2)
        )
        layout.add_widget(self.estado_actual)

        self.label_item = Label(
            text="# Item: ",
            size_hint=(1, 0.04),
            pos_hint={'center_x': 0.5},
            halign='center',
            valign='middle'
        )
        self.label_item.bind(size=self.label_item.setter('text_size'))  # pylint: disable=no-member
        layout.add_widget(self.label_item)

        layout.add_widget(self.img1, 0)

        #Interfaz kivi
        bottom_layout = BoxLayout(
            orientation='horizontal',
            size_hint=(1,None),
            height=100,
            pos_hint={'center_x': 0.5, 'bottom':1}
        )
        # Crear un AnchorLayout para centrar el GridLayout (box2) horizontalmente
        anchor_layout = AnchorLayout(anchor_x='center', anchor_y='bottom', size_hint=(1, 1))

        self.box2 = GridLayout(
            cols = 11,
            col_default_width=20,
            row_default_height=80,
            size_hint=(None, None)
        )
        # pylint: disable=no-member
        self.box2.bind(minimum_size=self.box2.setter('size'))

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
        self.btn_abrir_carpeta.bind(on_press=self.abrir_carpeta)

        self.box2.add_widget(self.btn_diapo)
        self.box2.add_widget(self.btn_caratula)
        self.box2.add_widget(self.btn_apertura)
        self.box2.add_widget(self.btn_ndiapo)
        self.box2.add_widget(self.btn0)
        self.box2.add_widget(self.btn1)
        self.box2.add_widget(self.btn_directorio)
        self.box2.add_widget(self.btn_rollo)
        self.box2.add_widget(self.btn_abrir_carpeta)
        self.box2.add_widget(self.btn_rotar_diapo)
        self.box2.add_widget(self.btn2)  # Salir siempre al final

        anchor_layout.add_widget(self.box2)
        bottom_layout.add_widget(anchor_layout)
        layout.add_widget(bottom_layout)
        # layout.add_widget(box2,0)
        self.cartel_rollo = GridLayout()
        self.timer = any

        return layout

    def _choice_to_str(self, choice):
        '''Normaliza choices de gphoto2 (str o [índice, label]).'''
        if isinstance(choice, (list, tuple)):
            for part in reversed(choice):
                if isinstance(part, str):
                    return part
            return str(choice[-1]) if choice else ''
        return str(choice)

    def _configurar_capturetarget_ram(self, camera):
        '''
        Fuerza captura a RAM interna (sin tarjeta SD).
        En locale ES: "RAM Interna"; en EN: "Internal RAM".
        '''
        try:
            config = camera.get_config()
            # pylint: disable=no-member
            ok, widget = gp.gp_widget_get_child_by_name(config, 'capturetarget')
            if ok < gp.GP_OK:  # pylint: disable=no-member
                print("No se encontró el parámetro capturetarget")
                return False

            count = gp.gp_widget_count_choices(widget)  # pylint: disable=no-member
            elegido = None
            for i in range(count):
                choice_raw = gp.gp_widget_get_choice(widget, i)  # pylint: disable=no-member
                choice = self._choice_to_str(choice_raw)
                print(f"capturetarget[{i}]: {choice_raw} -> {choice}")
                choice_l = choice.lower()
                if (
                    'ram' in choice_l
                    or 'interna' in choice_l
                    or 'internal' in choice_l
                ) and 'card' not in choice_l and 'tarjeta' not in choice_l:
                    elegido = choice
                    break

            if elegido is None and count > 0:
                elegido = self._choice_to_str(gp.gp_widget_get_choice(widget, 0))  # pylint: disable=no-member
                print(f"Usando choice[0] por defecto: {elegido}")

            if not elegido:
                print("No hay choices para capturetarget")
                return False

            try:
                widget.set_value(elegido)
            except Exception:  # pylint: disable=broad-exception-caught
                gp.gp_widget_set_value(widget, elegido)  # pylint: disable=no-member

            camera.set_config(config)
            actual = widget.get_value()
            print(f"capturetarget configurado: {actual}")
            return True
        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"Error configurando capturetarget: {e}")
            return False

    def asignar_camaras(self):
        """Asignar las cámaras disponibles basadas en los seriales y cantidad_camaras."""
        print(f"Comenzando asignación de cámaras (modo {self.cantidad_camaras})")

        try:
            # Liberar cualquier cámara previamente asignada
            for attr in ['camera', 'camera_01', 'camara']:
                if hasattr(self, attr) and getattr(self, attr):
                    try:
                        getattr(self, attr).exit()
                    except Exception as e:  # pylint: disable=broad-exception-caught
                        print(f"Error liberando {attr}: {e}")
                    setattr(self, attr, None)

            camera_list = []

            try:
                # Misma forma que book-scan: autodetect() sin Context evita lista vacía
                # con bindings nuevos de python-gphoto2.
                camera_list = list(gp.Camera.autodetect())
            except Exception as e:  # pylint: disable=broad-exception-caught
                print(f"autodetect() falló ({e}), intentando método alternativo...")
                try:
                    context = gp.Context()
                    port_info_list = gp.PortInfoList()
                    port_info_list.load()
                    abilities_list = gp.CameraAbilitiesList()
                    abilities_list.load(context)
                    for name, addr in abilities_list.detect(port_info_list, context):
                        camera_list.append((name, addr))
                except Exception as e2:  # pylint: disable=broad-exception-caught
                    print(f"Método alternativo de detección falló: {e2}")

            if not camera_list:
                print("No se detectaron cámaras conectadas")
                return False

            camera_list.sort(key=lambda x: x[0])

            port_info_list = gp.PortInfoList()
            port_info_list.load()

            for name, addr in camera_list:
                print(f"Detectada cámara: {name} en {addr}")
                camara = None
                try:
                    camara = gp.Camera()
                    idx = port_info_list.lookup_path(addr)
                    camara.set_port_info(port_info_list[idx])

                    print("Inicializando cámara...")
                    camara.init()
                    config_camara = camara.get_config()

                    # Búsqueda recursiva del widget (igual que book-scan).
                    # get_child_by_name() solo mira hijos directos y falla en Canon.
                    # pylint: disable=no-member
                    gp_ok, serialnumber_config = gp.gp_widget_get_child_by_name(
                        config_camara,
                        'serialnumber'
                    )
                    if gp_ok < gp.GP_OK:  # pylint: disable=no-member
                        print(f"No se pudo obtener el número de serie para la cámara {name}.")
                        camara.exit()
                        continue

                    raw_value = serialnumber_config.get_value()
                    print(f"Serial detectado: {raw_value}")

                    if raw_value == CAMARA_2:
                        self._configurar_capturetarget_ram(camara)
                        self.camera_01 = camara
                        print(f"Asignada cámara diapo (serial: {raw_value})")
                    elif raw_value == CAMARA_1:
                        if self.cantidad_camaras == 2:
                            self._configurar_capturetarget_ram(camara)
                            self.camera = camara
                            print(f"Asignada cámara marco (serial: {raw_value})")
                        else:
                            print("Cámara marco detectada pero no requerida en modo 1; se libera")
                            camara.exit()
                    else:
                        print(f"Serial no reconocido: {raw_value}")
                        camara.exit()

                except gp.GPhoto2Error as e:
                    print(f"Error al inicializar cámara {name}: {e}")
                    if camara:
                        try:
                            camara.exit()
                        except Exception:  # pylint: disable=broad-exception-caught
                            pass

            if not self.camera_01:
                print("No se asignó la cámara de diapo")
                return False
            if self.cantidad_camaras == 2 and not self.camera:
                print("No se asignó la cámara de marco")
                return False

            print("Cámaras asignadas correctamente.")
            return True
        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"Error inesperado: {str(e)}")
            return False

    def key_action(self, *args):
        '''Teclas'''
        print (f"got a key event: {args[3]}")

        if args[3] == 'm': # Salir
            self.btn_exit_callback()
        elif args[3] == 'z': # Diapo / Capturar
            self.btn0_callback_camera_01(self,'diapo')
        elif args[3] == 'x': # Anverso
            if self.cantidad_camaras == 2:
                self.btn0_callback(self,'anverso')
        elif args[3] == 'c': # Reverso
            if self.cantidad_camaras == 2:
                self.btn0_callback(self,'reverso')
        elif args[3] == 'v': # Item Numero
            self.pido_rollo()
        elif args[3]=='b': # Prev Marco
            if self.cantidad_camaras == 2:
                self.arranca_callback(self,'0')
        elif args[3]=='n': # Prev Diapo / Prev Camara
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

        Clock.schedule_once(lambda dt: self.pido_qty_camaras(), 0.1)
        print ('arrancó')

    def pido_qty_camaras(self):
        '''Popup para seleccionar la cantidad de cámaras'''
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        mensaje = Label(
            text=MENSAJE_PIDO_QTY_CAMARAS,
            size_hint=(1, 0.4)
        )
        layout.add_widget(mensaje)

        botones = GridLayout(cols=2, spacing=10, size_hint=(1, 0.6))
        btn_1_camara = Button(text="1 Cámara")
        btn_2_camaras = Button(text="2 Cámaras")

        botones.add_widget(btn_1_camara)
        botones.add_widget(btn_2_camaras)
        layout.add_widget(botones)

        self.popup_qty_camaras = Popup(
            title="Seleccionar cantidad de cámaras",
            content=layout,
            size_hint=(None, None),
            size=(350, 250),
            auto_dismiss=False
        )

        btn_1_camara.bind(on_release=self._set_cantidad_camaras_1)  # pylint: disable=no-member
        btn_2_camaras.bind(on_release=self._set_cantidad_camaras_2)  # pylint: disable=no-member

        self.popup_qty_camaras.open()

    def _set_cantidad_camaras_1(self, *args):  # pylint: disable=unused-argument
        self.cantidad_camaras = 1
        self.popup_qty_camaras.dismiss()
        if not self.asignar_camaras():
            self.show_error_dialog(
                "No se encontró la cámara de diapo.\nVerifique el serial y la conexión."
            )
            return
        self._aplicar_ui_modo_camaras()
        self.pido_rollo()

    def _set_cantidad_camaras_2(self, *args):  # pylint: disable=unused-argument
        self.cantidad_camaras = 2
        self.popup_qty_camaras.dismiss()
        if not self.asignar_camaras():
            self.show_error_dialog(
                "No se pudieron asignar ambas cámaras.\nVerifique los seriales y la conexión."
            )
            return
        self._aplicar_ui_modo_camaras()
        self.pido_rollo()

    def _aplicar_ui_modo_camaras(self):
        '''Ajusta textos y botones según cantidad de cámaras (sin toggle en caliente).'''
        if self.cantidad_camaras == 1:
            self.camara_previ = '1'
            self.btn_diapo.text = "Capturar\n(z)"
            self.btn1.text = "Prev Camara\n(n)"
            self.btn_rotar_diapo.text = self._texto_btn_rotar(False)
            for btn in (self.btn_caratula, self.btn_apertura, self.btn0):
                if btn.parent:
                    btn.parent.remove_widget(btn)
        else:
            self.camara_previ = '0'
            self.btn_diapo.text = "Diapo\n(z)"
            self.btn1.text = "Prev Diapo\n(n)"
            self.btn_rotar_diapo.text = self._texto_btn_rotar(False)

    def _texto_btn_rotar(self, activo=False):
        base = "Rotar" if self.cantidad_camaras == 1 else "Rotar Diapo"
        if activo:
            return f"{base}\n(r)\n✓ ON"
        return f"{base}\n(r)"

    def pido_rollo(self):
        '''Ventana emergente para pedir el numero de rollo'''
        Window.unbind(on_key_down=self.key_action)
        try:
            Window.unbind(on_key_down=self._yes_no_key_action)
        except Exception:  # pylint: disable=broad-exception-caught
            pass
        try:
            Window.unbind(on_keyboard=self._popup_on_keyboard)
        except Exception:  # pylint: disable=broad-exception-caught
            pass

        path = self.directorio_app
        print('Data:', self.numero_de_rollo, path)

        digitos_default = str(self.cantidad_digitos) if self.cantidad_digitos else '4'
        numero_default = ''
        try:
            if str(self.numero_de_rollo).strip():
                numero_default = str(int(self.numero_de_rollo))
        except (TypeError, ValueError):
            numero_default = ''

        self.cartel_rollo = GridLayout(cols=1, rows=7)
        cartel = Label(text=MENSAJE_PIDO_ROLLO, valign='middle')
        self.error_label = Label(text='', color=(1, 0, 0, 1))
        archivo_nuevo = Button(text="Continuar")
        self.cartel_rollo.add_widget(cartel)

        label_digitos = Label(
            text="Cantidad de digitos",
            size_hint_y=None,
            height=30,
            valign='middle'
        )
        self.textinput_digitos = TextInput(
            text=digitos_default,
            input_filter='int',
            multiline=False,
            hint_text="Cantidad de digitos"
        )
        label_num_rollo = Label(
            text="Numero de Rollo",
            size_hint_y=None,
            height=30,
            valign='middle'
        )
        self.textinput = TextInput(
            text=numero_default,
            unfocus_on_touch=False,
            multiline=False,
            input_filter='int',
            hint_text="Numero de Rollo",
        )

        self.cartel_rollo.add_widget(label_digitos)
        self.cartel_rollo.add_widget(self.textinput_digitos)
        self.cartel_rollo.add_widget(label_num_rollo)
        self.cartel_rollo.add_widget(self.textinput)
        self.cartel_rollo.add_widget(self.error_label)
        self.cartel_rollo.add_widget(archivo_nuevo)

        self.popup = Popup(
            title='Ingrese Numero de Rollo y Cantidad de Digitos',
            content=self.cartel_rollo,
            size_hint=(None, None),
            size=(450, 400),
            auto_dismiss=False
        )
        self.popup.open()

        def focus_input(*args):  # pylint: disable=unused-argument
            self.textinput.focus = True
        Clock.schedule_once(focus_input, 0.1)

        archivo_nuevo.bind(on_press=self.asignar_numero_rollo)  # pylint: disable=no-member
        self.textinput.bind(  # pylint: disable=no-member
            on_text_validate=lambda instance: self.asignar_numero_rollo()
        )
        self.textinput_digitos.bind(  # pylint: disable=no-member
            on_text_validate=lambda instance: self.asignar_numero_rollo()
        )

        Window.bind(on_key_down=self._pido_rollo_key_action)
        Window.bind(on_keyboard=self._popup_on_keyboard)
        self._popup_keyboard_mode = 'pido_rollo'
        self.crear_directorio_temporal()

    def _pido_rollo_key_action(self, *args):
        '''Esc cierra Editar N item sin cambios.'''
        key_str = self._keycode_name(*args)
        print(f"pido_rollo key_down: {args[1:4]!r} -> {key_str!r}")
        if key_str == 'escape' or (len(args) > 1 and args[1] == 27):
            self._cancelar_pido_rollo()
            return True
        return False

    def _cancelar_pido_rollo(self, *args):  # pylint: disable=unused-argument
        '''Cierra el popup de item sin modificar el numero.'''
        try:
            Window.unbind(on_key_down=self._pido_rollo_key_action)
        except Exception:  # pylint: disable=broad-exception-caught
            pass
        try:
            Window.unbind(on_keyboard=self._popup_on_keyboard)
        except Exception:  # pylint: disable=broad-exception-caught
            pass
        self._popup_keyboard_mode = None
        if hasattr(self, 'popup') and self.popup and not isinstance(self.popup, str):
            try:
                self.popup.dismiss()
            except Exception:  # pylint: disable=broad-exception-caught
                pass
        Window.bind(on_key_down=self.key_action)

    def _actualizar_ui_numero(self):
        '''Actualiza botones/labels que muestran el numero de item.'''
        nro = str(self.numero_de_rollo)
        if hasattr(self, 'muestro_nro_rollo') and self.muestro_nro_rollo:
            self.muestro_nro_rollo.text = nro
        if hasattr(self, 'btn_rollo') and self.btn_rollo:
            self.btn_rollo.text = "Ítem: " + nro + "\n(+)"
        if hasattr(self, 'label_item') and self.label_item:
            self.label_item.text = f"# Item: {nro}"

    def asignar_numero_rollo(self, *args):  # pylint: disable=unused-argument
        '''Asigna el numero de rollo'''
        try:
            try:
                Window.unbind(on_key_down=self._pido_rollo_key_action)
            except Exception:  # pylint: disable=broad-exception-caught
                pass
            try:
                Window.unbind(on_keyboard=self._popup_on_keyboard)
            except Exception:  # pylint: disable=broad-exception-caught
                pass
            self._popup_keyboard_mode = None

            numero_txt = self.textinput.text.strip()
            if not numero_txt:
                self.error_label.text = "Por favor, ingrese el numero de rollo."
                return

            num_rollo = int(numero_txt)
            cantidad_digitos_text = self.textinput_digitos.text.strip()
            if not cantidad_digitos_text:
                self.error_label.text = "Por favor, ingrese la cantidad de digitos."
                return

            cantidad_digitos = int(cantidad_digitos_text)
            if cantidad_digitos < 1:
                self.error_label.text = "La cantidad de digitos debe ser mayor a 0."
                return

            self.cantidad_digitos = cantidad_digitos
            self.numero_de_rollo = f"{num_rollo:0{cantidad_digitos}d}"
            print('Num Rollo', self.numero_de_rollo)
            self._actualizar_ui_numero()

            Window.bind(on_key_down=self.key_action)
            self.popup.dismiss()
            self.arranca_callback(self, '1')
        except ValueError:
            self.error_label.text = "Por favor, ingrese un numero valido."
            print("Error: El valor ingresado no es un numero valido.")
        except Exception as e:  # pylint: disable=broad-exception-caught
            self.error_label.text = "Ocurrio un error inesperado."
            print(f"Error inesperado: {e}")

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

    def _detener_preview(self):
        '''Corta el liveview de Kivy para no pelear con capture().'''
        if getattr(self, 'timer', None):
            try:
                Clock.unschedule(self.timer)
            except Exception:  # pylint: disable=broad-exception-caught
                pass
            try:
                Clock.unschedule(self.update)
            except Exception:  # pylint: disable=broad-exception-caught
                pass
            self.timer = None
        self.lview = False
        print("Preview detenido")

    def _apagar_viewfinder(self, camera):
        '''Apaga EVF/liveview en Canon antes de disparar.'''
        for widget_name in ('eosviewfinder', 'viewfinder'):
            try:
                config = camera.get_config()
                # pylint: disable=no-member
                ok, widget = gp.gp_widget_get_child_by_name(config, widget_name)
                if ok < gp.GP_OK:  # pylint: disable=no-member
                    continue
                try:
                    widget.set_value(0)
                except Exception:  # pylint: disable=broad-exception-caught
                    try:
                        widget.set_value('0')
                    except Exception:  # pylint: disable=broad-exception-caught
                        continue
                camera.set_config(config)
                print(f"Viewfinder apagado vía {widget_name}")
                return True
            except Exception as e:  # pylint: disable=broad-exception-caught
                print(f"No se pudo apagar {widget_name}: {e}")
        print("No se encontró widget de viewfinder; se continúa igual")
        return False

    def _drenar_eventos_camara(self, camera, timeout_ms=10):
        '''Vacía la cola PTP hasta timeout (como thermal-scanner).'''
        while True:
            typ, _data = camera.wait_for_event(timeout_ms)
            if typ == gp.GP_EVENT_TIMEOUT:  # pylint: disable=no-member
                return

    def _captura_fallida(self, mensaje):
        print(f"Error en captura: {mensaje}")
        self.operacion_en_curso = False
        self.loading_cursor(False)
        try:
            self.mostrar_popup_error(str(mensaje))
        except Exception:  # pylint: disable=broad-exception-caught
            pass
        preview = self.camara_previ if self.camara_previ in ('0', '1') else '1'
        if self.cantidad_camaras == 1:
            preview = '1'
        self.arranca_callback(self, preview)

    def capture_and_save_image(self, camera, args, camera_type):
        '''Lógica común para capturar y guardar imagen de cualquier cámara'''
        if hasattr(self, 'operacion_en_curso') and self.operacion_en_curso:
            print("Otra operación está en curso. Espera a que termine.")
            return
        if not camera:
            print(f"Cámara {camera_type} no disponible")
            return

        self.operacion_en_curso = True
        self._detener_preview()
        self.loading_cursor()
        print(f'Camera {camera_type} Canon — preparando captura en hilo')

        etiqueta = args[1]

        def trabajo_captura():
            try:
                self._apagar_viewfinder(camera)
                self._drenar_eventos_camara(camera)
                # Por si la cámara volvió a "Tarjeta de memoria" (sin SD = hang).
                self._configurar_capturetarget_ram(camera)
                # Espera real: deja que la cámara salga de liveview.
                time.sleep(0.5)

                print(f'Disparando capture() en {camera_type}...')
                file_path = camera.capture(gp.GP_CAPTURE_IMAGE)  # pylint: disable=no-member
                print(f'Camera {camera_type} file path: {file_path.folder}/{file_path.name}')

                if self.cantidad_camaras == 1:
                    nombre = NOMBRE_ARCHIVO + str(self.numero_de_rollo) + '.jpg'
                else:
                    nombre = (
                        NOMBRE_ARCHIVO +
                        str(self.numero_de_rollo) +
                        '-' +
                        str(etiqueta) +
                        '.jpg'
                    )
                target = os.path.join(self.directorio_app, nombre)
                print('Copying image to', target)

                if not os.path.isdir(self.directorio_app):
                    Clock.schedule_once(
                        lambda dt: self._captura_fallida(
                            f"El directorio '{self.directorio_app}' no existe."
                        ),
                        0
                    )
                    return

                camera_file = camera.file_get(
                    file_path.folder,
                    file_path.name,
                    gp.GP_FILE_TYPE_NORMAL  # pylint: disable=no-member
                )
                target_temp = os.path.join(
                    self.directorio_temporal,
                    str(etiqueta) + '-' + file_path.name
                )
                print("Guardando imagen temporal")
                camera_file.save(target_temp)

                Clock.schedule_once(
                    lambda dt: self._despues_de_captura(
                        camera, args, camera_type, file_path, target, target_temp
                    ),
                    0
                )
            except Exception as e:  # pylint: disable=broad-exception-caught
                print(f"Error en hilo de captura: {e}")
                Clock.schedule_once(lambda dt, err=e: self._captura_fallida(err), 0)

        threading.Thread(target=trabajo_captura, daemon=True).start()

    def _despues_de_captura(self, camera, args, camera_type, file_path, target, target_temp):
        '''Continúa en el hilo de Kivy tras una captura exitosa.'''
        if hasattr(self, 'popup') and self.popup and not isinstance(self.popup, str) and self.popup.parent:
            self.operacion_en_curso = False
            return

        def save_image():
            self.loading_cursor()
            print("Copying image to ", target)
            camera_file = camera.file_get(
                file_path.folder,
                file_path.name,
                gp.GP_FILE_TYPE_NORMAL  # pylint: disable=E1101
            )
            try:
                camera_file.save(target)

                if camera_type == 'camera_01' and self.imagen_espejada:
                    img_pil = Imge.open(target)
                    img_array = np.asarray(img_pil)
                    img_array_flipped = np.fliplr(img_array)
                    img_pil_flipped = Imge.fromarray(img_array_flipped.astype('uint8'))
                    img_pil_flipped.save(target)
                    print(f"Imagen espejada y guardada en {target}")
                else:
                    print(f"Imagen guardada en {target}")

            except Exception as e:  # pylint: disable=broad-exception-caught
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
            while typ != gp.GP_EVENT_TIMEOUT and attempts > 0:  # pylint: disable=no-member
                print("Event")
                if typ == gp.GP_EVENT_FILE_ADDED:  # pylint: disable=no-member
                    print(f'Camera: {camera_type} - file path: {data.folder}/{data.name}')
                    if self.cantidad_camaras == 1:
                        raw_nombre = (
                            NOMBRE_ARCHIVO +
                            str(self.numero_de_rollo) +
                            '.cr3'
                        )
                    elif camera_type == "camera_01":
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
                            str(args[1]) + '.nef'
                        )
                    raw_target = os.path.join(self.directorio_app, raw_nombre)
                    print('Copying image to', raw_target)
                    camera_file = camera.file_get(
                        data.folder,
                        data.name,
                        gp.GP_FILE_TYPE_NORMAL  # pylint: disable=no-member
                    )
                    camera_file.save(raw_target)

                    if camera_type == 'camera_01':
                        if self.cantidad_camaras == 1:
                            self.aumentar_1_nro_rollo()
                            self.arranca_callback(self, '1')
                        else:
                            self.arranca_callback(self, '0')
                    elif camera_type == 'camera':
                        self.mostrar_pregunta(self.manejar_respuesta)

                typ, data = camera.wait_for_event(1)
                attempts -= 1

        self._show_confirmation_popup(target, target_temp, save_image)


    def _keycode_name(self, *args, key=None, codepoint=None):
        '''Normaliza teclas de Kivy/SDL2 a nombres (escape, enter, down, ...).'''
        if key is None and len(args) > 1:
            key = args[1]
        if codepoint is None and len(args) > 3:
            codepoint = args[3]

        if isinstance(key, (tuple, list)) and len(key) > 1:
            return str(key[1]).lower()

        if isinstance(key, int):
            try:
                from kivy.core.window import Keyboard
                for name, code in Keyboard.keycodes.items():
                    if code == key:
                        return name
            except Exception:  # pylint: disable=broad-exception-caught
                pass
            fallback = {
                27: 'escape',
                13: 'enter',
                271: 'numpadenter',
                273: 'up',
                274: 'down',
            }
            if key in fallback:
                return fallback[key]

        if codepoint:
            return str(codepoint).lower()
        return ''

    def _bind_yes_no_keys(self, btn_yes, btn_no, on_yes, on_no):
        '''Teclado para popups Si/No: Enter confirma foco, flechas ciclan, Esc=No.'''
        Window.unbind(on_key_down=self.key_action)
        try:
            Window.unbind(on_key_down=self._pido_rollo_key_action)
        except Exception:  # pylint: disable=broad-exception-caught
            pass
        try:
            Window.unbind(on_key_down=self._yes_no_key_action)
        except Exception:  # pylint: disable=broad-exception-caught
            pass
        try:
            Window.unbind(on_keyboard=self._popup_on_keyboard)
        except Exception:  # pylint: disable=broad-exception-caught
            pass

        self._yn_focus = 0
        self._yn_buttons = (btn_yes, btn_no)
        self._yn_callbacks = (on_yes, on_no)
        self._yn_normal_colors = (
            tuple(btn_yes.background_color),
            tuple(btn_no.background_color),
        )
        self._popup_keyboard_mode = 'yes_no'
        self._update_yn_focus_visual()
        Window.bind(on_key_down=self._yes_no_key_action)
        # Esc en SDL2 llega por on_keyboard -> on_request_close; hay que interceptarlo.
        Window.bind(on_keyboard=self._popup_on_keyboard)

    def _unbind_yes_no_keys(self):
        try:
            Window.unbind(on_key_down=self._yes_no_key_action)
        except Exception:  # pylint: disable=broad-exception-caught
            pass
        try:
            Window.unbind(on_keyboard=self._popup_on_keyboard)
        except Exception:  # pylint: disable=broad-exception-caught
            pass
        self._popup_keyboard_mode = None
        Window.bind(on_key_down=self.key_action)

    def _update_yn_focus_visual(self):
        for i, btn in enumerate(self._yn_buttons):
            if i == self._yn_focus:
                btn.background_color = self.color_boton_foco
            else:
                btn.background_color = (
                    self._yn_normal_colors[i]
                    if self._yn_normal_colors else self.color_botones
                )

    def _handle_yes_no_key(self, key_str):
        if key_str in ('down', 'up'):
            self._yn_focus = 1 - self._yn_focus
            self._update_yn_focus_visual()
            return True
        if key_str in ('enter', 'numpadenter'):
            self._unbind_yes_no_keys()
            self._yn_callbacks[self._yn_focus]()
            return True
        if key_str == 'escape':
            self._unbind_yes_no_keys()
            self._yn_callbacks[1]()
            return True
        return False

    def _yes_no_key_action(self, *args):
        key_str = self._keycode_name(*args)
        print(f"yes_no key_down: args={args[1:4]!r} -> {key_str!r}")
        if self._handle_yes_no_key(key_str):
            return True
        return True

    def _popup_on_keyboard(self, window, key, scancode=None, codepoint=None,
                           modifier=None, **kwargs):  # pylint: disable=unused-argument
        '''Intercepta teclas de popup; crítico para Esc (evita cerrar la app).'''
        key_str = self._keycode_name(key=key, codepoint=codepoint)
        print(f"popup on_keyboard: key={key!r} codepoint={codepoint!r} -> {key_str!r} mode={self._popup_keyboard_mode}")

        if self._popup_keyboard_mode == 'yes_no':
            if self._handle_yes_no_key(key_str):
                return True
            # Consumir Esc aunque no matchee, para no disparar on_request_close.
            if key == 27 or key_str == 'escape':
                self._unbind_yes_no_keys()
                self._yn_callbacks[1]()
                return True
            return False

        if self._popup_keyboard_mode == 'pido_rollo':
            if key == 27 or key_str == 'escape':
                self._cancelar_pido_rollo()
                return True
            return False

        return False

    def _show_confirmation_popup(self, target, target_temp, save_image):
        self.loading_cursor(False)

        try:
            img_pil = Imge.open(target_temp)
            img_array = np.asarray(img_pil)
            print(f"Camara Previ: {self.camara_previ}, Imagen Espejada: {self.imagen_espejada}")
            if self.camara_previ == '1' and self.imagen_espejada:
                img_array = np.fliplr(img_array)
            img_pil_processed = Imge.fromarray(img_array.astype('uint8'))
            preview_temp = os.path.join(self.directorio_temporal, 'preview_temp.jpg')
            img_pil_processed.save(preview_temp)
        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"Error procesando imagen para preview: {e}")
            preview_temp = target_temp

        def on_confirm(instance=None):  # pylint: disable=unused-argument
            self._unbind_yes_no_keys()
            self.loading_cursor()
            self.popup.dismiss()
            self.timer = Clock.schedule_interval(self.update, 1.0 / 24.0)
            if os.path.exists(target_temp):
                os.remove(target_temp)
            if os.path.exists(preview_temp):
                try:
                    os.remove(preview_temp)
                except Exception:  # pylint: disable=broad-exception-caught
                    pass
            save_image()
            self.loading_cursor(False)
            self.operacion_en_curso = False

        def on_cancel(instance=None):  # pylint: disable=unused-argument
            self._unbind_yes_no_keys()
            self.loading_cursor(False)
            self.popup.dismiss()
            self.timer = Clock.schedule_interval(self.update, 1.0 / 24.0)
            if os.path.exists(target_temp):
                os.remove(target_temp)
            if os.path.exists(preview_temp):
                try:
                    os.remove(preview_temp)
                except Exception:  # pylint: disable=broad-exception-caught
                    pass
            print("Operacion cancelada por el usuario.")
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
        btn_yes.bind(on_release=on_confirm)  # pylint: disable=E1101
        btn_no.bind(on_release=on_cancel)  # pylint: disable=E1101

        print(f"Target: {target}")
        print(f"Exite? {os.path.isfile(target)}")
        if os.path.isfile(target):
            label_popup = (
                f"El archivo '{os.path.basename(target)}' " +
                "ya existe. ¿Desea sobreescribirlo?"
            )
        else:
            label_popup = "¿Desea guardar la imagen?"

        box.add_widget(Label(text=label_popup))
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
        self._bind_yes_no_keys(btn_yes, btn_no, on_confirm, on_cancel)

    def btn_exit_callback(self, *args, **kwargs):  # pylint: disable=unused-argument
        '''Salir del programa liberando la sesión PTP sin reabrirla.'''
        # Esc con popup abierto a veces llega acá vía on_request_close(source=keyboard).
        if kwargs.get('source') == 'keyboard' and self._popup_keyboard_mode:
            if self._popup_keyboard_mode == 'pido_rollo':
                self._cancelar_pido_rollo()
                return True
            if self._popup_keyboard_mode == 'yes_no' and self._yn_callbacks:
                self._unbind_yes_no_keys()
                self._yn_callbacks[1]()
                return True

        if getattr(self, 'timer', None):
            try:
                Clock.unschedule(self.timer)
            except Exception:  # pylint: disable=broad-exception-caught
                pass
            self.timer = None

        self.eliminar_directorio_temporal()

        for attr in ('camera', 'camera_01', 'camara'):
            cam = getattr(self, attr, None)
            if cam:
                try:
                    cam.exit()
                    print(f"Cámara {attr} cerrada")
                except Exception as e:  # pylint: disable=broad-exception-caught
                    print(f"Error al cerrar {attr}: {e}")
                setattr(self, attr, None)

        App.get_running_app().stop()
        return True

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
        if hasattr(self, 'popup') and self.popup and not isinstance(self.popup, str) and self.popup.parent:
            print("El popup ya está abierto, no se abrirá nuevamente")
            self.popup.dismiss()

        def close_app(instance): # pylint: disable=unused-argument
            App.get_running_app().stop()
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

        self.popup = Popup(
            title="Error",
            content=layout,
            size_hint=(None, None),
            size=(500, 200),
            auto_dismiss=False  # Evita que el usuario cierre el popup sin el botón
        )

        self.popup.open()

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
        ''' Muestra un popup con una pregunta de Si o No '''
        print("Esperando 2 segundo para que la camara termina la operacion anterior...")
        Clock.schedule_once(self._despues_de_esperar, 2)

        if hasattr(self, 'popup') and self.popup and not isinstance(self.popup, str) and self.popup.parent:
            print("El popup ya esta abierto, no se abrira nuevamente")
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

        def on_yes(instance=None):  # pylint: disable=unused-argument
            self._unbind_yes_no_keys()
            self._cerrar_popup(callback, True)

        def on_no(instance=None):  # pylint: disable=unused-argument
            self._unbind_yes_no_keys()
            self._cerrar_popup(callback, False)

        btn_si.bind(on_press=on_yes)  # pylint: disable=no-member
        btn_no.bind(on_press=on_no)  # pylint: disable=no-member

        self.popup = Popup(
            title="Finalizar proceso",
            content=box,
            size_hint=(None, None),
            size=(400, 200),
            auto_dismiss=False
        )
        self.popup.open()
        self._bind_yes_no_keys(btn_si, btn_no, on_yes, on_no)
        self.loading_cursor(False)

    def _cerrar_popup(self, callback, respuesta):
        ''' Cierra el popup y llama a la funcion de callback con la respuesta '''
        Clock.schedule_once(lambda dt: self.popup.dismiss(), 0.1)
        Clock.schedule_once(lambda dt: callback(respuesta), 0.2)

    def aumentar_1_nro_rollo(self, *args):  # pylint: disable=W0613
        '''Funcion para aumentar en 1 el nro de rollo'''
        try:
            digits = self.cantidad_digitos or len(str(self.numero_de_rollo))
            if not digits:
                digits = 4
            num = int(self.numero_de_rollo) + 1
            self.cantidad_digitos = digits
            self.numero_de_rollo = f"{num:0{digits}d}"
            print(f'Nuevo numero de rollo: {self.numero_de_rollo}')
            self._actualizar_ui_numero()
        except (TypeError, ValueError) as e:
            print(f"No se pudo aumentar el numero de item: {e}")

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
            print("El usuario eligio Si")
            if not self.combinar_imagenes():
                self.loading_cursor(False)
                return

            self.cambio_de_diapo()

            self.numero_de_rollo_anterior = self.numero_de_rollo
            digits = self.cantidad_digitos or 4
            num = int(self.numero_de_rollo) + 1
            self.numero_de_rollo = f"{num:0{digits}d}"
            print('# nuevo', self.numero_de_rollo)
            self._actualizar_ui_numero()

            self.arranca_callback(self, '1')
            Clock.schedule_once(lambda dt: self.arranca_callback(self, '1'), 0.1)
            self.loading_cursor(False)
        else:
            print("El usuario eligio No")
            self.arranca_callback(self, '0')
            Clock.schedule_once(lambda dt: self.arranca_callback(self, '0'), 0.1)
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

    def _asegurar_zenity(self):
        '''Instala zenity si falta (diálogo nativo GTK compatible con Kivy).'''
        if shutil.which('zenity'):
            return True
        print("zenity no está instalado. Instalando...")
        try:
            subprocess.check_call(['sudo', 'apt', 'install', '-y', 'zenity'])
        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"No se pudo instalar zenity: {e}")
            return False
        return bool(shutil.which('zenity'))

    def _elegir_carpeta_nativa(self, initial_dir):
        '''
        Selector de carpeta nativo de Ubuntu.
        Usa zenity (GTK): tkinter.askdirectory pelea el foco con la ventana SDL/Kivy
        y el diálogo queda inutilizable (solo Esc cancela).
        '''
        initial_dir = initial_dir or os.path.expanduser("~/Documentos")
        if not os.path.isdir(initial_dir):
            initial_dir = os.path.expanduser("~")

        if self._asegurar_zenity():
            cmd = [
                'zenity',
                '--file-selection',
                '--directory',
                '--title=Seleccionar Carpeta',
                f'--filename={initial_dir.rstrip("/")}/',
            ]
            print(f"Abriendo zenity: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            if result.returncode == 0:
                return result.stdout.strip()
            if result.stderr:
                print(f"zenity stderr: {result.stderr.strip()}")
            return ''

        # Fallback (puede fallar el foco con Kivy)
        print("Fallback a tkinter.filedialog (puede fallar el foco con Kivy)")
        root = tk.Tk()
        root.withdraw()
        try:
            root.attributes('-topmost', True)
        except Exception:  # pylint: disable=broad-exception-caught
            pass
        carpeta = filedialog.askdirectory(
            title="Seleccionar Carpeta",
            initialdir=initial_dir
        )
        try:
            root.destroy()
        except Exception:  # pylint: disable=broad-exception-caught
            pass
        return carpeta or ''

    def cambiar_directorio(self, *args):  # pylint: disable=unused-argument
        '''Abre el dialogo nativo de Ubuntu para elegir carpeta.'''
        if self._eligiendo_directorio:
            print("Ya hay un diálogo de directorio abierto; se ignora reentrada.")
            return
        self._eligiendo_directorio = True
        Window.unbind(on_key_down=self.key_action)
        try:
            carpeta = self._elegir_carpeta_nativa(self.directorio_app)
        finally:
            Window.bind(on_key_down=self.key_action)
            self._eligiendo_directorio = False

        if not carpeta:
            print("No se selecciono ninguna carpeta.")
            return

        if carpeta != self.directorio_app:
            self.directorio_app = carpeta
            self.estado_actual.text = f"Directorio: {carpeta}"
            print(f"Carpeta seleccionada: {self.directorio_app}")
        else:
            print("La carpeta seleccionada es la misma.")

    def select_directory(self, selection):
        '''Compatibilidad: selecciona directorio desde lista.'''
        if not selection:
            print("No se selecciono ninguna carpeta.")
            return
        selected_path = selection[0]
        if os.path.isfile(selected_path):
            selected_path = os.path.dirname(selected_path)
        if selected_path != self.directorio_app:
            self.directorio_app = selected_path
            self.estado_actual.text = f"Directorio: {selected_path}"
            print(f"Carpeta seleccionada: {self.directorio_app}")
        if hasattr(self, 'popup') and self.popup and not isinstance(self.popup, str) and getattr(self.popup, 'parent', None):
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
            self.btn_rotar_diapo.text = self._texto_btn_rotar(True)
            self.btn_rotar_diapo.background_color = (0.2, 0.8, 0.2, 0.8)  # Verde
        else:
            self.btn_rotar_diapo.text = self._texto_btn_rotar(False)
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
