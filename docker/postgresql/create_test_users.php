<?php
/**
 * Script para crear usuarios y cursos de prueba para Locust
 * 
 * Este script crea usuarios de estudiantes y profesores, crea cursos de prueba
 * y asigna usuarios a los cursos para que puedan ser usados en pruebas de carga
 * con Locust.
 * 
 * Uso: php create_test_users.php
 */

define('CLI_SCRIPT', true);
require(__DIR__ . '/config.php');
require_once($CFG->libdir.'/adminlib.php');
require_once($CFG->dirroot.'/user/lib.php');
require_once($CFG->dirroot.'/course/lib.php');
require_once($CFG->dirroot.'/group/lib.php');

// Configuración
$NUM_STUDENTS = 20;
$NUM_TEACHERS = 5;
$PASSWORD = 'password';

// Datos para generar usuarios más realistas
$FIRST_NAMES = array(
    "Juan", "María", "Carlos", "Ana", "Pedro", "Lucía", "Miguel", "Laura",
    "José", "Elena", "Antonio", "Sofía", "David", "Carmen", "Javier", "Isabel",
    "Francisco", "Paula", "Manuel", "Marta", "Alejandro", "Cristina", "Daniel",
    "Natalia", "Fernando", "Andrea", "Pablo", "Beatriz", "Sergio", "Raquel"
);

$LAST_NAMES = array(
    "García", "Rodríguez", "Martínez", "López", "González", "Pérez", "Fernández",
    "Sánchez", "Ramírez", "Torres", "Flores", "Rivera", "Gómez", "Díaz", "Reyes",
    "Morales", "Ortiz", "Cruz", "Castillo", "Romero", "Moreno", "Jiménez", "Vega",
    "Herrera", "Medina", "Castro", "Vargas", "Gutiérrez", "Álvarez", "Mendoza"
);

// Roles estándar en Moodle
$ROLE_STUDENT = 5;  // ID estándar del rol de estudiante
$ROLE_TEACHER = 3;  // ID estándar del rol de profesor

// Función para crear un usuario
function create_test_user($username, $password, $firstname, $lastname, $email, $role = 'student') {
    global $DB, $CFG;
    
    echo "Creando usuario $username ($firstname $lastname) como $role...\n";
    
    $user = new stdClass();
    $user->auth = 'manual';
    $user->confirmed = 1;
    $user->mnethostid = $CFG->mnet_localhost_id;
    $user->username = $username;
    $user->password = $password;
    $user->firstname = $firstname;
    $user->lastname = $lastname;
    $user->email = $email;
    $user->deleted = 0;

    try {
        // Verificar si el usuario ya existe
        $existing_user = $DB->get_record('user', array('username' => $username), '*', IGNORE_MISSING);
        if ($existing_user) {
            echo "El usuario $username ya existe con ID {$existing_user->id}\n";
            return $existing_user->id;
        }
        
        // Crear el usuario
        $user_id = user_create_user($user, true, false);
        echo "Usuario $username creado con ID $user_id\n";
        return $user_id;
    } catch (Exception $e) {
        echo "Error al crear el usuario $username: " . $e->getMessage() . "\n";
        return false;
    }
}

// Función para crear un curso
function create_test_course($shortname, $fullname, $category = 1) {
    global $DB;
    
    echo "Creando curso $shortname ($fullname)...\n";
    
    try {
        // Verificar si el curso ya existe
        $existing_course = $DB->get_record('course', array('shortname' => $shortname), '*', IGNORE_MISSING);
        if ($existing_course) {
            echo "El curso $shortname ya existe con ID {$existing_course->id}\n";
            return $existing_course->id;
        }
        
        // Crear el curso
        $course = new stdClass();
        $course->category = $category;
        $course->shortname = $shortname;
        $course->fullname = $fullname;
        $course->summaryformat = FORMAT_HTML;
        $course->format = 'topics';
        $course->visible = 1;
        $course->newsitems = 5;
        
        $course_id = create_course($course)->id;
        echo "Curso $shortname creado con ID $course_id\n";
        return $course_id;
    } catch (Exception $e) {
        echo "Error al crear el curso $shortname: " . $e->getMessage() . "\n";
        return false;
    }
}

