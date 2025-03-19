#!/usr/bin/env python3
"""
Script para crear usuarios de prueba en Moodle utilizando la línea de comandos.
Este script debe ejecutarse en el contenedor de Moodle.

Uso:
    docker exec -it <container_id_moodle> python /path/to/create_test_users.py
"""

import os
import sys
import subprocess
import random
import string

# Configuración
NUM_STUDENTS = 20  # Número de estudiantes a crear
NUM_TEACHERS = 5   # Número de profesores a crear
PASSWORD = "password"  # Contraseña común para todos los usuarios

# Datos ficticios para generar usuarios más realistas
FIRST_NAMES = [
    "Juan", "María", "Carlos", "Ana", "Pedro", "Lucía", "Miguel", "Laura",
    "José", "Elena", "Antonio", "Sofía", "David", "Carmen", "Javier", "Isabel",
    "Francisco", "Paula", "Manuel", "Marta", "Alejandro", "Cristina", "Daniel",
    "Natalia", "Fernando", "Andrea", "Pablo", "Beatriz", "Sergio", "Raquel"
]

LAST_NAMES = [
    "García", "Rodríguez", "Martínez", "López", "González", "Pérez", "Fernández",
    "Sánchez", "Ramírez", "Torres", "Flores", "Rivera", "Gómez", "Díaz", "Reyes",
    "Morales", "Ortiz", "Cruz", "Castillo", "Romero", "Moreno", "Jiménez", "Vega",
    "Herrera", "Medina", "Castro", "Vargas", "Gutiérrez", "Álvarez", "Mendoza"
]

def generate_username(first_name, last_name):
    """Genera un nombre de usuario a partir del nombre y apellido"""
    return f"{first_name.lower()}.{last_name.lower()}"

def generate_email(username):
    """Genera un email ficticio a partir del nombre de usuario"""
    return f"{username}@example.com"

def create_user(username, password, firstname, lastname, email, role="student"):
    """Crea un usuario en Moodle utilizando el comando CLI"""
    print(f"Creando usuario {username} ({firstname} {lastname}) como {role}...")
    
    # Comando para crear usuario
    cmd = [
        "php", "admin/cli/create_user.php",
        "--username", username,
        "--password", password,
        "--firstname", firstname,
        "--lastname", lastname,
        "--email", email
    ]
    
    try:
        # Ejecutar el comando
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            print(f"Error al crear usuario {username}: {stderr.decode('utf-8')}")
            return False
        
        print(f"Usuario {username} creado correctamente")
        return True
    except Exception as e:
        print(f"Excepción al crear usuario {username}: {str(e)}")
        return False

def assign_role(username, role_id, context_id=1):
    """Asigna un rol a un usuario en Moodle"""
    print(f"Asignando rol {role_id} al usuario {username}...")
    
    # Comando para asignar rol
    cmd = [
        "php", "admin/cli/assign_role.php",
        "--role", str(role_id),
        "--user", username,
        "--contextid", str(context_id)
    ]
    
    try:
        # Ejecutar el comando
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            print(f"Error al asignar rol {role_id} a {username}: {stderr.decode('utf-8')}")
            return False
        
        print(f"Rol {role_id} asignado correctamente a {username}")
        return True
    except Exception as e:
        print(f"Excepción al asignar rol a {username}: {str(e)}")
        return False

def create_test_course(shortname, fullname, category=1):
    """Crea un curso de prueba en Moodle"""
    print(f"Creando curso {shortname} ({fullname})...")
    
    # Comando para crear curso
    cmd = [
        "php", "admin/cli/create_course.php",
        "--shortname", shortname,
        "--fullname", fullname,
        "--category", str(category)
    ]
    
    try:
        # Ejecutar el comando
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            print(f"Error al crear curso {shortname}: {stderr.decode('utf-8')}")
            return None
        
        # Extraer el ID del curso creado
        output = stdout.decode('utf-8')
        course_id = None
        for line in output.split('\n'):
            if "id:" in line:
                course_id = int(line.split("id:")[1].strip())
        
        print(f"Curso {shortname} creado correctamente con ID {course_id}")
        return course_id
    except Exception as e:
        print(f"Excepción al crear curso {shortname}: {str(e)}")
        return None

def enrol_user_in_course(username, course_id, role_id):
    """Inscribe a un usuario en un curso con un rol específico"""
    print(f"Inscribiendo a {username} en curso {course_id} con rol {role_id}...")
    
    # Comando para inscribir usuario
    cmd = [
        "php", "admin/cli/enrol_user.php",
        "--user", username,
        "--course", str(course_id),
        "--role", str(role_id)
    ]
    
    try:
        # Ejecutar el comando
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            print(f"Error al inscribir a {username} en curso {course_id}: {stderr.decode('utf-8')}")
            return False
        
        print(f"Usuario {username} inscrito correctamente en curso {course_id}")
        return True
    except Exception as e:
        print(f"Excepción al inscribir a {username} en curso {course_id}: {str(e)}")
        return False

def main():
    """Función principal"""
    # Verificar que estamos en el directorio correcto
    if not os.path.exists('config.php'):
        print("Error: Este script debe ejecutarse desde el directorio raíz de Moodle")
        sys.exit(1)
    
    # Crear cursos de prueba
    courses = [
        create_test_course("PROG101", "Introducción a la Programación"),
        create_test_course("MATH201", "Matemáticas Avanzadas"),
        create_test_course("PHYS101", "Física Básica"),
        create_test_course("HIST301", "Historia Contemporánea"),
        create_test_course("ENG202", "Inglés Intermedio")
    ]
    
    # Filtrar cursos que no se pudieron crear
    courses = [c for c in courses if c is not None]
    
    if not courses:
        print("Error: No se pudo crear ningún curso")
        sys.exit(1)
    
    # Crear profesores
    teachers = []
    for i in range(NUM_TEACHERS):
        firstname = random.choice(FIRST_NAMES)
        lastname = random.choice(LAST_NAMES)
        username = f"teacher{i+1}"  # Asegurar nombres únicos
        email = generate_email(username)
        
        if create_user(username, PASSWORD, firstname, lastname, email, role="teacher"):
            teachers.append(username)
            assign_role(username, 3)  # 3 es el ID típico para el rol de profesor
    
    # Crear estudiantes
    students = []
    for i in range(NUM_STUDENTS):
        firstname = random.choice(FIRST_NAMES)
        lastname = random.choice(LAST_NAMES)
        username = f"student{i+1}"  # Asegurar nombres únicos
        email = generate_email(username)
        
        if create_user(username, PASSWORD, firstname, lastname, email):
            students.append(username)
            assign_role(username, 5)  # 5 es el ID típico para el rol de estudiante
    
    # Inscribir usuarios en cursos
    for course_id in courses:
        # Asignar algunos profesores a cada curso
        for teacher in random.sample(teachers, min(2, len(teachers))):
            enrol_user_in_course(teacher, course_id, 3)  # 3 = profesor
        
        # Asignar varios estudiantes a cada curso
        for student in random.sample(students, min(10, len(students))):
            enrol_user_in_course(student, course_id, 5)  # 5 = estudiante
    
    print("\nResumen:")
    print(f"- {len(courses)} cursos creados")
    print(f"- {len(teachers)} profesores creados")
    print(f"- {len(students)} estudiantes creados")
    print("\nUsuarios de prueba listos para ser utilizados con Locust!")

if __name__ == "__main__":
    main()
