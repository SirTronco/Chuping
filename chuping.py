# Chuping v2.0 - Raúl Ferrer 2024  para COLEGIOS LAUDE

# TODO:
#   - Auto-registre de terminació d'arxius
#   - Inserció de IPs manualment - Fará falta fer un sistema manual de inserció de dades
#   - Grabació de Monitors
#   - Si no podem fer una consola de comando que rebose, tenim que:
#       • Limitar la impresió de linees
#       • Bloquetjar la pantalla
#       • Opcionar la informació que es veu
#   - opcion -s que conecta a servidor para CHUPARRRRR los hosts de la base de datos
#   - opcion -a que conecta a un servidor por API





import subprocess
import threading
import os
import sys
import re
from colorama import Fore, Style, Back
from blessed import Terminal
import time
import json
from wcwidth import wcswidth
import ctypes
from ctypes import wintypes


# ------------------------------------------------------------------------------------------------------------------------------------------------
#                                       CLASSES I ESTRUCTURES
# ------------------------------------------------------------------------------------------------------------------------------------------------
class COORD(ctypes.Structure):
    _fields_ = [
        ("X", wintypes.SHORT),
        ("Y", wintypes.SHORT),
    ]

    def copy(self): # per a poder fer copies
        return COORD(X = self.X, Y = self.Y)

    def __eq__(self, other): # per a poder fer comparacions ==
        if isinstance(other, COORD): #comprovar si l'altra instancia es també del tipo COORD
            return self.X == other.X and self.Y == other.Y
        return False


# Cargar kernel32.dll
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

# Obtener el identificador de la consola estándar
stdout_handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE = -11

tamanyFinestraAnterior = COORD(X=0, Y=0)
tamanyFinestraAra = COORD(X=0, Y=0)

# DEBUG - Lista de hosts als que volem fer PING
grupPing = {
    "nomgrup": "TEST GOOGLE",
    "hosts":[
        {
            "ordre": 1,
            "nom": "Google",
            "ip": "8.8.8.8",
            "historial": ""
        }
    ]
}





