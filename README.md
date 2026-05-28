# ⚡ crear_red_electrica — Plugin QGIS

> Plugin QGIS para el trazado y modelado de redes eléctricas de media tensión.  
> Desarrollado para la cooperativa eléctrica de la zona Colonia Caroya / Jesús María, Córdoba, Argentina.

---

## 📋 Descripción

`crear_red_electrica` permite digitalizar y estructurar redes de media tensión directamente en QGIS, incluyendo líneas, dispositivos de maniobra y elementos de protección. Las capas generadas son compatibles con el script de conversión a [pandapower](https://www.pandapower.org/).

**Características principales:**
- Trazado de líneas MT con atributos configurables (sección, tipo de conductor, tensión)
- Inserción de dispositivos de maniobra: seccionadores, interruptores, reconectadores
- Inserción de elementos de protección: fusibles, pararrayos
- Generación automática de topología de red
- Capas vectoriales exportables a shapefile / GeoPackage

---

## 🛠️ Requisitos

| Requisito | Versión mínima |
|---|---|
| QGIS | 3.22 LTR |
| Python | 3.9+ |

> No requiere dependencias externas adicionales.

---

## 🚀 Instalación

1. Clonar o descargar el repositorio:

```bash
git clone https://github.com/ricardo32vm/crear-red-electrica.git
```

2. Copiar la carpeta `crear_red_electrica` a la carpeta de plugins de QGIS:

```
# Windows
%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\

# Linux
~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/
```

3. En QGIS → **Complementos** → **Administrar e instalar complementos** → activar **Crear Red Eléctrica**.

---

## 📁 Estructura

```
crear_red_electrica/
├── __init__.py
├── crear_red_electrica.py
├── crear_red_electrica_dialog.py
├── metadata.txt
└── resources/
    ├── icons/
    └── ui/
```

---

## 💡 Uso básico

1. Activar el plugin desde la barra de herramientas o el menú **Complementos**
2. Seleccionar el tipo de elemento a digitalizar (línea MT, seccionador, fusible, etc.)
3. Dibujar sobre el mapa
4. Completar los atributos en el formulario emergente
5. Exportar las capas para usar con `shp_a_pandapower`

---

## 🗺️ Contexto de aplicación

Herramienta desarrollada para la gestión del área de concesión de la cooperativa eléctrica de **Colonia Caroya / Jesús María**, Provincia de Córdoba, Argentina.

---

## 👨‍💻 Autor

**Ing. Ricardo Luis Castro**  
Docente-investigador — UTN Facultad Regional Villa María  
📍 Villa María, Córdoba, Argentina

---

## 📄 Licencia

[GPL v2](https://www.gnu.org/licenses/old-licenses/gpl-2.0.html) — compatible con la licencia estándar de plugins QGIS.
