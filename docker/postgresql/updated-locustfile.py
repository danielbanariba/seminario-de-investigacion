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
        self.token = '466a8b3c540b5d736b2d8b626d73db92'  # Reemplazar con tu token
        self.courses = []
        self.user_info = {}
        self.logged_in = True  # Con token, estamos siempre "logged in"
    
    def on_start(self):
        """
        Inicialización del usuario - Obtenemos información inicial
        """
        # Obtener información del sitio
        self.get_site_info()
        
        # Obtener cursos disponibles
        self.get_available_courses()
    
    def get_site_info(self):
        """
        Obtiene información del sitio mediante la API
        """
        logger.info("Obteniendo información del sitio")
        
        params = {
            'wstoken': self.token,
            'wsfunction': 'core_webservice_get_site_info',
            'moodlewsrestformat': 'json'
        }
        
        with self.client.get(
            "/webservice/rest/server.php",
            params=params,
            name="/webservice/rest/server.php?core_webservice_get_site_info",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                try:
                    self.user_info = response.json()
                    logger.info(f"Información del sitio obtenida para usuario: {self.user_info.get('username', 'unknown')}")
                except Exception as e:
                    logger.error(f"Error procesando respuesta JSON: {str(e)}")
            else:
                logger.error(f"Error obteniendo información del sitio: {response.status_code}")
    
    def get_available_courses(self):
        """
        Obtiene la lista de cursos disponibles para el usuario mediante la API
        """
        logger.info("Obteniendo lista de cursos disponibles")
        
        params = {
            'wstoken': self.token,
            'wsfunction': 'core_course_get_courses',
            'moodlewsrestformat': 'json'
        }
        
        with self.client.get(
            "/webservice/rest/server.php",
            params=params,
            name="/webservice/rest/server.php?core_course_get_courses",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                try:
                    courses_data = response.json()
                    self.courses = []
                    
                    for course in courses_data:
                        if course.get('id') != 1:  # Excluir el curso sitio
                            self.courses.append({
                                'id': course.get('id'),
                                'name': course.get('fullname')
                            })
                    
                    logger.info(f"Encontrados {len(self.courses)} cursos para el usuario")
                    
                    # Obtener actividades de los cursos
                    for course in self.courses:
                        self.get_course_contents(course)
                except Exception as e:
                    logger.error(f"Error procesando respuesta JSON de cursos: {str(e)}")
            else:
                logger.error(f"Error obteniendo cursos: {response.status_code}")
    
    def get_course_contents(self, course):
        """
        Obtiene el contenido de un curso específico mediante la API
        """
        course_id = course['id']
        logger.info(f"Obteniendo contenido del curso {course['name']} (ID: {course_id})")
        
        params = {
            'wstoken': self.token,
            'wsfunction': 'core_course_get_contents',
            'courseid': course_id,
            'moodlewsrestformat': 'json'
        }
        
        with self.client.get(
            "/webservice/rest/server.php",
            params=params,
            name="/webservice/rest/server.php?core_course_get_contents",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                try:
                    course_contents = response.json()
                    activities = []
                    
                    for section in course_contents:
                        for module in section.get('modules', []):
                            module_type = self._determine_activity_type(module.get('modname', ''))
                            if module_type != 'unknown':
                                activities.append({
                                    'id': module.get('id'),
                                    'name': module.get('name'),
                                    'type': module_type,
                                    'url': module.get('url', '')
                                })
                    
                    course['activities'] = activities
                    logger.info(f"Encontradas {len(activities)} actividades en el curso {course_id}")
                except Exception as e:
                    logger.error(f"Error procesando contenido del curso {course_id}: {str(e)}")
            else:
                logger.error(f"Error obteniendo contenido del curso {course_id}: {response.status_code}")
    
    def _determine_activity_type(self, modname):
        """
        Determina el tipo de actividad a partir del nombre del módulo
        """
        if modname == 'forum':
            return 'forum'
        elif modname == 'assign':
            return 'assignment'
        elif modname == 'quiz':
            return 'quiz'
        elif modname == 'resource':
            return 'resource'
        elif modname == 'page':
            return 'page'
        elif modname == 'book':
            return 'book'
        else:
            return 'unknown'
    
    @tag('home')
    @task(3)
    def access_home(self):
        """
        Simula acceso a la página principal de Moodle obteniendo información del sitio
        """
        if not self.logged_in:
            return
        
        params = {
            'wstoken': self.token,
            'wsfunction': 'core_webservice_get_site_info',
            'moodlewsrestformat': 'json'
        }
        
        self.client.get(
            "/webservice/rest/server.php",
            params=params,
            name="/webservice/rest/server.php?core_webservice_get_site_info"
        )
    
    @tag('courses')
    @task(5)
    def access_course(self):
        """
        Accede a un curso aleatorio de la lista de cursos disponibles usando la API
        """
        if not self.logged_in or not self.courses:
            return
        
        # Seleccionar un curso aleatorio
        course = random.choice(self.courses)
        course_id = course['id']
        
        logger.info(f"Accediendo al curso {course['name']} (ID: {course_id})")
        
        # Obtener el contenido del curso usando la API
        params = {
            'wstoken': self.token,
            'wsfunction': 'core_course_get_contents',
            'courseid': course_id,
            'moodlewsrestformat': 'json'
        }
        
        self.client.get(
            "/webservice/rest/server.php",
            params=params,
            name="/webservice/rest/server.php?core_course_get_contents"
        )
    
    @tag('activity', 'forum')
    @task(2)
    def access_forum(self):
        """
        Accede a un foro aleatorio usando la API
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
        
        # Obtener las discusiones del foro usando la API
        params = {
            'wstoken': self.token,
            'wsfunction': 'mod_forum_get_forum_discussions_paginated',
            'forumid': forum['id'],
            'page': 0,
            'perpage': 10,
            'moodlewsrestformat': 'json'
        }
        
        with self.client.get(
            "/webservice/rest/server.php",
            params=params,
            name="/webservice/rest/server.php?mod_forum_get_forum_discussions_paginated",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    discussions = data.get('discussions', [])
                    
                    if discussions:
                        # Acceder a una discusión aleatoria
                        discussion = random.choice(discussions)
                        discussion_id = discussion.get('id')
                        
                        # Obtener mensajes de la discusión
                        params = {
                            'wstoken': self.token,
                            'wsfunction': 'mod_forum_get_forum_discussion_posts',
                            'discussionid': discussion_id,
                            'moodlewsrestformat': 'json'
                        }
                        
                        self.client.get(
                            "/webservice/rest/server.php",
                            params=params,
                            name="/webservice/rest/server.php?mod_forum_get_forum_discussion_posts"
                        )
                except Exception as e:
                    logger.error(f"Error procesando discusiones del foro {forum['id']}: {str(e)}")
    
    @tag('activity', 'assignment')
    @task(2)
    def access_assignment(self):
        """
        Accede a una tarea aleatoria usando la API
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
        
        # Obtener información de la tarea
        params = {
            'wstoken': self.token,
            'wsfunction': 'mod_assign_get_assignments',
            'courseids[0]': assignment['id'],
            'moodlewsrestformat': 'json'
        }
        
        self.client.get(
            "/webservice/rest/server.php",
            params=params,
            name="/webservice/rest/server.php?mod_assign_get_assignments"
        )
    
    @tag('calendar')
    @task(1)
    def access_calendar(self):
        """
        Accede al calendario usando la API
        """
        if not self.logged_in:
            return
        
        logger.info("Accediendo al calendario")
        
        # Obtener eventos del calendario
        current_time = int(time.time())
        params = {
            'wstoken': self.token,
            'wsfunction': 'core_calendar_get_calendar_upcoming_view',
            'moodlewsrestformat': 'json'
        }
        
        self.client.get(
            "/webservice/rest/server.php",
            params=params,
            name="/webservice/rest/server.php?core_calendar_get_calendar_upcoming_view"
        )
    
    @tag('profile')
    @task(1)
    def access_profile(self):
        """
        Accede al perfil del usuario usando la API
        """
        if not self.logged_in or not self.user_info:
            return
        
        logger.info("Accediendo al perfil")
        
        user_id = self.user_info.get('userid')
        if not user_id:
            return
        
        # Obtener información del perfil
        params = {
            'wstoken': self.token,
            'wsfunction': 'core_user_get_users_by_id',
            'userids[0]': user_id,
            'moodlewsrestformat': 'json'
        }
        
        self.client.get(
            "/webservice/rest/server.php",
            params=params,
            name="/webservice/rest/server.php?core_user_get_users_by_id"
        )
    
    @tag('category')
    @task(1)
    def browse_course_categories(self):
        """
        Navega por las categorías de cursos usando la API
        """
        if not self.logged_in:
            return
        
        logger.info("Navegando por categorías de cursos")
        
        # Obtener todas las categorías
        params = {
            'wstoken': self.token,
            'wsfunction': 'core_course_get_categories',
            'moodlewsrestformat': 'json'
        }
        
        with self.client.get(
            "/webservice/rest/server.php",
            params=params,
            name="/webservice/rest/server.php?core_course_get_categories",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                try:
                    categories = response.json()
                    
                    if categories:
                        # Seleccionar una categoría aleatoria
                        category = random.choice(categories)
                        category_id = category.get('id')
                        
                        # Obtener cursos en esta categoría
                        params = {
                            'wstoken': self.token,
                            'wsfunction': 'core_course_get_courses_by_field',
                            'field': 'category',
                            'value': category_id,
                            'moodlewsrestformat': 'json'
                        }
                        
                        self.client.get(
                            "/webservice/rest/server.php",
                            params=params,
                            name="/webservice/rest/server.php?core_course_get_courses_by_field"
                        )
                except Exception as e:
                    logger.error(f"Error procesando categorías: {str(e)}")
    
    @tag('search')
    @task(1)
    def search_courses(self):
        """
        Realiza una búsqueda de cursos usando la API
        """
        if not self.logged_in:
            return
        
        search_terms = ["programación", "matemáticas", "ciencia", "historia", "inglés", "física", "química"]
        search_term = random.choice(search_terms)
        
        logger.info(f"Buscando cursos con término '{search_term}'")
        
        # Buscar cursos
        params = {
            'wstoken': self.token,
            'wsfunction': 'core_course_search_courses',
            'criterianame': 'search',
            'criteriavalue': search_term,
            'moodlewsrestformat': 'json'
        }
        
        self.client.get(
            "/webservice/rest/server.php",
            params=params,
            name="/webservice/rest/server.php?core_course_search_courses"
        )