# ------------------------------------------------------------------------------------------------------------------------------------------------
#                                       P I N G 
# ------------------------------------------------------------------------------------------------------------------------------------------------
def ping(host):
    # Valors trivials
    ms = ""
    resultat = ""
    coloret = f"{Style.RESET_ALL}"

    # Imprimim la petició ping
    imprimemela("🔳 ", host, resultat, ms, coloret)


    # Executa el comando 'ping' y redirigeix la eixida linia a linea
    process = subprocess.Popen(["ping", host["ip"],"-n", "1", "-w", "2000"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    # Seleccionar sólo las respuestas adecuadas
    # Valors trivials (tenen que vindre ací, si no es sobre escribeix antes de saltar el process)
    ms = "- -"
    resultat = "...nope"
    paso = lagMeter()
    coloret = f"{Back.RED}"
    host["fallos"] += 1 # de moment el fallo tel endus, ahi, de calentet

    # aquí el rollo es que la respuesta del programa PING son muchas lineas, y sólo nos interesa saber si hay alguna
    # que empieze por "Respuesta desde", de no ser así, damos por hecho que hay un fallo.
    for line in process.stdout:
        # recuperem cada linia
        eixida = line.strip()


        if eixida[:15]  == "Respuesta desde": # triem només la linia que informa de la resposta

            #resultat = eixida
            # Ara busquem a vore si hi han millisegons de resposta
            encontrar_ms = re.search(r"tiempo([<=])\s*(\d+(\.\d+)?)\s*(ms?)", eixida)
            
            if encontrar_ms:
                resultat = "Resposta!"
                ms = int( encontrar_ms.group(2) )
                paso = lagMeter(ms)
                ms = str(ms) + "ms" # el pasem a string

                coloret = f"{Back.GREEN}"
                host["fallos"] -= 1 # Va, tel lleve

    # Imprimim el resultat si coincideix
    host["historial"] += paso
    imprimemela("🔲 ",host, resultat, ms, coloret)

# ---------------------------------------
# Control de THREADS
# ---------------------------------------
def chuping(hosts):
    # Crea un hilo separado para cada host
    threads = []
    
    for host in hosts:
        thread = threading.Thread(target=ping, args=(host,))
        threads.append(thread)
        thread.start()

    # Espera a que todos los hilos terminen
    #for thread in threads:
    #    thread.join()


# ---------------------------------------------------------------------------------------------------------------------
#               I M P R I M E M E L A
# ---------------------------------------------------------------------------------------------------------------------
# Aquí rebrem les peticions de impresió i imprimirem cada ping al seu lloc
def imprimemela(prefixe, host, resultat, ms, coloret, debug = ""):
    # Inicialitzem
    primeraLinia = -1 if grupPing["nomgrup"]=="" else 0
    fallos = ""
    historial = host["historial"]

    # preparem debug. Si te valor li fiquem un guionet darrere y separació
    debug = " - " + debug if debug != "" else debug

    # Formatejar el nom del host a un tamany fixe, independent de la resposta
    nom = host["nom"].ljust(15,".")
    nom = nom[:15]

    ip = "(" + host["ip"] +")" 
    ip = ip.rjust(17)

    # Apliquem fondo segons l'ordre
    fondoLinia = pantalla.on_color_rgb(50, 50, 50)
    fondoVERD = pantalla.on_color_rgb(50, 170, 50)
    fondoROIG = pantalla.on_color_rgb(200, 50, 50)
    fondoBLAU = pantalla.on_color_rgb(0, 000, 255)

    ordre = 0
    ordre=host["ordre"] 
    if  ordre % 2 == 0:
        fondoLinia = pantalla.on_color_rgb(30, 30, 30)
        fondoVERD = pantalla.on_color_rgb(50, 140, 50)
        fondoROIG = pantalla.on_color_rgb(170, 50, 50)
        fondoBLAU = pantalla.on_color_rgb(0, 000, 215)

    # Seleccionem el color de la linia, segons la resposta
    coloret = fondoROIG
    if resultat == "Resposta!": coloret = fondoVERD

    # Tenim que discernir si estem fent petició, o estem mostrat resultat
    if resultat != "":
        resultat = resultat.ljust(10)
        resultat = f"{coloret}  {resultat} {Style.RESET_ALL}"
        fallos = str (host["fallos"])
        fallos = fallos.rjust(6)
        fallos = f"{coloret}-  Fallos:{fallos}  {Style.RESET_ALL}"

        # Formatejem el historial, per a que sempre mostre 10 espais, y només els 10 últims, així fem el efecte de gráfica
        historial = historial.ljust(20)
        historial = historial[-20:]
        historial = historial.replace("", " ") # les añadimos espacios
        historial = historial.replace (".", f"{Fore.RED}█{Fore.LIGHTWHITE_EX}") # cambiamos y coloreamos a bloque color ROJO

    else: # si no te resultat, entenem que estem imprint la linia de mostreig.
        fallos = ""
        ms = ""
        historial = ""


    if ms !="": # si no tenim ms es perque encara no estem mostrant resultat
        ms = ms.center(7) 
        ms = f"{fondoBLAU} {ms} "

    # preparem la traca final
    imprimemelo = f"{fondoLinia}{Fore.LIGHTWHITE_EX}{prefixe}{nom}. {ip}: {resultat}{fallos}{ms}{fondoLinia}{historial}{debug}"

    print( pantalla.move_yx(host["ordre"] + primeraLinia, 0) + imprimemelo )


# -----------------------------------------------------------------------------------------------------
#                           L A G M E T E R  
# -----------------------------------------------------------------------------------------------------
def lagMeter(ms=1000): # Pre-condición Trivial
    resultat = "." # valor trivial: no hay respuesta
       
    #  ▁ ▃ ▅ ▇
    # Sel·leccionem els umbrals
    # 1 - Correcto:     < 5
    if ms < 5:
        resultat ="▁"

    # 2 - Congestión:   < 15
    elif ms < 15:
        resultat ="▃"

    # 3 - Sobercarga:   < 25
    elif ms < 25:
        resultat ="▅"

    # 4 - Sobercarga:   < 1000
    elif ms < 1000:
        resultat ="▇"

    # 5 - Desconectado: > 1000 >
    # no cal fer res, es el valor trivial

    return resultat



#   ------------------------------------------------------------------------------------------------------
#                                 --------------  MAIN  -----------------
#   ------------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    # Inicialitzem pantalla
    pantalla = Terminal()

    # Guardem l'arxiu
    # with open("hosts.json", "w", encoding="utf-8") as file:
    #   json.dump(hosts, file, indent=4, ensure_ascii = False)
            
    # -- CONTROL DE ARGUMENTS DE ENTRADA
    # Si te un argument, carreguem els hosts
    if len(sys.argv) > 1:
        
        # -----------------------------------------------------
        # ES UN ARXIU
        opcio1 = str(sys.argv[1])
        if opcio1[-8:] == ".chuping":
            try:
                with open(opcio1, "r", encoding="utf-8") as file:
                    grupPing = json.load(file)

                    # Ara agregar-li els camps que no volem guardar, pero si fan falta
                    index = 0
                    for host in grupPing["hosts"]:
                        # Historial de conexió
                        host["historial"] = ""  
                        
                        # Ordre de aparició
                        index += 1
                        host["ordre"] = index

                        # Fallos de resposta
                        host["fallos"] = 0
                
                print(f"Arxiu {opcio1} JSON carregat:{grupPing}")

            except FileNotFoundError:
                print(f"Arxiu {opcio1} no existeix")
                time.sleep()

            except json.JSONDecodeError:
                print (f"L'arxiu no pareix que tinga la estructura correcta")
                time.sleep()

        else:
            # -----------------------------------------------------
            # ES UN HOST
            nomHost = "el HOST"

            # Si tenim un altre parámetre, aquest serà el nom
            if len(sys.argv) > 2:
                nomHost = sys.argv[2]
            
            grupPing = {
                "nomgrup": "",
                "hosts":[
                    {
                        "ordre": 1,
                        "nom": nomHost,
                        "ip": opcio1,
                        "historial": "",
                        "fallos": 0
                    }
                ]
            }
        



    # Desgranem les variables
    hosts = grupPing["hosts"]
    nomgrup = grupPing["nomgrup"]


    # Dibuixem la pantalla per a grupos
    if nomgrup != "":     # Imprimim títol de grup
        nomgrup = nomgrup.center(80)
        print(f"{Back.LIGHTBLACK_EX}{nomgrup}{Style.RESET_ALL}")

    # Formem la pantalla, depenent de les linees de hosts
    #os.system("mode con: cols=123 lines=" + str(len(hosts)) )


    # -------------------------------------------------------------------------------------
    # EL BUCLE
    # -----------------------------------------------------------------------------------
    os.system('cls')     # Borrar la pantalla
    
    tamanyFinestraAnterior.X = pantalla.width
    tamanyFinestraAnterior.Y = pantalla.height
    totalPINGS = 0

    while True:
        # ------------------------------
        # Preparar pantalla
        
        tamanyFinestraAra.X = pantalla.width
        tamanyFinestraAra.Y = pantalla.height
        totalPINGS += 1

        # comprovem si ha hagut camvi de finestra, y refresquem la pantalla
        if tamanyFinestraAnterior != tamanyFinestraAra:
            tamanyFinestraAnterior = tamanyFinestraAra.copy() #actualitzem
            # Borrar la pantalla
            os.system('cls')

        # -- Preparem la pantalla
        barraSuperior = grupPing["nomgrup"]
        if barraSuperior != "":
            barraSuperior = barraSuperior.center(pantalla.width-1)
            print(pantalla.move_yx(0, 0) + f"{Back.WHITE}{Fore.BLACK}{barraSuperior}{Style.RESET_ALL}")

        barraInferior ="Total PINGS: " + str(totalPINGS)
        barraInferior = barraInferior.center(pantalla.width-1)
        print(pantalla.move_yx(pantalla.height-2, 0) + f"{Back.LIGHTBLACK_EX}{barraInferior}{Style.RESET_ALL}")


        with pantalla.hidden_cursor(): # llevem el cursor
            
            chuping(hosts)
        
            # Ralentizem 1 segon la següent iteració
            time.sleep(3)


