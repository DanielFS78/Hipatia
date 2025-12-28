# 🏭 Industrial Production Simulator & Optimizer (Built with AI)

[![Tests](https://img.shields.io/badge/Tests-1136%20PASSED-success?style=for-the-badge)](https://github.com/DanielFS78/Hipatia)
[![Coverage](https://img.shields.io/badge/Coverage-100%25%20(Repos)-brightgreen?style=for-the-badge)](https://github.com/DanielFS78/Hipatia)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

> [!IMPORTANT]
> **REQUEST FOR AUDIT:** I am a non-programmer who built this 60k LOC project over 1,000 hours using AI. It works perfectly and has **1136 tests**, but I need experts to review its core architecture, security, and maintainability.

---

## 🇪🇸 Resumen del Proyecto

Este software es un **Motor de Simulación y Optimización de Tiempos de Fabricación**. Permite a plantas industriales planificar cargas de trabajo, optimizar la asignación de operarios y realizar un seguimiento mediante códigos QR.

📖 **[Descargar Manual de Usuario (DOCX)](Documentacion/Manual_de_uso_corregido.docx)** - Documentación detallada de todas las funcionalidades.

### El Experimento:
Este proyecto comenzó como un simple script de sumas en la terminal y evolucionó a través de **12 refactorizaciones completas** asistidas por IA. Mi objetivo es validar si este nivel de complejidad es sostenible y seguro para su implementación real en fábrica.

---

## 🇺🇸 Project Overview

An advanced **Production Flow Simulator & Optimization Engine** tailored for industrial environments. It manages task queues, worker assignments, and real-time tracking via QR codes.

### The AI Experiment:
This project is a 5-month journey of collaboration between a non-technical founder and AI models. From a terminal script to a full PyQt6/SQLAlchemy ecosystem, it has undergone 12 major architectural shifts.

---

## 🛠 Technical Highlights

- **Simulation Engine:** Event-driven simulation using priority queues (`heapq`).
- **Optimization Strategy:** Dynamic resource allocation to meet production deadlines.
- **Architectural Rigor:** **1136 unit and integration tests** (100% repository coverage).
- **Modern UI:** Built with PyQt6 featuring drag-and-drop production flow editors and Gantt visualizations.
- **Database:** Robust SQLAlchemy ORM with versioned migrations (v1-v11).

---

## 🧪 The "1136 Tests" Guarantee

I don't know the specifics of every line of code, but I know it works because it's battle-tested.
To run the verification suite:

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
source .venv/bin/activate
python run_tests.py
```

---

## 🔍 What I Need from Experts (The Audit)

If you are a senior Python developer or architect, I would value your feedback on:
1. **Maintainability:** Is the modular structure (MVC) solid or just a facade?
2. **Security:** Are there hidden vulnerabilities in the data management or file handling?
3. **Efficiency:** Can the `Optimizer` and `SimulationEngine` be more performant?
4. **General Sanity:** Does this code "smell" like a professional project or an AI hallucination?

---

## 📜 License
Published under the **MIT License**. Use it, break it, and please, help me improve it.

---

*Built with persistence and a lot of AI prompts.*