// Función para matricular un usuario en un curso
function enrol_test_user_in_course($user_id, $course_id, $role_id) {
    global $DB;
    
    echo "Matriculando usuario $user_id en curso $course_id con rol $role_id...\n";
    
    try {
        // Obtener el contexto del curso
        $context = context_course::instance($course_id);
        
        // Verificar si el usuario ya está matriculado
        $role_assignments = $DB->get_records('role_assignments', 
            array('contextid' => $context->id, 'userid' => $user_id, 'roleid' => $role_id));
        
        if (count($role_assignments) > 0) {
            echo "El usuario $user_id ya está matriculado en el curso $course_id con rol $role_id\n";
            return true;
        }
        
        // Obtener la instancia de inscripción manual
        $enrol = $DB->get_record('enrol', array('courseid' => $course_id, 'enrol' => 'manual'), '*', MUST_EXIST);
        
        // Matricular el usuario
        $manual_enrol = enrol_get_plugin('manual');
        $manual_enrol->enrol_user($enrol, $user_id, $role_id);
        
        echo "Usuario $user_id matriculado en curso $course_id con rol $role_id\n";
        return true;
    } catch (Exception $e) {
        echo "Error al matricular usuario $user_id en curso $course_id: " . $e->getMessage() . "\n";
        return false;
    }
}

// Función para crear un foro en un curso
function create_test_forum($course_id, $name, $intro) {
    global $DB;
    
    echo "Creando foro $name en curso $course_id...\n";
    
    try {
        // Verificar si el módulo foro está disponible
        $module = $DB->get_record('modules', array('name' => 'forum'), '*', MUST_EXIST);
        
        // Verificar si el foro ya existe
        $existing_forums = $DB->get_records('forum', array('course' => $course_id, 'name' => $name));
        
        if (count($existing_forums) > 0) {
            $forum_id = reset($existing_forums)->id;
            echo "El foro $name ya existe en el curso $course_id con ID $forum_id\n";
            return $forum_id;
        }
        
        // Crear el foro
        $forum = new stdClass();
        $forum->course = $course_id;
        $forum->name = $name;
        $forum->intro = $intro;
        $forum->introformat = FORMAT_HTML;
        $forum->type = 'general';
        $forum->assessed = 0;
        $forum->scale = 0;
        $forum->timemodified = time();
        
        $forum_id = $DB->insert_record('forum', $forum);
        
        // Agregar el módulo al curso
        $section_id = $DB->get_field('course_sections', 'id', array('course' => $course_id, 'section' => 0));
        
        $coursemodule = new stdClass();
        $coursemodule->course = $course_id;
        $coursemodule->module = $module->id;
        $coursemodule->instance = $forum_id;
        $coursemodule->section = $section_id;
        $coursemodule->visible = 1;
        $coursemodule->visibleold = 1;
        $coursemodule->added = time();
        
        $cmid = add_course_module($coursemodule);
        
        echo "Foro $name creado en curso $course_id con ID $forum_id\n";
        return $forum_id;
    } catch (Exception $e) {
        echo "Error al crear foro $name en curso $course_id: " . $e->getMessage() . "\n";
        return false;
    }
}

