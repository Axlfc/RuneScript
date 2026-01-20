from datetime import datetime
from plyer import notification

class Notificador:
    @staticmethod
    def enviar_titulo_mensaje(titulo, mensaje):
        try:
            notification.notify(title=titulo, message=mensaje, timeout=10)
        except Exception as e:
            print(f"Error enviando notificaciÃ³n: {e}")
