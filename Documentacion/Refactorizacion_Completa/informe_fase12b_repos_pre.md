# MCP Informe Pre-Fase: Consolidación Fase 12B (Repositorios)

**Fecha:** 2026-03-09
**Fase:** 12B - Convertir Mixins en Gestores

## Estado Inicial de la Cuestión
En la primera etapa de la Fase 12B, se logró migrar con éxito los Controladores (`WorkerController` y `ProductController`) de la arquitectura heredada con Mixins a una arquitectura **Fachada (Facade) con Composición**, basada estrictamente en **Protocolos**.

Durante la inspección de cara a continuar con los dominios `Historial` y `Simulation`, se descubrió que:
1. Sus Controladores **ya utilizan Gestores** (por lo que su refactorización estaba hecha).
2. Quedan 5 archivos `*_mixin.py` en sus carpetas que son **código muerto** (nunca importados).
3. Una búsqueda global reveló que la capa de **Repositorios (`database/repositories/`)** aloja la mayoría de los Mixins sobrevivientes en el proyecto, y de hecho, el objetivo del MCP para esta fase explicita *"Los controladores _y repositorios_ dejarán de ser aglomeraciones de herencia múltiple..."*.

## ¿Qué se va a hacer?
Extender la lógica de la Fase 12B para erradicar la herencia múltiple en los repositorios:
1. Eliminar permanentemente el código muerto en `controllers/historial/` y `controllers/simulation/`.
2. Romper los 3 grandes repositorios monolíticos (`PreprocesoRepository`, `TrackingRepository`, `WorkerRepository`) que heredan de múltiples *Mixins*.
3. Transformar cada *Mixin* de la base de datos en un gestor DAO independiente (e.g., `PreprocesoManager` en lugar de `PreprocesoMixin`).
4. Reestructurar las clases principales de Repository para instanciar estos gestores y delegarles las llamadas, respetando su rol como de **Fachada**.

## ¿Cómo se va a hacer? (Técnicas)
Dado que estas clases DAO necesitan acceso al objeto `Session` de la base de datos, cada nuevo Gestor/DAO continuará heredando de `BaseRepository` para aprovechar transparentemente el método `self.safe_execute`.
El `Repository` principal (que será registrado en el sistema de Inyección de Dependencias como siempre) inicializará sus *managers* pasándoles la misma `session_factory` o inyectándolos y servirá de enrutador simple.

## Protocolo de Seguridad
Dado que esto toca las operaciones CRUD subyacentes de todo el sistema, haremos un testeo agresivo. La suite global de `pytest` (>2300 tests) es la red de seguridad principal. No alteraremos firmas o retornos, sólo la estructura interna de cómo llega la llamada a `safe_execute`.
