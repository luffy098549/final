from extensions import db
from datetime import datetime
import json

class ReporteGuardado(db.Model):
    __tablename__ = 'reportes_guardados'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200), nullable=False)
    tipo_reporte = db.Column(db.String(50), nullable=False)
    fecha_generacion = db.Column(db.DateTime, default=datetime.utcnow)
    generado_por = db.Column(db.String(100), nullable=False)
    total_registros = db.Column(db.Integer, default=0)
    
    datos_json = db.Column(db.Text, nullable=False)
    columnas_json = db.Column(db.Text, nullable=True)
    filtros_json = db.Column(db.Text, nullable=True)
    estilos_json = db.Column(db.Text, nullable=True)          # <-- NUEVO
    
    def set_datos(self, registros_dict_list):
        self.datos_json = json.dumps(registros_dict_list, ensure_ascii=False, default=str)
        self.total_registros = len(registros_dict_list)
    
    def get_datos(self):
        return json.loads(self.datos_json) if self.datos_json else []
    
    def set_columnas(self, columnas_list):
        self.columnas_json = json.dumps(columnas_list, ensure_ascii=False)
    
    def get_columnas(self):
        return json.loads(self.columnas_json) if self.columnas_json else []
    
    def set_filtros(self, filtros_dict):
        self.filtros_json = json.dumps(filtros_dict, ensure_ascii=False, default=str)
    
    def get_filtros(self):
        return json.loads(self.filtros_json) if self.filtros_json else {}
    
    def set_estilos(self, estilos_dict):
        self.estilos_json = json.dumps(estilos_dict, ensure_ascii=False)
    
    def get_estilos(self):
        return json.loads(self.estilos_json) if self.estilos_json else {}
    
    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'tipo_reporte': self.tipo_reporte,
            'fecha_generacion': self.fecha_generacion.strftime('%d/%m/%Y %H:%M'),
            'generado_por': self.generado_por,
            'total_registros': self.total_registros
        }