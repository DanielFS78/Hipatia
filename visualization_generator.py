# visualization_generator.py

import graphviz
import logging
import os
from datetime import datetime
from constants import DEPARTMENT_COLORS


class VisualizationGenerator:
    """
    Genera un organigrama detallado del flujo de producción, destacando
    dependencias, recursos y cuellos de botella.
    """

    def __init__(self, simulation_results, audit_log, fabrication_description=""):
        self.results = simulation_results
        self.audit = audit_log  # <-- AHORA RECIBIMOS EL LOG DE AUDITORÍA
        self.fabrication_description = fabrication_description
        self.logger = logging.getLogger("EvolucionTiemposApp.VisualizationGenerator")
        self.logger.info(f"Generador de organigrama inicializado para '{self.fabrication_description}'.")

    def generate_organigram_image(self, output_filename):
        """
        Crea el gráfico completo y lo renderiza a un archivo de imagen.
        """
        self.logger.info("Iniciando la generación del organigrama como imagen única.")

        if not self.results:
            return False, "No hay datos en la simulación para generar el organigrama."

        dot = graphviz.Digraph(comment=self.fabrication_description)
        dot.attr('graph',
                 rankdir='TB',
                 splines='ortho',
                 nodesep='0.8',
                 ranksep='1.0',
                 label=f"Flujo de Producción: {self.fabrication_description}\nGenerado: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                 fontsize='20',
                 fontname='Helvetica,Arial,sans-serif')

        dot.attr('node',
                 shape='box',
                 style='rounded,filled',
                 fontname='Helvetica,Arial,sans-serif',
                 fontsize='11')

        dot.attr('edge',
                 fontname='Helvetica,Arial,sans-serif',
                 fontsize='9')

        for task_data in self.results:
            node_id = str(task_data['Index'])
            task_audit = [d for d in self.audit if d.task_name == task_data['Tarea']]

            # --- EXTRACCIÓN DE DATOS ADICIONALES DE LA AUDITORÍA ---
            wait_decision = next((d for d in task_audit if d.decision_type == 'ESPERA POR RECURSO'), None)

            machine_name = task_data.get('nombre_maquina', 'N/A')

            # --- LÓGICA DE ESTILO VISUAL ---
            border_color = "#d9534f" if wait_decision else "#5cb85c"  # Rojo si hay espera, si no Verde
            department = task_data.get('Departamento', 'Default')
            fill_color = DEPARTMENT_COLORS.get(department, DEPARTMENT_COLORS['Default'])

            # --- CONSTRUCCIÓN DE LA ETIQUETA HTML DEL NODO ---
            start_time_str = task_data['Inicio'].strftime('%d/%m %H:%M')
            end_time_str = task_data['Fin'].strftime('%H:%M')
            workers_str = ", ".join(task_data['Trabajador Asignado'])

            label = f"""<
            <TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" COLOR="{border_color}">
                <TR>
                    <TD COLSPAN="2" BGCOLOR="#333333"><FONT COLOR="white"><B>{task_data['Tarea']}</B></FONT></TD>
                </TR>
                <TR><TD ALIGN="LEFT">Departamento:</TD><TD ALIGN="LEFT" BGCOLOR="{fill_color}">{department}</TD></TR>
                <TR><TD ALIGN="LEFT">Inicio:</TD><TD ALIGN="LEFT">{start_time_str}</TD></TR>
                <TR><TD ALIGN="LEFT">Fin:</TD><TD ALIGN="LEFT">{end_time_str}</TD></TR>
                <TR><TD ALIGN="LEFT">Máquina:</TD><TD ALIGN="LEFT">{machine_name}</TD></TR>
                <TR><TD ALIGN="LEFT">Operarios:</TD><TD ALIGN="LEFT">{workers_str}</TD></TR>
            """
            # Añadir fila de espera solo si existe
            if wait_decision:
                wait_minutes = wait_decision.details.get('wait_minutes', 0)
                resource_info = wait_decision.details.get("resource", "Recurso no especificado")
                label += f'<TR><TD ALIGN="LEFT" BGCOLOR="#f0ad4e"><B>Espera:</B></TD><TD ALIGN="LEFT" BGCOLOR="#f0ad4e"><B>{wait_minutes:.1f} min ({resource_info})</B></TD></TR>'

            label += "</TABLE>>"

            dot.node(node_id, label=label, shape='none')

        # --- Crear Aristas de Dependencia ---
        for task_data in self.results:
            parent_index = task_data.get('Parent Index')
            if parent_index is not None and parent_index < len(self.results):
                parent_task_id = self.results[parent_index]['Index']
                source_id = str(parent_task_id)
                target_id = str(task_data['Index'])
                dot.edge(source_id, target_id)

        # --- Renderizar y Guardar ---
        try:
            output_base = os.path.splitext(output_filename)[0]
            dot.render(output_base, format='png', view=False, cleanup=True)
            self.logger.info(f"Organigrama guardado con éxito como '{output_base}.png'.")
            return True, None
        except (graphviz.backend.execute.ExecutableNotFound, FileNotFoundError):
            error_msg = "No se encontró 'dot.exe'. Asegúrese de que Graphviz esté instalado y en el PATH del sistema."
            self.logger.critical(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Error inesperado al renderizar el organigrama: {e}"
            self.logger.critical(error_msg, exc_info=True)
            return False, error_msg