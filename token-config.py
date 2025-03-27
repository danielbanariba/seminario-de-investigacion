import time
import random
import re
import logging
from bs4 import BeautifulSoup
from locust import HttpUser, task, between, tag

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MoodleUser(HttpUser):
    """
    Usuario simulado para pruebas de carga en Moodle usando token de autenticación
    """
    # Tiempo de espera entre tareas (entre 2 y 5 segundos)
    wait_time = between(2, 5)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Token de autenticación para la API de Moodle
        # Este token debe ser reemplazado con el token generado para el usuario admin
        # Lo obtendremos automáticamente del comando:
        # php admin/cli/create_token.php --username=admin --password=password --name=locust_token --service=moodle_mobile_app
        self.token = 'TOKEN_VALUE'  # Reemplazar con el token generado
        self.courses = []
        self.user_info = {}
        self.logged_in = True  # Con token, estamos siempre "logged in"
