from extensions import db
from datetime import datetime
import json

class ReportePlantilla(db.Model):
    __tablename__ = 'reportes_plantillas'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200), nullable=False)
    tipo_reporte = db.Column(db.String(50), nullable=False)
    filtros_json = db.Column(db.Text, nullable=False, default='{}')
    columnas_json = db.Column(db.Text, nullable=False, default='[]')
    created_by = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_filtros(self, filtros):
        self.filtros_json = json.dumps(filtros, default=str, ensure_ascii=False)
    
    def get_filtros(self):
        return json.loads(self.filtros_json) if self.filtros_json else {}
    
    def set_columnas(self, columnas):
        self.columnas_json = json.dumps(columnas, ensure_ascii=False)
    
    def get_columnas(self):
        return json.loads(self.columnas_json) if self.columnas_json else []
    
    estilos_json = db.Column(db.Text, nullable=True)  # JSON con opciones de estilo