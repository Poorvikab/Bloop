# Bloop - AI-Powered Educational Learning Platform

<div align="center">

**Transform any concept into comprehensive learning experiences with AI-powered videos, personalized roadmaps, and interactive games.**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-green.svg)](https://fastapi.tiangolo.com/)
[![Manim](https://img.shields.io/badge/Manim-Community-orange.svg)](https://www.manim.community/)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![FFmpeg](https://img.shields.io/badge/FFmpeg-Latest-green.svg)](https://ffmpeg.org/)

</div>

---

## 🎯 Overview

Bloop revolutionizes educational content creation by generating **fully animated explainer videos** from simple text queries or documents. Unlike traditional educational AI systems that produce static text or slides, Bloop creates dynamic visual explanations with synchronized narration and optional photorealistic talking avatars - all generated on-demand without precomputed assets.

### ✨ Key Features

- 🎨 **Programmatic Animation Generation** - Create stunning Manim animations automatically from educational concepts
- 🎙️ **Scene-Aligned Narration** - Neural TTS with perfect temporal synchronization
- 🤖 **Talking Avatar Integration** - Photorealistic avatars using SadTalker for human-like delivery
- 🧠 **LLM-Orchestrated Pipeline** - Intelligent scene planning and automated error repair
- 🎯 **Fault-Tolerant Rendering** - Scene-isolated execution with graceful degradation
- 📚 **Document-Based Learning** - Generate videos from PDFs, textbooks, or research papers
- 🗺️ **Personalized Roadmaps** - AI-generated learning paths tailored to your level
- 🎮 **Interactive Learning Games** - Engaging educational games with voice interaction

## 🏗️ Architecture

Bloop employs a sophisticated microservices architecture designed for real-time video generation:

```
Client Query
    │
    ▼
FastAPI Gateway (QA Service)
    │
    ├─► LLM Answer Generation
    │   └─► Document Analysis & Understanding
    │
    └─► Manim Video Service
        │
        ├─► Scene Planning (LLM → JSON)
        │   └─► Structured Scene Graphs
        │
        ├─► Scene-by-Scene Rendering
        │   ├─► Independent Execution Context
        │   ├─► Error Detection & Capture
        │   ├─► LLM-Based Auto Repair
        │   └─► Scene Skipping (if unrecoverable)
        │
        ├─► TTS Generation (Per Scene)
        │   └─► Neural Text-to-Speech
        │
        ├─► FFmpeg Audio-Video Alignment
        │   ├─► Temporal Synchronization
        │   └─► Duration Padding
        │
        └─► Scene Stitching
            └─► Final Animation Output
                │
                └─► (Optional) SadTalker Avatar
                    ├─► Audio Extraction
                    ├─► Avatar Rendering
                    └─► Side-by-Side Composition
```

## Quick Start

### Prerequisites

- Python 3.8+
- FFmpeg
- LaTeX (for mathematical expressions)
- GPU (optional, for faster avatar generation)
- CUDA (optional, for SadTalker acceleration)

### 1. Clone the Repository

```bash
git clone https://github.com/poorvikab/bloop.git
cd bloop
```

### 2. Backend Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Manim
pip install manim

# Install additional dependencies
sudo apt-get install libcairo2-dev pkg-config python3-dev
sudo apt-get install ffmpeg

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration
```

### 3. Configure Environment

```env
# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key
AZURE_OPENAI_ENDPOINT=your-azure-endpoint  # Optional

# TTS Configuration
TTS_PROVIDER=azure  # or 'elevenlabs', 'google'
AZURE_SPEECH_KEY=your-speech-key
AZURE_SPEECH_REGION=eastus

# SadTalker Configuration (Optional)
SADTALKER_MODEL_PATH=./models/sadtalker
ENABLE_AVATAR=true

# File Paths
UPLOAD_DIR=uploads
OUTPUT_DIR=outputs
TEMP_DIR=temp

# Performance
MAX_SCENE_RETRIES=1
SCENE_TIMEOUT=120
PARALLEL_SCENES=false
```

### 4. Start the Server

```bash
# Development mode
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production mode
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker
```

### 5. Access the API

Visit `http://localhost:8000/docs` for interactive API documentation.

## Core Features

### ASK MODE - Intelligent Learning Assistant

Bloop's Ask mode combines all the capabilities of NotebookLM with powerful visual content generation:

#### Video Generation
Bloop generates educational videos in real-time through a sophisticated pipeline:

**Scene Planning via LLMs**

```python
# Example scene structure
{
  "scenes": [
    {
      "id": "scene_1",
      "concept": "Pythagorean Theorem",
      "visual_intent": "Show right triangle with labeled sides",
      "duration": 8,
      "manim_hints": ["Polygon", "MathTex", "Animation"]
    }
  ]
}
```

**Automated Manim Code Generation**
- LLM generates Manim Python code for each scene
- Validates syntax and API compatibility
- Optimizes for rendering performance

**Scene-Isolated Rendering**

Each scene renders independently to prevent cascading failures:

```
Scene 1: ✓ Success
Scene 2: ✗ Failed → LLM Repair → ✓ Success
Scene 3: ✓ Success
Scene 4: ✗ Failed → LLM Repair → ✗ Failed → Skip
Scene 5: ✓ Success
```

**Intelligent Error Repair**

When a scene fails:

1. The Manim error log is captured
2. The failing scene code + error is sent back to the LLM
3. A corrected scene is regenerated
4. Rendering is retried once
5. Scene is skipped if still invalid

This design ensures **progressive output generation** under uncertainty.

---

## **6. Audio Generation and Synchronization**

Narration is generated **per scene** using neural TTS.
FFmpeg is used to:

* Pad video if audio is longer
* Pad audio if video is longer
* Preserve temporal alignment without re-encoding loss

This guarantees narration always matches visual pacing.

---

## **7. Talking Avatar Integration**

Bloop optionally generates a **talking avatar** using SadTalker:

* Final video audio is extracted
* Audio + avatar image sent to SadTalker
* Avatar video is rendered asynchronously
* Final output combines:

  * Left: Educational animation
  * Right: Talking avatar

This avoids visual occlusion and preserves instructional clarity.

---

## **8. Side-by-Side Video Composition**

Instead of picture-in-picture overlays, Bloop uses **horizontal concatenation**:

```
┌───────────────────────┬───────────────────────┐
│  Manim Animation      │  Talking Avatar        │
│  (Concept Visuals)    │  (Narration)           │
└───────────────────────┴───────────────────────┘
```

This layout maintains both:

* Visual explanation fidelity
* Human-like delivery presence

---

## **9. Fault Tolerance & Reliability**

Bloop is designed with **failure as a first-class consideration**:

* Scene-level isolation
* Partial video delivery
* Graceful degradation
* No pipeline-wide crashes
* Deterministic outputs under retries

---

## **10. Implementation Stack**
```

| Component        | Technology         |
| ---------------- | ------------------ |
| Backend API      | FastAPI            |
| LLM              | GPT / Azure OpenAI |
| Animation        | Manim Community    |
| TTS              | Neural TTS         |
| Video Processing | FFmpeg             |
| Avatar           | SadTalker          |
| Orchestration    | Python subprocess  |
| Rendering        | On-demand          |
```
---

## **11. Experimental Results**

During hackathon evaluation, Bloop successfully generated:

* Multi-scene STEM explainer videos
* Real-time Manim animations
* Fully synchronized narration
* Side-by-side avatar videos

Judges highlighted **system depth, integration complexity, and robustness**.

---

## **12. Limitations**

* Rendering time increases with scene complexity
* GPU acceleration not yet applied to Manim
* Avatar generation latency depends on SadTalker model

---

## **13. Future Work**

* Adaptive pacing based on learner profile
* Emotion-aware avatar narration
* Interactive timelines
* Classroom-scale batch rendering
* Cloud-native job scheduling

---

## **14. Conclusion**

Bloop demonstrates that **real-time, fully visual educational video generation** is feasible using current generative AI systems when combined with disciplined system design.

By treating visuals, audio, and avatars as first-class outputs—and by embracing fault tolerance—Bloop moves beyond text-based education toward **explainable, visual intelligence**.

---

# 🎞️ Demo & GIF Previews

> Replace these placeholders with actual GIFs once uploaded.

### 🧮 Manim Animation Generation

![Manim Animation Demo](assets/gifs/manim_generation.gif)

### 🔊 Scene-Aligned Narration

![TTS Sync Demo](assets/gifs/tts_sync.gif)

### 🤖 Talking Avatar (SadTalker)

![Avatar Demo](assets/gifs/avatar_generation.gif)

### 🧩 Final Side-by-Side Video

![Final Video Demo](assets/gifs/final_output.gif)

---

## 🏆 Hackathon Recognition

> *“One of the most technically complete real-time AI pipelines we’ve seen. Exceptional integration of Manim and avatar-based explanation.”*

---
