

#set up and enable OPCache (PHP) (?)

# Copy drupal11 blank project to C:\APACHE24\htdocs\drupal11 from internet https://ftp.drupal.org/files/projects/drupal-11.1.3.zip

# Set up databases for drupal: (.\PythonFiles\.venv\Scripts\python .\PythonFiles\mysql_manager.py setup --services drupal --root-password root)

# Warning: Deshabilite la agregación de CSS/JS (C:\APACHE24\htdocs\drupal11\sites\default\settings.php)
'''
// TEMPORAL: Deshabilita la agregación para evitar el problema de permisos en /files.
$config['system.performance']['css']['preprocess'] = FALSE;
$config['system.performance']['js']['preprocess'] = FALSE;
'''

