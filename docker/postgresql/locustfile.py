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
    Usuario simulado para pruebas de carga en Moodle
    """
    # Tiempo de espera entre tareas (entre 2 y 5 segundos)
    wait_time = between(2, 5)
    
    # Credenciales de prueba (múltiples usuarios)
    test_users = [
        {"username": "student1", "password": "password"},
        {"username": "student2", "password": "password"},
        {"username": "student3", "password": "password"},
        {"username": "teacher1", "password": "password"},
        {"username": "admin", "password": "W0lf12345%"}
    ]
    
    def on_start(self):
        """
        Inicialización del usuario - Login en Moodle
        """
        self.logged_in = False
        self.courses = []
        self.sesskey = None
        self.user_info = {}
        
        # Seleccionar un usuario aleatorio para las pruebas
        self.user_creds = random.choice(self.test_users)
        
        # Realizar login
        self.login()
        
        # Si el login es exitoso, obtener la lista de cursos
        if self.logged_in:
            self.get_available_courses()
    
    def login(self):
        """
        Realiza el proceso de login en Moodle
        """
        logger.info(f"Intentando login con usuario: {self.user_creds['username']}")
        
        # Primero, obtener la página de login para extraer el token de login
        response = self.client.get("/login/index.php")
        
        if response.status_code != 200:
            logger.error(f"Error accediendo a la página de login: {response.status_code}")
            return
        
        # Extraer logintoken del formulario
        soup = BeautifulSoup(response.text, 'html.parser')
        login_token_input = soup.find('input', {'name': 'logintoken'})
        
        if not login_token_input:
            logger.error("No se pudo encontrar el token de login en la página")
            return
        
        login_token = login_token_input.get('value')
        
        # Realizar el login con el token
        login_data = {
            'username': self.user_creds['username'],
            'password': self.user_creds['password'],
            'logintoken': login_token
        }
        
        response = self.client.post("/login/index.php", data=login_data)
        
        # Verificar si el login fue exitoso
        if "loginerrors" in response.text or response.status_code != 200:
            logger.error(f"Login fallido para usuario {self.user_creds['username']}")
            return
        
        # Extraer sesskey para futuras peticiones
        sesskey_match = re.search(r'"sesskey":"([^"]+)"', response.text)
        if sesskey_match:
            self.sesskey = sesskey_match.group(1)
            logger.info(f"Login exitoso para usuario {self.user_creds['username']} con sesskey {self.sesskey}")
            self.logged_in = True
        else:
            logger.warning("Login aparentemente exitoso pero no se encontró sesskey")
            self.logged_in = True
    
    def get_available_courses(self):
        """
        Obtiene la lista de cursos disponibles para el usuario
        """
        logger.info("Obteniendo lista de cursos disponibles")
        
        response = self.client.get("/my/")
        
        if response.status_code != 200:
            logger.error(f"Error accediendo a la página principal: {response.status_code}")
            return
        
        # Extraer IDs de cursos de la página
        soup = BeautifulSoup(response.text, 'html.parser')
        course_links = soup.select('.coursename a')
        
        for link in course_links:
            href = link.get('href')
            if href and 'course/view.php?id=' in href:
                course_id = re.search(r'id=(\d+)', href).group(1)
                course_name = link.text.strip()
                self.courses.append({
                    'id': course_id,
                    'name': course_name
                })
        
        logger.info(f"Encontrados {len(self.courses)} cursos para el usuario")
    
    @tag('home')
    @task(3)
    def access_home(self):
        """
        Accede a la página principal de Moodle
        """
        if not self.logged_in:
            return
        
        self.client.get("/my/")
    
    @tag('courses')
    @task(5)
    def access_course(self):
        """
        Accede a un curso aleatorio de la lista de cursos disponibles
        """
        if not self.logged_in or not self.courses:
            return
        
        # Seleccionar un curso aleatorio
        course = random.choice(self.courses)
        course_id = course['id']
        
        logger.info(f"Accediendo al curso {course['name']} (ID: {course_id})")
        
        # Acceder al curso
        response = self.client.get(f"/course/view.php?id={course_id}")
        
        if response.status_code != 200:
            logger.error(f"Error accediendo al curso {course_id}: {response.status_code}")
            return
        
        # Extraer elementos del curso para posibles accesos posteriores
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Actividades como foros, tareas, etc.
        activities = []
        activity_links = soup.select('.activityinstance a')
        
        for link in activity_links:
            href = link.get('href')
            if href:
                activity_id_match = re.search(r'id=(\d+)', href)
                if activity_id_match:
                    activity_id = activity_id_match.group(1)
                    activity_name = link.text.strip()
                    activity_type = self._determine_activity_type(href)
                    
                    activities.append({
                        'id': activity_id,
                        'name': activity_name,
                        'type': activity_type,
                        'url': href
                    })
        
        # Guardar las actividades para posibles accesos posteriores
        course['activities'] = activities
    
    def _determine_activity_type(self, url):
        """
        Determina el tipo de actividad a partir de la URL
        """
        if 'mod/forum' in url:
            return 'forum'
        elif 'mod/assign' in url:
            return 'assignment'
        elif 'mod/quiz' in url:
            return 'quiz'
        elif 'mod/resource' in url:
            return 'resource'
        elif 'mod/page' in url:
            return 'page'
        elif 'mod/book' in url:
            return 'book'
        else:
            return 'unknown'
    
    @tag('activity', 'forum')
    @task(2)
    def access_forum(self):
        """
        Accede a un foro aleatorio
        """
        if not self.logged_in or not self.courses:
            return
        
        # Buscar foros en los cursos
        forums = []
        for course in self.courses:
            if 'activities' in course:
                forums.extend([a for a in course['activities'] if a['type'] == 'forum'])
        
        if not forums:
            return
        
        # Seleccionar un foro aleatorio
        forum = random.choice(forums)
        
        logger.info(f"Accediendo al foro {forum['name']} (ID: {forum['id']})")
        
        # Acceder al foro
        response = self.client.get(forum['url'])
        
        if response.status_code != 200:
            logger.error(f"Error accediendo al foro {forum['id']}: {response.status_code}")
            return
        
        # Extraer discusiones del foro
        soup = BeautifulSoup(response.text, 'html.parser')
        discussion_links = soup.select('.topic a')
        
        discussions = []
        for link in discussion_links:
            href = link.get('href')
            if href and 'discuss.php' in href:
                discussion_id_match = re.search(r'd=(\d+)', href)
                if discussion_id_match:
                    discussion_id = discussion_id_match.group(1)
                    discussion_name = link.text.strip()
                    
                    discussions.append({
                        'id': discussion_id,
                        'name': discussion_name,
                        'url': href
                    })
        
        # Si hay discusiones, acceder a una aleatoria
        if discussions:
            discussion = random.choice(discussions)
            logger.info(f"Accediendo a la discusión {discussion['name']} (ID: {discussion['id']})")
            
            self.client.get(discussion['url'])
    
    @tag('activity', 'assignment')
    @task(2)
    def access_assignment(self):
        """
        Accede a una tarea aleatoria
        """
        if not self.logged_in or not self.courses:
            return
        
        # Buscar tareas en los cursos
        assignments = []
        for course in self.courses:
            if 'activities' in course:
                assignments.extend([a for a in course['activities'] if a['type'] == 'assignment'])
        
        if not assignments:
            return
        
        # Seleccionar una tarea aleatoria
        assignment = random.choice(assignments)
        
        logger.info(f"Accediendo a la tarea {assignment['name']} (ID: {assignment['id']})")
        
        # Acceder a la tarea
        self.client.get(assignment['url'])
    
    @tag('calendar')
    @task(1)
    def access_calendar(self):
        """
        Accede al calendario de Moodle
        """
        if not self.logged_in:
            return
        
        logger.info("Accediendo al calendario")
        
        self.client.get("/calendar/view.php")
    
    @tag('profile')
    @task(1)
    def access_profile(self):
        """
        Accede al perfil del usuario
        """
        if not self.logged_in:
            return
        
        logger.info("Accediendo al perfil")
        
        self.client.get("/user/profile.php")
    
    @tag('category')
    @task(1)
    def browse_course_categories(self):
        """
        Navega por las categorías de cursos
        """
        if not self.logged_in:
            return
        
        logger.info("Navegando por categorías de cursos")
        
        # Acceder a la página de categorías
        response = self.client.get("/course/index.php")
        
        if response.status_code != 200:
            logger.error(f"Error accediendo a las categorías: {response.status_code}")
            return
        
        # Extraer categorías
        soup = BeautifulSoup(response.text, 'html.parser')
        category_links = soup.select('.category a')
        
        categories = []
        for link in category_links:
            href = link.get('href')
            if href and 'category.php' in href:
                category_id_match = re.search(r'id=(\d+)', href)
                if category_id_match:
                    category_id = category_id_match.group(1)
                    category_name = link.text.strip()
                    
                    categories.append({
                        'id': category_id,
                        'name': category_name,
                        'url': href
                    })
        
        # Si hay categorías, acceder a una aleatoria
        if categories:
            category = random.choice(categories)
            logger.info(f"Accediendo a la categoría {category['name']} (ID: {category['id']})")
            
            self.client.get(category['url'])
    
    @tag('search')
    @task(1)
    def search_courses(self):
        """
        Realiza una búsqueda de cursos
        """
        if not self.logged_in:
            return
        
        search_terms = ["programación", "matemáticas", "ciencia", "historia", "inglés", "física", "química"]
        search_term = random.choice(search_terms)
        
        logger.info(f"Buscando cursos con término '{search_term}'")
        
        response = self.client.get(f"/course/search.php?q={search_term}")
        
        if response.status_code != 200:
            logger.error(f"Error en la búsqueda: {response.status_code}")
    
    @tag('logout')
    @task(1)
    def logout(self):
        """
        Cierra sesión en Moodle
        """
        if not self.logged_in:
            return
        
        logger.info(f"Cerrando sesión para usuario {self.user_creds['username']}")
        
        if self.sesskey:
            logout_url = f"/login/logout.php?sesskey={self.sesskey}"
        else:
            logout_url = "/login/logout.php"
        
        response = self.client.get(logout_url)
        
        if response.status_code == 200:
            logger.info("Logout exitoso")
            self.logged_in = False
            self.sesskey = None
            self.courses = []
            
            # Iniciar sesión nuevamente para continuar con las pruebas
            time.sleep(1)
            self.login()
            if self.logged_in:
                self.get_available_courses()
