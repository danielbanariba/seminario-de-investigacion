import http from 'k6/http';
import { check } from 'k6';
import { Trend } from 'k6/metrics';

// Definir métricas personalizadas
let responseTimeTrendUsers = new Trend('response_time_users');
let responseTimeTrendCourses = new Trend('response_time_courses');
let responseTimeTrendAssignments = new Trend('response_time_assignments');
let responseTimeTrendUpcomingAssignments = new Trend('response_time_upcoming_assignments');
let responseTimeTrendRoles = new Trend('response_time_roles');
let responseTimeTrendSections = new Trend('response_time_sections');
let responseTimeTrendCombined = new Trend('response_time_combined');

// Definir opciones de carga
export let options = {
  vus: 20,
  duration: '30s',
};

// Token de autenticación de Moodle (usando tu token real)
const token = '466a8b3c540b5d736b2d8b626d73db92';
// Usar la IP directa del contenedor
const moodleUrl = 'http://localhost:8081/webservice/rest/server.php';

export default function () {
  // Parámetros comunes para todas las solicitudes
  const baseParams = {
    wstoken: token,
    moodlewsrestformat: 'json'
  };

  // Opciones para seguir redirecciones automáticamente
  const requestOptions = {
    redirects: 5,  // Seguir hasta 5 redirecciones
  };

  // Función auxiliar para construir URL con parámetros
  function buildUrl(baseUrl, params) {
    let url = baseUrl + '?';
    for (const key in params) {
      if (url.slice(-1) !== '?') {
        url += '&';
      }
      url += `${key}=${encodeURIComponent(params[key])}`;
    }
    return url;
  }

  let loginUrl = 'http://localhost:8081/login/token.php';

  // Obtener token de autenticación (opcional, si no se proporciona en el script)
  let res = http.post(loginUrl, {
    username: 'admin',
    password: 'password',
    service: 'moodle_mobile_app'
  });

  // Hacer solicitudes GET a los endpoints de Moodle con seguimiento de redirecciones
  let users = http.get(buildUrl(moodleUrl, {
    ...baseParams,
    wsfunction: 'core_user_get_users'
  }), requestOptions);
  
  let courses = http.get(buildUrl(moodleUrl, {
    ...baseParams,
    wsfunction: 'core_course_get_courses'
  }), requestOptions);
  
  let assignments = http.get(buildUrl(moodleUrl, {
    ...baseParams,
    wsfunction: 'mod_assign_get_assignments',
    courseids: '1'
  }), requestOptions);
  
  let upcomingAssignments = http.get(buildUrl(moodleUrl, {
    ...baseParams,
    wsfunction: 'core_calendar_get_upcoming_view'
  }), requestOptions);
  
  let roles = http.get(buildUrl(moodleUrl, {
    ...baseParams,
    wsfunction: 'core_role_get_roles'
  }), requestOptions);
  
  let sections = http.get(buildUrl(moodleUrl, {
    ...baseParams,
    wsfunction: 'core_course_get_contents',
    courseid: '1'
  }), requestOptions);

  // Verificar respuestas y registrar si hay redirecciones
  check(users, {
    'users endpoint response check': (r) => r.status === 200 || r.status === 303,
    'users response not empty': (r) => r.body.length > 0,
  });

  check(courses, {
    'courses endpoint response check': (r) => r.status === 200 || r.status === 303,
    'courses response not empty': (r) => r.body.length > 0,
  });

  check(assignments, {
    'assignments endpoint response check': (r) => r.status === 200 || r.status === 303,
    'assignments response not empty': (r) => r.body.length > 0,
  });

  check(upcomingAssignments, {
    'upcoming assignments endpoint response check': (r) => r.status === 200 || r.status === 303,
    'upcoming assignments response not empty': (r) => r.body.length > 0,
  });

  check(roles, {
    'roles endpoint response check': (r) => r.status === 200 || r.status === 303,
    'roles response not empty': (r) => r.body.length > 0,
  });

  check(sections, {
    'sections endpoint response check': (r) => r.status === 200 || r.status === 303,
    'sections response not empty': (r) => r.body.length > 0,
  });

  // Registrar las métricas de tiempo de respuesta
  responseTimeTrendUsers.add(users.timings.duration);
  responseTimeTrendCourses.add(courses.timings.duration);
  responseTimeTrendAssignments.add(assignments.timings.duration);
  responseTimeTrendUpcomingAssignments.add(upcomingAssignments.timings.duration);
  responseTimeTrendRoles.add(roles.timings.duration);
  responseTimeTrendSections.add(sections.timings.duration);

  // Registrar la métrica combinada de tiempo de respuesta
  responseTimeTrendCombined.add(users.timings.duration);
  responseTimeTrendCombined.add(courses.timings.duration);
  responseTimeTrendCombined.add(assignments.timings.duration);
  responseTimeTrendCombined.add(upcomingAssignments.timings.duration);
  responseTimeTrendCombined.add(roles.timings.duration);
  responseTimeTrendCombined.add(sections.timings.duration);
}

// * Estos cambios son opcionales y solo para probar esa paja de manera correcta

// import http from 'k6/http';
// import { check } from 'k6';
// import { Trend } from 'k6/metrics';

// const moodleUrl = 'http://localhost:8081/webservice/rest/server.php';
// const loginUrl = 'http://localhost:8081/login/token.php';

// // Credenciales de administrador
// const moodleAdminUser = 'admin';
// const moodleAdminPass = 'password';

// // Obtener token de autenticación
// function getAuthToken() {
//   let res = http.post(loginUrl, {
//     username: moodleAdminUser,
//     password: moodleAdminPass,
//     service: 'moodle_mobile_app'
//   });

//   check(res, {
//     'login response is 200': (r) => r.status === 200,
//     'token is present': (r) => r.json().hasOwnProperty('token'),
//   });

//   return res.json().token;
// }

// // Obtener el token antes de ejecutar los tests
// const token = getAuthToken();

// // Definir métricas personalizadas
// let responseTimeTrendUsers = new Trend('response_time_users');
// let responseTimeTrendCourses = new Trend('response_time_courses');

// export let options = {
//   vus: 20,
//   duration: '30s',
// };

// // Parámetros comunes para todas las solicitudes
// const baseParams = {
//   wstoken: token,
//   moodlewsrestformat: 'json'
// };

// // Función para construir URLs con parámetros
// function buildUrl(baseUrl, params) {
//   let url = baseUrl + '?';
//   for (const key in params) {
//     if (url.slice(-1) !== '?') {
//       url += '&';
//     }
//     url += `${key}=${encodeURIComponent(params[key])}`;
//   }
//   return url;
// }

// export default function () {
//   let users = http.get(buildUrl(moodleUrl, {
//     ...baseParams,
//     wsfunction: 'core_user_get_users'
//   }));

//   let courses = http.get(buildUrl(moodleUrl, {
//     ...baseParams,
//     wsfunction: 'core_course_get_courses'
//   }));

//   check(users, {
//     'users endpoint response check': (r) => r.status === 200,
//     'users response not empty': (r) => r.body.length > 0,
//   });

//   check(courses, {
//     'courses endpoint response check': (r) => r.status === 200,
//     'courses response not empty': (r) => r.body.length > 0,
//   });

//   responseTimeTrendUsers.add(users.timings.duration);
//   responseTimeTrendCourses.add(courses.timings.duration);
// }
