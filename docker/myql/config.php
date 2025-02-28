<?php
///////////////////////////////////////////////////////////////////////////
//                                                                       //
// Moodle configuration file                                             //
//                                                                       //
// This file should be renamed "config.php" in the top-level directory   //
//                                                                       //
///////////////////////////////////////////////////////////////////////////
//                                                                       //
// NOTICE OF COPYRIGHT                                                   //
//                                                                       //
// Moodle - Modular Object-Oriented Dynamic Learning Environment         //
//          http://moodle.org                                            //
//                                                                       //
// Copyright (C) 1999 onwards  Martin Dougiamas  http://moodle.com       //
//                                                                       //
// This program is free software; you can redistribute it and/or modify  //
// it under the terms of the GNU General Public License as published by  //
// the Free Software Foundation; either version 3 of the License, or     //
// (at your option) any later version.                                   //
//                                                                       //
// This program is distributed in the hope that it will be useful,       //
// but WITHOUT ANY WARRANTY; without even the implied warranty of        //
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         //
// GNU General Public License for more details:                          //
//                                                                       //
//          http://www.gnu.org/copyleft/gpl.html                         //
//                                                                       //
///////////////////////////////////////////////////////////////////////////
unset($CFG);  // Ignore this line
global $CFG;  // This is necessary here for PHPUnit execution
$CFG = new stdClass();

//=========================================================================
// 1. DATABASE SETUP
//=========================================================================
// First, you need to configure the database where all Moodle data       //
// will be stored.  This database must already have been created         //
// and a username/password created to access it.                         //

function loadenv($envName, $default = "") {
    return getenv($envName) ? getenv($envName) : $default;
}

$CFG->dbtype    = 'mysqli';      // DEBE SER mysqli para MySQL
$CFG->dblibrary = 'native';     // 'native' only at the moment
$CFG->dbhost    = loadenv('MOODLE_DB_HOST', 'db');  // Cambiado a 'db' como valor predeterminado para Docker
$CFG->dbname    = loadenv('MOODLE_DB_NAME', 'moodle');
$CFG->dbuser    = loadenv('MOODLE_DB_USER', 'moodle');   // Cambiado a 'moodle' como valor predeterminado
$CFG->dbpass    = loadenv('MOODLE_DB_PASSWORD', 'password');   // Cambiado a 'password' como valor predeterminado
$CFG->prefix    = loadenv('MOODLE_DB_PREFIX', 'mdl_');
$CFG->dboptions = array(
    'dbpersist' => false,
    'dbsocket'  => false,
    'dbport'    => loadenv('MOODLE_DB_PORT', '3306'),  // Puerto por defecto para MySQL es 3306
    'dbhandlesoptions' => false,
    'dbcollation' => 'utf8mb4_unicode_ci',  // Colación para MySQL
);


//=========================================================================
// 2. WEB SITE LOCATION
//=========================================================================
// Now you need to tell Moodle where it is located. Specify the full
// web address to where moodle has been installed.

$CFG->wwwroot   = loadenv('MOODLE_URL', 'http://localhost:8080');  // Cambiado al puerto 8080 para evitar conflictos


//=========================================================================
// 3. DATA FILES LOCATION
//=========================================================================

$CFG->dataroot  = '/moodledata';


//=========================================================================
// 4. DATA FILES PERMISSIONS
//=========================================================================

$CFG->directorypermissions = 02777;


//=========================================================================
// 5. DIRECTORY LOCATION
//=========================================================================

$CFG->admin = 'admin';


//=========================================================================
// 6. OTHER MISCELLANEOUS SETTINGS
//=========================================================================

// Redis session handler configuration
if (getenv('REDIS_HOST')) {
    $CFG->session_handler_class = '\core\session\redis';
    $CFG->session_redis_host = loadenv('REDIS_HOST', '127.0.0.1');
    $CFG->session_redis_port = loadenv('REDIS_PORT', 6379);
    $CFG->session_redis_database = loadenv('REDIS_DB', 0);  // Usar DB 0 para MySQL
    $CFG->session_redis_auth = ''; 
    $CFG->session_redis_prefix = loadenv('REDIS_PREFIX', ''); 
    $CFG->session_redis_acquire_lock_timeout = 120;
    $CFG->session_redis_lock_expire = 7200;
}

// Proxy settings
$CFG->reverseproxy = filter_var(loadenv('MOODLE_REVERSE_PROXY', false), FILTER_VALIDATE_BOOLEAN);
$CFG->sslproxy = filter_var(loadenv('MOODLE_SSL_PROXY', false), FILTER_VALIDATE_BOOLEAN);

// Cache directory
$CFG->localcachedir = '/var/local/cache';

// Update autodeploy
$CFG->disableupdateautodeploy = filter_var(loadenv('MOODLE_DISABLE_UPDATE_AUTODEPLOY', true), FILTER_VALIDATE_BOOLEAN);

//=========================================================================
// 7. SETTINGS FOR DEVELOPMENT SERVERS - not intended for production use!!!
//=========================================================================

if (getenv('MOODLE_DEBUG')) {
    @ini_set('display_errors', '1');
    $CFG->debug = (E_ALL | E_STRICT);
    $CFG->debugdisplay = 1;
    $CFG->debugusers = '2';
    $CFG->themedesignermode = true;
    $CFG->debugimap = true;
    $CFG->cachejs = false;
    $CFG->yuiloginclude = array(
        'moodle-core-dock-loader' => true,
        'moodle-course-categoryexpander' => true,
    );
    $CFG->yuilogexclude = array(
        'moodle-core-dock' => true,
        'moodle-core-notification' => true,
    );
    $CFG->yuiloglevel = 'debug';
    $CFG->langstringcache = false;
    $CFG->noemailever = true;
    $CFG->divertallemailsto = 'root@localhost.local';
    $CFG->divertallemailsexcept = 'tester@dev.com, fred(\+.*)?@example.com';
    $CFG->xmldbdisablecommentchecking = true;
    $CFG->upgradeshowsql = true;
    $CFG->showcronsql = true;
    $CFG->showcrondebugging = true;
}

//=========================================================================
// 13. SYSTEM PATHS
//=========================================================================

$CFG->pathtophp = '/usr/local/bin/php';
$CFG->pathtodu = '/usr/bin/du';
$CFG->aspellpath = '/usr/bin/aspell';
$CFG->pathtodot = '/usr/bin/dot';

//=========================================================================
// ALL DONE!  To continue installation, visit your main page with a browser
//=========================================================================

require_once(__DIR__ . '/lib/setup.php'); // Do not edit

// There is no php closing tag in this file,
// it is intentional because it prevents trailing whitespace problems!