// Función para crear una tarea en un curso
function create_test_assignment($course_id, $name, $intro, $duedate = null) {
    global $DB;
    
    echo "Creando tarea $name en curso $course_id...\n";
    
    try {
        // Verificar si el módulo assign está disponible
        $module = $DB->get_record('modules', array('name' => 'assign'), '*', MUST_EXIST);
        
        // Verificar si la tarea ya existe
        $existing_assigns = $DB->get_records('assign', array('course' => $course_id, 'name' => $name));
        
        if (count($existing_assigns) > 0) {
            $assign_id = reset($existing_assigns)->id;
            echo "La tarea $name ya existe en el curso $course_id con ID $assign_id\n";
            return $assign_id;
        }
        
        // Crear la tarea
        $assign = new stdClass();
        $assign->course = $course_id;
        $assign->name = $name;
        $assign->intro = $intro;
        $assign->introformat = FORMAT_HTML;
        $assign->timemodified = time();
        
        if ($duedate) {
            $assign->duedate = $duedate;
        }
        
        $assign_id = $DB->insert_record('assign', $assign);
        
        // Agregar el módulo al curso
        $section_id = $DB->get_field('course_sections', 'id', array('course' => $course_id, 'section' => 0));
        
        $coursemodule = new stdClass();
        $coursemodule->course = $course_id;
        $coursemodule->module = $module->id;
        $coursemodule->instance = $assign_id;
        $coursemodule->section = $section_id;
        $coursemodule->visible = 1;
        $coursemodule->visibleold = 1;
        $coursemodule->added = time();
        
        $cmid = add_course_module($coursemodule);
        
        echo "Tarea $name creada en curso $course_id con ID $assign_id\n";
        return $assign_id;
    } catch (Exception $e) {
        echo "Error al crear tarea $name en curso $course_id: " . $e->getMessage() . "\n";
        return false;
    }
}

// Crear cursos de prueba
$courses = array(
    create_test_course("PROG101", "Introducción a la Programación"),
    create_test_course("MATH201", "Matemáticas Avanzadas"),
    create_test_course("PHYS101", "Física Básica"),
    create_test_course("HIST301", "Historia Contemporánea"),
    create_test_course("ENG202", "Inglés Intermedio")
);

// Filtrar cursos que no se pudieron crear
$courses = array_filter($courses);

if (empty($courses)) {
    die("Error: No se pudo crear ningún curso\n");
}

// Crear profesores
$teachers = array();
for ($i = 0; $i < $NUM_TEACHERS; $i++) {
    $firstname = $FIRST_NAMES[array_rand($FIRST_NAMES)];
    $lastname = $LAST_NAMES[array_rand($LAST_NAMES)];
    $username = "teacher" . ($i + 1);
    $email = $username . "@example.com";
    
    $teacher_id = create_test_user($username, $PASSWORD, $firstname, $lastname, $email, 'teacher');
    if ($teacher_id) {
        $teachers[] = $teacher_id;
    }
}

// Crear estudiantes
$students = array();
for ($i = 0; $i < $NUM_STUDENTS; $i++) {
    $firstname = $FIRST_NAMES[array_rand($FIRST_NAMES)];
    $lastname = $LAST_NAMES[array_rand($LAST_NAMES)];
    $username = "student" . ($i + 1);
    $email = $username . "@example.com";
    
    $student_id = create_test_user($username, $PASSWORD, $firstname, $lastname, $email, 'student');
    if ($student_id) {
        $students[] = $student_id;
    }
}

// Añadir algo de contenido a los cursos
foreach ($courses as $course_id) {
    // Añadir un foro de discusión
    create_test_forum(
        $course_id, 
        "Foro General", 
        "Este es el foro general para discusiones del curso."
    );
    
    // Añadir algunas tareas
    create_test_assignment(
        $course_id,
        "Tarea 1",
        "Esta es la primera tarea del curso.",
        time() + (7 * 24 * 60 * 60) // Una semana en el futuro
    );
    
    create_test_assignment(
        $course_id,
        "Tarea 2",
        "Esta es la segunda tarea del curso.",
        time() + (14 * 24 * 60 * 60) // Dos semanas en el futuro
    );
}

// Inscribir usuarios en cursos
foreach ($courses as $course_id) {
    // Asignar algunos profesores a cada curso
    $course_teachers = array_slice($teachers, 0, min(2, count($teachers)));
    foreach ($course_teachers as $teacher_id) {
        enrol_test_user_in_course($teacher_id, $course_id, $ROLE_TEACHER);
    }
    
    // Asignar varios estudiantes a cada curso
    $course_students = array_slice($students, 0, min(10, count($students)));
    foreach ($course_students as $student_id) {
        enrol_test_user_in_course($student_id, $course_id, $ROLE_STUDENT);
    }
}

echo "\nResumen:\n";
echo "- " . count($courses) . " cursos creados\n";
echo "- " . count($teachers) . " profesores creados\n";
echo "- " . count($students) . " estudiantes creados\n";
echo "\nUsuarios de prueba listos para ser utilizados con Locust!\n";
