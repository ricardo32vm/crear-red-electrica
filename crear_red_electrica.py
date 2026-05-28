import os
from qgis.PyQt.QtWidgets import QAction, QMessageBox
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import QVariant
from qgis.core import (
    QgsProject,
    QgsVectorLayer,
    QgsField,
    QgsFeature,
    QgsGeometry,
    QgsPointXY,
    QgsSpatialIndex,
    QgsWkbTypes,
    QgsCoordinateReferenceSystem,
    edit
)

# Prefijos de ID para cada tipo de elemento
ID_PREFIX = {
    "nodos_electricos":    ("id_nodo", "N"),
    "seccionadores":       ("id",      "S"),
    "reconectadores":      ("id",      "R"),
    "subestaciones":       ("id",      "SE"),
    "fusibles":            ("id",      "F"),
    "lineas_electricas":   ("id_linea","L"),
}

# Nombre del campo ID en cada capa de puntos
ID_FIELD = {
    "nodos_electricos": "id_nodo",
    "seccionadores":    "id",
    "reconectadores":   "id",
    "subestaciones":    "id",
    "fusibles":         "id",
}

CRS = "EPSG:22174"


class ElectricNetworkPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.canvas = iface.mapCanvas()

        self.action_nodo          = None
        self.action_linea         = None
        self.action_seccionador   = None
        self.action_reconectador  = None
        self.action_subestacion   = None
        self.action_fusible       = None

        self.nodos_layer          = None
        self.lineas_layer         = None
        self.seccionadores_layer  = None
        self.reconectadores_layer = None
        self.subestaciones_layer  = None
        self.fusibles_layer       = None

        self._indices_elementos   = {}

        self.plugin_dir = os.path.dirname(__file__)

    # ------------------------------------------------------------------
    # QGIS lifecycle
    # ------------------------------------------------------------------

    def initGui(self):
        def icon(name):
            return QIcon(os.path.join(self.plugin_dir, "icons", name))

        self.action_nodo = QAction(icon("icon_nodo.svg"), "Crear Nodos Electricos", self.iface.mainWindow())
        self.action_nodo.setToolTip("Inicializa la capa de nodos y activa el editor")
        self.action_nodo.triggered.connect(self.activar_nodos)

        self.action_linea = QAction(icon("icon_linea.svg"), "Crear Lineas Electricas", self.iface.mainWindow())
        self.action_linea.setToolTip("Activa el editor de lineas (requiere al menos 2 elementos en la red)")
        self.action_linea.setEnabled(False)
        self.action_linea.triggered.connect(self.activar_lineas)

        self.action_seccionador = QAction(icon("icon_seccionador.svg"), "Crear Seccionadores", self.iface.mainWindow())
        self.action_seccionador.setToolTip("Inicializa la capa de seccionadores y activa el editor")
        self.action_seccionador.triggered.connect(self.activar_seccionadores)

        self.action_reconectador = QAction(icon("icon_reconectador.svg"), "Crear Reconectadores", self.iface.mainWindow())
        self.action_reconectador.setToolTip("Inicializa la capa de reconectadores y activa el editor")
        self.action_reconectador.triggered.connect(self.activar_reconectadores)

        self.action_subestacion = QAction(icon("icon_subestacion.svg"), "Crear Subestaciones", self.iface.mainWindow())
        self.action_subestacion.setToolTip("Inicializa la capa de subestaciones y activa el editor")
        self.action_subestacion.triggered.connect(self.activar_subestaciones)

        self.action_fusible = QAction(icon("icon_fusible.svg"), "Crear Fusibles", self.iface.mainWindow())
        self.action_fusible.setToolTip("Inicializa la capa de fusibles y activa el editor")
        self.action_fusible.triggered.connect(self.activar_fusibles)

        for action in (
            self.action_nodo,
            self.action_seccionador,
            self.action_reconectador,
            self.action_subestacion,
            self.action_fusible,
            self.action_linea,
        ):
            self.iface.addToolBarIcon(action)
            self.iface.addPluginToMenu("Red Electrica", action)

    def unload(self):
        for action in (
            self.action_nodo,
            self.action_linea,
            self.action_seccionador,
            self.action_reconectador,
            self.action_subestacion,
            self.action_fusible,
        ):
            if action:
                self.iface.removeToolBarIcon(action)
                self.iface.removePluginMenu("Red Electrica", action)

    # ------------------------------------------------------------------
    # Creacion de capas
    # ------------------------------------------------------------------

    def _crear_capa_nodos(self):
        layer = QgsVectorLayer(f"Point?crs={CRS}", "nodos_electricos", "memory")
        pr = layer.dataProvider()
        pr.addAttributes([
            QgsField("id_nodo",  QVariant.String),
            QgsField("coord_x",  QVariant.Double),
            QgsField("coord_y",  QVariant.Double),
        ])
        layer.updateFields()
        return layer

    def _crear_capa_lineas(self):
        layer = QgsVectorLayer(f"LineString?crs={CRS}", "lineas_electricas", "memory")
        pr = layer.dataProvider()
        pr.addAttributes([
            QgsField("id_linea",           QVariant.String),
            QgsField("start_line",         QVariant.String),
            QgsField("end_line",           QVariant.String),
            QgsField("longitud",           QVariant.Double),
            QgsField("seccion_conductor",  QVariant.String),
            QgsField("tipo_conductor",     QVariant.String),
            QgsField("tipo_linea",         QVariant.String),
            QgsField("resistencia",        QVariant.Double),
            QgsField("reactancia",         QVariant.Double),
        ])
        layer.updateFields()
        return layer

    def _crear_capa_seccionadores(self):
        layer = QgsVectorLayer(f"Point?crs={CRS}", "seccionadores", "memory")
        pr = layer.dataProvider()
        pr.addAttributes([
            QgsField("id",               QVariant.String),
            QgsField("tipo_seccionador", QVariant.String),
            QgsField("end_line",         QVariant.String),
            QgsField("start_line",       QVariant.String),
        ])
        layer.updateFields()
        return layer

    def _crear_capa_reconectadores(self):
        layer = QgsVectorLayer(f"Point?crs={CRS}", "reconectadores", "memory")
        pr = layer.dataProvider()
        pr.addAttributes([
            QgsField("id",                QVariant.String),
            QgsField("tipo_reconectador", QVariant.String),
            QgsField("end_line",          QVariant.String),
            QgsField("start_line",        QVariant.String),
        ])
        layer.updateFields()
        return layer

    def _crear_capa_subestaciones(self):
        layer = QgsVectorLayer(f"Point?crs={CRS}", "subestaciones", "memory")
        pr = layer.dataProvider()
        pr.addAttributes([
            QgsField("id",          QVariant.String),
            QgsField("tipo_subest", QVariant.String),
            QgsField("potencia",    QVariant.Double),
            QgsField("end_line",    QVariant.String),
            QgsField("start_line",  QVariant.String),
        ])
        layer.updateFields()
        return layer

    def _crear_capa_fusibles(self):
        layer = QgsVectorLayer(f"Point?crs={CRS}", "fusibles", "memory")
        pr = layer.dataProvider()
        pr.addAttributes([
            QgsField("id",           QVariant.String),
            QgsField("tipo_fusible", QVariant.String),
            QgsField("end_line",     QVariant.String),
            QgsField("start_line",   QVariant.String),
        ])
        layer.updateFields()
        return layer

    # ------------------------------------------------------------------
    # Activacion de capas
    # ------------------------------------------------------------------

    def _activar_capa_puntos(self, nombre_capa, factory, callback_signal):
        existing = QgsProject.instance().mapLayersByName(nombre_capa)
        if existing:
            layer = existing[0]
        else:
            layer = factory()
            QgsProject.instance().addMapLayer(layer)

        try:
            layer.featureAdded.disconnect(callback_signal)
        except Exception:
            pass
        layer.featureAdded.connect(callback_signal)

        self.iface.setActiveLayer(layer)
        layer.startEditing()
        self.iface.actionAddFeature().trigger()
        return layer

    def activar_nodos(self):
        self.nodos_layer = self._activar_capa_puntos(
            "nodos_electricos", self._crear_capa_nodos, self._on_nodo_agregado)
        self._actualizar_boton_linea()

    def activar_seccionadores(self):
        self.seccionadores_layer = self._activar_capa_puntos(
            "seccionadores", self._crear_capa_seccionadores, self._on_seccionador_agregado)
        self._actualizar_boton_linea()

    def activar_reconectadores(self):
        self.reconectadores_layer = self._activar_capa_puntos(
            "reconectadores", self._crear_capa_reconectadores, self._on_reconectador_agregado)
        self._actualizar_boton_linea()

    def activar_subestaciones(self):
        self.subestaciones_layer = self._activar_capa_puntos(
            "subestaciones", self._crear_capa_subestaciones, self._on_subestacion_agregada)
        self._actualizar_boton_linea()

    def activar_fusibles(self):
        self.fusibles_layer = self._activar_capa_puntos(
            "fusibles", self._crear_capa_fusibles, self._on_fusible_agregado)
        self._actualizar_boton_linea()

    def activar_lineas(self):
        if self._total_elementos() < 2:
            QMessageBox.warning(
                None, "Red Electrica",
                "Debe digitalizar al menos 2 elementos (nodos, seccionadores, "
                "reconectadores, subestaciones o fusibles) antes de crear lineas."
            )
            return

        existing = QgsProject.instance().mapLayersByName("lineas_electricas")
        if existing:
            self.lineas_layer = existing[0]
        else:
            self.lineas_layer = self._crear_capa_lineas()
            QgsProject.instance().addMapLayer(self.lineas_layer)

        try:
            self.lineas_layer.featureAdded.disconnect(self._on_linea_agregada)
        except Exception:
            pass
        self.lineas_layer.featureAdded.connect(self._on_linea_agregada)

        self._reconstruir_indices()

        self.iface.setActiveLayer(self.lineas_layer)
        self.lineas_layer.startEditing()
        self.iface.actionAddFeature().trigger()

    # ------------------------------------------------------------------
    # Eventos: autonumeracion de elementos puntuales
    # ------------------------------------------------------------------

    def _autonumerar(self, layer, nombre_capa, fid):
        id_field, prefix = ID_PREFIX[nombre_capa]
        ids_existentes = []
        for f in layer.getFeatures():
            val = f[id_field]
            if val and str(val).startswith(prefix):
                try:
                    ids_existentes.append(int(str(val)[len(prefix):]))
                except ValueError:
                    pass
        next_num = max(ids_existentes) + 1 if ids_existentes else 1
        new_id = f"{prefix}{next_num}"
        layer.changeAttributeValue(fid, layer.fields().indexFromName(id_field), new_id)
        return new_id

    def _on_nodo_agregado(self, fid):
        layer = self.nodos_layer
        self._autonumerar(layer, "nodos_electricos", fid)
        feature = layer.getFeature(fid)
        geom = feature.geometry()
        if not geom or geom.isNull():
            return
        point = geom.asPoint()
        layer.changeAttributeValue(fid, layer.fields().indexFromName("coord_x"), round(point.x(), 3))
        layer.changeAttributeValue(fid, layer.fields().indexFromName("coord_y"), round(point.y(), 3))
        self._actualizar_boton_linea()

    def _on_seccionador_agregado(self, fid):
        self._autonumerar(self.seccionadores_layer, "seccionadores", fid)
        self._actualizar_boton_linea()

    def _on_reconectador_agregado(self, fid):
        self._autonumerar(self.reconectadores_layer, "reconectadores", fid)
        self._actualizar_boton_linea()

    def _on_subestacion_agregada(self, fid):
        self._autonumerar(self.subestaciones_layer, "subestaciones", fid)
        self._actualizar_boton_linea()

    def _on_fusible_agregado(self, fid):
        self._autonumerar(self.fusibles_layer, "fusibles", fid)
        self._actualizar_boton_linea()

    # ------------------------------------------------------------------
    # Evento: linea agregada
    # ------------------------------------------------------------------

    def _on_linea_agregada(self, fid):
        if not self._indices_elementos:
            self._reconstruir_indices()

        layer = self.lineas_layer
        feature = layer.getFeature(fid)
        geom = feature.geometry()
        if not geom or geom.isNull():
            return

        vertices = [v for v in geom.vertices()]
        if len(vertices) < 2:
            return

        start_pt = QgsPointXY(vertices[0].x(),  vertices[0].y())
        end_pt   = QgsPointXY(vertices[-1].x(), vertices[-1].y())
        longitud = round(geom.length(), 3)

        id_inicio = self._elemento_mas_cercano(start_pt)
        id_fin    = self._elemento_mas_cercano(end_pt)

        ids_lineas = []
        for f in layer.getFeatures():
            val = f["id_linea"]
            if val and str(val).startswith("L"):
                try:
                    ids_lineas.append(int(str(val)[1:]))
                except ValueError:
                    pass
        next_num = max(ids_lineas) + 1 if ids_lineas else 1
        new_id = f"L{next_num}"

        layer.changeAttributeValue(fid, layer.fields().indexFromName("id_linea"),   new_id)
        layer.changeAttributeValue(fid, layer.fields().indexFromName("start_line"), id_inicio)
        layer.changeAttributeValue(fid, layer.fields().indexFromName("end_line"),   id_fin)
        layer.changeAttributeValue(fid, layer.fields().indexFromName("longitud"),   longitud)

        # Retroalimentar start_line / end_line en los elementos conectados
        self._registrar_linea_en_elemento(id_inicio, new_id, "start_line")
        self._registrar_linea_en_elemento(id_fin,    new_id, "end_line")

    # ------------------------------------------------------------------
    # Indice espacial unificado
    # ------------------------------------------------------------------

    def _capas_elementos(self):
        candidatos = {
            "nodos_electricos":    self.nodos_layer,
            "seccionadores":       self.seccionadores_layer,
            "reconectadores":      self.reconectadores_layer,
            "subestaciones":       self.subestaciones_layer,
            "fusibles":            self.fusibles_layer,
        }
        for nombre in list(candidatos.keys()):
            if candidatos[nombre] is None:
                existing = QgsProject.instance().mapLayersByName(nombre)
                if existing:
                    candidatos[nombre] = existing[0]
        return {k: v for k, v in candidatos.items() if v is not None}

    def _reconstruir_indices(self):
        self._indices_elementos = {}
        for nombre, layer in self._capas_elementos().items():
            self._indices_elementos[nombre] = QgsSpatialIndex(layer.getFeatures())

    def _elemento_mas_cercano(self, punto: QgsPointXY) -> str:
        mejor_id   = ""
        mejor_dist = float("inf")

        for nombre, layer in self._capas_elementos().items():
            idx = self._indices_elementos.get(nombre)
            if idx is None:
                continue
            nearest_ids = idx.nearestNeighbor(punto, 1)
            if not nearest_ids:
                continue
            feat = layer.getFeature(nearest_ids[0])
            geom = feat.geometry()
            if geom is None or geom.isNull():
                continue
            dist = geom.asPoint().distance(punto)
            if dist < mejor_dist:
                mejor_dist = dist
                id_field   = ID_FIELD[nombre]
                mejor_id   = str(feat[id_field])

        return mejor_id

    # ------------------------------------------------------------------
    # Retroalimentacion: registrar linea en el elemento conectado
    # ------------------------------------------------------------------

    def _registrar_linea_en_elemento(self, elemento_id: str, linea_id: str, campo: str):
        if not elemento_id:
            return
        # nodos_electricos no tiene end_line / start_line, se omite
        capas_con_campo = ["seccionadores", "reconectadores", "subestaciones", "fusibles"]
        for nombre in capas_con_campo:
            layer = self._capas_elementos().get(nombre)
            if layer is None:
                continue
            id_field = ID_FIELD[nombre]
            for feat in layer.getFeatures():
                if str(feat[id_field]) == elemento_id:
                    idx = layer.fields().indexFromName(campo)
                    if idx >= 0:
                        layer.changeAttributeValue(feat.id(), idx, linea_id)
                    return

    # ------------------------------------------------------------------
    # Utilidades
    # ------------------------------------------------------------------

    def _total_elementos(self) -> int:
        return sum(l.featureCount() for l in self._capas_elementos().values())

    def _actualizar_boton_linea(self):
        if self.action_linea:
            self.action_linea.setEnabled(self._total_elementos() >= 2)
