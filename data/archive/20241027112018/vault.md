

Link: https://raw.githubusercontent.com/Axlfc/ScriptsEditor/b8f16d40e6dc06aaac38d3226f97bf821d738d7c/main.py
================================================================================================================
from src.views.app_layers import create_app
from src.views.tk_utils import root

def main():
    """
        Initializes and runs the main application window.

        This function sets up the main window for the Scripts Editor application. It defines window properties,
        initializes the user interface components, and enters the main event loop to start the application.

        Parameters:
        None

        Returns:
        None
    """

    def run_app():
        # TODO: LOADS FROM USER CONFIG IF THERE IS ONE
        create_app()
        root.mainloop()

    run_app()

if __name__ == '__main__':
    main()
USER: What does this function do?
AI: The `main()` function initializes and runs the main application window of the Scripts Editor application. It likely uses the `create_app` function from `src.views.app_layers` to create the main window and utilizes Tkinter (`root` from `src.views.tk_utils`) for the user interface.

Document: ProyectoFinal_Axel_Fernandez.pdf
==============================================
Propuesta de trabajo 2ª Evaluación PMV, 23D, RVA y PIA – 2022-2023
Entrega 21 de Febrero 2023
 Principal referencia:
https://www.youtube.com/watch?v=HFtQ7yix1-U
RV A (Mikel Louvelli):
 
Primera fase
Crearemos un PDF con el siguiente contenido:
 
a-Sinopsis:
En tres-cuatro frases contamos nuestra  historia. Hay un acontecimiento que ha roto la  rutina y 
desata nuestra misión. Marcamos el objetivo y los obstáculos que encontraremos en el camino.
Un día, el toro de San Fermín salió de su establo y esto desató una misión para llevarlo de 
vuelta a su hogar. El objetivo era guiar al toro a través de los desafíos y peligros de la ciudad. 
Nuestro objetivo: salvar al toro de San Fermín. Atravesamos una serie de pruebas, superando 
los obstáculos a superar incluyendo vallas, carteles, multitudes de personas, perros y otros 
animales que se nos presentan en el camino. Con determinación y valentía, el toro de San 
Fermín logra llegar a su hogar seguro. ¡Una hazaña para recordar! 
b- Referencias visuales:
Es muy importante recoger referencias que nos aporten ideas y detalles que enriquecerán nuestro 
proyecto. Insertar en el PDF Enlaces a vídeos, imágenes, etc  de otras producciones (películas, 
juegos, series, animación, …) en los que nos guste la ambientación (texturas, iluminación, 
elementos de composición). Añadir  junto a la referencia una anotación explicando qué es lo que 
os gusta de esa referencia en concreto.
Añadir mínimo 10 referencias.
https://www.youtube.com/watch?v=fB2QVTd7uJQ
https://www.youtube.com/watch?v=PBxZiqkSwIo
https://www.youtube.com/watch?v=IM0dif-4vpo

https://www.youtube.com/watch?v=v6efaVMwPzI
https://www.youtube.com/watch?v=L9RDath65XA

https://www.youtube.com/watch?v=H3Rc_7dj4Ow
https://www.youtube.com/watch?v=HTMDNZOlUq4
https://www.youtube.com/watch?v=VKnJf5jn68w

https://www.youtube.com/watch?v=hK13SieHm6I

https://www.youtube.com/watch?v=ee8e84r8y5s

Segunda fase
Se trabajará y valorará:
-Que se añada algún elemento texturizado utilizando Substance Painter (utilizando bake de 
texturas y las herramientas presentadas en la primera evaluación).
 
-Harmonía del nivel en cuanto a la utilización de la paleta de colores y texturizado (se explicará 
con ejemplos en clase).
 
-Harmonía del nivel en cuanto a la ambientación. Tanto combinando elementos diferentes para la
composición de espacios  como efectos de iluminación (se explicará con ejemplos en clase).
 
-Diseño de flujo de atención (recursos de utilización de elementos, formas,  color y/o 
iluminación, etc).
Proyecto PMV y 23D
Se trata de desarrollar un nivel jugable con un diseño coherente y funcional, que tenga mecánicas y un 
sistema de juego. 
-Se debe usar el THIRD PERSON TEMPLATE.
-Debe ser un escenario funcional, transitable y definido, sin espacios vacíos ni zonas por las que no se 
pueda pasar si no hay una barrera visible.
-El nivel debe tener diseñado el flujo de atención y debe ser comprensible la transitabilidad y las zonas 
importantes.
-Debe tener un personaje principal con una máquina de estados que pueda, al menos, andar, correr, 
saltar e interactuar de alguna manera (cogiendo, pulsando o haciendo algo).
-Debe existir un gameplay, o sea, que a través de una serie de mecánicas, se pueda conseguir un objetivo
(o varios) superando un reto del tipo que sea.
-Debe tener un menú de entrada y un menú de pausa.
-Debe ser funcional desde el arranque, teniendo configurados los niveles y su carga de manera 
adecuada.
-Debe tener una iluminación movable usando Lumen.
Proyecto I.A. Unreal
El ejercicio final del tema de Inteligencia Artificial, es un proyecto en el que al menos un NPC
debe implementar una serie de acciones definidas. Para ello, se ha de utilizar la herramienta que
proporciona Unreal para especificar el comportamiento de personajes no controlados por el
jugador (Behaviour Tree/Blackboard).
El Árbol de Decisiones que ese genere, debe cumplir los siguientes requisitos mínimos:
- 4 ramas Selector
- 4 ramas Sequence
- 8 Task (de las cuales 4 deben ser personalizadas)
- 4 Decorators
- 1 Service
El tema del proyecto a realizar es libre, pero el Árbol de Decisión que se genere debe como
mínimo implementar el movimiento del NPC y la reacción ante el personaje controlado por el
jugador.
Además, tal y como el termino IA indica, el comportamiento del NPC debe ser lo más realista
posible.

Link: https://raw.githubusercontent.com/Axlfc/ScriptsEditor/b8f16d40e6dc06aaac38d3226f97bf821d738d7c/main.py
================================================================================================================
from src.views.app_layers import create_app
from src.views.tk_utils import root

def main():
    """
        Initializes and runs the main application window.

        This function sets up the main window for the Scripts Editor application. It defines window properties,
        initializes the user interface components, and enters the main event loop to start the application.

        Parameters:
        None

        Returns:
        None
    """

    def run_app():
        # TODO: LOADS FROM USER CONFIG IF THERE IS ONE
        create_app()
        root.mainloop()

    run_app()

if __name__ == '__main__':
    main()
USER: What does this function do?
AI: The `main()` function initializes and runs the main application window of the Scripts Editor application. It likely uses the `create_app` function from `src.views.app_layers` to create the main window and utilizes Tkinter (`root` from `src.views.tk_utils`) for the user interface.
USER: ¿QUé partes tiene el proyecto?
AI: El proyecto parece tener las siguientes partes:

* **Interfaz de usuario:** Usa Tkinter para la interfaz gráfica.
* **Lógica de aplicación:** Existe en el módulo `src.views.app_layers` y maneja las funcionalidades principales de la aplicación.
* **Utilidades de Tkinter:** Probablemente contiene funciones y clases para gestionar los elementos de Tkinter y las interacciones del usuario.
