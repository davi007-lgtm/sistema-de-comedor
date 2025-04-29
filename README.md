# Sistema de Gestión de Cafetería Escolar

Un sistema moderno y eficiente para la gestión de cafeterías escolares, desarrollado con Flask y Bootstrap 5.

## Características

- 🔐 Sistema de autenticación seguro
- 📊 Dashboard interactivo con estadísticas en tiempo real
- 👥 Gestión de estudiantes (becados y pagados)
- 🍽️ Gestión de menús diarios
- ✅ Control de asistencia mediante códigos QR
- 📈 Generación de reportes en PDF y CSV
- 📱 Diseño responsivo para todos los dispositivos

## Tecnologías Utilizadas

- **Backend**: Python 3.13, Flask 3.0
- **Frontend**: Bootstrap 5, Chart.js
- **Base de Datos**: SQLite (fácilmente escalable a PostgreSQL)
- **Autenticación**: Flask-Login
- **Formularios**: Flask-WTF
- **Reportes**: ReportLab, pandas

## Instalación

1. Clonar el repositorio:
   ```bash
   git clone https://github.com/tu-usuario/sistema-cafeteria.git
   cd sistema-cafeteria
   ```

2. Crear un entorno virtual:
   ```bash
   python -m venv .venv
   ```

3. Activar el entorno virtual:
   - Windows:
     ```bash
     .\.venv\Scripts\activate
     ```
   - Linux/Mac:
     ```bash
     source .venv/bin/activate
     ```

4. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```

5. Inicializar la base de datos:
   ```bash
   python init_db.py
   ```

6. Ejecutar la aplicación:
   ```bash
   python app.py
   ```

## Estructura del Proyecto

```
sistema-cafeteria/
├── app.py              # Aplicación principal
├── extensions.py       # Extensiones de Flask
├── models.py           # Modelos de la base de datos
├── init_db.py         # Script de inicialización de BD
├── requirements.txt    # Dependencias del proyecto
├── static/            # Archivos estáticos
├── templates/         # Plantillas HTML
└── routes/            # Rutas de la aplicación
    ├── auth.py        # Autenticación
    ├── students.py    # Gestión de estudiantes
    ├── attendance.py  # Control de asistencia
    ├── menus.py      # Gestión de menús
    ├── reports.py    # Generación de reportes
    └── admin.py      # Administración
```

## Configuración

El sistema utiliza variables de entorno para la configuración. Crea un archivo `.env` con:

```env
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=tu-clave-secreta
DATABASE_URL=sqlite:///cafeteria.db
```

## Uso

1. Accede a http://localhost:5000
2. Inicia sesión con las credenciales por defecto:
   - Email: admin@example.com
   - Contraseña: admin123

## Contribuir

1. Fork el proyecto
2. Crea una rama para tu función: `git checkout -b feature/nueva-funcion`
3. Commit tus cambios: `git commit -am 'Añade nueva función'`
4. Push a la rama: `git push origin feature/nueva-funcion`
5. Crea un Pull Request

## Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.
